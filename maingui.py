"""
CB-UNpak Tool GUI
尘白禁区批量解包工具 - Qt6 图形界面

License: GNU General Public License Version 3
Copyright (C) 2025 friends-xiaohuli
"""

import sys
import re
from os import path, makedirs
from datetime import datetime
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QCheckBox, QRadioButton,
    QButtonGroup, QGroupBox, QTextEdit, QLineEdit, QSpinBox,
    QFileDialog, QMessageBox, QProgressBar, QScrollArea, QFrame,
    QSplitter, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat, QIcon

from loguru import logger
from config_manager import ConfigManager, resource_path
from CBUnpack3 import CBUNpakMain, activity_ui, login_ui, bgm, chara, ser, fashion, dialogue
from CBUnpack import CBUNpakIncr
from check import check_tool_availability
from convert import convert_to_png
from spinejsonexport2 import sjemain
import winsound

# 版本号
VER = "4.0.1"
BUILD = "2026-1"


# ======================== #
#      日志系统初始化        #
# ======================== #
def init_logger():
    """初始化日志系统：CMD详细输出，GUI简洁输出"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_directory = path.join(path.dirname(path.abspath(__file__)), "logs")
    makedirs(log_directory, exist_ok=True)
    log_path = path.join(log_directory, f"{today}.log")
    
    logger.remove()
    # CMD窗口：完整调试信息
    logger.add(sys.stderr, level="DEBUG", 
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    # 文件日志
    logger.add(log_path, encoding="utf-8", level="DEBUG",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}")
    logger.info(f"日志系统已初始化 -> {log_path}")


# ======================== #
#       GUI日志处理器        #
# ======================== #
class GUILogSignal(QThread):
    """日志信号发射器"""
    log_signal = pyqtSignal(str, str)  # (message, level)


class GUILogHandler:
    """
    GUI日志处理器
    - 过滤DEBUG级别
    - 简洁输出，无emoji
    - 符号美化 + 着色
    """
    
    # 符号映射
    SYMBOLS = {
        'INFO': '[*]',
        'SUCCESS': '[+]',
        'WARNING': '[!]',
        'ERROR': '[-]',
        'CRITICAL': '[X]',
    }
    
    def __init__(self, signal_emitter: GUILogSignal):
        self.signal = signal_emitter.log_signal
        self._buffer = ""
    
    def write(self, message):
        """处理loguru输出"""
        self._buffer += message
        if '\n' in self._buffer:
            lines = self._buffer.split('\n')
            for line in lines[:-1]:
                self._process_line(line)
            self._buffer = lines[-1]
    
    def _process_line(self, line):
        """处理单行日志"""
        if not line.strip():
            return
        
        # 提取级别和消息
        level, msg = self._parse_loguru_line(line)
        
        # 过滤DEBUG
        if level == 'DEBUG':
            return
        
        # 移除emoji，替换为空
        msg = self._remove_emoji(msg)
        
        # 获取符号
        symbol = self.SYMBOLS.get(level, '[*]')
        
        # 发送到GUI
        formatted_msg = f"{symbol} {msg}"
        self.signal.emit(formatted_msg, level)
    
    def _parse_loguru_line(self, line):
        """解析loguru格式的日志行"""
        # 尝试匹配常见的loguru输出格式
        # 格式: HH:mm:ss | LEVEL    | module:line - message
        match = re.search(r'\|\s*(DEBUG|INFO|SUCCESS|WARNING|ERROR|CRITICAL)\s*\|.*?-\s*(.*)', line)
        if match:
            return match.group(1), match.group(2)
        
        # 如果匹配失败，返回INFO和原始行
        return 'INFO', line
    
    def _remove_emoji(self, text):
        """移除emoji字符"""
        # 常见emoji的Unicode范围
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # 表情
            "\U0001F300-\U0001F5FF"  # 符号
            "\U0001F680-\U0001F6FF"  # 交通
            "\U0001F1E0-\U0001F1FF"  # 旗帜
            "\U00002702-\U000027B0"  # 杂项符号
            "\U0001F900-\U0001F9FF"  # 补充
            "\U00002600-\U000026FF"  # 杂项符号
            "\U00002B50-\U00002B55"  # 星星等
            "✔️✖️→"
            "]+", 
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text).strip()
    
    def flush(self):
        pass


# ======================== #
#       工作线程类          #
# ======================== #
class WorkerThread(QThread):
    """
    通用工作线程
    - 执行耗时任务
    - 发送日志和进度信号
    - 不阻塞UI
    """
    log_signal = pyqtSignal(str, str)      # (message, level)
    progress_signal = pyqtSignal(int, int)  # (current, total)
    finished_signal = pyqtSignal(bool, str) # (success, message)
    section_signal = pyqtSignal(str)        # 分区标题
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def run(self):
        try:
            result = self.task_func(*self.args, **self.kwargs)
            if not self._is_cancelled:
                self.finished_signal.emit(True, "任务完成")
        except Exception as e:
            logger.exception(f"任务执行失败: {e}")
            self.finished_signal.emit(False, str(e))
    
    def cancel(self):
        self._is_cancelled = True


# ======================== #
#       日志显示组件        #
# ======================== #
class LogTextEdit(QTextEdit):
    """
    日志显示区域
    - 着色输出
    - 符号美化
    - 自动滚动
    """
    
    # 颜色配置
    COLORS = {
        'INFO': '#FFFFFF',      # 白色
        'SUCCESS': '#4CAF50',   # 绿色
        'WARNING': '#FF9800',   # 橙色
        'ERROR': '#F44336',     # 红色
        'CRITICAL': '#D32F2F',  # 深红
        'SECTION': '#9E9E9E',   # 灰色
        'PROGRESS': '#2196F3',  # 蓝色
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
            }
        """)
    
    def append_log(self, message: str, level: str = 'INFO'):
        """添加日志条目"""
        color = self.COLORS.get(level, self.COLORS['INFO'])
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        
        cursor.insertText(message + '\n', fmt)
        
        # 自动滚动到底部
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    
    def append_section(self, title: str):
        """添加分区标题"""
        line = f"[-------- {title} --------]"
        self.append_log(line, 'SECTION')
    
    def append_progress(self, message: str):
        """添加进度信息"""
        self.append_log(f"[>] {message}", 'PROGRESS')
    
    def clear_log(self):
        """清空日志"""
        self.clear()


