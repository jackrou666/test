# 导入所需的库
import os  # 用于与操作系统交互，如文件路径操作、遍历文件夹等
import csv  # 用于读写CSV文件
import pandas as pd  # 强大的数据处理和分析库，这里主要用于数据转置
import sys  # 用于访问与Python解释器交互的变量和函数，如此处的命令行参数


# --- 函数定义部分 ---

# 定义一个函数，用于从FreeSurfer的stats文件中提取数据并存为CSV
def extract(input_file_path, output_file_path):
    """
    读取一个.stats文件，提取表头和数据行，并将其写入一个新的CSV文件。
    它会忽略以'#'开头的注释行，但专门处理以'# ColHeaders'开头的表头行。
    """
    # 使用'with'语句安全地打开输入和输出文件，确保文件最终会被关闭
    with open(input_file_path) as file:  # 打开原始的.stats文件
        with open(output_file_path, 'w', newline='') as csvfile:  # 创建并打开用于写入的CSV文件
            # 'newline='''参数可以防止在写入CSV时出现多余的空行
            writer = csv.writer(csvfile)  # 创建一个CSV写入对象

            # 遍历输入文件中的每一行
            for line in file:
                # 检查行是否是表头定义行
                if line.startswith('# ColHeaders'):
                    # 提取表头内容（去除'# ColHeaders'前缀和首尾空格）
                    title_line = line[len('# ColHeaders'):].strip()
                    # 将表头字符串按空格分割成字段列表
                    fields = title_line.rstrip().split()
                    # 将表头字段写入CSV文件
                    writer.writerow(fields)
                # 检查行是否不是注释行（即，行在去除左侧空格后不以'#'开头）
                elif not line.lstrip().startswith('#'):
                    # 提取数据行内容（去除末尾的换行符和空格）
                    fields = line.rstrip().split()
                    # 将数据字段写入CSV文件
                    writer.writerow(fields)


# 定义一个函数，用于处理指定文件夹下的所有'aseg.stats'文件
def process_stats_files(folder_path):
    """
    遍历指定文件夹及其所有子文件夹，查找名为'aseg.stats'的文件，
    并使用extract函数将其转换为CSV格式。
    """
    # os.walk会递归地遍历文件夹结构
    for root, dirs, files in os.walk(folder_path):
        # 遍历当前文件夹下的所有文件名
        for file_name in files:
            # 如果文件名是'aseg.stats'
            if file_name == 'aseg.stats':
                # 构建该文件的完整路径
                file_path = os.path.join(root, file_name)
                # 定义输出的CSV文件名（在原文件名后加上.csv）
                output_file_path = file_path + '.csv'
                # 调用extract函数进行转换
                extract(file_path, output_file_path)


# 定义一个函数，用于读取CSV数据，提取特定列，并将其添加到主数据字典中
def transpose_and_append_column(input_file_path, data, folder_name):
    """
    从一个CSV文件中读取'StructName'和'Volume_mm3'列。
    然后以'StructName'为键，将'Volume_mm3'的值存入一个嵌套字典中。
    这个结构（data[结构名][被试名] = 体积）便于后续生成汇总表。
    """
    # 定义我们感兴趣的列名
    columns = ['StructName', 'Volume_mm3']
    # 使用pandas读取CSV文件
    df = pd.read_csv(input_file_path)

    # 检查CSV文件是否包含所有我们需要的列
    if not all(col in df.columns for col in columns):
        print(f"文件 {input_file_path} 中缺少所需的列 {columns}")
        return  # 如果缺少列，则打印错误信息并跳过此文件

    # 遍历DataFrame的每一行
    for index, row in df.iterrows():
        struct_name = row['StructName']  # 获取结构名称
        volume = row['Volume_mm3']  # 获取对应的体积

        # 如果这个结构名是第一次出现，先在data字典中为它创建一个空字典
        if struct_name not in data:
            data[struct_name] = {}
        # 将当前被试(folder_name)的体积数据存入
        data[struct_name][folder_name] = volume


# 定义一个辅助函数，用于从文件路径中获取上级文件夹的名称
def get_parent_folder_name(path, levels_up=3):
    """
    根据文件路径向上追溯指定层数，获取文件夹名。
    这里默认'levels_up=3'，是为了从类似 '.../subject_id/stats/aseg.stats.csv' 的路径中提取 'subject_id'。
    """
    # 将路径标准化以适应不同操作系统（例如，转换'/'和'\'）并按分隔符分割
    parts = os.path.normpath(path).split(os.sep)
    # 如果路径深度足够，返回倒数第'levels_up'个部分，否则返回空字符串
    return parts[-levels_up] if len(parts) >= levels_up else ''


# --- 主逻辑函数 ---

