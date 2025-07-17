import subprocess
from os import path, getcwd, remove, walk
import json
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from config_manager import cfg
from pathlib import Path

SPINE_EXE = cfg.get("spine_path")
ffm_path = str(cfg.get("ffm_path"))
with open("res/template.export.json", 'r', encoding='utf-8') as f:
    ejtdata = json.load(f)


def convert_mov_to_mp4(mov_path):
    """使用 ffmpeg 将 .mov 转换为 .mp4 格式"""
    output_file = path.splitext(mov_path)[0] + ".mp4"
    cmd = [
        ffm_path, "-i", str(mov_path),
        "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-strict", "experimental", str(output_file)
    ]
    logger.info(f"🚀 转换 MOV 到 MP4: {path.basename(mov_path)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode == 0:
            logger.success(f"✅ 转换成功: {output_file}")
        else:
            logger.error(f"❌ 转换失败 (退出码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误信息:\n{result.stderr.strip()}")
    except Exception as e:
        logger.error(f"❌ 转换过程中出错: {e}")


def exportSpineJson(input_json_path, out_path=None):
    _INPUT_JSON = input_json_path
    Export_JSON = path.splitext(input_json_path)[0] + ".export.json"
    OUTPUT_SPINE = path.splitext(input_json_path)[0] + ".spine"

    cmd = [
        SPINE_EXE,
        "-i", _INPUT_JSON,
        "-o", OUTPUT_SPINE,
        "-r", "cache"
    ]
    try:
        print(f"正在导入 {_INPUT_JSON} 到 Spine 项目...")
        subprocess.run(cmd, check=True)
        print(f"成功创建 Spine 项目: {OUTPUT_SPINE}")
    except subprocess.CalledProcessError as e:
        print(f"导入失败: {e}")
        return
    except Exception as e:
        print(f"发生错误: {e}")
        return

        # 读取JSON文件
    with open(_INPUT_JSON, 'r', encoding='utf-8') as file:
        ijdata = json.load(file)
    ejdata = dict(ejtdata)
    if len(ijdata["animations"]) == 1:
        if out_path:
            _path = path.join(out_path, Path(_INPUT_JSON).name)
        else:
            _path = _INPUT_JSON
        ejdata["output"] = _path.replace(".json", ".mov")
    else:
        if out_path:
            ejdata["output"] = out_path
        else:
            ejdata["output"] = Path(_INPUT_JSON).parent
    ejdata["project"] = OUTPUT_SPINE
    with open(Export_JSON, 'w', encoding='utf-8') as file:
        json.dump(ejdata, file, ensure_ascii=False, indent=4)
    cmd = [
        SPINE_EXE,
        "-e", Export_JSON
    ]
    try:
        print(f"正在渲染导出 {_INPUT_JSON} ...")
        subprocess.run(cmd, check=True)
        print(f"成功导出: {_INPUT_JSON}")
    except subprocess.CalledProcessError as e:
        print(f"导入失败: {e}")
        return
    except Exception as e:
        print(f"发生错误: {e}")
        return
    remove(Export_JSON)
    remove(OUTPUT_SPINE)
    mov_file = ejdata["output"]
    if path.isfile(mov_file):
        convert_mov_to_mp4(mov_file)
    else:
        mov_list = []

        # 遍历文件夹
        for root, dirs, files in walk(mov_file):
            for file in files:
                # 检查文件扩展名是否为.mov（不区分大小写）
                if file.lower().endswith('.mov'):
                    # 获取文件的完整路径并添加到列表
                    full_path = path.join(root, file)
                    mov_list.append(full_path)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(convert_mov_to_mp4, i)
                for i in mov_list
            ]
            # 可选：等待所有任务完成（with 语句会自动等待）
            for future in futures:
                future.result()  # 检查是否有异常


def sjemain():
    max_workers = cfg.get("max_workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务到线程池，并传入索引 i
        futures = [
            executor.submit(exportSpineJson, json_file, None)
            for json_file in cfg.Json_list
        ]

        # 可选：等待所有任务完成（with 语句会自动等待）
        for future in futures:
            future.result()  # 检查是否有异常


# 使用示例
if __name__ == "__main__":
    # INPUT_JSON = r"E:\Unpack\尘白禁区\登录界面spine\sp_login_bg019\sp_login_bg019.json"
    # exportSpineJson(INPUT_JSON)
    convert_mov_to_mp4(r"E:\Unpack\尘白禁区\登录界面spine\sp_login_bg019\sp_login_bg019.mov")
