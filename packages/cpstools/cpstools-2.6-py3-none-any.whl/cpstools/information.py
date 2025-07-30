import argparse
import os
from Bio import SeqIO

class CustomHelpFormatter(argparse.HelpFormatter):
    def format_help(self):
        base_help = super().format_help()
        description = """
        To get information and intron numbers from genbank files.
        Author: Xu wenbo
        Org:    China Pharmaceutical University
        Email:  xwb7533@163.com"""
        return f"{description}\n\n{base_help}"

def initialize_gene_categories():
    return {
        'subunits_photosystem_i': {},
        'subunits_photosystem_ii': {},
        'subunits_nadh_dehydrogenase': {},
        'subunits_cytochrome_bf_complex': {},
        'large_subunit_rubisco': {},
        'subunits_reductase': {},
        'subunits_rna_polymerase': {},
        'proteins_large_ribosomal': {},
        'proteins_small_ribosomal': {},
        'subunits_atp_synthase': {},
        'maturase': {},
        'protease': {},
        'Conserved_open_reading_frames': {},
        'orfs': {},
        'trna_genes': {},
        'rrna_genes': {},
        'envelope_membrane_proteins': {},
        'acetyl_coa': {},
        'translation_factors': {},
        'cytochrome_synthesis': {},
        'others': {}
    }

GENE_CATEGORY_MAP = [
    ('psa', 'subunits_photosystem_i'),
    ('psb', 'subunits_photosystem_ii'),
    ('ndh', 'subunits_nadh_dehydrogenase'),
    ('pet', 'subunits_cytochrome_bf_complex'),
    ('rbcl', 'large_subunit_rubisco'),
    ('rpo', 'subunits_rna_polymerase'),
    ('rpl', 'proteins_large_ribosomal'),
    ('rps', 'proteins_small_ribosomal'),
    ('atp', 'subunits_atp_synthase'),
    ('matk', 'maturase'),
    ('clpp', 'protease'),
    ('ycf', 'Conserved_open_reading_frames'),
    ('orf', 'orfs'),
    ('trn', 'trna_genes'),
    ('rrn', 'rrna_genes'),
    ('ch', 'subunits_reductase'),
    ('cem', 'envelope_membrane_proteins'),
    ('acc', 'acetyl_coa'),
    ('ccs', 'cytochrome_synthesis'),
    ('inf', 'translation_factors')
]

def categorize_gene(gene_name, categories):
    gene_lower = gene_name.lower()
    for prefix, category in GENE_CATEGORY_MAP:
        if gene_lower.startswith(prefix):
            categories[category][gene_name] = categories[category].get(gene_name, 0) + 1
            return
    categories['others'][gene_name] = categories['others'].get(gene_name, 0) + 1

def information_table(input_file, output_file):
    categories = initialize_gene_categories()
    intron_stats = get_intron_stats(input_file)  # 获取内含子统计信息
    total_genes = 0  # 用于统计所有基因的总数

    for record in SeqIO.parse(input_file, 'genbank'):
        for feature in record.features:
            if feature.type == 'gene':
                if 'gene' not in feature.qualifiers:
                    continue
                gene_name = feature.qualifiers['gene'][0]
                categorize_gene(gene_name, categories)

    with open(output_file, 'w') as f:
        # 写入表头
        f.write("Category\tGene Group\tGene Name\tNumber\n")
        
        # 写入分类信息并统计基因数量
        total_genes += write_category(f, "Photosynthesis", "Subunits of photosystem I", 
                                    categories['subunits_photosystem_i'], intron_stats)
        total_genes += write_category(f, " ", "Subunits of photosystem II", 
                                    categories['subunits_photosystem_ii'], intron_stats)
        total_genes += write_category(f, " ", "Subunits of NADH dehydrogenase", 
                                    categories['subunits_nadh_dehydrogenase'], intron_stats)
        total_genes += write_category(f, " ", "Subunits of cytochrome b/f complex", 
                                    categories['subunits_cytochrome_bf_complex'], intron_stats)
        total_genes += write_category(f, " ", "Large subunit of rubisco", 
                                    categories['large_subunit_rubisco'], intron_stats)
        total_genes += write_category(f, " ", "Subunits of ATP synthase", 
                                    categories['subunits_atp_synthase'], intron_stats)
        total_genes += write_category(f, " ", "Subunits photochlorophyllide reductase", 
                                    categories['subunits_reductase'], intron_stats)

        # Self-replication
        total_genes += write_category(f, "Self-replication", "Proteins of large ribosomal subunit", 
                                    categories['proteins_large_ribosomal'], intron_stats)
        total_genes += write_category(f, " ", "Proteins of small ribosomal subunit", 
                                    categories['proteins_small_ribosomal'], intron_stats)
        total_genes += write_category(f, " ", "Subunits of RNA polymerase", 
                                    categories['subunits_rna_polymerase'], intron_stats)
        total_genes += write_category(f, " ", "Ribosomal RNAs", 
                                    categories['rrna_genes'], intron_stats)
        total_genes += write_category(f, " ", "Transfer RNAs", 
                                    categories['trna_genes'], intron_stats)

        # Other genes
        total_genes += write_category(f, "Other genes", "Maturase", 
                                    categories['maturase'], intron_stats)
        total_genes += write_category(f, " ", "Protease", 
                                    categories['protease'], intron_stats)
        total_genes += write_category(f, " ", "Envelope membrane protein", 
                                    categories['envelope_membrane_proteins'], intron_stats)
        total_genes += write_category(f, " ", "Acetyl-CoA carboxylase", 
                                    categories['acetyl_coa'], intron_stats)
        total_genes += write_category(f, " ", "c-type cytochrome synthesis gene", 
                                    categories['cytochrome_synthesis'], intron_stats)
        total_genes += write_category(f, " ", "Translation initiation factor", 
                                    categories['translation_factors'], intron_stats)
        total_genes += write_category(f, " ", "Conserved open reading frames", 
                                    categories['Conserved_open_reading_frames'], intron_stats)
        total_genes += write_category(f, " ", "ORFs", 
                                    categories['orfs'], intron_stats)
        total_genes += write_category(f, " ", "Other", 
                                    categories['others'], intron_stats)

        # 写入总计行
        f.write(f"Total\t\t\t{total_genes}\n")
        f.write("#: Intron number, (n): Gene copy number")

