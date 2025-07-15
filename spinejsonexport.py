import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from loguru import logger
from typing import Optional

from config_manager import ConfigManager

# ================== 可配置区 ==================
cfg = ConfigManager()
ffm_path = str(cfg.get("ffm_path"))  # 获取配置中的 FFMPEG 路径
spine_path = str(cfg.get("spine_path"))  # 获取配置中的 FFMPEG 路径
SPINE_EXE = spine_path # Spine 可执行文件
VERSION = "3.8.75"  # 须与安装包版本一致
DEFAULT_OUTPUT_DIR = "export"  # 默认输出目录
DEFAULT_TEMPLATE_NAME = "template.export.json"  # 自动生成的模板文件名
CLEANUP = False  # 是否执行动画清理
BASE_DIR = Path(r"H:\SnowbreakContainmentZone\GameUnpack-master\CBUnpack3\out")
# =============================================


def convert_mov_to_mp4(mov_file: Path, output_dir: Path) -> Optional[Path]:
    """使用 ffmpeg 将 .mov 转换为 .mp4 格式"""
    output_file = output_dir / f"{mov_file.stem}.mp4"
    cmd = [
        ffm_path, "-i", str(mov_file),
        "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-strict", "experimental", str(output_file)
    ]
    logger.info(f"🚀 转换 MOV 到 MP4: {mov_file.name}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode == 0:
            logger.success(f"✅ 转换成功: {output_file}")
            return output_file
        else:
            logger.error(f"❌ 转换失败 (退出码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误信息:\n{result.stderr.strip()}")
            return None
    except Exception as e:
        logger.error(f"❌ 转换过程中出错: {e}")
        return None


def is_export_json(json_path: Path) -> bool:
    """判断文件是否为合法的 Spine 导出配置（class 以 export- 开头）"""
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, dict) and data.get("class", "").startswith("export-")
    except Exception as e:
        logger.warning(f"❌ 解析 export.json 出错：{json_path} | {e}")
        return False

def collect_projects(base_dir: Path) -> List[Tuple[Path, Dict[str, Union[Path, List[Path]]]]]:
    """扫描 BASE_DIR，收集包含 project/skeleton/atlas/images 的目录"""
    projects = []
    logger.info(f"🔍 开始扫描目录: {base_dir}")

    # 使用 pathlib 递归遍历目录
    for folder in base_dir.rglob("*"):
        if not folder.is_dir():
            continue
            
        project_info = {
            "projects": [],
            "skeletons": [],
            "atlases": [],
            "images": None,
            "exports": [],
        }
        
        # 检查是否有 images 目录
        images_dir = folder / "images"
        if images_dir.is_dir():
            project_info["images"] = images_dir

        # 收集目录下的所有相关文件
        for file in folder.iterdir():
            if not file.is_file():
                continue
                
            file_lower = file.name.lower()
            
            if file_lower.endswith(".spine"):
                project_info["projects"].append(file)
                
            elif file_lower.endswith(".skel") or file_lower.endswith(".json"):
                if is_export_json(file):
                    project_info["exports"].append(file)
                else:
                    project_info["skeletons"].append(file)
                    
            elif file_lower.endswith(".atlas"):
                project_info["atlases"].append(file)

        # 只将含有项目或骨架文件的目录存入项目列表
        if project_info["projects"] or project_info["skeletons"]:
            projects.append((folder, project_info))
            logger.debug(f"发现项目目录: {folder}")

    return projects

def build_export_template(img_dir: Path, output_dir: Path, base_name: str) -> dict:
    """
    构造 Spine 视频导出配置（MOV / PNG 动画帧序列）
    """
    return {
        "class": "export-mov",
        "name": "MOV",
        "output": str(output_dir / f"{base_name}.mov"),
        "images": str(img_dir),
        "open": False,
        "exportType": "animation",
        "skeletonType": "separate",
        "skeleton": None,
        "animationType": "all",
        "animation": None,
        "skinType": "current",
        "skinNone": False,
        "skin": None,
        "maxBounds": False,
        "renderImages": True,
        "renderBones": False,
        "renderOthers": False,
        "linearFiltering": True,
        "scale": 100,
        "fitWidth": 0,
        "fitHeight": 0,
        "enlarge": False,
        "background": None,
        "fps": 30,
        "lastFrame": False,
        "cropX": 0,
        "cropY": 0,
        "cropWidth": 0,
        "cropHeight": 0,
        "rangeStart": -1,
        "rangeEnd": -1,
        "pad": False,
        "msaa": 2,
        "outputType": "filePerAnimation",
        "animationRepeat": 1,
        "animationPause": 0,
        "encoding": "PNG",
        "quality": 0,
        "compression": 6,
        "audio": False
    }

