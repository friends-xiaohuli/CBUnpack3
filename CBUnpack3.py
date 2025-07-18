from os import (path, listdir, remove,
                makedirs, cpu_count)
import shutil
import subprocess
import sys
from loguru import logger
from convert import convert_to_png, convert_spine
from config_manager import ConfigManager
from check import check_tool_availability
from concurrent.futures import ThreadPoolExecutor

# 运行根目录
if '__compiled__' in globals():
    root_directory = sys.path[0]
else:
    root_directory = path.dirname(path.abspath(__file__))

cfg = ConfigManager()
vgm_path = str(cfg.get("vgm_path"))
ffm_path = str(cfg.get("ffm_path"))
UseCNName = cfg.get("UseCNName")


# 工具函数：检查路径
def check_dir(_path: str, desc: str) -> bool:
    if not path.isdir(_path):
        logger.warning(f"{desc} 不存在，跳过：{_path}")
        return False
    return True


def activity_ui(rootpath, out_path):
    _p1 = path.join(rootpath, r"Game\Content\Plot\CgPlot")
    _p2 = path.join(out_path, "CgPlot")
    if not check_dir(_p1, "CG动画资源"):
        return
    makedirs(_p2, exist_ok=True)

    try:
        for entry in listdir(_p1):
            if entry == "Login_Plots":
                continue
            pdp1 = path.join(_p1, entry)
            if not path.isdir(pdp1):
                continue
            pdp2 = path.join(_p2, entry)
            polt_asset = path.join(pdp1, "PoltAsset")
            if path.isdir(polt_asset):
                bg = path.join(polt_asset, "Bg")
                if path.isdir(bg):
                    convert_to_png(bg, path.join(pdp2, "Bg"))
                convert_spine(path.join(polt_asset, "Spine"), pdp2)
            else:
                convert_to_png(pdp1, pdp2)
                convert_spine(pdp1, pdp2)
    except Exception as e:
        logger.error(f"[activity_ui] 出现异常: {e}")


def login_ui(rootpath, out_path):
    _p1 = path.join(rootpath, r"Game\Content\Plot\CgPlot\Login_Plots\PoltAsset\Bg")
    _p2 = path.join(out_path, r"Login_Plots\Bg")
    if not check_dir(_p1, "开始页面动画资源"):
        return
    makedirs(_p2, exist_ok=True)
    convert_to_png(_p1, _p2)
    _p1 = path.join(rootpath, r"Game\Content\Plot\CgPlot\Login_Plots\PoltAsset\Spine")
    _p2 = path.join(out_path, r"Login_Plots")
    convert_to_png(_p1, _p2)
    convert_spine(_p1, _p2)


def chara(rootpath, out_path):
    _p1 = path.join(rootpath, r"Game\Content\Spine\Hero")
    _p2 = path.join(out_path, "Hero")
    if not check_dir(_p1, "角色Spine资源"):
        return
    makedirs(_p2, exist_ok=True)
    convert_to_png(_p1, _p2)
    convert_spine(_p1, _p2)


def ser(rootpath, out_path):
    _p1 = path.join(rootpath, r"Game\Content\UI\Pose\Ser")
    _p2 = path.join(out_path, "Ser")
    if not check_dir(_p1, "Ser 姿势图像"):
        return
    makedirs(_p2, exist_ok=True)
    convert_to_png(_p1, _p2)


def fashion(rootpath, out_path):
    _p1 = path.join(rootpath, r"Game\Content\UI\Pose\Fashion")
    _p2 = path.join(out_path, "Fashion")
    if not check_dir(_p1, "Fashion 姿势图像"):
        return
    makedirs(_p2, exist_ok=True)
    convert_to_png(_p1, _p2)


def dialogue(rootpath, out_path):
    _p1 = path.join(rootpath, r"Game\Content\UI\Picture\Dialogue")
    _p2 = path.join(out_path, "Dialogue")
    if not check_dir(_p1, "对话框图像"):
        return
    makedirs(_p2, exist_ok=True)
    convert_to_png(_p1, _p2)


