from pathlib import Path
import shutil
import pandas as pd
from Bio import SeqIO

def copy_files(input_files, params):
    shutil.copy(input_files['genome'], params['genomes'])
    shutil.copy(input_files['gbk'], params['gbks'])
    shutil.copy(input_files['plot'], params['plots'])

def count_hypothetical_proteins(params):
    count = 0
    for record in SeqIO.parse(input_files['gbk'], "genbank"):
        for feature in record.features:
            if feature.type == "CDS":
                if "product" in feature.qualifiers:
                    if "hypothetical protein" in feature.qualifiers["product"]:
                        count += 1
    return count

def generate_summary(input_files, output_summary, params):
    copy_files(input_files, params)
    with open(output_summary, 'w') as summary:
        summary.write(f"Sample: {params['sample']}\n")
        if Path(input_files['genome']).exists():            
                with open(input_files['taxa'], 'r') as taxa_file:
                    tax = pd.read_csv(taxa_file, sep='\t')
                    summary.write("Taxa name (Matching hashes):\t")
                    for index, row in tax.iterrows():
                        summary.write(f"{row['Description']}\t{row['mash_matching_hashes']}\n")

                with open(input_files['cds'], 'r') as cds:
                    cds_df=pd.read_csv(cds, sep='\t')
                    cds_data = cds_df[cds_df['Description'] == 'CDS']
                    count_value = cds_data['Count'].values[0]
                    summary.write(f"Number of CDS: {count_value}\n")
                
                hypothetical_protein_count = count_hypothetical_proteins(params)
                summary.write(f"Total number of CDS annotated as 'hypothetical protein': {hypothetical_protein_count}\n")

                with open(input_files['cdden'], 'r') as cdden:
                    cdn=pd.read_csv(cdden, sep='\t')
                    gc_percent = cdn['gc_perc'].values[0]
                    coding_density = cdn['cds_coding_density'].values[0]
                    summary.write(f"GC percent: {gc_percent}\n")
                    summary.write(f"Coding density: {coding_density}\n")

                found_gene = False
                gbk_records = SeqIO.parse(input_files['gbk'], 'genbank')
                for record in gbk_records:
                    for feature in record.features:
                        if feature.type == "CDS" and 'product' in feature.qualifiers and 'integra' in feature.qualifiers['product'][0].lower():
                            #print (feature)
                            found_gene = True
                            gene_id = feature.qualifiers['locus_tag'][0]
                            function = feature.qualifiers['function'][0]
                            product = feature.qualifiers['product'][0]
                            summary.write(f"\t{gene_id}: function=\"{function}\", product=\"{product}\"\n")

                if not found_gene:
                    if 'integra' not in open(input_files['gbk']).read().lower():
                        summary.write("No Integrases\n")
                    else:
                        summary.write("No Integrases\n")
                        summary.write("\t...but Phynteny predicted a few unknown function genes to have some similarity with integrase genes but with low confidence. Maybe a false positive or a novel integrase gene\n")

                    if 'recombinase' not in open(input_files['gbk']).read().lower():
                        summary.write("No recombinase\n")
                    else: 
                        summary.write("Recombinases found in genome\n")
                    if 'transposase' not in open(input_files['gbk']).read().lower():
                        summary.write("No transposase\n")
                    else: 
                        summary.write("Transposases found in genome\n")
                #AMR genes 
                if (len(open(input_files['amr']).readlines()) == 1) and (len(open(input_files['card']).readlines()) == 0):
                    summary.write("No AMR genes found\n")
                else:
                    summary.write("AMR genes found\n")                

                #Virulence genes 
                if (len(open(input_files['vfdb']).readlines()) == 1) and (len(open(input_files['vfdb_phold']).readlines()) == 0):
                    summary.write("No virulence factor genes\n")
                else:
                    summary.write("Virulence genes found\n")

                #CRISPR spacers 
                if (len(open(input_files['spacers']).readlines()) == 0) and (len(open(input_files['acr']).readlines()) == 0):
                    summary.write("No CRISPR spacers found\n")
                else:
                    summary.write("CRISPR spacers found\n")
                
                #Defense finder genes  
                if (len(open(input_files['defense']).readlines()) == 0):
                    summary.write("No Defense genes found\n")
                else:
                    summary.write("Defense genes found\n")

# Replace input_files and output_params with the actual paths to your input/output files and parameters
input_files = {
        'genome': snakemake.input.genome,
        'gbk': snakemake.input.gbk,
        'plot': snakemake.input.plot,
        'taxa': snakemake.input.ph_taxa,
        'cdden': snakemake.input.cdden,
        'cds': snakemake.input.cds,
        'amr': snakemake.input.amr,
        'vfdb': snakemake.input.vfdb,
        'spacers': snakemake.input.spacers,
        'acr': snakemake.input.acr,
        'card': snakemake.input.card,
        'defense': snakemake.input.defense,
        'vfdb_phold': snakemake.input.vfdb_phold,
}

output_summary = snakemake.output.summary

params = {
    'sample' : snakemake.params.sample,
    'genomes': snakemake.params.genomes,
    'gbks' : snakemake.params.gbks,
    'plots': snakemake.params.plots
}

generate_summary(input_files, output_summary, params)