def main(current_folder):
    """
    这是脚本的核心执行函数。
    它协调整个流程：转换.stats文件，聚合数据，最后生成转置后的汇总CSV表。
    """
    # 1. 转换所有'aseg.stats'文件为CSV格式
    process_stats_files(current_folder)

    # 2. 初始化用于存储聚合数据的变量
    data = {}  # 字典，用于存储所有被试的体积数据
    folder_names = []  # 列表，用于存储所有被试的ID（文件夹名），以保证最终CSV列的顺序
    output_path = os.path.join(current_folder, 'total.csv')  # 定义最终输出文件的完整路径

    # 3. 遍历文件夹，读取转换后的CSV，聚合数据
    for root, dirs, files in os.walk(current_folder):
        for file_name in files:
            if file_name == 'aseg.stats.csv':
                file_path = os.path.join(root, file_name)
                # 确保不会把最终要生成的总文件当作输入文件来处理
                if file_path == output_path:
                    print(f"跳过文件 {file_path}，因为输入路径等于输出路径")
                    continue
                # 获取被试ID
                folder_name = get_parent_folder_name(file_path, levels_up=3)
                # 将新的被试ID添加到列表中（如果尚未存在）
                if folder_name not in folder_names:
                    folder_names.append(folder_name)
                # 读取该文件的数据并添加到主'data'字典中
                transpose_and_append_column(file_path, data, folder_name)

    # 4. 将聚合的数据写入初始的'total.csv'文件
    #    此时的格式是：行为大脑结构，列为被试
    with open(output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # 写入表头，第一列是'StructName'，其余是各个被试ID
        headers = ['StructName'] + folder_names
        writer.writerow(headers)
        # 遍历'data'字典，写入每一行
        for struct_name, volumes in data.items():
            # 构建行数据：结构名 + 对应各个被试的体积（如果某个被试没有该结构的数据，则留空）
            row = [struct_name] + [volumes.get(folder_name, '') for folder_name in folder_names]
            writer.writerow(row)

    # 5. 使用pandas进行数据转置，得到最终想要的格式
    #    最终格式：行为被试，列为大脑结构
    source_df = pd.read_csv(output_path)  # 读入刚刚创建的CSV
    transposed_df = source_df.T  # 进行转置操作
    transposed_df.columns = transposed_df.iloc[0]  # 将转置后的第一行（原来的'StructName'列）设置为新的表头
    transposed_df = transposed_df[1:]  # 去掉作为表头的那一行
    # 将转置后的数据写回'total.csv'，'index=True'会把行索引（即被试ID）也写入文件作为第一列
    transposed_df.to_csv(output_path, index=True, header=True)


# --- 从 brainvol.stats 文件提取并追加数据的函数 ---
#
# 下面这一系列'process_*'函数遵循完全相同的模式：
# 1. 遍历文件夹结构，寻找'brainvol.stats'文件。
# 2. 从文件中找到包含特定关键词的行（例如'Brain Segmentation Volume'）。
# 3. 解析该行，提取出体积数据。
# 4. 将被试ID和提取到的体积存入一个'results'字典。
# 5. 读取现有的'total.csv'文件。
# 6. 在内存中为数据添加一个新列（即当前函数要提取的指标）。
# 7. 将更新后的数据完全重写回'total.csv'文件。
#
# **注意**: 这种反复读写同一个CSV文件的方式效率较低。如果数据量非常大，
# 更高效的做法是先提取所有需要的数据到内存中，最后一次性写入CSV。
# 但对于典型使用场景，这种方法是可行的。
#

def process_brain_segmentation_volume(root_dir, output_file):
    """从'brainvol.stats'提取'Brain Segmentation Volume'并追加到汇总文件。"""
    results = {}  # 存储 {文件夹名: 体积}
    for subdir, _, files in os.walk(root_dir):
        if 'brainvol.stats' in files:
            stats_file_path = os.path.join(subdir, 'brainvol.stats')
            with open(stats_file_path, 'r') as stats_file:
                for line in stats_file:
                    if 'BrainSeg, BrainSegVol, Brain Segmentation Volume' in line:
                        volume = line.split(',')[3].strip()  # 按逗号分割并取第四个元素
                        folder_name = os.path.basename(os.path.dirname(os.path.dirname(stats_file_path)))
                        results[folder_name] = volume
                        break  # 找到后即可停止读取此文件

    # 读取现有CSV数据
    rows = []
    with open(output_file, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)  # 读取表头
        for row in csvreader:
            rows.append(row)

    # 写入新数据，增加一列
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['Brain Segmentation Volume'])  # 写入新表头
        for row in rows:
            folder_name = row[0]  # 第一列是被试ID
            row.append(results.get(folder_name, 'N/A'))  # 查找并追加体积数据，找不到则填'N/A'
            csvwriter.writerow(row)


# 下面的函数与上面的 `process_brain_segmentation_volume` 结构完全相同，
# 只是它们搜索的关键词和添加的列名不同。

