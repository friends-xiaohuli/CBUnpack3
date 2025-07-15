import os
import sys
import json
from loguru import logger

def get_root_directory():
    """获取程序根目录，支持打包和源码运行"""
    if '__compiled__' in globals():
        return sys.path[0]
    else:
        return os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = get_root_directory()

CONFIG_NAME = "config.json"


class ConfigManager:
    _REQUIRED_KEYS = ("ffm_path", "umo_path", "vgm_path","spine_path", "out_path", "input_path")
    _TEMPLATE = {
        "ffm_path":  r"{root}\tool\ffmpeg\bin\ffmpeg.exe",
        "umo_path":  r"{root}\tool\umodel\umodel_materials.exe",
        "vgm_path":  r"{root}\tool\vgmstream\vgmstream-cli.exe",
        "spine_path":  r"{root}\tool\spine\Spine.exe",
        "out_path":  r"{root}\out",
        "input_path": "NULL"
    }

    def __init__(self, filename: str = CONFIG_NAME) -> None:
        self.file = os.path.join(ROOT_DIR, filename)
        self.config: dict[str, str] = {}
        self._load_or_create()

    # ---------- public API ----------
    def get(self, key: str, default=None):
        """获取配置项，带键合法性与存在性检查"""
        if key not in self._REQUIRED_KEYS:
            logger.warning(f"尝试访问未知配置项: {key!r}")
            return default
        
        if key not in self.config:
            logger.warning(f"配置项 {key!r} 缺失，将返回默认值")
            return default

        return self.config.get(key, default)

    def set(self, key: str, value):
        if key not in self._REQUIRED_KEYS:
            logger.warning(f"非法配置键：{key!r}")
            return
        self.config[key] = value
        self._write(self.config)
        logger.info(f"已更新 {key} = {value}")

    def all(self) -> dict:
        return self.config.copy()

    def reset(self):
        """恢复出厂设置"""
        try:
            os.remove(self.file)
        except FileNotFoundError:
            logger.debug("配置文件本就不存在，跳过删除")
        except PermissionError as e:
            logger.error(f"权限不足，无法删除配置：{e}")
            return
        except OSError as e:
            logger.error(f"删除配置文件失败：{e}")
            return

        self._load_or_create()
        logger.success("> 配置文件已重置为默认")

    # ---------- internal ----------
    def _load_or_create(self):
        """尝试加载；如失败则一次性写入默认并加载"""
        need_create = False
        if not os.path.isfile(self.file):
            logger.info("首次运行：生成默认配置")
            need_create = True
        else:
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if self._validate_config(data):
                    self.config = data
                    logger.info("配置文件读取成功！")
                    return
                logger.warning("配置缺键或损坏，将重建")
                need_create = True
            except json.JSONDecodeError as e:
                logger.warning(f"配置解析失败({e}), 将重建")
                need_create = True
            except Exception as e:
                logger.error(f"读取配置异常：{e}")
                need_create = True

        if need_create:                         # 只在必要时写一次
            self._write(self._render_template())
            self.config = self._render_template()
            logger.info("默认配置已生成并载入")

    def _validate_config(self, data: dict) -> bool:
        """检查是否包含全部必需键"""
        return all(k in data for k in self._REQUIRED_KEYS)

    def _render_template(self) -> dict:
        """把 {root} 占位符替换成实际路径"""
        return {k: v.format(root=ROOT_DIR) for k, v in self._TEMPLATE.items()}

    def _write(self, data: dict):
        """写磁盘；确保目录存在"""
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        try:
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"写入配置文件失败：{e}")

def resource_path(relative_path: str) -> str:
    base_path = os.path.join(os.path.dirname(__file__), "res")
    logger.debug(f'资源目录：{base_path}')
    return os.path.join(base_path, relative_path)
