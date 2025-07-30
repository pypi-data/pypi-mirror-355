import gzip
import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.use('Agg')


def check_fastq_format(file_path):
    open_func = gzip.open if file_path.endswith(".gz") else open
    try:
        with open_func(file_path, 'rt') as f:
            count = 0
            while True:
                lines = [next(f).strip() for _ in range(4)]
                if not lines[0].startswith('@'):
                    print(f"[ERROR] Line {4*count+1} does not start with '@'")
                    return False
                if not lines[2].startswith('+'):
                    print(f"[ERROR] Line {4*count+3} does not start with '+'")
                    return False
                if len(lines[1]) != len(lines[3]):
                    print(f"[ERROR] Line {4*count+1}: sequence and quality lengths differ")
                    return False
                count += 1
    except StopIteration:
        print(f"[OK] Total {count} reads checked, all passed!")
        return True
    except Exception as e:
        print(f"[ERROR] FASTQ check error: {e}")
        return False

def run_depth(reference, fastq1, fastq2, output_dir, threads:int):
    os.makedirs(output_dir, exist_ok=True)
    tmp_dir = os.path.abspath("tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    # file pathway
    index_prefix = os.path.join(tmp_dir, "ref")
    sam_file = os.path.join(tmp_dir, "map2ref.sam")
    bam_file = os.path.join(tmp_dir, "mapped.bam")
    sorted_bam = os.path.join(tmp_dir, "mapped_sort.bam")
    depth_file = os.path.join(output_dir, "depth.txt")

    # build Bowtie2 index
    print("[INFO] Building Reference Index...")
    subprocess.run(['bowtie2-build', reference, index_prefix], check=True)

    # map reads to reference
    print("[INFO] Mapping To Reference...")
    with open(sam_file, 'w') as sam_out:
        subprocess.run([
            'bowtie2',
            '-x', index_prefix,
            '-1', fastq1,
            '-2', fastq2,
            '-p', str(threads)
        ], stdout=sam_out, check=True)

    # mapped reads not -F 4
    with open(bam_file, 'wb') as bam_out:
        subprocess.run([
            'samtools', 'view', '-h', '-F', '4',
            sam_file, '-@', str(threads)
        ], stdout=bam_out, check=True)

    # sort BAM
    print("[INFO] Sorting BAM...")
    subprocess.run([
        'samtools', 'sort', '-o', sorted_bam,
        '-@',  str(threads), bam_file
    ], check=True)

    print("[INFO] Index BAM...")
    subprocess.run([
        'samtools', 'index', '-@',  str(threads), sorted_bam
    ], check=True)

    print("[INFO] Calculating depth...")
    with open(depth_file, 'w') as depth_out:
        subprocess.run([
            'samtools', 'depth', sorted_bam
        ], stdout=depth_out, check=True)

    print(f"[OK] Depth calculation completed. Output saved to: {depth_file}")

    return depth_file


def calculate_average_depth_blocks(depth_file, output_file, block_size:int=2000):
    if block_size < 1:
        print("Please provide a validated block size!")
        sys.exit(1)

    with open(depth_file, 'r') as file:
        lines = file.readlines()

    print(f"[INFO] Total {len(lines)} lines loaded from depth file.")

    with open(output_file, 'w') as ff:
        for i in range(0, len(lines), block_size):
            start = i
            end = min(i + block_size, len(lines))
            middle = start + (end - start) // 2
            all_sum = 0

            for j in range(start, end):
                try:
                    all_sum += int(lines[j].split('\t')[2])
                except IndexError:
                    print(f"[WARNING] Skipping malformed line {j+1}: {lines[j].strip()}")
                    continue

            avg_depth = round(all_sum / (end - start), 0)
            # print(f"[BLOCK] Middle index: {middle}, Average depth: {avg_depth}")
            ff.write(f"{middle}\t{avg_depth}\n")


def plot_function(depth_file, output_file, block_size):

    # 读取数据
    data1 = pd.read_csv(depth_file, sep="\t", header=None, names=["Species", "index", "depth"])
    data2 = pd.read_csv(output_file, sep="\t", header=None, names=["Middle", "depth"])

    plt.figure(figsize=(10, 5))
    plt.plot(data1["index"], data1["depth"], color="blue", linestyle='-')
    # 图形属性设置
    plt.ylabel("Depth")
    plt.grid(False)

    # show
    plt.tight_layout()
    plt.savefig("sequencing_depth_line.pdf", dpi=300, bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(12, 5))
    plt.bar(data2["Middle"], data2["depth"], width=1800, color="skyblue", edgecolor="black")

    # 设置图形属性
    plt.xlabel(f"Sequence Position (Middle of {block_size}bp block)")
    plt.ylabel("Mean Depth")
    plt.title(f"Average Sequencing Depth per {block_size}bp Block")
    plt.xticks(rotation=45)

    # 显示图形
    plt.tight_layout()
    plt.savefig("mean_sequencing_depth_bar.pdf", dpi=300, bbox_inches='tight')
    plt.close()


def depth_plot(args):
    # 自动设置输出目录
    if args.output is None:
        args.output = os.path.dirname(os.path.abspath(args.p1))
        print(f"[INFO] Output directory not specified. Using: {args.output}")

    # 检查 FASTQ 格式
    for fq in [args.p1, args.p2]:
        if not check_fastq_format(fq):
            print(f"[ERROR] FASTQ file check failed: {fq}")
            return

    # 运行主流程
    try:
        depth_file = run_depth(args.input_fasta, args.p1, args.p2, args.output, args.threads)
        mean_depth_file = os.path.join(args.output, "mean_depth.txt")
        calculate_average_depth_blocks(depth_file, mean_depth_file, args.block_size)
        plot_function(depth_file, mean_depth_file, args.block_size)
        print("[DONE] Depth pipeline completed successfully.")

    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")




if __name__ == "__main__":
    main()