def process_Brain_Segmentation_Volume_Without_Ventricles(root_dir, output_file):
    """提取'Brain Segmentation Volume Without Ventricles'并追加。"""
    results = {}
    for subdir, _, files in os.walk(root_dir):
        if 'brainvol.stats' in files:
            stats_file_path = os.path.join(subdir, 'brainvol.stats')
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
        rows.extend(csvreader)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['Brain Segmentation Volume Without Ventricles'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_SupratentorialVol(root_dir, output_file):
    """提取'SupratentorialVol' (幕上体积) 并追加。"""
    results = {}
    for subdir, _, files in os.walk(root_dir):
        if 'brainvol.stats' in files:
            stats_file_path = os.path.join(subdir, 'brainvol.stats')
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
        rows.extend(csvreader)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SupratentorialVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


# ... (为简洁起见，省略了其余结构相似的 process_* 函数的重复注释) ...
# 每个函数都执行相同的“查找-提取-追加”逻辑，只是针对不同的度量指标。

def process_SupraTentorialVolNotVent(root_dir, output_file):
    """提取'SupraTentorialVolNotVent' (不含脑室的幕上体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SupraTentorialVolNotVent'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_SubCortGrayVol(root_dir, output_file):
    """提取'SubCortGrayVol' (皮层下灰质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SubCortGrayVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_lhCortexVol(root_dir, output_file):
    """提取'lhCortexVol' (左半球皮层灰质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['lhCortexVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_rhCortexVol(root_dir, output_file):
    """提取'rhCortexVol' (右半球皮层灰质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['rhCortexVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_TotalGrayVol(root_dir, output_file):
    """提取'TotalGrayVol' (总灰质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['TotalGrayVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_CortexVol(root_dir, output_file):
    """提取'CortexVol' (总皮层灰质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['CortexVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_lhCerebralWhiteMatterVol(root_dir, output_file):
    """提取'lhCerebralWhiteMatterVol' (左半球大脑白质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['lhCerebralWhiteMatterVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_rhCerebralWhiteMatterVol(root_dir, output_file):
    """提取'rhCerebralWhiteMatterVol' (右半球大脑白质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['rhCerebralWhiteMatterVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_CerebralWhiteMatterVol(root_dir, output_file):
    """提取'CerebralWhiteMatterVol' (总大脑白质体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['CerebralWhiteMatterVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_MaskVol(root_dir, output_file):
    """提取'MaskVol' (Mask 体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['MaskVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_SupraTentorialVolNotVentVox(root_dir, output_file):
    """提取'SupraTentorialVolNotVentVox' (幕上体积体素计数) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['SupraTentorialVolNotVentVox'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_BrainSegVolNotVentSurf(root_dir, output_file):
    """提取'BrainSegVolNotVentSurf' (来自表面的不含脑室的脑分割体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['BrainSegVolNotVentSurf'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


def process_VentricleChoroidVol(root_dir, output_file):
    """提取'VentricleChoroidVol' (脑室和脉络丛体积) 并追加。"""
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
        for row in csvreader: rows.append(row)
    with open(output_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers + ['VentricleChoroidVol'])
        for row in rows:
            folder_name = row[0]
            row.append(results.get(folder_name, 'N/A'))
            csvwriter.writerow(row)


# --- 脚本入口点 ---
# 当这个 .py 文件被直接执行时（而不是作为模块导入时），下面的代码块会运行
if __name__ == "__main__":
    # 检查命令行参数的数量是否正确
    # sys.argv 是一个包含命令行参数的列表，第一个元素(sys.argv[0])是脚本名
    if len(sys.argv) != 2:
        # 如果参数不等于2（脚本名 + 文件夹路径），则打印用法并退出
        print("用法: python3 script.py <folder_path>")
        sys.exit(1)  # 退出脚本，返回状态码1表示错误

    # 获取命令行提供的文件夹路径
    current_folder = sys.argv[1]

    # 按顺序执行所有处理步骤：
    # 1. 创建基础的、转置后的 total.csv，包含 aseg.stats 的数据
    main(current_folder)

    # 2. 逐个调用函数，将 brainvol.stats 中的各项指标追加到 total.csv 中
    #    每个函数都会读取 total.csv，增加一列，然后再写回文件。
    output_csv_path = os.path.join(current_folder, 'total.csv')
    process_brain_segmentation_volume(current_folder, output_csv_path)
    process_Brain_Segmentation_Volume_Without_Ventricles(current_folder, output_csv_path)
    process_SupratentorialVol(current_folder, output_csv_path)
    process_SupraTentorialVolNotVent(current_folder, output_csv_path)
    process_SubCortGrayVol(current_folder, output_csv_path)
    process_lhCortexVol(current_folder, output_csv_path)
    process_rhCortexVol(current_folder, output_csv_path)
    process_CortexVol(current_folder, output_csv_path)
    process_TotalGrayVol(current_folder, output_csv_path)
    process_lhCerebralWhiteMatterVol(current_folder, output_csv_path)
    process_rhCerebralWhiteMatterVol(current_folder, output_csv_path)
    process_CerebralWhiteMatterVol(current_folder, output_csv_path)
    process_MaskVol(current_folder, output_csv_path)
    process_SupraTentorialVolNotVentVox(current_folder, output_csv_path)
    process_BrainSegVolNotVentSurf(current_folder, output_csv_path)
    process_VentricleChoroidVol(current_folder, output_csv_path)

    print(f"处理完成！所有数据已汇总到 {output_csv_path}")
