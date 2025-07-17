from os import (path, listdir, remove,
                makedirs, cpu_count)
import shutil
import subprocess
import sys
from loguru import logger
from convert import convert_to_png, convert_spine
from config_manager import cfg
from check import check_tool_availability
from concurrent.futures import ThreadPoolExecutor

# 运行根目录
if '__compiled__' in globals():
    root_directory = sys.path[0]
else:
    root_directory = path.dirname(path.abspath(__file__))
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
                _ = [_l[1], _l[2]] + _l[2].split("_")
                while len(_) < 6:
                    _.append("")
                _sheet.append(_)

    # print(_sheet)
    dlcstr = ""
    for i in _sheet:
        if "DLC" in i[3]:
            dlcstr = "BGM_" + i[3] + "_name"
            break
    if dlcstr:
        _path = path.join(rootpath, r"Game\Content\Settings\riki\Riki.txt")
        _txt = open(_path, 'r+', encoding='utf-8')
        _lines1 = []
        for _line in _txt:
            if dlcstr in _line:
                __ = _line.split("\t")
                __ = __[9].split("|")[-1], __[10].split(".")[-1]
                _lines1.append(__)
                # print(__)
        _path = path.join(rootpath, r"Game\Content\Settings\language\riki.txt")
        _txt = open(_path, 'r+', encoding='utf-8')
        _lines2 = []
        for _line in _txt:
            if dlcstr in _line:
                _lines2.append(_line.strip().split("\t"))
                # print(_line.strip().split("\t"))
        lines = []
        linesnum = 0
        for i in _lines2:
            for u in _lines1:
                if i[0] == u[1]:
                    if "DLC" not in u[0]:
                        linesnum += 1
                    lines.append(i + [u[0]])
                    break
        # print(lines)
        _sheetsnum = 0
        for i in _sheet:
            if "Story" == i[3]:
                _sheetsnum += 1
        flag = True if _sheetsnum == linesnum else False
        # print("flag", flag, _sheetsnum, linesnum)
        _n1 = 0
        for n, i in enumerate(_sheet):
            for u in lines:
                if i[3] + "_" + i[4] == u[2]:
                    _sheet[n].extend(["", u[1]])
                    break
            else:
                if flag and i[3] == 'Story':
                    # print(i)
                    _n = int(_n1)
                    for u in lines:
                        if "DLC" not in u[2]:
                            # print(u[2])
                            if not _n:
                                _n1 += 1
                                _sheet[n].extend(["", u[1]])
                                break
                            else:
                                _n -= 1

    # 写出 sheet.txt
    sheet_path = path.join(out_path, "sheet.txt")
    with open(sheet_path, 'w', encoding='utf-8') as f:
        for i in _sheet:
            f.write("\t".join(i) + "\n")
    logger.success(f"[✔] 已生成标签文件: {sheet_path}")

    if UseCNName:
        cnnali = [i[7] if len(i) == 8 else "" for i in _sheet]
        nnli = []
        for i in _sheet:
            if len(i) == 8 and 1 == cnnali.count(cnna := i[7]):
                nnli.append(f"{cnna} - 尘白禁区")
            else:
                nnli.append(i[0])
    else:
        nnli = list(wem_names)
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
