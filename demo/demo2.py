from tkinter import filedialog
import os


def convert(_input_path):
    spine_path = r"D:\Kin-project\Krename\uexp_to_Spine\sptem.spine"
    spine_config_tem = r"D:\Kin-project\Krename\uexp_to_Spine\spine-config.json"
    for root, dirs, files in os.walk(_input_path):
        # print(f"当前目录: {root, dirs, files}")
        for file in files:
            ba, suf = os.path.splitext(file)
            if suf == ".skel":
                skel_path = os.path.join(root, file)
                sk_name = os.path.splitext(file)[0]
                if os.path.exists(spine_path):
                    os.remove(spine_path)
                cmd1 = f'Spine -i {skel_path} -o {spine_path} -r {sk_name}'
                os.system(cmd1)
                cmd2 = f'Spine -i {spine_path} -o {root} -e {spine_config_tem}'
                os.system(cmd2)
                json_path = os.path.splitext(skel_path)[0]+".json"
                print(f'Convert: {skel_path} -> {json_path}')
            else:
                continue


# 将目录中skel文件转化为json
if __name__ == '__main__':
    # spine安装路径
    new_directory = r"D:\Program Files (Green)\spinepro_3.8.75"
    os.chdir(new_directory)
    input_path = filedialog.askdirectory(title="选择需要批量转化的目录")
    convert(input_path)
