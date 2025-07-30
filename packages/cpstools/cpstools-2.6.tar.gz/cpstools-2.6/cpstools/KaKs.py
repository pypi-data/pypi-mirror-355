import os
import sys
from Bio import SeqIO
import subprocess
from Bio.Seq import Seq
from Bio.Align import MultipleSeqAlignment
from Bio.SeqRecord import SeqRecord
from Bio import AlignIO
from tqdm import tqdm
import argparse


class CustomHelpFormatter(argparse.HelpFormatter):
    def format_help(self):
        help_text = super().format_help()
        description = """
        Calculate KaKs value from Genbank files.
        Author: Xu wenbo
        Org:    China Pharmaceutical University
        Email:  xwb7533@163.com """
        return f"{description}\n\n{help_text}"



# find kaks_calculator
def find_kaks_calculator():
    # self build kaks

    root = Path(__file__).resolve().parent       # cpstools/ 目录
    exe_name = "KaKs_Calculator.exe" if sys.platform.startswith("win") else "KaKs_Calculator"
    packaged = root / "deps" / exe_name
    if packaged.exists():
        return str(packaged)

    # 2）回落到系统 PATH 查找
    finder = "where" if os.name == "nt" else "which"
    try:
        result = subprocess.run(
            [finder, exe_name],
            capture_output=True, text=True, check=True
        )
        # 可能会返回多行，取第一行
        path = result.stdout.strip().splitlines()[0]
        return path
    except (subprocess.CalledProcessError, IndexError):
        raise KaKs_CalculatorNotFoundError(
            f"既没有在 deps/{exe_name}，也没在系统 PATH 里找到 {exe_name}"
        )

# find mafft
def find_mafft():
    try:
        # 针对不同系统的查找命令
        if os.name == 'nt':  # Windows 系统
            result = subprocess.run(['where', 'mafft'], capture_output=True, text=True, check=True)
        else:  # Unix/Linux 或 macOS 系统
            result = subprocess.run(['which', 'mafft'], capture_output=True, text=True, check=True)

        # 获取命令的输出，移除首尾空格
        mafft_path = result.stdout.strip()

        # 检查是否找到了路径
        if mafft_path:
            return os.path.abspath(mafft_path)
        else:
            raise MafftNotFoundError("MAFFT not found on the system.")
    except subprocess.CalledProcessError:
        # 如果命令失败，表示没有找到 mafft
        raise MafftNotFoundError("MAFFT not found on the system.")



# pro align to nucleotide align
def map_protein_to_nucleotide_alignment(protein_alignment_file, cds_file, output_file):
    protein_alignment = SeqIO.parse(protein_alignment_file, 'fasta')
    protein_dict = {record.id: str(record.seq) for record in protein_alignment}
    cds_sequences = SeqIO.parse(cds_file, 'fasta')
    cds_dict = {record.id: str(record.seq) for record in cds_sequences}
    nucleotide_alignment = []
    for seq_id in protein_dict:
        protein_seq = protein_dict[seq_id]
        cds_seq = cds_dict[seq_id]
        nucleotide_seq = ""
        codon_index = 0
        for aa in protein_seq:
            if aa == "-":
                nucleotide_seq += "---"
            else:
                nucleotide_seq += cds_seq[codon_index:codon_index + 3]
                codon_index += 3
        if len(nucleotide_seq) != len(protein_seq) * 3:
            raise ValueError(f"Mapping error for {seq_id}, lengths do not match.")
        nucleotide_alignment.append(SeqRecord(Seq(nucleotide_seq), id=seq_id, description=""))
    SeqIO.write(MultipleSeqAlignment(nucleotide_alignment), output_file, 'fasta')


# fasta to axt format
def fasta_to_axt(fasta_file, axt_file):
    alignment = AlignIO.read(fasta_file, 'fasta')
    if len(alignment) != 2:
        raise ValueError("The FASTA alignment must contain exactly two sequences for AXT format.")
    seq1 = alignment[0]
    seq2 = alignment[1]
    seq1_id = seq1.id
    seq2_id = seq2.id
    seq1_len = len(seq1.seq)
    seq2_len = len(seq2.seq)
    axt_content = []
    axt_content.append(f"1 {seq1_id} {seq2_id} 1 {seq1_len} 0")
    axt_content.append(str(seq1.seq))
    axt_content.append(str(seq2.seq))
    # 每个比对块之间用一个空行分隔
    axt_content.append("")

    # 将AXT内容写入文件
    with open(axt_file, 'w') as output_handle:
        output_handle.write("\n".join(axt_content))

