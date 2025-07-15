import subprocess
import os
game_content = r"E:\Unpack\尘白禁区\2.7\Game\Content\Plot\CgPlot\Login_Plots\PoltAsset\Bg"

from PIL import Image

def convert_to_png(input_path, output_path):
    try:
        img = Image.open(input_path)
        img.save(output_path, "PNG")
        print(f"转换成功: {output_path}")
    except Exception as e:
        print(f"转换失败: {e}")

# 批量图片解包
for file in os.listdir(game_content):
    if file.endswith(".uexp"):
        file_name = os.path.splitext(file)[0]
        print(file_name)
        subprocess.run([
            r"D:\Program Files (Green)\umodel_win32\umodel_64.exe",
            f"-path={game_content}",
            "-game=ue4.26",
            "-export",
            f"-out={game_content}",
            file_name
        ])
        convert_to_png(
            os.path.join(game_content, file.replace(".uexp", ".tga")),
            os.path.join(game_content, file.replace(".uexp", ".png"))
        )
        os.remove(os.path.join(game_content, file.replace(".uexp", ".tga")))
