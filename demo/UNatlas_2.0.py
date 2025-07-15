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
    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(config, file)

# GUI窗口居中显示
def center_window(root, width=400, height=250):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

# GUI窗口
def process_files_combined():
    global selected_folder, total_files, failed_files, files_to_delete
    initial_dir = load_last_folder()
    folder_path = filedialog.askdirectory(initialdir=initial_dir)
    if folder_path:
        selected_folder = folder_path  # 保存选择的文件夹路径
        save_last_folder(folder_path)
        total_files = 0
        failed_files = 0
        files_to_delete = []  # 清空需要删除的文件列表
        process_files(folder_path)
        # 在所有文件处理完后执行清理
        clean_up_files(selected_folder)
        messagebox.showinfo("完成", f"处理完成！总文件数：{total_files}，失败文件数：{failed_files}")

# 拆分文本并保存为不同的文件
def split_and_save(text_data, un_folder, original_filename):
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
            atlas_path = os.path.join(un_folder, atlas_filename)
            with open(atlas_path, 'w', encoding='utf-8') as atlas_file:
                atlas_file.write(atlas_content)
            atlas_saved = True

        # 如果有json内容，保存为.json文件
        if json_content:
            json_filename = f"{clean_filename}.json"
            json_path = os.path.join(un_folder, json_filename)
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json_file.write(json_content)
            json_saved = True

        # 根据atlas和json的保存情况返回是否成功
        return atlas_saved or json_saved

    except Exception as e:
        return False  # 表示失败

# 处理文件，将uexp文件转为txt
def process_files(folder_path):
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

                        # 创建新txt文件，文件名为源文件名加'_UN'
                        new_filename = f"{os.path.splitext(filename)[0]}_UN.txt"
                        new_file_path = os.path.join(un_folder, new_filename)
                        with open(new_file_path, 'w', encoding='utf-8') as new_file:
                            new_file.write(text_data)

                        # 尝试拆分文本并生成atlas和json文件
                        original_filename = os.path.splitext(filename)[0]
                        if not split_and_save(text_data, un_folder, original_filename):
                            failed_files += 1  # 如果拆分失败，计入失败次数
                            files_to_delete.append(new_file_path)  # 记录需要删除的txt文件
                        
                except Exception as e:
                    failed_files += 1  # 如果处理失败，计入失败次数
                    files_to_delete.append(file_path)  # 记录需要删除的uexp文件

# 清理无效文件并删除空的UN文件夹
def clean_up_files(folder_path):
    global files_to_delete
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)  # 删除记录的文件
    # 删除无效的UN文件夹
    for root, dirs, files in os.walk(folder_path):
        un_folder = root
        if os.path.exists(un_folder):
            # 如果UN文件夹为空，则删除该文件夹
            if not os.listdir(un_folder):
                os.rmdir(un_folder)

# 第二步：分离已生成的txt文件
def split_texts():
    if not selected_folder:
        messagebox.showwarning("警告", "请先选择文件夹并处理文件。")
        return

    for root, dirs, files in os.walk(selected_folder):
        for filename in files:
            if filename.endswith("_UN.txt"):
                txt_file_path = os.path.join(root, filename)
                original_filename = filename.replace("_UN.txt", "")  # 获取原始文件名
                un_folder = root  # UN 文件夹
                try:
                    with open(txt_file_path, 'r', encoding='utf-8') as file:
                        text_data = file.read()
                        # 拆分文本并保存为.atlas和.json文件
                        if not split_and_save(text_data, un_folder, original_filename):
                            # 删除失败的txt文件
                            files_to_delete.append(txt_file_path)  # 记录需要删除的txt文件

                except Exception as e:
                    # 删除失败的txt文件
                    files_to_delete.append(txt_file_path)  # 记录需要删除的txt文件
                    messagebox.showerror("错误", f"处理 {filename} 时出错: {e}")

    # 最后清理无效文件
    clean_up_files(selected_folder)
    messagebox.showinfo("完成", "所有txt文件已拆分并保存为.atlas和.json文件！")

# 主程序入口
root = tk.Tk()
root.title("uexp 文件处理器")

# 设置窗口大小并锁定
root.geometry("400x250")
root.resizable(False, False)  # 锁定窗口大小
center_window(root)  # 居中窗口

# 标签和合并按钮
label = tk.Label(root, text="请选择包含 .uexp 文件的文件夹并处理")
label.pack(pady=20)

# 合并按钮
btn_process = tk.Button(root, text="选择文件夹并处理为UTF-8的txt和拆分为.atlas与.json", command=process_files_combined)
btn_process.pack(pady=10)

# 启动GUI主循环
root.mainloop()
