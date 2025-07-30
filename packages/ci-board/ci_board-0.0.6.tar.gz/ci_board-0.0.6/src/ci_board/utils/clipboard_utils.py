# 杂鱼♡～本喵重构后的简化版剪贴板工具类喵～
# 杂鱼♡～现在只负责整合其他模块，不再是庞然大物了喵～
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .clipboard_reader import ClipboardReader
from .message_pump import MessagePump
from .win32_api import (ClipboardAccessDenied, ClipboardError, ClipboardFormat,
                        ClipboardTimeout, Win32API)
from ..core.source_tracker_ import SourceTracker


class ClipboardUtils:
    """
    杂鱼♡～重构后的剪贴板工具类，现在变得轻量级了喵～
    本喵把原来1251行的怪物拆分成了多个职责明确的小类：
    - Win32API: Windows API封装
    - ClipboardReader: 剪贴板数据读取
    - SourceTracker: 源应用追踪
    - MessagePump: 消息泵和窗口管理
    """

    # 杂鱼♡～将所有子模块的功能暴露出来，保持兼容性喵～

    # ============= 杂鱼♡～基本操作喵～ =============

    @classmethod
    def is_format_available(cls, format_type: ClipboardFormat) -> bool:
        """杂鱼♡～检查剪贴板格式是否可用喵～"""
        return ClipboardReader.is_format_available(format_type)

    @classmethod
    def get_available_formats(cls) -> List[str]:
        """杂鱼♡～获取可用的剪贴板格式列表喵～"""
        return ClipboardReader.get_available_formats()

    @classmethod
    def detect_content_type(cls) -> Optional[str]:
        """杂鱼♡～检测剪贴板内容类型喵～"""
        return ClipboardReader.detect_content_type()

    @classmethod
    def get_clipboard_stats(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板统计信息喵～"""
        return ClipboardReader.get_clipboard_stats()

    # ============= 杂鱼♡～内容读取喵～ =============

    @classmethod
    def get_text_content(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[str]:
        """杂鱼♡～获取剪贴板文本内容喵～"""
        return ClipboardReader.get_text_content(retry_count, timeout)

    @classmethod
    def get_image_content(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[Any]:
        """杂鱼♡～获取剪贴板图片内容喵～"""
        return ClipboardReader.get_image_content(retry_count, timeout)

    @classmethod
    def get_file_list(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[List[str]]:
        """杂鱼♡～获取剪贴板文件列表喵～"""
        return ClipboardReader.get_file_list(retry_count, timeout)

    @classmethod
    def get_clipboard_content(
        cls, retry_count: int = None, timeout: float = None, with_source: bool = False
    ) -> Tuple[Optional[str], Any, Optional[Dict[str, Any]]]:
        """杂鱼♡～获取剪贴板内容和类型（增强版）喵～"""
        # 杂鱼♡～如果需要源信息，先获取源应用信息，避免和内容读取竞争喵～
        source_info = None
        if with_source:
            try:
                source_info = SourceTracker.get_source_info(avoid_clipboard_access=False)
            except Exception as e:
                cls.logger.error(f"杂鱼♡～获取源信息时出错喵：{e}")
                source_info = None

        # 杂鱼♡～然后获取剪贴板内容喵～
        content_type, content = ClipboardReader.get_clipboard_content(
            retry_count, timeout
        )

        return (content_type, content, source_info)

    # ============= 杂鱼♡～源应用追踪喵～ =============

    @classmethod
    def get_source_application_info(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板内容源应用信息喵～"""
        return SourceTracker.get_source_info(avoid_clipboard_access=True)

    # ============= 杂鱼♡～消息泵和窗口管理喵～ =============

    @classmethod
    def create_hidden_window(
        cls, window_name: str = "ClipboardMonitor"
    ) -> Optional[Any]:
        """杂鱼♡～创建隐藏窗口用于监听喵～"""
        return MessagePump.create_hidden_window(window_name)

    @classmethod
    def destroy_window(cls, hwnd) -> bool:
        """杂鱼♡～销毁窗口喵～"""
        return MessagePump.destroy_window(hwnd)

    @classmethod
    def add_clipboard_listener(cls, hwnd, callback: Callable = None) -> bool:
        """杂鱼♡～添加剪贴板监听器喵～"""
        return MessagePump.add_clipboard_listener(hwnd, callback)

    @classmethod
    def remove_clipboard_listener(cls, hwnd) -> bool:
        """杂鱼♡～移除剪贴板监听器喵～"""
        return MessagePump.remove_clipboard_listener(hwnd)

    @classmethod
    def pump_messages(
        cls, hwnd, callback: Callable = None, timeout_ms: int = 100
    ) -> bool:
        """杂鱼♡～处理Windows消息泵喵～"""
        return MessagePump.pump_messages(hwnd, callback, timeout_ms)

    @classmethod
    def wait_for_clipboard_message(cls, hwnd, timeout_ms: int = 1000) -> bool:
        """杂鱼♡～等待剪贴板更新消息喵～"""
        return MessagePump.wait_for_clipboard_message(hwnd, timeout_ms)

    @classmethod
    def get_clipboard_sequence_number(cls) -> int:
        """杂鱼♡～获取剪贴板序列号，用于检测变化喵～"""
        return MessagePump.get_clipboard_sequence_number()

    # ============= 杂鱼♡～高级功能喵～ =============

    @classmethod
    def wait_for_clipboard_change(
        cls, timeout: float = 10.0, callback: Callable[[str, Any], None] = None
    ) -> Tuple[Optional[str], Any]:
        """杂鱼♡～等待剪贴板变化喵～"""
        initial_seq = cls.get_clipboard_sequence_number()
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_seq = cls.get_clipboard_sequence_number()
            if current_seq != initial_seq:
                content_type, content = ClipboardReader.get_clipboard_content()
                if callback:
                    try:
                        callback(content_type, content)
                    except Exception as e:
                        cls.logger.error(f"杂鱼♡～回调函数出错喵：{e}")
                return (content_type, content)

            # 杂鱼♡～短暂休眠避免CPU占用过高喵～
            time.sleep(0.01)

        raise ClipboardTimeout(f"杂鱼♡～等待剪贴板变化超时喵～({timeout}s)")

    # ============= 杂鱼♡～兼容性别名喵～ =============

    # 杂鱼♡～为了保持和旧版本的兼容性，提供一些别名喵～
    DEFAULT_RETRY_COUNT = ClipboardReader.DEFAULT_RETRY_COUNT
    DEFAULT_RETRY_DELAY = ClipboardReader.DEFAULT_RETRY_DELAY
    DEFAULT_TIMEOUT = ClipboardReader.DEFAULT_TIMEOUT

    # 杂鱼♡～常量定义喵～
    WM_CLIPBOARDUPDATE = Win32API.WM_CLIPBOARDUPDATE
    HWND_MESSAGE = Win32API.HWND_MESSAGE


# 杂鱼♡～保持向后兼容，导出所有异常类喵～
__all__ = [
    "ClipboardUtils",
    "ClipboardFormat",
    "ClipboardError",
    "ClipboardTimeout",
    "ClipboardAccessDenied",
]
