from Bio import SeqIO
from Bio.Seq import Seq
import os
import argparse
import sys



class CustomHelpFormatter(argparse.HelpFormatter):
    def format_help(self):
        help_text = super().format_help()
        description = """Extract gene sequences for chloroplast genome annotation.
        Author: Xu wenbo
        Org:    China Pharmaceutical University
        Email:  xwb7533@163.com"""

        return f"{description}\t\t{help_text}"

def check_files(input_file):
    try:
        if input_file.endswith('.gb') or input_file.endswith('.gbk'):
            for rec in SeqIO.parse(input_file, 'genbank'):
                return True
        raise ValueError(f"Unsupported file format for '{input_file}'. "
                         f"Please use  GenBank (.gb or .gbk) files.")
    except Exception as e:
        if isinstance(e, FileNotFoundError):
            raise  # Reraise the FileNotFoundError
        elif os.path.exists(input_file):
            raise ValueError(f"Error processing file '{input_file}': {e}")
        else:
            raise FileNotFoundError(f"No such file: {input_file}")

def find_(rec, feature, gene_name):
    for i, part in enumerate(feature.location.parts):
        if len(feature.location.parts) > 1:
            if part.strand == -1:
                print(f">{gene_name}_{i + 1}-{part.end-part.start + 1}(-)\n{rec.seq[part.start:part.end].reverse_complement()}")
            if part.strand == 1:
                print(f">{gene_name}_{i + 1}+{part.end-part.start + 1}(+)\n{rec.seq[part.start:part.end]}")
        else:
            if part.strand == -1:
                print(f">{gene_name}(-)")
            if part.strand == 1:
                print(f">{gene_name}(+)")
    print(feature.extract(rec.seq), len(feature.extract(rec.seq)), sep='\n')
    if feature.type == 'CDS':
        print(feature.extract(rec.seq).translate())


def extract_(input_file, gene_name):
    for rec in SeqIO.parse(input_file, 'genbank'):
        for feature in rec.features:
            if feature.type in ['CDS', 'tRNA', 'rRNA']:
                if feature.qualifiers['gene'] and gene_name.lower() == feature.qualifiers['gene'][0].lower():
                    find_(rec, feature, gene_name)

def extract_seq(input_file, ref_file, gene_name):
    # 获取输入文件所在的文件夹路径
    input_folder = os.path.dirname(input_file)
    # 提取input_file中的序列
    extract_(input_file, gene_name)

    # 如果ref_file是一个文件夹，则遍历该文件夹中的所有文件
    if os.path.isdir(ref_file):
        for file_name in os.listdir(ref_file):
            check_files(ref_file + '/' + file_name)
            file_path = os.path.join(ref_file, file_name)
            if os.path.isfile(file_path):
                extract_(file_path, gene_name)
    # 如果ref_file不是文件夹，则直接读取该文件
    elif os.path.isfile(ref_file):
        check_files(ref_file)
        extract_(ref_file, gene_name)



def Extract(args):
    input_file = args.input_file
    ref_file = args.ref_file
    gene_name = args.gene_name
    try:
        result = check_files(input_file)
        if result:
            extract_seq(input_file, ref_file, gene_name)
    except (ValueError, FileNotFoundError) as e:
        print(e)

def main():
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument('-i', '--input_file', help='input Genbank format file', required=True)
    parser.add_argument('-r', '--ref_file', help='ref GenBank format file', required=True)
    parser.add_argument('-n', '--gene_name', help='Name of extracted gene', required=True)
    args = parser.parse_args()
    input_file = args.input_file
    ref_file = args.ref_file
    gene_name = args.gene_name
    try:
        result = check_files(input_file)
        if result:
            extract_seq(input_file, ref_file, gene_name)
    except (ValueError, FileNotFoundError) as e:
        print(e)


if __name__ == '__main__':
    main()