def is_file_empty(file_path):
    return os.path.exists(file_path) and os.stat(file_path).st_size == 0


# extract common coding gene
def common_cds_extract(input_file, kaks_calculator_path, mode="MLWL"):
    # mafft path
    mafft_path = find_mafft()
    if mafft_path:
        print('-'*40)
        print(f"MAFFT found at: {mafft_path}")
        print('-'*40)
    else:
        print('-'*40)
        print("MAFFT not found in PATH.")
        print('-'*40)
        sys.exit()
    work_dir = os.path.dirname(input_file)
    ref_file = os.path.basename(input_file).split('.')[0]
    all_gene = []
    for rec in SeqIO.parse(input_file, format='genbank'):
        for feature in rec.features:
            if feature.type == 'CDS':
                if feature.qualifiers['gene'][0] not in all_gene:
                    all_gene.append(feature.qualifiers['gene'][0])
    for files in os.listdir(work_dir):
        if files.endswith('gb') or files.endswith('gbk'):
            single_gene = []
            gb_file = os.path.join(work_dir, files)
            for rec in SeqIO.parse(gb_file, format='genbank'):
                for feature in rec.features:
                    if feature.type == 'CDS':
                        if feature.qualifiers['gene'][0] not in single_gene:
                            single_gene.append(feature.qualifiers['gene'][0])
            # delete unigue gene
            for gene_index in range(len(all_gene) - 1, -1, -1):
                if all_gene[gene_index].lower() not in [y.lower() for y in single_gene]:
                    all_gene.remove(all_gene[gene_index])
    print('-'*40)               
    print(f"After filtering, The common gene number is : {len(all_gene)}\n And the genes list is {all_gene}")
    print('-'*40)

    # save directory exist check.
    save_dir = os.path.join(os.path.dirname(work_dir), 'common_gene')
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    else:
        print(f"The directory '{save_dir}' already exists.")
        sys.exit()
    # save common gene sequences
    for gene_name in all_gene:
        file_name = str(gene_name) + '.fasta'
        file_path = os.path.join(save_dir, file_name)
        with open(file_path, 'w') as fasta_file:
            for gb_file in os.listdir(work_dir):
                gb_file_path = os.path.join(work_dir, gb_file)
                fasta_file.write(f">{gb_file.split('.')[0]}\n")
                for rec in SeqIO.parse(gb_file_path, format='genbank'):
                    my_seqs = []
                    for feature in rec.features:
                        if feature.type == 'CDS':
                            if feature.qualifiers['gene'][0].lower() == gene_name.lower():
                                my_seqs.append(feature.extract(rec.seq))
                    if len(my_seqs) == 1:
                        fasta_file.write(f"{my_seqs[0]}\n")
                    if len(my_seqs) == 2:
                        my_seqs.remove(my_seqs[0]) if len(my_seqs[0]) <= len(my_seqs[1]) else my_seqs.remove(my_seqs[1])
                        fasta_file.write(f"{my_seqs[0]}\n")


    for i in tqdm(os.listdir(save_dir), desc="Extracting and Aligning sequences..."):
        all_info = {}
        split_file_path = os.path.join(save_dir, i)
        for rec in SeqIO.parse(split_file_path, format='fasta'):
            all_info[rec.id] = str(rec.seq)
        for name in all_info.keys():
            if name != ref_file:
                split_file_name = ref_file + "_vs_" + name
                save_split_dir = os.path.join(save_dir, split_file_name)
                if not os.path.exists(save_split_dir):
                    os.makedirs(save_split_dir)
                split_abspath = os.path.join(save_split_dir, i.split('.')[0] + '_cds.fasta')
                split_abspath_pro = os.path.join(save_split_dir, i.split('.')[0] + '_pro.fasta')
                ff = open(split_abspath, 'w')
                gg = open(split_abspath_pro, 'w')
                ff.write(f">{ref_file}\n{all_info[ref_file]}\n>{name}\n{all_info[name]}\n")
                ref_pro = Seq(str(all_info[ref_file])).translate(table=11)
                pro_seq = Seq(str(all_info[name])).translate(table=11)
                gg.write(f">{ref_file}\n{ref_pro}\n>{name}\n{pro_seq}\n")
                ff.close()
                gg.close()
                # 构建mafft命令
                # input_file_path = split_abspath_pro
                file_name, file_extension = os.path.splitext(split_abspath_pro)
                output_file_path = file_name + '_align.fasta'
                mafft_cmd = [mafft_path, '--auto', split_abspath_pro]

                # 调用mafft进行比对
                with open(output_file_path, 'w') as out_file:
                    subprocess.run(mafft_cmd, stdout=out_file, stderr=subprocess.DEVNULL)

    for dir_ in os.listdir(save_dir):
        dir_name = os.path.join(save_dir, dir_)
        if os.path.isdir(dir_name):
            # results_file = os.path.join(dir_name, 'KaKs_results.txt')

            # # 创建或清空 results_file 文件
            # with open(results_file, 'w') as f:
            #     pass
            for file in os.listdir(dir_name):
                if file.endswith('_align.fasta'):
                    gene_suffix = file.split('_')[0]
                    final_file = os.path.join(dir_name, gene_suffix + '_cds_pep_aln.fasta')
                    cds_file = os.path.join(dir_name, gene_suffix + '_cds.fasta')
                    pro_file = os.path.join(dir_name, file)

                    # 生成CDS与蛋白质比对映射文件
                    map_protein_to_nucleotide_alignment(pro_file, cds_file, final_file)

                    # 生成AXT文件
                    axt_file = os.path.join(dir_name, gene_suffix + '.axt')
                    fasta_to_axt(final_file, axt_file)

            combined_results_file = os.path.join(dir_name, 'combined_KaKs_results.txt')

            # 如果结果文件存在，则清空文件内容
            if os.path.exists(combined_results_file):
                with open(combined_results_file, 'w') as k:
                    k.write("")

            # KaKS 结果输出目录
            output_dir = os.path.join(dir_name, 'KaKS_results')
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)

            # 遍历所有 AXT 文件进行 KaKs 计算
            for file in tqdm(os.listdir(dir_name), desc="Calculating KaKs values..."):
                if file.endswith('.axt'):
                    gene_suffix = file.split('.')[0]

                    # KaKS 计算结果文件
                    output_file = os.path.join(output_dir, gene_suffix + '_KaKs.txt')

                    # KaKs Calculator 命令
                    axt_file_path = os.path.join(dir_name, file)
                    kaks_cmd = f"{kaks_calculator_path} -i {axt_file_path} -o {output_file} -m {mode} -c 11"

                    try:
                        # 运行 KaKs Calculator 并将输出重定向到文件
                        with open(os.devnull, 'w') as devnull:  # 忽略所有输出
                            subprocess.run(kaks_cmd, shell=True, check=True, stdout=devnull, stderr=devnull)
                    except subprocess.CalledProcessError as e:
                        print(f"Error occurred while running KaKs Calculator for {gene_suffix}: {e}")
                        continue

                    # 将结果追加到总的结果文件中
                    try:
                        with open(combined_results_file, 'a') as combined_file, open(output_file, 'r') as single_result:
                            if is_file_empty(combined_results_file):
                                lines = single_result.readlines()
                                line_split = lines[1].split('\t')
                                line_split[0] = gene_suffix
                                lines[1] = '\t'.join(line_split)
                                combined_file.write(lines[0])
                                combined_file.write(lines[1])
                            else:
                                # 如果文件不为空，只写入 single_result 的第二行（即从 single_result 中读取所有行）
                                lines = single_result.readlines()
                                if len(lines) > 1:
                                    line_split = lines[1].split('\t')
                                    line_split[0] = gene_suffix
                                    lines[1] = '\t'.join(line_split)
                                    combined_file.write(lines[1])  # 写入第二行（索引为1）
                                else:
                                    print(f"File {output_file} does not have enough lines.")
                    except FileNotFoundError as e:
                        print(f"File not found error for {output_file}: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")

    print("All KaKs calculations are completed and combined results have been saved.")


def KaKs_cal(args):
    # Check for KaKs_Calculator path when this function is executed
    kaks_calculator_path = find_kaks_calculator()
    if kaks_calculator_path:
        print('-'*40)
        print(f"KaKs_Calculator found at: {kaks_calculator_path}")
        print('-'*40)
    else:
        print("KaKs_Calculator not found in PATH.")
        sys.exit()

    # Now that KaKs_Calculator is confirmed, continue with the rest of the logic for KaKs_cal

    input_file = os.path.abspath(args.input_reference)
    mode = args.mode if hasattr(args, 'mode') else "MLWL"
    common_cds_extract(input_file, kaks_calculator_path, mode=mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument("-i", "--input_reference", help="Input path of reference genbank file", required=True)
    parser.add_argument("-m", "--mode", help="KaKs calculator mode")
    args = parser.parse_args()
    if args.input_reference:
        input_file = os.path.abspath(args.input_reference)
        common_cds_extract(input_file, kaks_calculator_path, args.mode)
    else:
        parser.print_help()
