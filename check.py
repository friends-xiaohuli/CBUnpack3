from os import path
import subprocess
from config_manager import ConfigManager
from loguru import logger


def check_tool_availability() -> int:
    """
    检查配置文件中指定的工具路径是否有效并可运行。
    返回 0 表示所有工具均通过；返回 1 表示存在不可用的工具。
    """
    cfg = ConfigManager()
    tool_paths = {
        "FFmpeg":    (cfg.get("ffm_path"), ["-version"]),
        "vgmstream": (cfg.get("vgm_path"), []),
        "UModel":    (cfg.get("umo_path"), ["-help"]),
        "Spine":    (cfg.get("spine_path"), ["--help"]),
        "quickbms":    (cfg.get("quickbms_path"), [""]),
    }

    failed = False  # 标记是否有检查失败

    for tool, (exe, args) in tool_paths.items():
        logger.info(f"检查 {tool} …")

        if not exe or not path.isfile(exe):
            logger.error(f"[路径无效] {tool} 的路径配置错误或文件不存在：{exe}")
            failed = True
            continue

        cmd = [exe, *args]
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=8
            )

            output = proc.stdout.strip()
            # 对 UModel 特判输出内容
            passed = proc.returncode == 0 or ("Usage:" in output or "Options:" in output)

            if passed:
                logger.success(f"{tool} 可用 ✔️")
                logger.debug(f"{tool} 输出片段:\n" + "\n".join(output.splitlines()[0:5]))
            else:
                logger.error(f"{tool} 运行异常（返回码 {proc.returncode}）")
                failed = True

        except subprocess.TimeoutExpired:
            logger.error(f"[超时] {tool} 执行超时 ❌")
            failed = True
        except Exception as e:
            logger.exception(f"[异常] {tool} 执行失败: {e}")
            failed = True

    return 0 if not failed else 1

if __name__ == '__main__':
    check_tool_availability()