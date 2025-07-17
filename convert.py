from os import (path, listdir, walk,
                cpu_count, remove, makedirs)
import subprocess
import binascii
from loguru import logger
from PIL import Image
from config_manager import cfg
from atlas_unpack import split_atlas
from concurrent.futures import ThreadPoolExecutor
import json


# 工具函数：检查目录是否存在
def check_dir(_path: str, desc: str) -> bool:
    if not path.isdir(_path):
        logger.warning(f"{desc} 不存在，跳过：{_path}")
        return False
    return True


def png_convert(file_path, out_path):
    import tempfile

    root, name = path.split(file_path)
    file_name = path.splitext(name)[0]
    umo_path = str(cfg.get("umo_path"))

    if not path.isfile(umo_path):
        logger.critical(f"[路径无效] UModel 路径不存在: {umo_path}")
        return

    if not path.exists(root):
        logger.critical(f"[路径无效] 文件所在目录不存在: {root}")
        return

    if not path.exists(file_path):
        logger.critical(f"[目标文件缺失] 指定文件不存在: {file_path}")
        return

    try:
        # 使用临时文件收集stderr
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as err_log:
            subprocess.run([
                umo_path,
                f"-path={root}",
                "-game=ue4.26",
                "-export",
                f"-out={out_path}",
                file_name
            ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=err_log)

            # 检查是否导出成功的 .tga 文件
            tga_candidates = [f for f in listdir(out_path) if f.endswith('.tga') and file_name in f]
            if not tga_candidates:
                logger.error(f"[TGA 导出失败] 未生成任何匹配 TGA 文件（{file_name}.tga）")
                return

            tga = path.join(out_path, tga_candidates[0])
            png = path.join(out_path, f"{file_name}.png")

            try:
                img = Image.open(tga)
                img.save(png, "PNG")
                logger.success(f"[成功] PNG 生成成功: {png}")
                remove(tga)
            except Exception as e:
                logger.error(f"[图像处理失败] 无法处理 TGA 文件 {tga} → {e}")

    except subprocess.CalledProcessError as e:
        err_log.seek(0)
        error_output = err_log.read().strip()
        logger.error(f"[UModel 执行失败] 导出命令返回码 {e.returncode}")
        if error_output:
            logger.debug(f"[UModel stderr]\n{error_output}")
        else:
            logger.warning(f"[无详细错误] 可能原因包括：文件名错误、未识别的资源或格式不兼容")

    except FileNotFoundError:
        logger.error(f"[文件缺失] TGA 文件未生成，或路径错误: {file_name}.tga")

    except Exception as e:
        logger.exception(f"[未知错误] 在转换过程中发生异常: {e}")


def convert_png_single(file, root, input_path, output_path):
    out_dir = path.join(output_path, root.replace(input_path, "").strip("\\"))
    makedirs(out_dir, exist_ok=True)
    png_convert(path.join(root, file), out_dir)


def convert_to_png(input_path, output_path):
    if not check_dir(input_path, "输入目录"):
        return
    _file_list = []
    for root, dirs, files in walk(input_path):
        for file in files:
            if file.endswith(".uexp") and "_144." not in file:
                _file_list.append([file, root])

    max_workers = min(32, (cpu_count() or 1) * 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务到线程池，并传入索引 i
        futures = [
            executor.submit(convert_png_single, file, root, input_path, output_path)
            for file, root in _file_list
        ]

        # 可选：等待所有任务完成（with 语句会自动等待）
        for future in futures:
            future.result()  # 检查是否有异常


def split_and_save(text_data, clean_filename):
    try:
        # 查找文件内容
        start_png = text_data.find(f'{clean_filename}.png')
        end_atlas = text_data.rfind('index: -1') + len('index: -1')
        atlas_content = text_data[start_png:end_atlas] if start_png != -1 and end_atlas != -1 else ''

        start_json = text_data.find('{\n"skeleton": {')
        if start_json == -1:
            start_json = text_data.find('{"skeleton":{"hash":')  # 修改匹配条件
        end_json = text_data.rfind('}')
        json_content = text_data[start_json:end_json + 1] if start_json != -1 and end_json != -1 else ''
        return atlas_content, json_content
    except Exception as e:
        logger.error(f"拆分和保存时出现异常: {e}")
        return False, False


def convert_spine_single(filename, root, input_path, output_path):
    file_path = path.join(root, filename)
    try:
        with open(file_path, 'rb') as file:
            hex_data = binascii.hexlify(file.read())
            text_data = bytes.fromhex(hex_data.decode('utf-8')).decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return

    # 尝试拆分并保存为 atlas 和 json 文件
    original_filename = path.splitext(filename)[0]
    clean_filename = original_filename.replace('-atlas', '').replace('-data', '')
    atlas_content, json_content = split_and_save(text_data, clean_filename)

    out_dir = path.join(output_path, root.replace(input_path, "").strip("\\"))
    makedirs(out_dir, exist_ok=True)

    # 保存 atlas 文件
    if atlas_content:
        atlas_filename = f"{clean_filename}.atlas"
        atlas_path = path.join(out_dir, atlas_filename)
        with open(atlas_path, 'w', encoding='utf-8') as atlas_file:
            atlas_file.write(atlas_content)

    # 保存 json 文件
    if json_content:
        json_filename = f"{clean_filename}.json"
        json_path = path.join(out_dir, json_filename)
        _dict = json.loads(json_content)
        _dict["images"] = "./images/"
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json_file.write(json.dumps(_dict))
            cfg.Json_list.append(json_path)


def convert_atlas_single(filename, root):
    atlas_path = path.join(root, filename)
    unit_name = path.split(filename)[1]
    output_path_images = path.join(root, 'images')
    makedirs(output_path_images, exist_ok=True)
    split_atlas(unit_name, output_path=output_path_images, atlas_path=atlas_path)


def convert_spine(input_path, output_path):
    if not check_dir(input_path, "输入路径"):
        return
    _file_list = []
    for root, dirs, files in walk(input_path):
        for filename in files:
            if filename.endswith(".uexp") and "_a" not in filename:
                _file_list.append([filename, root])
    max_workers = min(32, (cpu_count() or 1) * 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务到线程池，并传入索引 i
        futures = [
            executor.submit(convert_spine_single, filename, root, input_path, output_path)
            for filename, root in _file_list
        ]

        # 可选：等待所有任务完成（with 语句会自动等待）
        for future in futures:
            future.result()  # 检查是否有异常

    convert_to_png(input_path, output_path)
    _file_list = []
    # 拆分 atlas 文件
    for root, dirs, files in walk(output_path):
        for filename in files:
            if filename.endswith(".atlas"):
                _file_list.append([filename, root])
    max_workers = min(32, (cpu_count() or 1) * 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务到线程池，并传入索引 i
        futures = [
            executor.submit(convert_atlas_single, filename, root)
            for filename, root in _file_list
        ]

        # 可选：等待所有任务完成（with 语句会自动等待）
        for future in futures:
            future.result()  # 检查是否有异常


if __name__ == '__main__':
    # convert_to_png(r"E:\Unpack\尘白禁区\cache\step1\Game\Content\UI\Picture\DLC30",
    #                r"E:\Unpack\尘白禁区\DLC30")
    # convert_spine(r"E:\Unpack\尘白禁区\step1\Game\Content\Plot\CgPlot\Dlc17_plots\PoltAsset\spine",
    #               r"E:\Unpack\尘白禁区\活动界面spine")
    # convert_to_png(r"H:\SnowbreakContainmentZone\V3.0.0.130-20250710\UNPAK\Game\Content\UI\Pose",
    #                r"H:\SnowbreakContainmentZone\V3.0.0.130-20250710\UNPAK\Game\Content\UI\Pose\img")
    logger.debug("程序已退出")
