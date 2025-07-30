# 杂鱼♡～本喵的文件处理器喵～
import os
from typing import Callable, List, Optional

from ..interfaces.callback_interface import BaseClipboardHandler
from ..types import ProcessInfo
from ..utils.logger import get_component_logger

# 杂鱼♡～获取组件专用logger喵～
logger = get_component_logger("handlers.file_handler")


class FileHandler(BaseClipboardHandler):
    """杂鱼♡～专门处理文件的处理器喵～"""

    def __init__(self, callback: Optional[Callable] = None):
        """
        杂鱼♡～初始化文件处理器喵～

        Args:
            callback: 处理文件列表的回调函数，可以是：
                      - callback(files) - 旧格式，只接收文件列表
                      - callback(files, source_info) - 新格式，接收文件列表和源信息
        """
        super().__init__(callback)

    def is_valid(self, data: Optional[List[str]] = None) -> bool:
        """杂鱼♡～检查文件数据是否有效喵～"""
        if not isinstance(data, list):
            return False

        if len(data) == 0:
            return False

        # 杂鱼♡～检查每个文件路径喵～
        for file_path in data:
            if not os.path.exists(file_path):
                return False

        return True

    def _default_handle(
        self, data: List[str], source_info: Optional[ProcessInfo] = None
    ) -> None:
        """杂鱼♡～默认的文件处理方法喵～"""
        logger.info("杂鱼♡～检测到文件变化喵：")
        logger.info(f"  文件数量：{len(data)}")

        for i, file_path in enumerate(data, 1):
            file_info = self.get_file_info(file_path)
            logger.info(f"  文件{i}：{file_info['name']} ({file_info['size']})")

        # 杂鱼♡～显示源应用程序信息喵～
        if source_info and self._include_source_info:
            process_name = source_info.process_name or "Unknown"

            # 杂鱼♡～根据不同情况显示不同的信息喵～
            if process_name == "Unknown":
                logger.warning("  源应用程序：❓ 未知 (无法获取)")
            else:
                logger.info(f"  源应用程序：{process_name}")

            # 杂鱼♡～显示其他详细信息喵～
            if source_info.process_path and process_name != "Unknown":
                logger.debug(f"  程序路径：{source_info.process_path}")
            if source_info.window_title:
                logger.debug(f"  窗口标题：{source_info.window_title}")
            if source_info.process_id:
                logger.debug(f"  进程ID：{source_info.process_id}")

        logger.info("-" * 50)

    def get_file_info(self, file_path: str) -> dict:
        """杂鱼♡～获取文件信息喵～"""
        import datetime
        import os

        info = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "directory": os.path.dirname(file_path),
            "extension": os.path.splitext(file_path)[1],
            "exists": os.path.exists(file_path),
            "size": "unknown",
            "modified": "unknown",
        }

        if info["exists"]:
            try:
                stat = os.stat(file_path)
                info["size"] = self._format_file_size(stat.st_size)
                info["modified"] = str(datetime.datetime.fromtimestamp(stat.st_mtime))
            except Exception as e:
                # 杂鱼♡～处理失败了喵～
                error_msg = f"杂鱼♡～文件处理失败了喵：{e}"
                logger.error(error_msg)
                self._handle_error(error_msg, [file_path])
                return False

        return info

    def _format_file_size(self, size_bytes: int) -> str:
        """杂鱼♡～格式化文件大小喵～"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math

        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
