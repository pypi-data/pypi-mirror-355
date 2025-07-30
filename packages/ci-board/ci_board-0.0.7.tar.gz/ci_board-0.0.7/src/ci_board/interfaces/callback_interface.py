# 杂鱼♡～本喵设计的回调接口定义喵～
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..types.t_source import ProcessInfo


class CallbackInterface(ABC):
    """杂鱼♡～抽象的回调接口，所有处理器都要继承这个喵～"""

    @abstractmethod
    def handle(self, data: Any, source_info: Optional[ProcessInfo] = None) -> None:
        """
        杂鱼♡～处理剪贴板数据的抽象方法喵～

        Args:
            data: 剪贴板数据，类型根据具体处理器而定
            source_info: 源应用程序信息，包含进程路径、窗口标题等
        """

    @abstractmethod
    def is_valid(self, data: Any) -> bool:
        """
        杂鱼♡～检查数据是否有效的抽象方法喵～

        Args:
            data: 需要验证的数据

        Returns:
            bool: 数据是否有效
        """


class BaseClipboardHandler(CallbackInterface):
    """杂鱼♡～基础剪贴板处理器，提供通用功能喵～"""

    def __init__(self, callback: Optional[callable] = None):
        """
        杂鱼♡～初始化处理器喵～

        Args:
            callback: 可选的回调函数，现在接收(data, source_info)两个参数
        """
        self._callback = callback
        self._enabled = True
        self._include_source_info = True  # 杂鱼♡～默认包含源信息喵～

    def set_callback(self, callback: callable) -> None:
        """杂鱼♡～设置回调函数喵～"""
        self._callback = callback

    def enable_source_info(self) -> None:
        """杂鱼♡～启用源应用信息喵～"""
        self._include_source_info = True

    def disable_source_info(self) -> None:
        """杂鱼♡～禁用源应用信息喵～"""
        self._include_source_info = False

    def enable(self) -> None:
        """杂鱼♡～启用处理器喵～"""
        self._enabled = True

    def disable(self) -> None:
        """杂鱼♡～禁用处理器喵～"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """杂鱼♡～检查处理器是否启用喵～"""
        return self._enabled

    def handle(self, data: Any, source_info: Optional[ProcessInfo] = None) -> None:
        """杂鱼♡～处理数据的通用方法喵～"""
        if not self._enabled:
            return

        if not self.is_valid(data):
            return

        if self._callback:
            self._callback(data, source_info if self._include_source_info else None)
        else:
            self._default_handle(data, source_info)

    def _default_handle(
        self, data: Any, source_info: Optional[ProcessInfo] = None
    ) -> None:
        """杂鱼♡～默认处理方法，子类可以重写喵～"""
        # 杂鱼♡～这里需要添加logger，但BaseClipboardHandler没有定义logger喵～
        # 杂鱼♡～子类应该重写这个方法并使用自己的logger喵～
        print(f"杂鱼♡～处理数据：{data}")
        if source_info and self._include_source_info:
            print(
                f"杂鱼♡～源应用程序：{source_info.process_name} ({source_info.process_path})"
            )
