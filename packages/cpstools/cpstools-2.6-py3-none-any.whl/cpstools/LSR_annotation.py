import argparse
import os
import re
from Bio import SeqIO


class CustomHelpFormatter(argparse.HelpFormatter):
    def format_help(self):
        help_text = super().format_help()
        description = """
        Annotated LSRs in chloroplast genomes.
        Author: Xu wenbo
        Org:    China Pharmaceutical University
        Email:  xwb7533@163.com
        """

        return f"{description}\n\n{help_text}"


def check_files(input_file):
    try:
        if input_file.endswith('.fasta') or input_file.endswith('.fa'):
            for rec in SeqIO.parse(input_file, 'fasta'):
                print("Please input Genbank format file")
        if input_file.endswith('.gb') or input_file.endswith('.gbk'):
            for rec in SeqIO.parse(input_file, 'genbank'):
                return str(rec.seq)
        raise ValueError(f"Unsupported file format for '{input_file}'. "
                         f"Please use FASTA (.fasta or .fa) or GenBank (.gb or .gbk) files.")
    except Exception as e:
        if isinstance(e, FileNotFoundError):
            raise  # Reraise the FileNotFoundError
        elif os.path.exists(input_file):
            raise ValueError(f"Error processing file '{input_file}': {e}")
        else:
            raise FileNotFoundError(f"No such file: {input_file}")


def fix_line_format(line):
    """Fix the format of a line by replacing multiple spaces with a tab."""
    return re.sub(r'\s+', '\t', line.strip())


