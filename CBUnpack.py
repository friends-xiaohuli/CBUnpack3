from os import path, makedirs, remove, listdir, cpu_count
from convert import convert_to_png, convert_spine, png_convert
import shutil
import subprocess
from loguru import logger
from config_manager import ConfigManager
from check import check_tool_availability
from concurrent.futures import ThreadPoolExecutor

cfg = ConfigManager()
UseCNName = cfg.get("UseCNName")
vgm_path = str(cfg.get("vgm_path"))


# 工具函数：检查路径
def check_dir(_path: str, desc: str) -> bool:
    if not path.isdir(_path):
        logger.warning(f"{desc} 不存在，跳过：{_path}")
        return False
    return True


def activity_ui(_past_path, _new_path, _increase_path):
    _path = r"Game\Content\Plot\CgPlot"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    path_out = path.join(_increase_path, "CgPlot")
    if path.exists(path_out):
        shutil.rmtree(path_out)
    makedirs(path_out)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            pdp1 = path.join(_p2, i)
            pdp2 = path.join(path_out, i)
            if path.exists(path.join(pdp1, "PoltAsset")):
                bg_path1 = path.join(pdp1, "PoltAsset", "Bg")
                bg_path2 = path.join(pdp2, "Bg")
                convert_to_png(bg_path1, bg_path2)
                sp_path1 = path.join(pdp1, "PoltAsset", "Spine")
                convert_spine(sp_path1, pdp2)
            else:
                convert_to_png(pdp1, pdp2)
                convert_spine(pdp1, pdp2)
    _path = r"Game\Content\UI\Picture"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[1]:
        for i in _list[1]:
            if "DLC" in i:
                inp = path.join(_p2, i)
                outp = path.join(path_out, i)
                convert_to_png(inp, outp)


def login_ui(_past_path, _new_path, _increase_path):
    path_out = path.join(_increase_path, "Login_Plots")
    if path.exists(path_out):
        shutil.rmtree(path_out)
    makedirs(path_out)
    _path = r"Game\Content\Plot\CgPlot\Login_Plots\PoltAsset\Bg"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            if i.endswith(".uexp"):
                png_convert(path.join(_p2, i), path_out)

    _path = r"Game\Content\Plot\CgPlot\Login_Plots\PoltAsset\Spine"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            pdp = path.join(_p2, i)
            path_out = path.join(_increase_path, f"Login_Plots\\{i}")
            convert_spine(pdp, path_out)


def ser(_past_path, _new_path, _increase_path):
    path_out = path.join(_increase_path, "Ser")
    if path.exists(path_out):
        shutil.rmtree(path_out)
    makedirs(path_out)
    _path = r"Game\Content\UI\Pose\Ser"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            if i.endswith(".uexp"):
                png_convert(path.join(_p2, i), path_out)


def fashion(_past_path, _new_path, _increase_path):
    path_out = path.join(_increase_path, "Fashion")
    if path.exists(path_out):
        shutil.rmtree(path_out)
    makedirs(path_out)
    _path = r"Game\Content\UI\Pose\Fashion"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            if i.endswith(".uexp"):
                png_convert(path.join(_p2, i), path_out)


def dialogue(_past_path, _new_path, _increase_path):
    path_out = path.join(_increase_path, "Dialogue")
    if path.exists(path_out):
        shutil.rmtree(path_out)
    makedirs(path_out)
    _path = r"Game\Content\UI\Picture\Dialogue"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            if i.endswith(".uexp"):
                png_convert(path.join(_p2, i), path_out)


def convert_audio_single(oldn, newn, path_out):
    try:
        # 1. 用 vgmstream 解码为 WAV
        wav_path = path.join(path_out, f"{newn}.wav")
        wem_path = path.join(path_out, f"{oldn}.wem")
        subprocess.run(
            [vgm_path, 
             "-o", wav_path,
             wem_path], check=True)

        # 2. 用 FFmpeg 转 WAV 为 FLAC
        subprocess.run([
            r"D:\Program Files\ffmpeg\ffmpeg.exe",
            "-i", wav_path,
            "-c:a", "flac",
            path.join(path_out, f"{newn}.flac")
        ])

    finally:
        if path.exists(wav_path):
            remove(wav_path)
        if path.exists(wem_path):
            remove(wem_path)