def write_category(output_handle, main_category, sub_category, genes, intron_stats):
    """写入分类信息，并添加内含子统计和基因数量"""
    if not genes:
        return 0  # 如果没有基因，返回 0

    gene_list = []
    gene_count = 0  # 统计当前分类的基因数量
    for gene_name, count in genes.items():
        # 添加基因名称和重复次数
        gene_entry = gene_name
        if count > 1:
            gene_entry += f"({count})"
        # 添加内含子统计
        if gene_name in intron_stats:
            intron_count = intron_stats[gene_name]
            if intron_count > 0:
                gene_entry += "#" * intron_count
        gene_list.append(gene_entry)
        gene_count += count  # 累加基因数量

    # 写入当前分类的信息
    output_handle.write(f"{main_category}\t{sub_category}\t{', '.join(gene_list)}\t{gene_count}\n")
    return gene_count  # 返回当前分类的基因数量

def get_intron_stats(input_file):
    """获取内含子统计信息"""
    intron_stats = {}
    for record in SeqIO.parse(input_file, 'genbank'):
        for feature in record.features:
            if feature.type in ['CDS', 'tRNA', 'rRNA'] and 'gene' in feature.qualifiers:
                gene_name = feature.qualifiers['gene'][0]
                exon_count = len(feature.location.parts)
                intron_count = exon_count - 1  # 内含子数量 = 外显子数量 - 1
                if gene_name not in intron_stats or intron_count > intron_stats[gene_name]:
                    intron_stats[gene_name] = intron_count
    return intron_stats



def intron_find(input_file):
    intron_stats = {'two_exons': set(), 'three_exons': set(), 'more_exons': set()}
    
    for record in SeqIO.parse(input_file, 'genbank'):
        for feature in record.features:
            if feature.type in ['CDS', 'tRNA', 'rRNA'] and 'gene' in feature.qualifiers:
                exon_count = len(feature.location.parts)
                gene_name = feature.qualifiers['gene'][0]
                if exon_count == 2:
                    intron_stats['two_exons'].add(gene_name)
                elif exon_count == 3:
                    intron_stats['three_exons'].add(gene_name)
                elif exon_count > 3:
                    intron_stats['more_exons'].add(gene_name)

    print("Intron statistics:")
    for category, genes in intron_stats.items():
        if genes:
            print(f"{category.replace('_', ' ').title()}: {', '.join(sorted(genes))}")

def information(args):
    if args.input_file.endswith('gb') or args.input_file.endswith('gbk'):
        input_file_path = os.path.abspath(args.input_file)
        output_file_path = input_file_path.split('.')[0] + '.tsv'
        information_table(args.input_file, output_file_path)
        intron_find(args.input_file)
        # abs_path = os.path.abspath(args.output_file)
        print(f"The statistic results has been saved into {output_file_path}")
    else:
        print(f"please input genbank format files and endwith 'gb' or 'gbk'! ")

def main():
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument("-i", "--input_file", required=True,
                        help="Input GenBank file (.gb or .gbk)")
    args = parser.parse_args()

    if not args.input_file.lower().endswith(('.gb', '.gbk')):
        print("Error: Input file must be in GenBank format (.gb or .gbk)")
        return

    output_file = os.path.splitext(args.input_file)[0] + '_analysis.tsv'
    
    try:
        information_table(args.input_file, output_file)
        intron_find(args.input_file)
        print(f"Analysis complete. Results saved to: {os.path.abspath(output_file)}")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()