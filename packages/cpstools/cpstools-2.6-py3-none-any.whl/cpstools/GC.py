import argparse
import os
import sys
from cpstools.IR import identify_regions, find_repeat_regions
import re
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


def parse_file(input_file):
    file_type = ''
    if input_file.endswith(".gb") or input_file.endswith(".gbk") or input_file.endswith(".gbf"):
        file_type = "genbank"
    elif input_file.endswith(".fasta") or input_file.endswith(".fa"):
        file_type = "fasta"
    else:
        raise ValueError("Please provide a file in genbank or fasta format.")

    for rec in SeqIO.parse(input_file, file_type):
        if rec.seq:
            return rec.seq
        else:
            raise ValueError("Please provide a file in genbank or fasta format.")


def GC_calculate(my_seq):
    my_seq = my_seq.upper()
    GC_ratio = round((my_seq.count('G')  + my_seq.count('C')) / len(my_seq) * 100, 2)
    return GC_ratio


def parse_regions(region_line):
    region_dict = {}
    # 拆分为 LSC:xxx IRb:xxx ...
    for item in region_line.strip().split():
        region_name, coords = item.split(":")
        ranges = []
        # 支持逗号分隔多个区段
        for part in coords.split(","):
            start, end = map(int, part.split("-"))
            # 转为 0-based Python 区间
            ranges.append((start - 1, end))
        region_dict[region_name] = ranges
    return region_dict


def gc_calculate(args):
    seq = parse_file(args.input_file)
    if seq is None:
        raise ValueError("Sequence could not be parsed from input file.")

    region_string = find_repeat_regions(str(seq))
    regions = parse_regions(region_string)

    result = {}
    for name, ranges in regions.items():
        region_seq = "".join([str(seq[start:end]) for start, end in ranges])
        gc = GC_calculate(region_seq)
        result[name] = {
            "GC": gc,
            "Length": len(region_seq)
        }

    for key, values in result.items():
        print(key, values)

def main():
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument("-i", "--input_file", required=True,
                        help="Input GenBank/fasta format file")
    args = parser.parse_args()

    try:
        result = gc_calculate(args.input_file)
        for region, info in result.items():
            print(f"{region}: GC={info['GC']}%, Length={info['Length']}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