def bgm(_past_path, _new_path, _increase_path):
    path_out = path.join(_increase_path, "BGM")
    if path.exists(path_out):
        shutil.rmtree(path_out)
    makedirs(path_out)
    _path = r"Game\Content\Wwise\Windows"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            if i.endswith(".wem"):
                shutil.copy(path.join(_p2, i), path.join(_increase_path, f"BGM\\{i}"))
                ...
    _list = []
    for filename in listdir(path_out):
        if ".wem" in filename:
            _list += [filename.removesuffix(".wem")]
    # print(_list)
    _path = path.join(_new_path, r"Game\Content\Wwise\Windows\BGM.txt")
    _m3u = open(_path, 'r+', encoding='utf-8')
    _sheet = []
    for _line in _m3u:
        for i in _list:
            if i in _line:
                _l = _line.split("\t")
                _p = _l[5].split("\\")
                if "Chapter" in _p:
                    _la2 = _p[3:8]
                else:
                    _la2 = _p[3:6]
                _str = _l[2]
                if " " in _str:
                    _str = _str.split(" ")[0]
                _ = [_l[1], "|".join(_la2), _str] + _str.split("_")
                while len(_) < 8:
                    _.append("")
                _sheet.append(_)

    # print(_sheet)

    _path = path.join(_new_path, r"Game\Content\Settings\language\riki.txt")
    _txt = open(_path, 'r+', encoding='utf-8')
    _dict = {}
    for _line in _txt:
        if "BGM_DLC" in _line and "_name" in _line:
            sl = _line.split("\t")
            _dict[sl[0]] = sl[1]
    _path = path.join(_new_path, r"Game\Content\Settings\riki\Riki.txt")
    _txt = open(_path, 'r+', encoding='utf-8')
    _lines1 = []
    for _line in _txt:
        if "BGM|" in _line:
            __ = _line.split("\t")
            nameseq = __[10].split(".")[-1]
            labels = __[9].split("|")
            for n, i in enumerate(labels):
                labels[n] = i.split(",")[0]
            if "Fight|" in _line:
                label = "|".join(labels[:-1])
            else:
                label = "|".join(labels)
            _lines1.append([label, nameseq, _dict[nameseq]])

    _path = path.join(_past_path, r"Game\Content\Settings\language\riki.txt")
    _txt = open(_path, 'r+', encoding='utf-8')
    _dict = {}
    for _line in _txt:
        if "BGM_DLC" in _line and "_name" in _line:
            sl = _line.split("\t")
            _dict[sl[0]] = sl[1]
    _path = path.join(_past_path, r"Game\Content\Settings\riki\Riki.txt")
    _txt = open(_path, 'r+', encoding='utf-8')
    _lines2 = []
    for _line in _txt:
        if "BGM|" in _line:
            __ = _line.split("\t")
            nameseq = __[10].split(".")[-1]
            labels = __[9].split("|")
            for n, i in enumerate(labels):
                labels[n] = i.split(",")[0]
            if "Fight|" in _line:
                label = "|".join(labels[:-1])
            else:
                label = "|".join(labels)
            _lines2.append([label, nameseq, _dict[nameseq]])
    _lines0 = []
    for i in _lines1:
        if i not in _lines2:
            _lines0.append(i)

    # 写出 sheet.txt
    sheet_path = path.join(_increase_path, "增量音频中文名对照.txt")
    with open(sheet_path, 'w', encoding='utf-8') as f:
        for i in _lines0:
            f.write("\t".join(i) + "\n")
    logger.success(f"[✔] 已生成标签文件: {sheet_path}")

    _dict = {}
    for l1, _, l2 in _lines0:
        _l = l1.split("|")
        if len(_l) > 3:
            _d: dict = _dict.get("|".join(_l[:3]).lower(), {})
            _d["|".join(_l[3:]).lower()] = l2

            _dict["|".join(_l[:3]).lower()] = _d
        else:
            _dict[l1.lower()] = l2

    # print("_dict:", _dict)
    dd = set()
    for n, line in enumerate(_sheet):
        _str = line[1]
        if "Chapter" in _str:
            v1 = _dict.get("|".join(_str.split("|")[:3]).lower(), None)
        else:
            v1 = _dict.get(_str.lower(), None)
        if isinstance(v1, str):
            _sheet[n].append(v1)
            dd.add(v1)
            continue
        elif isinstance(v1, dict):
            if "Chapter" in _str:
                _cn = v1.get("|".join(_str.split("|")[3:]).lower(), None)
            else:
                _cn = v1.get(f"{line[4]}|{line[5]}".lower(), None)
            if isinstance(_cn, str):
                dd.add(_cn)
                _sheet[n].append(_cn)
                continue
            elif isinstance(_cn, dict):
                raise
        _cn = _dict.get(f"BGM|Story|{line[4]}_{line[5]}".lower(), None)
        if not _cn:
            _cn = _dict.get(f"BGM|UI|{line[4]}_{line[5]}".lower(), None)
        if isinstance(_cn, str):
            dd.add(_cn)
        else:
            _cn = ""
        _sheet[n].append(_cn)

    # print("num:", len(dd))
    # print("dd:", dd)

    # 写出 sheet.txt
    sheet_path = path.join(_increase_path, "增量音乐文件信息对照.txt")
    with open(sheet_path, 'w', encoding='utf-8') as f:
        for i in _sheet:
            f.write("\t".join(i) + "\n")
    logger.success(f"[✔] 已生成标签文件: {sheet_path}")

    # 写出 sheet.txt
    sheet_path = path.join(_increase_path, "未成功匹配的中文名对照.txt")
    with open(sheet_path, 'w', encoding='utf-8') as f:
        for i in _lines0:
            if i[2] not in dd:
                f.write("\t".join(i) + "\n")
    logger.success(f"[✔] 已生成标签文件: {sheet_path}")

    if UseCNName:
        cnnali = [i[8] if len(i) == 8 else "" for i in _sheet]
        nnli = []
        for i in _sheet:
            if len(i) == 8 and 1 == cnnali.count(cnna := i[8]):
                nnli.append(f"{cnna} - 尘白禁区")
            else:
                nnli.append(i[0])
    else:
        nnli = list(_list)

    max_workers = min(32, (cpu_count() or 1) * 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务到线程池，并传入索引 i
        futures = [
            executor.submit(convert_audio_single, oldn, newn, path_out)
            for oldn, newn in zip(_list, nnli)
        ]

        # 可选：等待所有任务完成（with 语句会自动等待）
        for future in futures:
            future.result()  # 检查是否有异常


def chara(_past_path, _new_path, _increase_path):
    path_out = path.join(_increase_path, "Hero")
    if path.exists(path_out):
        shutil.rmtree(path_out)
    makedirs(path_out)
    _path = r"Game\Content\Spine\Hero"
    _p1 = path.join(_past_path, _path)
    _p2 = path.join(_new_path, _path)
    _list = compare_folders_by_name(_p1, _p2)
    if _list[0]:
        print(f"删除：{_list[0]}")
    if _list[1]:
        for i in _list[1]:
            pdp = path.join(_p2, i)
            path_out = path.join(_increase_path, f"Hero\\{i}")
            convert_spine(pdp, path_out)


def compare_folders_by_name(dir1, dir2):
    """对比两个文件夹中的文件名差异"""
    # 获取两个文件夹中的文件列表
    files1 = set(listdir(dir1))
    files2 = set(listdir(dir2))

    # 找出差异
    only_in_dir1 = files1 - files2
    only_in_dir2 = files2 - files1
    common_files = files1 & files2
    return [only_in_dir1, only_in_dir2, common_files]


def CBUNpakIncr():
    past_path = str(cfg.get("past_path"))
    new_path = str(cfg.get("new_path"))
    increase_path = str(cfg.get("increase_path"))

    if not check_dir(past_path, f"根目录past {past_path}"):
        logger.critical("终止处理：past目录无效")
        return
    if not check_dir(new_path, f"根目录new {new_path}"):
        logger.critical("终止处理：new目录无效")
        return

    if check_tool_availability() != 0:
        logger.critical("终止处理：存在无效工具目录")
        return

    logger.info("开始资源解包流程...")

    activity_ui(past_path, new_path, increase_path)
    login_ui(past_path, new_path, increase_path)
    bgm(past_path, new_path, increase_path)
    chara(past_path, new_path, increase_path)
    ser(past_path, new_path, increase_path)
    fashion(past_path, new_path, increase_path)
    dialogue(past_path, new_path, increase_path)

    logger.success("资源处理完成 ✅")
