import os
import shutil
import click
import defense_finder
import defense_finder_posttreat
from pyhmmer.easel import SequenceFile, TextSequence, Alphabet
import pyrodigal
import sys

from warnings import simplefilter, catch_warnings

with catch_warnings():
    simplefilter("ignore")
    import defense_finder_updater

from macsypy.scripts.macsydata import get_version_message
from macsypy.scripts.macsydata import _find_all_installed_packages
from macsypy.scripts.macsydata import RemoteModelIndex
import datetime

import colorlog
try:
    logging = colorlog.logging.logging
except AttributeError:
    logging = colorlog.wrappers.logging


def check_last_version_models():
    file_lastver = os.path.join(os.environ["HOME"], ".defensefinder_model_lastversion")
    if os.path.isfile(file_lastver):
        with open(file_lastver, "r") as file_lastver_file:
            time_last_ver, last_version = file_lastver_file.read().split("___")
            time_last_ver = datetime.datetime.strptime(time_last_ver, '%Y-%m-%d')
    else:
        time_last_ver = datetime.datetime(1000, 1, 1)

    now = datetime.datetime.now()

    if time_last_ver < now - datetime.timedelta(days = 30):
        remote = RemoteModelIndex(org="mdmparis")
        packages = remote.list_packages()
        dfmods = [pack for pack in packages if pack == "defense-finder-models"][0]
        all_versions = remote.list_package_vers(dfmods)
        last_version = all_versions[0]
        with open(file_lastver, "w") as file_lastver_file:
            file_lastver_file.write(f"{now.strftime('%Y-%m-%d')}___{last_version}")

    return last_version

@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def cli():
    """Systematic search of all known anti-phage systems by MDM Labs, Paris.

    Prior to using defense-finder:

    - install hmmsearch: http://hmmer.org/documentation.html

    - get the models (run this every so often to stay up to date):

        $ defense-finder update

    Tool repository: https://github.com/mdmparis/defense-finder.
    """
    pass

@cli.command()
def version():
    """Get the version of DefenseFinder (software)
    """
    print(f"Using DefenseFinder version {__version__}")


@cli.command()
@click.option('--models-dir', 'models_dir', required=False, help='Specify a directory containing your models.')
@click.option('--force-reinstall', '-f', 'force_reinstall', is_flag=True,
              help='Force update even if models in already there.', default=False)
def update(models_dir=None, force_reinstall: bool = False):
    """Fetches the latest defense finder models.

    The models will be downloaded from mdmparis repositories and installed on macsydata.

    This will make them available to macsyfinder and ultimately to defense-finder.

    Models repository: https://github.com/mdmparis/defense-finder-models.
    """
    defense_finder_updater.update_models(models_dir, force_reinstall)




@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('-o', '--out-dir', 'outdir',
              help='The target directory where to store the results. Defaults to the current directory.')
@click.option('-w', '--workers', 'workers', default=0,
              help='The workers count. By default all cores will be used (w=0).')
@click.option('-c', '--coverage', 'coverage', default=0.4,
              help='Minimal percentage of coverage for each profiles. By default set to 0.4')
@click.option('--db-type', 'dbtype', default='ordered_replicon',
              help='The macsyfinder --db-type option. Run macsyfinder --help for more details. Possible values are\
               ordered_replicon, gembase, unordered, defaults to ordered_replicon.')
@click.option('--preserve-raw', 'preserve_raw', is_flag=True, default=False,
              help='Preserve raw MacsyFinder outputs alongside Defense Finder results inside the output directory.')
@click.option('--models-dir', 'models_dir', required=False, help='Specify a directory containing your models.')
@click.option('--no-cut-ga', 'no_cut_ga', is_flag=True, default=False,
              help='Advanced! Run macsyfinder in no-cut-ga mode. The validity of the genes and systems found is not guaranteed!')
@click.option('-a','--antidefensefinder', 'adf', is_flag=True, default=False,
              help='Also run AntiDefenseFinder models to find antidefense systems.')
@click.option("-A",'--antidefensefinder-only', 'adf_only', is_flag=True, default=False,
              help='Run only AntiDefenseFinder for antidefense system and not DefenseFinder')
@click.option('--log-level', 'loglevel', default="INFO",
              help='set the logging level among DEBUG, [INFO], WARNING, ERROR, CRITICAL')
@click.option('--index-dir', 'index_dir', required=False, help='Specify a directory to write the index files required by macsyfinder when the input file is in a read-only folder')
@click.option('--skip-model-version-check', is_flag=True, default=False,
              help='Skip model version check')