def convert_audio_single(oldn, newn, path_out):
    wav_path = path.join(path_out, f"{newn}.wav")
    wem_path = path.join(path_out, f"{oldn}.wem")
    flac_path = path.join(path_out, f"{newn}.flac")

    if not path.exists(wem_path):
        logger.warning(f"[×] 缺失 .wem 文件: {wem_path}，跳过")
        return

    try:
        logger.info(f"[→] 正在解码 {newn}.wem 为 WAV...")
        subprocess.run([vgm_path, "-o", wav_path, wem_path], check=True, stdout=subprocess.DEVNULL)
        logger.info(f"[✓] 已生成临时 WAV: {wav_path}")

        logger.info(f"[→] 正在转换 WAV 为 FLAC: {flac_path}")
        subprocess.run([ffm_path, "-y", "-i", wav_path, "-c:a", "flac", flac_path],
                       check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        logger.success(f"[✔] 成功转换 {newn}.wem → {newn}.flac")

    except subprocess.CalledProcessError as e:
        logger.error(f"[✖] 转换失败: {newn} - 命令错误 {e}")
    except Exception as e:
        logger.exception(f"[✖] 未知错误: {newn} - {e}")

    finally:
        for tmp in [wav_path, wem_path]:
            if path.exists(tmp):
                remove(tmp)
                logger.debug(f"[清理] 删除临时文件: {tmp}")


def bgm(rootpath, out_path):
    _p1 = path.join(rootpath, r"Game\Content\Wwise\Windows")
    _p2 = path.join(out_path, "BGM")
    if not check_dir(_p1, "音频目录"):
        return
    makedirs(_p2, exist_ok=True)

    wem_files = [f for f in listdir(_p1) if f.endswith(".wem")]
    if not wem_files:
        logger.warning("未找到任何 WEM 文件，跳过音频处理")
        return

    for wem in wem_files:
        shutil.copy(path.join(_p1, wem), path.join(_p2, wem))

    wem_names = [path.splitext(f)[0] for f in wem_files]
    logger.info(f"共提取 {len(wem_names)} 个音频")

    # 读取 BGM.txt
    txt_path = path.join(_p1, "BGM.txt")
    if not path.isfile(txt_path):
        logger.warning("未找到 BGM.txt，跳过生成 sheet.txt")
        return
    # print(_list)
    _path = path.join(rootpath, r"Game\Content\Wwise\Windows\BGM.txt")
    _m3u = open(_path, 'r+', encoding='utf-8')
    _sheet = []
    for _line in _m3u:
        for i in wem_names:
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

    _path = path.join(rootpath, r"Game\Content\Settings\language\riki.txt")
    _txt = open(_path, 'r+', encoding='utf-8')
    _dict = {}
    for _line in _txt:
        if "BGM_DLC" in _line and "_name" in _line:
            sl = _line.split("\t")
            _dict[sl[0]] = sl[1]
    _path = path.join(rootpath, r"Game\Content\Settings\riki\Riki.txt")
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
    # 写出 sheet.txt
    sheet_path = path.join(out_path, "全中文名对照.txt")
    with open(sheet_path, 'w', encoding='utf-8') as f:
        for i in _lines1:
            f.write("\t".join(i) + "\n")
    logger.success(f"[✔] 已生成标签文件: {sheet_path}")

    _dict = {}
    for l1, _, l2 in _lines1:
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
    sheet_path = path.join(out_path, "全音乐文件信息对照.txt")
    with open(sheet_path, 'w', encoding='utf-8') as f:
        for i in _sheet:
            f.write("\t".join(i) + "\n")
    logger.success(f"[✔] 已生成标签文件: {sheet_path}")

    # 写出 sheet.txt
    sheet_path = path.join(out_path, "未成功匹配的中文名对照.txt")
    with open(sheet_path, 'w', encoding='utf-8') as f:
        for i in _lines1:
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
        nnli = list(wem_names)
    # print("_sheet:", _sheet)
    # print("nnli:", nnli)
    # return
    # 解码 wem → flac
    max_workers = min(32, (cpu_count() or 1) * 4)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务到线程池，并传入索引 i
        futures = [
            executor.submit(convert_audio_single, oldn, newn, _p2)
            for oldn, newn in zip(wem_names, nnli)
        ]

        # 可选：等待所有任务完成（with 语句会自动等待）
        for future in futures:
            future.result()  # 检查是否有异常


def CBUNpakMain():
    input_path = str(cfg.get("unpack_path"))
    out_path = str(cfg.get("resource_path"))

    if not check_dir(input_path, f"根目录 {input_path}"):
        logger.critical("终止处理：输入目录无效")
        return

    if check_tool_availability() != 0:
        logger.critical("终止处理：存在无效工具目录")
        return

    logger.info("开始资源解包流程...")

    activity_ui(input_path, out_path)
    login_ui(input_path, out_path)
    bgm(input_path, out_path)
    chara(input_path, out_path)
    ser(input_path, out_path)
    fashion(input_path, out_path)
    dialogue(input_path, out_path)

    logger.success("资源处理完成 ✅")
