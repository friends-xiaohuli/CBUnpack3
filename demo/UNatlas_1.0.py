import os
import binascii
import tkinter as tk
from tkinter import filedialog, messagebox
import json

# 保存配置文件路径
config_file = 'config.json'
selected_folder = ''  # 全局变量存储选择的文件夹路径

# 读取上次保存的文件夹路径
def load_last_folder():
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
            return config.get('last_folder', '')
    return ''

# 保存当前选择的文件夹路径
def save_last_folder(folder_path):
    config = {'last_folder': folder_path}
    with open(config_file, 'w') as file:
        json.dump(config, file)

# GUI窗口
def select_folder():
    global selected_folder
    initial_dir = load_last_folder()
    folder_path = filedialog.askdirectory(initialdir=initial_dir)
    if folder_path:
        selected_folder = folder_path  # 保存选择的文件夹路径
        save_last_folder(folder_path)
        process_files(folder_path)

# 拆分文本并保存为不同的文件
def split_and_save(text_data, folder_path, original_filename):
    try:
        # 找到文件名.png到最后一个index: -1
        start_png = text_data.find(f'{original_filename}.png')
        end_atlas = text_data.rfind('index: -1') + len('index: -1')
        atlas_content = text_data[start_png:end_atlas] if start_png != -1 and end_atlas != -1 else ''
        
        # 找到"{\n\"skeleton\": {" 到最后一个 }
        start_json = text_data.find('{\n"skeleton": {')
        end_json = text_data.rfind('}')
        json_content = text_data[start_json:end_json + 1] if start_json != -1 and end_json != -1 else ''

        # 保存为.atlas文件（使用第一步的原文件名）
        atlas_filename = f"{original_filename}.atlas"
        atlas_path = os.path.join(folder_path, atlas_filename)
        if atlas_content:
            with open(atlas_path, 'w', encoding='utf-8') as atlas_file:
                atlas_file.write(atlas_content)

        # 保存为.json文件（使用第一步的原文件名）
        json_filename = f"{original_filename}.json"
        json_path = os.path.join(folder_path, json_filename)
        if json_content:
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json_file.write(json_content)

    except Exception as e:
        messagebox.showerror("错误", f"拆分 {original_filename} 时出错: {e}")

# 处理文件，将uexp文件转为txt
def process_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".uexp"):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'rb') as file:
                    # 读取文件内容并转换为16进制
                    hex_data = binascii.hexlify(file.read())
                    # 将16进制转换为文本（UTF-8解码，忽略错误）
                    text_data = bytes.fromhex(hex_data.decode('utf-8')).decode('utf-8', errors='ignore')
                    
                    # 创建新txt文件，文件名为源文件名加'_UN'
                    new_filename = f"{os.path.splitext(filename)[0]}_UN.txt"
                    new_file_path = os.path.join(folder_path, new_filename)
                    with open(new_file_path, 'w', encoding='utf-8') as new_file:
                        new_file.write(text_data)

            except Exception as e:
                messagebox.showerror("错误", f"处理 {filename} 时出错: {e}")
    
    messagebox.showinfo("完成", "所有文件已处理并生成UTF-8格式的txt文件！")

# 第二步：分离已生成的txt文件
def split_texts():
    if not selected_folder:
        messagebox.showwarning("警告", "请先选择文件夹并处理文件。")
        return

    for filename in os.listdir(selected_folder):
        if filename.endswith("_UN.txt"):
            txt_file_path = os.path.join(selected_folder, filename)
            original_filename = filename.replace("_UN.txt", "")  # 获取原始文件名
            try:
                with open(txt_file_path, 'r', encoding='utf-8') as file:
                    text_data = file.read()
                    # 拆分文本并保存为.atlas和.json文件
                    split_and_save(text_data, selected_folder, original_filename)

            except Exception as e:
                messagebox.showerror("错误", f"处理 {filename} 时出错: {e}")

    messagebox.showinfo("完成", "所有txt文件已拆分并保存为.atlas和.json文件！")

# 主程序入口
root = tk.Tk()
root.title("uexp 文件处理器")

# 窗口尺寸
root.geometry("400x250")

# 标签和按钮
label = tk.Label(root, text="请选择包含 .uexp 文件的文件夹并处理")
label.pack(pady=20)

btn_select_folder = tk.Button(root, text="选择文件夹并处理为UTF-8的txt", command=select_folder)
btn_select_folder.pack(pady=10)

btn_split_files = tk.Button(root, text="拆分文本为 .atlas 和 .json", command=split_texts)
btn_split_files.pack(pady=10)

# 启动GUI主循环
root.mainloop()