# ======================== #
#        路径选择组件       #
# ======================== #
class PathSelector(QWidget):
    """路径选择器组件"""
    
    path_changed = pyqtSignal(str)
    
    def __init__(self, label: str, placeholder: str = "", is_file: bool = False, 
                 file_filter: str = "", parent=None):
        super().__init__(parent)
        self.is_file = is_file
        self.file_filter = file_filter  # 例如 "Executable (*.exe)"
        self._setup_ui(label, placeholder)
    
    def _setup_ui(self, label: str, placeholder: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(label)
        self.label.setMinimumWidth(120)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.textChanged.connect(self.path_changed.emit)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMaximumWidth(80)
        self.browse_btn.clicked.connect(self._browse)
        
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit, 1)
        layout.addWidget(self.browse_btn)
    
    def _browse(self):
        if self.is_file:
            if self.file_filter:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择文件", "", self.file_filter
                )
            else:
                file_path, _ = QFileDialog.getOpenFileName(self, "选择文件")
            if file_path:
                self.line_edit.setText(file_path)
        else:
            folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if folder_path:
                self.line_edit.setText(folder_path)
    
    def get_path(self) -> str:
        return self.line_edit.text()
    
    def set_path(self, path_str: str):
        self.line_edit.setText(path_str)


# ======================== #
#         解包页面         #
# ======================== #
class UnpackPage(QWidget):
    """解包页面 - 分为PAK解密和资源整理两个模块，支持配置同步"""
    
    start_pak_decrypt = pyqtSignal(dict)   # PAK解密任务
    start_resource_extract = pyqtSignal(dict)  # 资源整理任务
    paths_changed = pyqtSignal()  # 路径变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self._setup_ui()
        self._load_config()
        self._connect_sync_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # ========== PAK解密模块 ==========
        pak_group = QGroupBox("PAK解密 (解密PAK文件到UE资源)")
        pak_layout = QVBoxLayout(pak_group)
        
        # PAK文件夹路径
        self.pak_path_selector = PathSelector("PAK文件夹", placeholder="选择游戏PAK文件所在目录")
        pak_layout.addWidget(self.pak_path_selector)
        
        # PAK解密输出路径 (即UE资源路径)
        self.pak_output_selector = PathSelector("解密输出", placeholder="选择解密后UE资源输出目录")
        pak_layout.addWidget(self.pak_output_selector)
        
        # 同步按钮
        sync_btn_layout = QHBoxLayout()
        self.sync_to_resource_btn = QPushButton("同步到资源整理 >>")
        self.sync_to_resource_btn.setToolTip("将解密输出路径同步到资源整理的UE资源路径")
        self.sync_to_resource_btn.clicked.connect(self._sync_pak_to_resource)
        sync_btn_layout.addStretch()
        sync_btn_layout.addWidget(self.sync_to_resource_btn)
        pak_layout.addLayout(sync_btn_layout)
        
        # PAK解密按钮
        self.pak_decrypt_btn = QPushButton("开始解密PAK")
        self.pak_decrypt_btn.setMinimumHeight(36)
        self.pak_decrypt_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #888888;
            }
        """)
        self.pak_decrypt_btn.clicked.connect(self._on_pak_decrypt)
        pak_layout.addWidget(self.pak_decrypt_btn)
        
        scroll_layout.addWidget(pak_group)
        
        # ========== 资源整理模块 ==========
        resource_group = QGroupBox("资源整理 (从UE资源提取转换)")
        resource_layout = QVBoxLayout(resource_group)
        
        # UE资源输入路径 (同步自PAK解密输出)
        self.ue_input_selector = PathSelector("UE资源路径", placeholder="选择已解密的UE资源目录")
        resource_layout.addWidget(self.ue_input_selector)
        
        # 资源输出路径
        self.resource_output_selector = PathSelector("资源输出", placeholder="选择提取资源输出目录")
        resource_layout.addWidget(self.resource_output_selector)
        
        # 资源提取模式
        mode_subgroup = QGroupBox("提取模式")
        mode_layout = QVBoxLayout(mode_subgroup)
        
        self.mode_btn_group = QButtonGroup(self)
        
        self.mode_full = QRadioButton("提取全部默认资源")
        self.mode_incr = QRadioButton("提取增量资源")
        
        self.mode_btn_group.addButton(self.mode_full, 0)
        self.mode_btn_group.addButton(self.mode_incr, 1)
        
        self.mode_full.setChecked(True)
        
        mode_layout.addWidget(self.mode_full)
        mode_layout.addWidget(self.mode_incr)
        
        resource_layout.addWidget(mode_subgroup)
        
        # 增量模式额外选项
        self.incr_options_widget = QWidget()
        incr_layout = QVBoxLayout(self.incr_options_widget)
        incr_layout.setContentsMargins(20, 0, 0, 0)
        
        # 旧版本路径 (增量模式)
        self.past_path_selector = PathSelector("旧版本路径", placeholder="选择旧版本UE资源目录")
        incr_layout.addWidget(self.past_path_selector)
        
        # 增量输出路径
        self.increase_path_selector = PathSelector("增量输出", placeholder="选择增量资源输出目录")
        incr_layout.addWidget(self.increase_path_selector)
        
        # Spine渲染选项
        self.spine_checkbox = QCheckBox("渲染Spine资源")
        incr_layout.addWidget(self.spine_checkbox)
        
        self.incr_options_widget.setVisible(False)
        resource_layout.addWidget(self.incr_options_widget)
        
        # 模式切换逻辑
        self.mode_btn_group.idClicked.connect(self._on_mode_changed)
        
        # 资源整理按钮
        self.resource_extract_btn = QPushButton("开始资源整理")
        self.resource_extract_btn.setMinimumHeight(36)
        self.resource_extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #888888;
            }
        """)
        self.resource_extract_btn.clicked.connect(self._on_resource_extract)
        resource_layout.addWidget(self.resource_extract_btn)
        
        scroll_layout.addWidget(resource_group)
        
        # ========== 保存配置按钮 ==========
        save_layout = QHBoxLayout()
        self.save_paths_btn = QPushButton("保存路径到配置")
        self.save_paths_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.save_paths_btn.clicked.connect(self._save_config)
        save_layout.addStretch()
        save_layout.addWidget(self.save_paths_btn)
        scroll_layout.addLayout(save_layout)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def _connect_sync_signals(self):
        """连接路径变更信号"""
        # PAK输出路径变更时可同步到UE输入路径
        self.pak_output_selector.path_changed.connect(self._on_path_changed)
        self.ue_input_selector.path_changed.connect(self._on_path_changed)
    
    def _on_path_changed(self, path_str):
        """路径变更时发出信号"""
        self.paths_changed.emit()
    
    def _sync_pak_to_resource(self):
        """同步PAK解密输出到资源整理UE输入"""
        pak_output = self.pak_output_selector.get_path()
        if pak_output:
            self.ue_input_selector.set_path(pak_output)
            logger.info(f"已同步路径: {pak_output}")
    
    def _load_config(self):
        """从配置文件加载路径"""
        # PAK路径
        pak_path = self.cfg.get("pak_path", "")
        if pak_path and pak_path != "NULL":
            self.pak_path_selector.set_path(pak_path)
        
        # 解包路径 (UE资源)
        unpack_path = self.cfg.get("unpack_path", "")
        if unpack_path and unpack_path != "NULL":
            self.pak_output_selector.set_path(unpack_path)
            self.ue_input_selector.set_path(unpack_path)
        
        # 资源输出路径
        resource_path = self.cfg.get("resource_path", "")
        if resource_path and resource_path != "NULL":
            self.resource_output_selector.set_path(resource_path)
        
        # 旧版本路径
        past_path = self.cfg.get("past_path", "")
        if past_path and past_path != "NULL":
            self.past_path_selector.set_path(past_path)
        
        # 增量输出路径
        increase_path = self.cfg.get("increase_path", "")
        if increase_path and increase_path != "NULL":
            self.increase_path_selector.set_path(increase_path)
    
    def _save_config(self):
        """保存路径到配置文件"""
        # PAK路径
        pak_path = self.pak_path_selector.get_path()
        if pak_path:
            self.cfg.set("pak_path", pak_path)
        
        # 解包路径 (PAK解密输出)
        unpack_path = self.pak_output_selector.get_path()
        if unpack_path:
            self.cfg.set("unpack_path", unpack_path)
        
        # 资源输出路径
        resource_path = self.resource_output_selector.get_path()
        if resource_path:
            self.cfg.set("resource_path", resource_path)
        
        # 新版本路径 (UE资源)
        ue_path = self.ue_input_selector.get_path()
        if ue_path:
            self.cfg.set("new_path", ue_path)
        
        # 旧版本路径
        past_path = self.past_path_selector.get_path()
        if past_path:
            self.cfg.set("past_path", past_path)
        
        # 增量输出路径
        increase_path = self.increase_path_selector.get_path()
        if increase_path:
            self.cfg.set("increase_path", increase_path)
        
        logger.success("路径配置已保存")
        QMessageBox.information(self, "提示", "路径配置已保存")
    
    def get_ue_resource_path(self) -> str:
        """获取当前UE资源路径（供小工具页面使用）"""
        return self.ue_input_selector.get_path()
    
    def _on_mode_changed(self, mode_id):
        """模式切换时更新增量选项可见性"""
        self.incr_options_widget.setVisible(mode_id == 1)
    
    def _on_pak_decrypt(self):
        """PAK解密按钮点击"""
        pak_path = self.pak_path_selector.get_path()
        output_path = self.pak_output_selector.get_path()
        
        if not pak_path:
            QMessageBox.warning(self, "警告", "请选择PAK文件夹路径")
            return
        if not output_path:
            QMessageBox.warning(self, "警告", "请选择解密输出路径")
            return
        
        # 保存路径到配置
        self.cfg.set("pak_path", pak_path)
        self.cfg.set("unpack_path", output_path)
        
        config = {
            'pak_path': pak_path,
            'output_path': output_path
        }
        self.start_pak_decrypt.emit(config)
    
    def _on_resource_extract(self):
        """资源整理按钮点击"""
        ue_path = self.ue_input_selector.get_path()
        mode = self.mode_btn_group.checkedId()
        
        if not ue_path:
            QMessageBox.warning(self, "警告", "请选择UE资源路径")
            return
        
        if mode == 0:
            # 全量模式
            output_path = self.resource_output_selector.get_path()
            if not output_path:
                QMessageBox.warning(self, "警告", "请选择资源输出路径")
                return
            
            self.cfg.set("unpack_path", ue_path)
            self.cfg.set("resource_path", output_path)
            
            config = {
                'ue_path': ue_path,
                'output_path': output_path,
                'mode': mode,
                'spine': False,
                'past_path': None
            }
        else:
            # 增量模式
            past_path = self.past_path_selector.get_path()
            output_path = self.increase_path_selector.get_path()
            
            if not past_path:
                QMessageBox.warning(self, "警告", "请选择旧版本路径")
                return
            if not output_path:
                QMessageBox.warning(self, "警告", "请选择增量输出路径")
                return
            
            self.cfg.set("past_path", past_path)
            self.cfg.set("new_path", ue_path)
            self.cfg.set("increase_path", output_path)
            
            config = {
                'ue_path': ue_path,
                'output_path': output_path,
                'mode': mode,
                'spine': self.spine_checkbox.isChecked(),
                'past_path': past_path
            }
        
        self.start_resource_extract.emit(config)
    
    def set_pak_running(self, running: bool):
        """设置PAK解密运行状态"""
        self.pak_decrypt_btn.setEnabled(not running)
        self.pak_decrypt_btn.setText("正在解密..." if running else "开始解密PAK")
    
    def set_resource_running(self, running: bool):
        """设置资源整理运行状态"""
        self.resource_extract_btn.setEnabled(not running)
        self.resource_extract_btn.setText("正在整理..." if running else "开始资源整理")


