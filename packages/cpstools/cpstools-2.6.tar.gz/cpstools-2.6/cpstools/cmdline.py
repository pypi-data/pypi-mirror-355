import argparse
from cpstools.IR import identify_regions
from cpstools.LSR_annotation import lsr_annotate
from cpstools.Pi_combine import calculate_pi
from cpstools.RSCU import get_rscu
from cpstools.SSRS_annotation import identify_ssr
from cpstools.converse import converse_format
from cpstools.gbcheck import gbcheck
from cpstools.information import information
from cpstools.phy_built import built_phy
from cpstools.seq_adj import seq_adj
from cpstools.KaKs import KaKs_cal
from cpstools.extract import Extract
from cpstools.GC import gc_calculate
from cpstools.depth import depth_plot


def main():
    parser = argparse.ArgumentParser(
        description="""
        CPStools command line tool
        Author: Xu Wenbo
        Org:    China Pharmaceutical University --> CACMS
        Email:  xwb7533@163.com
        Cite: CPStools: A package for analyzing chloroplast genome sequences
        Doi:  10.1002/imo2.25 
        QQ group: 398014377""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    # Add a version argument
    parser.add_argument('-v', '--version', action='version', version='CPStools version 2.6',
                        help="Show program's version number and exit")

    subparsers = parser.add_subparsers(title="sub-commands", help='sub-command help')

    # 添加子命令
    gbcheck_parser = subparsers.add_parser('gbcheck',
                                           help='Check annotated file and Compare gene counts and difference in two GenBank files.')
    gbcheck_parser.add_argument('-r', '--ref_file', help='reference GenBank file')
    gbcheck_parser.add_argument('-i', '--test_file', help='testing GenBank file', required=True)
    gbcheck_parser.set_defaults(func=gbcheck)

    info_parser = subparsers.add_parser('info', help='Statistic gene type and intron numbers from genbank files.')
    info_parser.add_argument("-i", "--input_file", help="Input genbank format file", required=True)
    # info_parser.add_argument("-o", "--output_file", help="output file ")
    info_parser.set_defaults(func=information)

    seq_parser = subparsers.add_parser('Seq', help='Adjust the Seq start in chloroplast genomes.')
    seq_parser.add_argument("-d", "--work_dir", help="Input directory of fasta files", required=True)
    # seq_parser.add_argument("-o", "--save_dir", help="Output directory for save files")
    seq_parser.add_argument("-f", "--info_file", help="file of the information of the fasta file four regions",
                            required=True)
    seq_parser.add_argument("-m", "--mode", choices=['SSC', 'LSC', 'RP'],
                            help="Mode: SSC for adjust_SSC_forward, LSC for adjust_start_to_LSC, RP for adjust sequence to reverse_complement")
    seq_parser.set_defaults(func=seq_adj)

    ir_parser = subparsers.add_parser('IR', help='Identify four regions in chloroplast genomes.')
    ir_parser.add_argument('-i', '--input_file', help='fasta/GenBank format file', required=True)
    ir_parser.set_defaults(func=identify_regions)

    pi_parser = subparsers.add_parser('Pi', help='Calculate Pi valus from Genbank files and sort as cp order.')
    pi_parser.add_argument("-d", "--work_dir", required=True, help="Input directory of genbank files")
    pi_parser.add_argument("-m", "--mafft_path", help="Path to MAFFT executable if not in environment path")
    pi_parser.set_defaults(func=calculate_pi)

    rscu_parser = subparsers.add_parser('RSCU', help='Get RSCU values from genbank files.')
    rscu_parser.add_argument("-d", "--work_dir", help="Input directory of genbank files", required=True)
    rscu_parser.add_argument('-l', '--filter_length', help='CDS filter length, default is 300', type=int)
    rscu_parser.set_defaults(func=get_rscu)

    ssr_parser = subparsers.add_parser('SSRs', help='Identify SSRs in chloroplast genomes and mark their types.')
    ssr_parser.add_argument('-i', '--input_file', help='GenBank format file', required=True)
    ssr_parser.add_argument('-k', '--kmer_length', help='SSRs length, default is 10,6,5,4,4,4')
    ssr_parser.set_defaults(func=identify_ssr)

    converse_parser = subparsers.add_parser('convert',
                                            help='Convert genbank format files to fasta/tbl/mVISTA format.')
    converse_parser.add_argument("-d", "--input_dir", help="Input path of genbank file", required=True)
    converse_parser.add_argument("-m", "--mode", choices=['fasta', 'mVISTA', 'tbl'],
                                 help="Mode: fasta for converse genbank format file into fasta format file;\n"
                                      "mVISTA for converse genbank format file into mVISTA format file;\n"
                                      "tbl for converse genbank format file into tbl format file", required=True)
    converse_parser.set_defaults(func=converse_format)

    lsr_parser = subparsers.add_parser('LSRs', help='Annotate LSRs in chloroplast genomes.')
    lsr_parser.add_argument('-i', '--input_file', help='GenBank format file', required=True)
    lsr_parser.set_defaults(func=lsr_annotate)

    phy_parser = subparsers.add_parser('phy',
                                       help='Extract and sort common cds/protein sequences for phylogenetic analysis from multi-gbfiles.')
    phy_parser.add_argument("-d", "--input_dir", help="Input the directory of genbank files", required=True)
    phy_parser.add_argument("-m", "--mode", choices=['cds', 'pro'],
                            help="Mode: cds for common cds sequences; pro for common protein sequences", required=True)
    phy_parser.set_defaults(func=built_phy)

    KaKs_parser = subparsers.add_parser('KaKs',
                                       help='Calculate KaKs value from Genbank files.')
    KaKs_parser.add_argument("-i", "--input_reference", help="Input path of reference genbank file", required=True)
    KaKs_parser.add_argument("-m", "--mode", help="KaKs calculator mode")
    KaKs_parser.set_defaults(func=KaKs_cal)

    exc_parser = subparsers.add_parser('exc',
                                       help='Extract gene sequences for chloroplast annotation.')
    exc_parser.add_argument("-i", "--input_file", help="Input path of reference genbank file", required=True)
    exc_parser.add_argument("-r", "--ref_file", help="Input path of reference genbank file", required=True)
    exc_parser.add_argument("-n", "--gene_name", help="Input path of reference genbank file", required=True)
    exc_parser.set_defaults(func=Extract)

    # GC
    gc_parser = subparsers.add_parser('GC',
                                      help='Calculate GC value from Genbank/Fasta file.')
    gc_parser.add_argument("-i", "--input_file", help="Input path of genbank/fasta format file", required=True)
    gc_parser.set_defaults(func=gc_calculate)
    # depth
    depth_parser = subparsers.add_parser('depth',
                                      help='Statistic depth of chloroplast genome sequence.')
    depth_parser.add_argument("-i", "--input_fasta", required=True, help="Input/reference fasta file")
    depth_parser.add_argument("-1", "--p1", required=True, help="Paired-End fastq file1")
    depth_parser.add_argument("-2", "--p2", required=True, help="Paired-End fastq file2")
    depth_parser.add_argument("-o", "--output", default=None, help="Output directory (default: same as --p1)")
    depth_parser.add_argument("-t", "--threads", type=int, default=10, help="Threads (default: 10)")
    depth_parser.add_argument("-b", "--block_size", type=int, default=2000, help="Block size (default: 2000)")
    depth_parser.set_defaults(func=depth_plot)



    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
