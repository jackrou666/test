import os
import csv
import pandas as pd
import sys

# 定义提取函数
def extract(input_file_path, output_file_path):
    with open(input_file_path) as file:
        with open(output_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for line in file:
                if line.startswith('# ColHeaders'):
                    title_line = line[len('# ColHeaders'):].strip()
                    fields = title_line.rstrip().split()
                    writer.writerow(fields)
                elif not line.lstrip().startswith('#'):
                    fields = line.rstrip().split()
                    writer.writerow(fields)

# 定义处理stats文件的函数
def process_stats_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name == 'aseg.stats':
                file_path = os.path.join(root, file_name)
                output_file_path = file_path + '.csv'
                extract(file_path, output_file_path)

# 定义转置并追加列的函数
def transpose_and_append_column(input_file_path, data, folder_name):
    columns = ['StructName', 'Volume_mm3']
    df = pd.read_csv(input_file_path)
    if not all(col in df.columns for col in columns):
        print(f"文件 {input_file_path} 中缺少所需的列 {columns}")
        return

    for index, row in df.iterrows():
        struct_name = row['StructName']
        volume = row['Volume_mm3']
        if struct_name not in data:
            data[struct_name] = {}
        data[struct_name][folder_name] = volume

# 获取上级文件夹名
def get_parent_folder_name(path, levels_up=3):
    parts = os.path.normpath(path).split(os.sep)
    return parts[-levels_up] if len(parts) >= levels_up else ''

# 主函数
def main(current_folder):
    process_stats_files(current_folder)
    data = {}
    folder_names = []
    output_path = os.path.join(current_folder, 'total.csv')

    for root, dirs, files in os.walk(current_folder):
        for file_name in files:
            if file_name == 'aseg.stats.csv':
                file_path = os.path.join(root, file_name)
                if file_path == output_path:
                    print(f"跳过文件 {file_path}，因为输入路径等于输出路径")
                    continue
                folder_name = get_parent_folder_name(file_path, levels_up=3)
                if folder_name not in folder_names:
                    folder_names.append(folder_name)
                transpose_and_append_column(file_path, data, folder_name)

    with open(output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        headers = ['StructName'] + folder_names
        writer.writerow(headers)
        for struct_name, volumes in data.items():
            row = [struct_name] + [volumes.get(folder_name, '') for folder_name in folder_names]
            writer.writerow(row)

    source_df = pd.read_csv(output_path)
    transposed_df = source_df.T
    transposed_df.columns = transposed_df.iloc[0]
    transposed_df = transposed_df[1:]
    transposed_df.to_csv(output_path, index=True, header=True)

# 脚本入口
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 script.py <folder_path>")
        sys.exit(1)

    current_folder = sys.argv[1]
    main(current_folder)