def IGS_extract(input_file):
    for rec in SeqIO.parse(input_file, format='genbank'):
        genome_length = [[int(part.end)] for part in rec.features[0].location.parts][0][0]
        my_seq = rec.seq
        all_feature = []
        all_info = []
        for feature in rec.features:
            if feature.type == 'CDS' or feature.type == 'tRNA' or feature.type == 'rRNA':
                all_feature.append(feature)
        for i in range(len(all_feature)):
            gene_name = all_feature[i].qualifiers['gene'][0]
            gene_location = all_feature[i].location.parts
            gene1_exon_info = [[int(part.start), int(part.end), part.strand] for part in gene_location]
            exon_number = len(gene_location)
            if exon_number == 1:
                all_info.append(
                    f"{gene_name}\t{gene1_exon_info[0][0]}\t{gene1_exon_info[0][1]}\t{gene1_exon_info[0][2]}")
                all_info.append(
                    f"{gene_name}\t{gene1_exon_info[0][0]}\t{gene1_exon_info[0][1]}\t{gene1_exon_info[0][2]}")
            if exon_number == 2:
                if gene1_exon_info[0][1] == genome_length:
                    all_info.append(
                        f"{gene_name}\t{gene1_exon_info[0][0]}\t{gene1_exon_info[0][1]}\t{gene1_exon_info[1][0]}\t{gene1_exon_info[1][1]}\t{gene1_exon_info[0][2]}")
                else:
                    all_info.append(
                        f"{gene_name}_1\t{gene1_exon_info[0][0]}\t{gene1_exon_info[0][1]}\t{gene1_exon_info[0][2]}")
                    all_info.append(
                        f"{gene_name}_2\t{gene1_exon_info[1][0]}\t{gene1_exon_info[1][1]}\t{gene1_exon_info[1][2]}")
            if exon_number == 3:
                all_info.append(
                    f"{gene_name}_1\t{gene1_exon_info[0][0]}\t{gene1_exon_info[0][1]}\t{gene1_exon_info[0][2]}")
                all_info.append(
                    f"{gene_name}_2\t{gene1_exon_info[1][0]}\t{gene1_exon_info[1][1]}\t{gene1_exon_info[1][2]}")
                all_info.append(
                    f"{gene_name}_3\t{gene1_exon_info[2][0]}\t{gene1_exon_info[2][1]}\t{gene1_exon_info[2][2]}")
        all_info = list(set(all_info))
        all_info.sort(key=lambda x: int(x.split('\t')[1]))
        save_file = os.path.join(os.path.dirname(input_file), os.path.basename(input_file).split('.')[0] + '_SSRs.txt')
        save_file_w = open(save_file, 'w')
        for i in range(len(all_info) - 1):
            info_list = all_info[i].split('\t')
            next_list = all_info[i + 1].split('\t')
            # print(info_list, next_list, info_list[0].split('_')[0], next_list[0])
            save_file_w.write(f"{info_list[0]}\t{info_list[1]}\t{info_list[2]}\tGene\n")
            save_file_w.write(f"{info_list[0]}-{next_list[0]}\t{info_list[-2]}\t{next_list[1]}\tIGS\n")
        save_file_w.write(f"{all_info[-1][:-1]}\tGene\n")
        end_gene_info = all_info[-1].split('\t')
        start_gene_info = all_info[0].split('\t')
        if int(end_gene_info[-2]) < int(start_gene_info[1]):
            save_file_w.write(f"{end_gene_info[0]}-{start_gene_info}[0]\t{end_gene_info[-2]}\t{start_gene_info[1]}"
                              f"\tGene\n")
        else:
            if int(end_gene_info[2]) < genome_length:
                save_file_w.write(f"{end_gene_info[0]}-{start_gene_info[0]}\t{end_gene_info[-2]}\t{genome_length}\t0\t\
                {start_gene_info[1]}\tIGS\n")
            else:
                pass
        save_file_w.close()

        # change location type 
        output_ = os.path.join(os.path.dirname(input_file), os.path.basename(input_file).split('.')[0] + '_SSRs2.txt')
        change_file = open(save_file, 'r').readlines()
        with open(output_, 'w') as gg:
            for loc2 in change_file:
                loc_type = loc2.split('\t')[0]
                if "matK" in loc_type and "trnK-UUU" in loc_type:
                    loc2_list = loc2.split('\t')
                    loc2_list[-1] = "Intron"
                    gg.write('\t'.join(loc_x for loc_x in loc2_list) + '\n')
                else:
                    if len(loc_type.split('_')) == 3:
                        N1, N3 = loc2.split('_')[0], loc2.split('_')[1]
                        if N1 in N3:
                            loc2_list = loc2.split('\t')
                            loc2_list[-1] = "Intron"
                            gg.write('\t'.join(loc_x for loc_x in loc2_list) + '\n')
                        else:
                            gg.write(loc2)
                    else:
                        gg.write(loc2)

        # get location
        file_name = os.path.basename(input_file).split('.')[0]
        save_name = file_name + ".txt"
        file1 = os.path.join(os.path.dirname(input_file), save_name)
        st_lines = open(output_, 'r').readlines()[1:]

        final_name = file_name + "_LSRs_loc_results1.txt"
        final_results = os.path.join(os.path.dirname(input_file), final_name)
        data = []
        st_lines2 = open(file1, 'r').readlines()[1:]
        unique_data = set()
        
        # 处理5列数据的部分
        for line in st_lines:
            parts = fix_line_format(line).split('\t')
            name = parts[0]
            start = int(parts[1])
            end = int(parts[2])
            loc = parts[-1]

            # 处理额外的范围
            if len(parts) == 6:
                extra_start = int(parts[3])
                extra_end = int(parts[4])
                unique_data.add((name, start, end, loc))
                unique_data.add((name, extra_start, extra_end, loc))
            else:
                unique_data.add((name, start, end, loc))

        data = list(unique_data)
        print(data)
        # print(data)
        printed_combinations = {}

        # write output results
        with open(final_results, 'w') as ff:
            for i in st_lines2:
                st_list = fix_line_format(i).split('\t')
                print(st_list)
                st_join = '\t'.join(info.strip() for info in st_list)
                start_point = int(st_list[1])
                length = int(st_list[0])
                # 将 label 的列表转换为元组
                label = tuple(st_list[:7])  # 这里做了更改，将列表转换为元组
                
                # 使用转换后的 label，现在 combination_key 应该不会导致错误了
                for num in range(start_point, start_point + length):
                    for name, start, end, loc in data:
                        if start <= num <= end:
                            combination_key = (start_point, length, label, name)
                            if combination_key not in printed_combinations:
                                printed_combinations[combination_key] = True
                                ff.write(f"{st_join}\t{name}\t{loc}\n")
        final_name2 = file_name + "_LSRs_loc_results.txt"
        final_results2 = os.path.join(os.path.dirname(input_file), final_name2)
        final_data = []
        with open(final_results, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:  # 跳过标题行
                line_list = line.strip().split('\t')
                new_line = '\t'.join([line_list[2], line_list[0], line_list[1], 
                                      str(int(line_list[1]) + int(line_list[0])), 
                                      line_list[7], line_list[8]])
                final_data.append(new_line)

        # 按照第三列（新的起始位置）进行排序
        sorted_list = sorted(final_data, key=lambda x: int(x.split('\t')[2]))

        # 将排序后的数据写入新的文件
        with open(final_results2, 'w') as ff:
            ff.write("type\tlength\tstart\tend\tloc\tloc_type\n")
            for i in sorted_list:
                ff.write(i + '\n')
        os.remove(output_)
        os.remove(save_file)
        os.remove(final_results)
        print(f"The results were written into:\n\t\t{os.path.abspath(final_results2)}\n{'-' * 80}")


def lsr_annotate(args):
    try:
        file_path = os.path.abspath(args.input_file)
        check_results = check_files(file_path)
        if check_results:
            IGS_extract(file_path)
    except (ValueError, FileNotFoundError) as e:
        print(e)


def main():
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument('-i', '--input_file', help='GenBank format file', required=True)
    # parser.add_argument('-o', '--output', help='output file')

    args = parser.parse_args()
    if args.input_file:
        try:
            file_path = os.path.abspath(args.input_file)
            check_results = check_files(file_path)
            if check_results:
                IGS_extract(file_path)
        except (ValueError, FileNotFoundError) as e:
            print(e)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
