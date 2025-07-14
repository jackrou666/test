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

# 处理Brain Segmentation Volume的函数
def process_brain_segmentation_volume(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'BrainSeg, BrainSegVol, Brain Segmentation Volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['Brain Segmentation Volume'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理 Brain Segmentation Volume Without Ventricles的函数
def process_Brain_Segmentation_Volume_Without_Ventricles(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'BrainSegNotVent, BrainSegVolNotVent, Brain Segmentation Volume Without Ventricles' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['Brain Segmentation Volume Without Ventricles'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理 SupratentorialVol的函数
def process_SupratentorialVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'SupraTentorial, SupraTentorialVol, Supratentorial volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SupratentorialVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理 SupraTentorialVolNotVent的函数
def process_SupraTentorialVolNotVent(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if ' SupraTentorialNotVent, SupraTentorialVolNotVent, Supratentorial volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SupraTentorialVolNotVent'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理SubCortGrayVol的函数
def process_SubCortGrayVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'SubCortGray, SubCortGrayVol, Subcortical gray matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SubCortGrayVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理lhCortexVol的函数
def process_lhCortexVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'lhCortex, lhCortexVol, Left hemisphere cortical gray matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['lhCortexVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理rhCortexVol的函数
def process_rhCortexVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'rhCortex, rhCortexVol, Right hemisphere cortical gray matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['rhCortexVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理TotalGrayVol的函数
def process_TotalGrayVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'TotalGray, TotalGrayVol, Total gray matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['TotalGrayVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理CortexVol的函数
def process_CortexVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if ' Cortex, CortexVol, Total cortical gray matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['CortexVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理 lhCerebralWhiteMatterVol的函数
def process_lhCerebralWhiteMatterVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'lhCerebralWhiteMatter, lhCerebralWhiteMatterVol, Left hemisphere cerebral white matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['lhCerebralWhiteMatterVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理rhCerebralWhiteMatterVol的函数
def process_rhCerebralWhiteMatterVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'rhCerebralWhiteMatter, rhCerebralWhiteMatterVol, Right hemisphere cerebral white matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['rhCerebralWhiteMatterVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理CerebralWhiteMatterVol的函数
def process_CerebralWhiteMatterVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'CerebralWhiteMatter, CerebralWhiteMatterVol, Total cerebral white matter volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['CerebralWhiteMatterVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理MaskVol的函数
def process_MaskVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'Mask, MaskVol, Mask Volume' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['MaskVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理SupraTentorialVolNotVentVox的函数
def process_SupraTentorialVolNotVentVox(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'SupraTentorialNotVentVox, SupraTentorialVolNotVentVox, Supratentorial volume voxel count' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SupraTentorialVolNotVentVox'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理BrainSegVolNotVentSurf的函数
def process_BrainSegVolNotVentSurf(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'BrainSegNotVentSurf, BrainSegVolNotVentSurf, Brain Segmentation Volume Without Ventricles from Surf' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['BrainSegVolNotVentSurf'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)

# 处理VentricleChoroidVol的函数
def process_VentricleChoroidVol(root_dir, output_file):
    results = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'brainvol.stats':
                stats_file_path = os.path.join(subdir, file)
                with open(stats_file_path, 'r') as stats_file:
                    for line in stats_file:
                        if 'VentricleChoroidVol, VentricleChoroidVol, Volume of ventricles and choroid plexus' in line:
                            volume = line.split(',')[3].strip()
                            folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                            results[folder_name] = volume
                            break

    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)
        for row in csvreader:
            rows.append(row)

    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['VentricleChoroidVol'])
        for row in rows:
            folder_name = row[0]
            if folder_name in results:
                row.append(results[folder_name])
            else:
                row.append('N/A')
            csvwriter.writerow(row)








# 脚本入口
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 script.py <folder_path>")
        sys.exit(1)

    current_folder = sys.argv[1]
    main(current_folder)
    process_brain_segmentation_volume(current_folder, os.path.join(current_folder, 'total.csv'))
    process_Brain_Segmentation_Volume_Without_Ventricles(current_folder, os.path.join(current_folder, 'total.csv'))
    process_SupratentorialVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_SupraTentorialVolNotVent(current_folder, os.path.join(current_folder, 'total.csv'))
    process_SubCortGrayVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_lhCortexVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_rhCortexVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_CortexVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_TotalGrayVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_lhCerebralWhiteMatterVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_rhCerebralWhiteMatterVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_CerebralWhiteMatterVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_MaskVol(current_folder, os.path.join(current_folder, 'total.csv'))
    process_SupraTentorialVolNotVentVox(current_folder, os.path.join(current_folder, 'total.csv'))
    process_BrainSegVolNotVentSurf(current_folder, os.path.join(current_folder, 'total.csv'))
    process_VentricleChoroidVol(current_folder, os.path.join(current_folder, 'total.csv'))