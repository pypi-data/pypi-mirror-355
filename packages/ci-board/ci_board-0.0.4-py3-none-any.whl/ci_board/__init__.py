# 杂鱼♡～本喵设计的剪贴板监控包喵～
"""
杂鱼♡～本喵的剪贴板监控包 v0.0.5
一个高扩展性的剪贴板监控解决方案喵～
"""

from .core.monitor import ClipboardMonitor
from .handlers.file_handler import FileHandler
from .handlers.image_handler import ImageHandler
from .handlers.text_handler import TextHandler
from .interfaces.callback_interface import CallbackInterface
from .utils.clipboard_utils import ClipboardUtils
from .types.t_image import BMPData

__author__ = "Neko"
__version__ = "0.0.5"

# 杂鱼♡～导出主要API，让杂鱼主人使用方便喵～


# 杂鱼♡～提供简单的函数式API给懒惰的杂鱼主人喵～
def create_monitor(
    async_processing: bool = True,
    event_driven: bool = True,
    max_workers: int = 4,
    handler_timeout: float = 30.0,
):
    """
    杂鱼♡～创建一个新的剪贴板监控器实例喵～

    Args:
        async_processing: 是否启用异步处理模式（默认True）
        max_workers: 处理器线程池最大工作线程数（默认4）
        handler_timeout: 单个处理器超时时间，秒（默认30.0）
    """
    return ClipboardMonitor(
        async_processing=async_processing,
        event_driven=event_driven,
        max_workers=max_workers,
        handler_timeout=handler_timeout,
    )


def create_text_handler(callback=None):
    """杂鱼♡～创建文本处理器喵～"""
    return TextHandler(callback)


def create_image_handler(callback=None):
    """杂鱼♡～创建图片处理器喵～"""
    return ImageHandler(callback)


def create_file_handler(callback=None):
    """杂鱼♡～创建文件处理器喵～"""
    return FileHandler(callback)


# 杂鱼♡～导出所有重要的类和函数喵～
__all__ = [
    "ClipboardMonitor",
    "TextHandler",
    "ImageHandler",
    "FileHandler",
    "CallbackInterface",
    "ClipboardUtils",
    "BMPData",
    "create_monitor",
    "create_text_handler",
    "create_image_handler",
    "create_file_handler",
]