def ensure_export_json(folder: Path, project_info: dict, atlas_path: Path) -> Optional[Path]:
    """生成 export-mov 模板配置文件并强制覆盖旧的"""
    img_dir = project_info["images"]
    if not img_dir or not img_dir.is_dir():
        logger.warning(f"⚠️ 缺少 images 目录，无法生成导出模板: {folder}")
        return None

    output_dir = folder / DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = folder.name
    template = build_export_template(img_dir, output_dir, base_name)
    tmpl_path = folder / DEFAULT_TEMPLATE_NAME

    try:
        # 强制覆盖写入模板配置
        with tmpl_path.open("w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        return tmpl_path
    except Exception as e:
        logger.error(f"❌ 写入模板失败: {e}")
        return None

def run_spine(cmd: List[str], project_name: str):
    """执行 Spine 导出命令"""
    logger.info(f"🚀 开始导出项目: {project_name}")
    logger.debug("执行命令: " + " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd))
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            errors="replace"
        )
        
        if result.returncode == 0:
            logger.success(f"✅ {project_name} 导出成功")
        else:
            logger.error(f"❌ {project_name} 导出失败 (退出码: {result.returncode})")
            if result.stderr:
                logger.error(f"错误信息:\n{result.stderr.strip()}")
    except Exception as e:
        logger.error(f"❌ 调用 Spine 进程异常: {e}")

def _export_single(folder: Path, project_info: dict, input_file: Path, file_type: str):
    """处理单个输入文件的导出"""
    logger.info(f"\n{'='*40}\n📂 处理 {file_type}: {input_file.name}")
    
    # 检查必备文件
    if not project_info["atlases"]:
        logger.warning("⚠️ 缺少 .atlas 文件，跳过")
        return
        
    atlas_file = project_info["atlases"][0]
    logger.debug(f"使用的 atlas 文件: {atlas_file.name}")

    # 准备导出配置
    export_json = ensure_export_json(folder, project_info, atlas_file)
    
    if not export_json:
        logger.warning("⚠️ 无法获得导出设置，跳过")
        return

    logger.info(f"📝 生成的 export.json 文件路径: {export_json}")

    cmd = [
        str(SPINE_EXE),
        "--update", VERSION,
        "--input", str(input_file),
        "--export", str(export_json)
    ]
    
    if CLEANUP:
        cmd.append("--clean")

    run_spine(cmd, input_file.stem)

    # 转换 MOV 文件为 MP4
    mov_file = folder / DEFAULT_OUTPUT_DIR / f"{input_file.stem}.mov"
    if mov_file.exists():
        convert_mov_to_mp4(mov_file, folder / DEFAULT_OUTPUT_DIR)

def export_bundle(folder: Path, project_info: dict):
    """处理单个目录的导出任务"""
    for project_file in project_info["projects"]:
        _export_single(folder, project_info, project_file, "项目文件")
    
    if not project_info["projects"]:
        for skeleton_file in project_info["skeletons"]:
            _export_single(folder, project_info, skeleton_file, "骨架文件")


# ========================== 主流程 ==========================
def main():
    logger.info("🚀 Spine 批量导出工具启动")
    logger.info(f"基础目录: {BASE_DIR}")
    logger.info(f"Spine 版本: {VERSION}")
    logger.info(f"清理模式: {'开启' if CLEANUP else '关闭'}")

    projects = collect_projects(BASE_DIR)
    logger.info(f"🔍 共发现 {len(projects)} 个项目目录")

    if not projects:
        logger.warning("⚠️ 未找到任何可导出的项目，程序退出")
        return

    for folder, project_info in projects:
        logger.info(f"🎬 开始处理目录: {folder}")
        export_bundle(folder, project_info)

    logger.success("🏁 全部导出任务完成")


if __name__ == "__main__":
    main()
