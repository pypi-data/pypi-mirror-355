import os
import pandas as pd


def export_defense_finder_systems(defense_finder_genes, outdir, filename):
    systems = build_defense_finder_systems(defense_finder_genes)
    systems.to_csv(os.path.join(outdir, filename + '_defense_finder_systems.tsv'), sep='\t', index=False)


def build_defense_finder_systems(defense_finder_genes):
    if defense_finder_genes.empty is False:
        out = defense_finder_genes.groupby(['sys_id', 'type', 'subtype', 'activity'])[['hit_id', 'hit_pos']].apply(lambda x: ",".join(x.sort_values('hit_pos').hit_id.to_list())).reset_index()
        out.columns = ['sys_id', 'type', 'subtype', 'activity', 'protein_in_syst']
        out['sys_beg'] = out.protein_in_syst.map(lambda x: x.split(",")[0])
        out['sys_end'] = out.protein_in_syst.map(lambda x: x.split(",")[-1])
        genes_count = defense_finder_genes.sys_id.value_counts().reset_index()
        genes_count.columns = ['sys_id', 'genes_count']
        out = out.merge(genes_count, on='sys_id')

        name_of_profiles_in_sys = defense_finder_genes.groupby('sys_id').gene_name.apply(lambda x: ",".join(x.sort_values())).reset_index().rename({'gene_name': 'name_of_profiles_in_sys'}, axis=1)
        out = out.merge(name_of_profiles_in_sys, on='sys_id')
        # Reorder by hit_pos
        out = out.merge(defense_finder_genes[['hit_id', 'hit_pos']], left_on='sys_beg', right_on='hit_id').sort_values('hit_pos').reset_index(drop=True)
        out = out.drop(columns=['hit_id', 'hit_pos'])
    else:
        out = pd.DataFrame(columns=['sys_id', 'type', 'subtype', 'activity', 'sys_beg', 'sys_end', 'protein_in_syst', 'genes_count', 'name_of_profiles_in_sys'])

    return out[['sys_id', 'type', 'subtype', 'activity', 'sys_beg', 'sys_end', 'protein_in_syst', 'genes_count', 'name_of_profiles_in_sys']]