def run(file: str, outdir: str, dbtype: str, workers: int, coverage: float, preserve_raw: bool, adf: bool,
        adf_only: bool, no_cut_ga: bool, models_dir: str = None, loglevel : str = "INFO",
        index_dir: str = None, skip_model_version_check: bool = False):
    """
    Search for all known anti-phage defense systems in the target fasta file.
    """
    global logger
    LOGFORMAT = " %(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    #logging.root.setLevel(LOG_LEVEL)
    formatter = colorlog.ColoredFormatter(LOGFORMAT, datefmt='%Y-%m-%d %H:%M:%S')

    stream = logging.StreamHandler()
    stream.setLevel(loglevel)
    stream.setFormatter(formatter)
    logger = colorlog.getLogger("Defense_Finder")
    logger.setLevel(loglevel)
    logger.addHandler(stream)
       
    filename = click.format_filename(file)
    # Prepare output folder

    logger.info(f"Received file {filename}")

    default_outdir = os.getcwd()
    logger.debug(f"Defaut outdir : {default_outdir}")
    outdir = outdir if outdir != None else default_outdir
    if not os.path.isabs(outdir):
        outdir = os.path.join(os.getcwd(), outdir)
    logger.debug(f"outdir : {outdir}")

    if os.path.exists(outdir):
        logger.warning(f"Out directory {outdir} already exists. Existing DefenseFinder output will be overwritten")
    os.makedirs(outdir, exist_ok=True)

    tmp_dir = os.path.join(outdir, 'defense-finder-tmp')
    if os.path.exists(tmp_dir):
        logger.warning(f"Temporary directory {tmp_dir} already exists. Overwriting it.")
        shutil.rmtree(tmp_dir)

    os.makedirs(tmp_dir)

    with SequenceFile(filename) as sf:
        seq = TextSequence()
        dic_genes = {}
        if sf.guess_alphabet() == Alphabet.dna():
            logger.info(f"{filename} is a nucleotide fasta file. Prodigal will annotate the CDS")
            while sf.readinto(seq) is not None: # iterate over sequences in case multifasta
                sseq = bytes(seq.sequence, encoding="utf-8")
                sname = seq.name.decode()
                if len(sseq) < 100000: # it is recommended to use the mode meta when seq is less than 100kb
                    orf_finder = pyrodigal.GeneFinder(meta=True)
                    dic_genes[sname] = orf_finder.find_genes(sseq)
                else:
                    orf_finder = pyrodigal.GeneFinder()
                    orf_finder.train(sseq)
                    dic_genes[sname] = orf_finder.find_genes(sseq)
                seq.clear()

            protein_file_name = os.path.join(outdir, f"{os.path.splitext(os.path.basename(filename))[0]}.prt")

            if os.path.exists(protein_file_name):
                logger.warning(f"{protein_file_name} already exists, writing in {protein_file_name + '_defensefinder.prt'} -- Overwriting it if already existing")
                protein_file_name += "_defensefinder.prt"
            logger.info(f"Prodigal annotated {len(dic_genes.keys())} replicons")
            with open(protein_file_name, "w") as protein_file:
                for key, genes in dic_genes.items():
                    # proteins will be like `> contig_name_i` with i being increasing integer 
                    genes.write_translations(protein_file, key)
            # prodigal correctly numbered the protein in a gembase like format (cf above)
            dbtype = "gembase"
            logger.info(f"Protein files written in {protein_file_name}")
            logger.info(f"{sum([len(v) for v in dic_genes.values()])} CDS were annotated")

        else:
            protein_file_name = filename
    versions_models = []

    models = _find_all_installed_packages(models_dir=models_dir).models()
    modelok = False
    for m in models:
        if "casfinder" in m.path.lower() or "defense-finder-models" in m.path.lower():
            versions_models.append([m.path, m.version])
            if ("defense-finder" in m.path.lower()):
                models_main_ver = int(m.version.split(".")[0])
                if skip_model_version_check:
                    logger.warning(f"Be careful, the model's version was not checked!'")
                else:
                    last_version_df = check_last_version_models()
                    if m.version != last_version_df.strip():
                        logger.warning(f"Be careful, this is not the latest version of the model, last version = {last_version_df}")
                        logger.warning(">>> Run `defense-finder update` to be up to date")
                    else:
                        logger.info(f"Awesome, you are using the last version of the defense-finder-models : {last_version_df}")                    

    if len(versions_models) != 2:
        logger.error(f"Uncomplete defense-finder models, we found only {' '.join([vm[0] for vm in versions_models])}. Cas and defense-finder models are required")
        logger.error(f">>> Run `defense-finder update` to download the models")
        sys.exit(1)

    logger.info(f"Running DefenseFinder version {__version__}")
    nl = '\n'
    tab = "\t"

    logger.info(f"""Using the following models:

{nl.join([f"{path+tab+version}" for path, version in versions_models])}
""")

    defense_finder.run(protein_file_name, dbtype, workers, coverage, adf,adf_only, tmp_dir, models_dir, no_cut_ga, loglevel, index_dir, models_main_ver)
    logger.info("Post-treatment of the data")
    defense_finder_posttreat.run(tmp_dir, outdir, os.path.splitext(os.path.basename(filename))[0])

    if not preserve_raw:
        shutil.rmtree(tmp_dir)



    nl = "\n"
    tab = "\t"

    logger.info(f"""\
Analysis done. Please cite :

Tesson F., Hervé A. , Mordret E., Touchon M., d’Humières C., Cury J., Bernheim A., 2022, Nature Communication
Systematic and quantitative view of the antiviral arsenal of prokaryotes

Using DefenseFinder version {__version__}.

DefenseFinder relies on MacSyFinder : 

{get_version_message().split("and don't")[0]}

Using the following models:

{nl.join([f"{path+tab+version}" for path, version in versions_models])}
""")

if __name__ == "__main__":
    __version__ = "Version_from_the_command_line"
    cli()
else:
    from ._version import __version__