# ======================== #
#        小工具页面        #
# ======================== #
class ToolsPage(QWidget):
    """小工具页面 - 使用解包页面的UE资源路径"""
    
    start_task = pyqtSignal(str, dict)  # (tool_name, config)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # ========== 路径配置 ==========
        path_group = QGroupBox("工作路径")
        path_layout = QVBoxLayout(path_group)
        
        # UE资源路径 (从解包页面同步)
        self.ue_path_selector = PathSelector("UE资源路径", placeholder="使用解包页面的路径或手动选择")
        path_layout.addWidget(self.ue_path_selector)
        
        # 输出路径
        self.output_path_selector = PathSelector("输出路径", placeholder="选择工具输出目录")
        path_layout.addWidget(self.output_path_selector)
        
        # 同步按钮
        sync_layout = QHBoxLayout()
        self.sync_from_unpack_btn = QPushButton("从解包页面同步路径")
        self.sync_from_unpack_btn.setToolTip("从解包页面获取UE资源路径")
        sync_layout.addWidget(self.sync_from_unpack_btn)
        sync_layout.addStretch()
        path_layout.addLayout(sync_layout)
        
        scroll_layout.addWidget(path_group)
        
        # ========== 解包流程工具组 ==========
        unpack_group = QGroupBox("单独解包流程")
        unpack_layout = QVBoxLayout(unpack_group)
        
        unpack_tools = [
            ("活动UI解包", "ACTIVITY_UI", "解包活动UI资源"),
            ("登录界面解包", "LOGIN_UI", "解包登录界面资源"),
            ("BGM背景音乐解包", "BGM", "解包BGM背景音乐"),
            ("角色立绘解包", "CHARA", "解包角色立绘资源"),
            ("后勤立绘解包", "SER", "解包后勤立绘资源"),
            ("时装图片解包", "FASHION", "解包时装图片"),
            ("对话图片解包", "DIALOGUE", "解包对话图片"),
        ]
        
        for name, key, tooltip in unpack_tools:
            btn = QPushButton(name)
            btn.setMinimumHeight(32)
            btn.setToolTip(tooltip)
            btn.clicked.connect(partial(self._on_tool_click, key))
            unpack_layout.addWidget(btn)
        
        scroll_layout.addWidget(unpack_group)
        
        # ========== 其他工具组 ==========
        other_group = QGroupBox("其他工具")
        other_layout = QVBoxLayout(other_group)
        
        other_tools = [
            ("PAK文件独立解密", "UNPAK", "使用QuickBMS解密PAK文件", False),
            ("SPINE动画独立渲染", "SPINE", "渲染Spine动画为视频", False),
            ("IMG图片遍历解包", "IMG", "批量转换图片为PNG格式", True),
        ]
        
        for name, key, tooltip, enabled in other_tools:
            btn = QPushButton(name)
            btn.setMinimumHeight(32)
            btn.setToolTip(tooltip)
            btn.setEnabled(enabled)
            if not enabled:
                btn.setText(f"{name} (待开发)")
            btn.clicked.connect(partial(self._on_tool_click, key))
            other_layout.addWidget(btn)
        
        scroll_layout.addWidget(other_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def _load_config(self):
        """从配置加载路径"""
        # UE资源路径
        unpack_path = self.cfg.get("unpack_path", "")
        if unpack_path and unpack_path != "NULL":
            self.ue_path_selector.set_path(unpack_path)
        
        # 资源输出路径
        resource_path = self.cfg.get("resource_path", "")
        if resource_path and resource_path != "NULL":
            self.output_path_selector.set_path(resource_path)
    
    def sync_from_unpack_page(self, ue_path: str):
        """从解包页面同步路径"""
        if ue_path:
            self.ue_path_selector.set_path(ue_path)
            logger.info(f"已同步UE资源路径: {ue_path}")
    
    def get_ue_path(self) -> str:
        """获取UE资源路径"""
        return self.ue_path_selector.get_path()
    
    def get_output_path(self) -> str:
        """获取输出路径"""
        return self.output_path_selector.get_path()
    
    def _on_tool_click(self, tool_key):
        """工具按钮点击"""
        config = {
            'ue_path': self.get_ue_path(),
            'output_path': self.get_output_path()
        }
        self.start_task.emit(tool_key, config)


# ======================== #
#       工具检查页面        #
# ======================== #
class CheckPage(QWidget):
    """工具检查页面"""
    
    start_check = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 说明
        desc_label = QLabel("检查配置文件中指定的工具路径是否有效并可运行")
        layout.addWidget(desc_label)
        
        # 工具状态显示区
        self.status_group = QGroupBox("工具状态")
        status_layout = QVBoxLayout(self.status_group)
        
        self.tool_labels = {}
        tools = ["FFmpeg", "UModel", "vgmstream", "Spine", "quickbms"]
        for tool in tools:
            row = QHBoxLayout()
            name_label = QLabel(tool)
            name_label.setMinimumWidth(100)
            status_label = QLabel("未检查")
            status_label.setStyleSheet("color: #888888;")
            self.tool_labels[tool] = status_label
            row.addWidget(name_label)
            row.addWidget(status_label, 1)
            status_layout.addLayout(row)
        
        layout.addWidget(self.status_group)
        
        # 检查按钮
        self.check_btn = QPushButton("开始检查")
        self.check_btn.setMinimumHeight(40)
        self.check_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.check_btn.clicked.connect(self.start_check.emit)
        layout.addWidget(self.check_btn)
        
        layout.addStretch()
    
    def update_tool_status(self, tool: str, ok: bool, message: str = ""):
        """更新工具状态"""
        if tool in self.tool_labels:
            label = self.tool_labels[tool]
            if ok:
                label.setText("OK")
                label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                label.setText(f"失败: {message}" if message else "不可用")
                label.setStyleSheet("color: #F44336;")
    
    def reset_status(self):
        """重置所有状态"""
        for label in self.tool_labels.values():
            label.setText("检查中...")
            label.setStyleSheet("color: #FF9800;")


# ======================== #
#         设置页面         #
# ======================== #
class SettingsPage(QWidget):
    """设置页面"""
    
    settings_saved = pyqtSignal()
    settings_reset = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 工具路径配置
        tools_group = QGroupBox("工具路径")
        tools_layout = QVBoxLayout(tools_group)
        
        self.path_selectors = {}
        # 工具路径 - 都是exe文件
        tool_paths = [
            ("ffm_path", "FFmpeg"),
            ("umo_path", "UModel"),
            ("vgm_path", "vgmstream"),
            ("quickbms_path", "QuickBMS"),
            ("spine_path", "Spine"),
        ]
        
        exe_filter = "可执行文件 (*.exe);;所有文件 (*.*)"
        for key, label in tool_paths:
            selector = PathSelector(label, is_file=True, file_filter=exe_filter)
            self.path_selectors[key] = selector
            tools_layout.addWidget(selector)
        
        scroll_layout.addWidget(tools_group)
        
        # 路径配置
        paths_group = QGroupBox("工作路径")
        paths_layout = QVBoxLayout(paths_group)
        
        work_paths = [
            ("pak_path", "PAK文件夹", False),
            ("unpack_path", "解包输入", False),
            ("resource_path", "资源导出", False),
            ("past_path", "旧版本文件夹", False),
            ("new_path", "新版本文件夹", False),
            ("increase_path", "增量导出", False),
        ]
        
        for key, label, is_file in work_paths:
            selector = PathSelector(label, is_file=is_file)
            self.path_selectors[key] = selector
            paths_layout.addWidget(selector)
        
        scroll_layout.addWidget(paths_group)
        
        # 运行时配置
        runtime_group = QGroupBox("运行时配置")
        runtime_layout = QVBoxLayout(runtime_group)
        
        # 多线程数
        workers_row = QHBoxLayout()
        workers_label = QLabel("多线程数")
        workers_label.setMinimumWidth(120)
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(2)
        workers_row.addWidget(workers_label)
        workers_row.addWidget(self.workers_spin)
        workers_row.addStretch()
        runtime_layout.addLayout(workers_row)
        
        # 中文名开关
        self.cn_name_checkbox = QCheckBox("音频文件应用中文名")
        runtime_layout.addWidget(self.cn_name_checkbox)
        
        scroll_layout.addWidget(runtime_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # 按钮区
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存设置")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        
        self.reset_btn = QPushButton("重置配置")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_settings)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reset_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_settings(self):
        """加载设置"""
        for key, selector in self.path_selectors.items():
            value = self.cfg.get(key, "")
            if value and value != "NULL":
                selector.set_path(value)
        
        self.workers_spin.setValue(self.cfg.get("max_workers", 2))
        self.cn_name_checkbox.setChecked(self.cfg.get("UseCNName", False))
    
    def _save_settings(self):
        """保存设置"""
        for key, selector in self.path_selectors.items():
            value = selector.get_path()
            if value:
                self.cfg.set(key, value)
        
        self.cfg.set("max_workers", self.workers_spin.value())
        self.cfg.set("UseCNName", self.cn_name_checkbox.isChecked())
        
        QMessageBox.information(self, "提示", "设置已保存")
        self.settings_saved.emit()
    
    def _reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置所有配置为默认值吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.cfg.reset()
            self._load_settings()
            QMessageBox.information(self, "提示", "配置已重置")
            self.settings_reset.emit()


# ======================== #
#         关于页面         #
# ======================== #
class AboutPage(QWidget):
    """关于页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._click_count = 0
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("CB-UNpak Tool")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 版本
        version = QLabel(f"版本 {VER} (Build {BUILD})")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        layout.addSpacing(20)
        
        # 描述
        desc = QLabel("尘白禁区批量解包工具")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        layout.addSpacing(20)
        
        # 作者
        self.author_btn = QPushButton("by 绘星痕、小狐狸")
        self.author_btn.setFlat(True)
        self.author_btn.setStyleSheet("color: #888888;")
        self.author_btn.clicked.connect(self._on_author_click)
        layout.addWidget(self.author_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(20)
        
        # 许可证
        license_label = QLabel("License: GNU General Public License Version 3")
        license_label.setStyleSheet("color: #666666;")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)
        
        layout.addStretch()
    
    def _on_author_click(self):
        """彩蛋触发"""
        self._click_count += 1
        if self._click_count >= 5:
            self._click_count = 0
            # 触发彩蛋 - 先播放声音，然后延迟显示对话框
            try:
                audio_path = resource_path("Ciallo.wav")
                logger.debug(f"播放彩蛋音效: {audio_path}")
                if path.exists(audio_path):
                    # 使用同步播放确保声音实际播放
                    def play_sound():
                        try:
                            winsound.PlaySound(audio_path, winsound.SND_FILENAME)
                        except Exception as e:
                            logger.error(f"播放音效异常: {e}")
                    
                    # 在单独线程中播放以避免阻塞
                    import threading
                    sound_thread = threading.Thread(target=play_sound, daemon=True)
                    sound_thread.start()
                else:
                    logger.warning(f"彩蛋音效文件不存在: {audio_path}")
            except Exception as e:
                logger.error(f"播放彩蛋音效失败: {e}")
            
            QMessageBox.information(self, "Ciallo~", 
                "Ciallo~(∠·w< )⌒*\n\n因幡巡 提醒您：这部分作者还没写完")


# ======================== #
#          主窗口          #
# ======================== #
class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.cfg = ConfigManager()
        self.worker = None
        self._setup_ui()
        self._setup_log_handler()
        self._connect_signals()
        
        # 初始化日志
        self.log_widget.append_section("程序已启动")
        self.log_widget.append_log("[*] 等待任务...")
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"CB-UNpak Tool v{VER}")
        self.setMinimumSize(800, 600)
        
        # 中央布局
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 标签页
        self.tabs = QTabWidget()
        
        self.unpack_page = UnpackPage()
        self.tools_page = ToolsPage()
        self.check_page = CheckPage()
        self.settings_page = SettingsPage()
        self.about_page = AboutPage()
        
        self.tabs.addTab(self.unpack_page, "解包")
        self.tabs.addTab(self.tools_page, "小工具")
        self.tabs.addTab(self.check_page, "工具检查")
        self.tabs.addTab(self.settings_page, "设置")
        self.tabs.addTab(self.about_page, "关于")
        
        splitter.addWidget(self.tabs)
        
        # 日志区
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout(log_group)
        self.log_widget = LogTextEdit()
        log_layout.addWidget(self.log_widget)
        
        # 日志控制按钮
        log_btn_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.log_widget.clear_log)
        log_btn_layout.addStretch()
        log_btn_layout.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_btn_layout)
        
        splitter.addWidget(log_group)
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def _setup_log_handler(self):
        """设置日志处理器"""
        self.log_signal = GUILogSignal()
        self.log_signal.log_signal.connect(self._on_log_message)
        
        self.gui_handler = GUILogHandler(self.log_signal)
        logger.add(self.gui_handler.write, level="INFO", format="{level} | {message}")
    
    def _connect_signals(self):
        """连接信号"""
        self.unpack_page.start_pak_decrypt.connect(self._start_pak_decrypt)
        self.unpack_page.start_resource_extract.connect(self._start_resource_extract)
        self.tools_page.start_task.connect(self._start_tool)
        self.check_page.start_check.connect(self._start_check)
        
        # 小工具页面同步按钮
        self.tools_page.sync_from_unpack_btn.clicked.connect(self._sync_tools_path)
    
    def _on_log_message(self, message: str, level: str):
        """处理日志消息"""
        self.log_widget.append_log(message, level)
    
    def _start_pak_decrypt(self, config: dict):
        """开始PAK解密任务"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "已有任务正在运行")
            return
        
        self.log_widget.append_section("PAK解密任务开始")
        self.unpack_page.set_pak_running(True)
        self.statusBar().showMessage("正在解密PAK文件...")
        
        pak_path = config['pak_path']
        output_path = config['output_path']
        
        def task():
            import subprocess
            from os import getcwd
            cfg = ConfigManager()
            quickbms_path = str(cfg.get("quickbms_path"))
            
            # 清理并创建输出目录
            if path.exists(output_path):
                import shutil
                shutil.rmtree(output_path)
            makedirs(output_path)
            
            logger.info(f"PAK路径: {pak_path}")
            logger.info(f"输出路径: {output_path}")
            
            bms_script = path.join(getcwd(), "res", "unreal_tournament_4_0.4.27e_snowbreak.bms")
            cmd = [
                f'"{quickbms_path}"',
                '-o -F "{}.pak"',
                f'"{bms_script}"',
                f'"{pak_path}"',
                f'"{output_path}"'
            ]
            logger.info(f"执行命令: {' '.join(cmd)}")
            subprocess.run(" ".join(cmd), shell=True)
            logger.success("PAK解密完成")
        
        self.worker = WorkerThread(task)
        self.worker.finished_signal.connect(lambda s, m: self._on_pak_finished(s, m))
        self.worker.start()
    
    def _start_resource_extract(self, config: dict):
        """开始资源整理任务"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "已有任务正在运行")
            return
        
        self.log_widget.append_section("资源整理任务开始")
        self.unpack_page.set_resource_running(True)
        self.statusBar().showMessage("正在整理资源...")
        
        ue_path = config['ue_path']
        output_path = config['output_path']
        mode = config['mode']
        spine = config['spine']
        past_path = config.get('past_path')
        
        def task():
            cfg = ConfigManager()
            cfg.Json_list = []
            
            # 临时设置路径
            cfg.set("unpack_path", ue_path)
            cfg.set("resource_path", output_path)
            
            if mode == 0:
                logger.info("正在提取全部默认资源...")
                logger.info(f"输入路径: {ue_path}")
                logger.info(f"输出路径: {output_path}")
                CBUNpakMain()
            elif mode == 1:
                if past_path:
                    cfg.set("past_path", past_path)
                cfg.set("new_path", ue_path)
                cfg.set("increase_path", output_path)
                
                logger.info("正在提取增量资源...")
                logger.info(f"旧版本: {past_path}")
                logger.info(f"新版本: {ue_path}")
                logger.info(f"输出: {output_path}")
                CBUNpakIncr()
                
                if spine:
                    logger.info("正在渲染Spine资源...")
                    sjemain()
            
            logger.success("资源整理完成")
        
        self.worker = WorkerThread(task)
        self.worker.finished_signal.connect(lambda s, m: self._on_resource_finished(s, m))
        self.worker.start()
    
    def _on_pak_finished(self, success: bool, message: str):
        """PAK解密完成回调"""
        self.unpack_page.set_pak_running(False)
        
        if success:
            self.log_widget.append_log("[+] PAK解密完成", "SUCCESS")
            self.statusBar().showMessage("PAK解密完成")
        else:
            self.log_widget.append_log(f"[-] PAK解密失败: {message}", "ERROR")
            self.statusBar().showMessage("PAK解密失败")
        
        self.log_widget.append_section("任务结束")
    
    def _on_resource_finished(self, success: bool, message: str):
        """资源整理完成回调"""
        self.unpack_page.set_resource_running(False)
        
        if success:
            self.log_widget.append_log("[+] 资源整理完成", "SUCCESS")
            self.statusBar().showMessage("资源整理完成")
        else:
            self.log_widget.append_log(f"[-] 资源整理失败: {message}", "ERROR")
            self.statusBar().showMessage("资源整理失败")
        
        self.log_widget.append_section("任务结束")
    
    def _start_tool(self, tool_key: str, config: dict):
        """开始小工具任务"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "已有任务正在运行")
            return
        
        # 获取路径
        ue_path = config.get('ue_path', '')
        output_path = config.get('output_path', '')
        
        # 单独解包流程工具
        unpack_tools = {
            "ACTIVITY_UI": ("活动UI解包", activity_ui),
            "LOGIN_UI": ("登录界面解包", login_ui),
            "BGM": ("BGM背景音乐解包", bgm),
            "CHARA": ("角色立绘解包", chara),
            "SER": ("服务器图片解包", ser),
            "FASHION": ("时装图片解包", fashion),
            "DIALOGUE": ("对话图片解包", dialogue),
        }
        
        if tool_key in unpack_tools:
            tool_name, tool_func = unpack_tools[tool_key]
            
            # 检查路径
            if not ue_path:
                QMessageBox.warning(self, "警告", "请先在小工具页面设置UE资源路径")
                return
            if not output_path:
                QMessageBox.warning(self, "警告", "请先在小工具页面设置输出路径")
                return
            
            self.log_widget.append_section(f"{tool_name}任务开始")
            self.statusBar().showMessage(f"正在执行{tool_name}...")
            logger.info(f"输入路径: {ue_path}")
            logger.info(f"输出路径: {output_path}")
            
            def task():
                makedirs(output_path, exist_ok=True)
                tool_func(ue_path, output_path)
                logger.success(f"{tool_name}完成")
            
            self.worker = WorkerThread(task)
            self.worker.finished_signal.connect(self._on_task_finished)
            self.worker.start()
        
        elif tool_key == "IMG":
            # IMG工具使用弹窗选择路径
            input_path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
            if not input_path:
                return
            
            img_output_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
            if not img_output_path:
                return
            
            self.log_widget.append_section("图片解包任务开始")
            self.statusBar().showMessage("正在执行图片解包...")
            
            def task():
                makedirs(img_output_path, exist_ok=True)
                convert_to_png(input_path, img_output_path)
                logger.success("图片解包完成")
            
            self.worker = WorkerThread(task)
            self.worker.finished_signal.connect(self._on_task_finished)
            self.worker.start()
        else:
            # 待开发功能
            try:
                audio_path = resource_path("Ciallo.wav")
                if path.exists(audio_path):
                    winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                logger.debug(f"播放音效失败: {e}")
            self.log_widget.append_log("[!] 该功能正在开发中...", "WARNING")
    
    def _sync_tools_path(self):
        """同步解包页面路径到小工具页面"""
        ue_path = self.unpack_page.get_ue_resource_path()
        if ue_path:
            self.tools_page.sync_from_unpack_page(ue_path)
        else:
            QMessageBox.warning(self, "警告", "解包页面未设置UE资源路径")
    
    def _start_check(self):
        """开始工具检查"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "已有任务正在运行")
            return
        
        self.log_widget.append_section("工具检查开始")
        self.check_page.reset_status()
        self.check_page.check_btn.setEnabled(False)
        self.check_page.check_btn.setText("检查中...")
        self.statusBar().showMessage("正在检查工具可用性...")
        
        # 保存页面引用用于回调
        check_page = self.check_page
        
        def task():
            """执行工具检查并收集结果"""
            cfg = ConfigManager()
            tool_paths = {
                "FFmpeg": (cfg.get("ffm_path"), ["-version"]),
                "vgmstream": (cfg.get("vgm_path"), []),
                "UModel": (cfg.get("umo_path"), ["-help"]),
                "Spine": (cfg.get("spine_path"), ["--help"]),
                "quickbms": (cfg.get("quickbms_path"), [""]),
            }
            
            results = {}
            import subprocess
            
            for tool, (exe, args) in tool_paths.items():
                logger.info(f"检查 {tool} ...")
                
                if not exe or not path.isfile(exe):
                    results[tool] = (False, "路径无效")
                    logger.error(f"[路径无效] {tool}")
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
                    passed = proc.returncode == 0 or ("Usage:" in output or "Options:" in output)
                    
                    if passed:
                        results[tool] = (True, "")
                        logger.success(f"{tool} 可用")
                    else:
                        results[tool] = (False, f"返回码 {proc.returncode}")
                        logger.error(f"{tool} 运行异常")
                except subprocess.TimeoutExpired:
                    results[tool] = (False, "超时")
                    logger.error(f"{tool} 执行超时")
                except Exception as e:
                    results[tool] = (False, str(e))
                    logger.error(f"{tool} 执行失败: {e}")
            
            return results
        
        self.worker = WorkerThread(task)
        self.worker.finished_signal.connect(lambda s, m: self._on_check_finished(s, m, check_page))
        self.worker.start()
    
    def _on_task_finished(self, success: bool, message: str):
        """任务完成回调"""
        self.unpack_page.set_running(False)
        
        if success:
            self.log_widget.append_log("[+] " + message, "SUCCESS")
            self.statusBar().showMessage("任务完成")
        else:
            self.log_widget.append_log("[-] " + message, "ERROR")
            self.statusBar().showMessage("任务失败")
        
        self.log_widget.append_section("任务结束")
    
    def _on_check_finished(self, success: bool, message: str, check_page=None):
        """工具检查完成回调"""
        if check_page is None:
            check_page = self.check_page
        
        # 恢复按钮状态
        check_page.check_btn.setEnabled(True)
        check_page.check_btn.setText("开始检查")
        
        # 由于WorkerThread返回结果在finished_signal中无法直接获取，
        # 我们通过日志信息来判断每个工具的状态
        # 更好的方式是重新检查一次状态
        cfg = ConfigManager()
        tool_checks = {
            "FFmpeg": cfg.get("ffm_path"),
            "UModel": cfg.get("umo_path"),
            "vgmstream": cfg.get("vgm_path"),
            "Spine": cfg.get("spine_path"),
            "quickbms": cfg.get("quickbms_path"),
        }
        
        for tool, exe_path in tool_checks.items():
            if exe_path and path.isfile(exe_path):
                check_page.update_tool_status(tool, True)
            else:
                check_page.update_tool_status(tool, False, "路径无效")
        
        self.statusBar().showMessage("工具检查完成")
        self.log_widget.append_section("检查完成")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "有任务正在运行，确定要退出吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.worker.cancel()
        
        event.accept()


# ======================== #
#          入口点          #
# ======================== #
def main():
    """程序入口"""
    init_logger()
    
    logger.info('''
 ###    License
 GNU General Public License Version 3

 Copyright (C) 2026  friends-xiaohuli
''')
    
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
