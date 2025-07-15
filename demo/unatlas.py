import os
import binascii
import tkinter as tk
from tkinter import filedialog, messagebox
import json

# 保存配置文件路径
config_file = 'config.json'
selected_folder = ''  # 全局变量存储选择的文件夹路径
total_files = 0       # 统计总文件数
failed_files = 0      # 统计失败文件数
files_to_delete = []  # 记录需要删除的文件

# 拆分文本并保存为不同的文件
def split_and_save(text_data, un_folder, original_filename, output_path):
    atlas_saved = False
    json_saved = False

    try:
        # 将"-atlas"或"-data"部分从文件名中删除
        clean_filename = original_filename.replace('-atlas', '').replace('-data', '')

        # 找到文件名.png到最后一个index: -1
        start_png = text_data.find(f'{clean_filename}.png')
        end_atlas = text_data.rfind('index: -1') + len('index: -1')
        atlas_content = text_data[start_png:end_atlas] if start_png != -1 and end_atlas != -1 else ''
        
        # 找到"{"skeleton":{"hash": 或者带换行的"{\n\"skeleton\": {" 到最后一个 }
        start_json = text_data.find('{\n"skeleton": {')
        if start_json == -1:
            start_json = text_data.find('{"skeleton":{"hash":')  # 修改匹配条件
        end_json = text_data.rfind('}')
        json_content = text_data[start_json:end_json + 1] if start_json != -1 and end_json != -1 else ''

        # 如果有atlas内容，保存为.atlas文件
        if atlas_content:
            atlas_filename = f"{clean_filename}.atlas"
            atlas_path = os.path.join(output_path, atlas_filename)
            with open(atlas_path, 'w', encoding='utf-8') as atlas_file:
                atlas_file.write(atlas_content)
            atlas_saved = True

        # 如果有json内容，保存为.json文件
        if json_content:
            json_filename = f"{clean_filename}.json"
            json_path = os.path.join(output_path, json_filename)
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json_file.write(json_content)
            json_saved = True

        # 根据atlas和json的保存情况返回是否成功
        return atlas_saved or json_saved

    except Exception as e:
        return False  # 表示失败

# 处理文件，将uexp文件转为txt
def process_files(folder_path, output_path):
    global total_files, failed_files, files_to_delete
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".uexp"):
                total_files += 1  # 计入总文件数
                file_path = os.path.join(root, filename)
                un_folder = root
                os.makedirs(un_folder, exist_ok=True)  # 创建UN文件夹
                
                try:
                    with open(file_path, 'rb') as file:
                        # 读取文件内容并转换为16进制
                        hex_data = binascii.hexlify(file.read())
                        # 将16进制转换为文本（UTF-8解码，忽略错误）
                        text_data = bytes.fromhex(hex_data.decode('utf-8')).decode('utf-8', errors='ignore')

                        # 尝试拆分文本并生成atlas和json文件
                        original_filename = os.path.splitext(filename)[0]
                        split_and_save(text_data, un_folder, original_filename, output_path)
                        
                except Exception as e:
                    failed_files += 1  # 如果处理失败，计入失败次数
                    files_to_delete.append(file_path)  # 记录需要删除的uexp文件



