# 杂鱼♡～本喵的文本处理器喵～
from typing import Callable, Optional

from ..interfaces.callback_interface import BaseClipboardHandler
from ..types import ProcessInfo
from ..utils.logger import get_component_logger

# 杂鱼♡～获取组件专用logger喵～
logger = get_component_logger("handlers.text_handler")


class TextHandler(BaseClipboardHandler):
    """杂鱼♡～专门处理文本的处理器喵～"""

    def __init__(self, callback: Optional[Callable] = None):
        """
        杂鱼♡～初始化文本处理器喵～

        Args:
            callback: 处理文本的回调函数，可以是：
                      - callback(text) - 旧格式，只接收文本
                      - callback(text, source_info) - 新格式，接收文本和源信息
        """
        super().__init__(callback)

    def is_valid(self, data: Optional[str] = None) -> bool:
        """杂鱼♡～检查文本数据是否有效喵～"""
        if not isinstance(data, str):
            return False

        if not data.strip():  # 杂鱼♡～空字符串不处理喵～
            return False

        return True

    def _default_handle(
        self, data: str, source_info: Optional[ProcessInfo] = None
    ) -> None:
        """杂鱼♡～默认的文本处理方法喵～"""
        logger.info("杂鱼♡～检测到文本变化喵：")
        logger.info(f"  内容长度：{len(data)} 字符")
        logger.info(f"  前50个字符：{data[:50]}...")

        # 杂鱼♡～显示源应用程序信息喵～
        if source_info and self._include_source_info:
            process_name = source_info.process_name

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