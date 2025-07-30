# 杂鱼♡～本喵为杂鱼主人创建的Windows消息泵处理器喵～
import ctypes
import ctypes.wintypes as w
import time
from typing import Callable, Dict, Optional

from .logger import get_component_logger
from .win32_api import Win32API, Win32Structures

# 杂鱼♡～获取组件专用logger喵～
logger = get_component_logger('utils.message_pump')


class MessagePump:
    """杂鱼♡～专门负责Windows消息处理的类喵～"""

    # 杂鱼♡～全局消息处理器映射喵～
    _window_callbacks: Dict[w.HWND, Optional[Callable]] = {}

    @classmethod
    def create_hidden_window(
        cls, window_name: str = "ClipboardMonitor"
    ) -> Optional[w.HWND]:
        """杂鱼♡～创建隐藏窗口用于监听喵～"""
        try:
            hwnd = Win32API.user32.CreateWindowExW(
                0,  # dwExStyle
                "STATIC",  # 杂鱼♡～使用系统预定义的窗口类喵～
                window_name,  # lpWindowName
                0,  # dwStyle (隐藏窗口)
                0,
                0,
                0,
                0,  # x, y, width, height
                Win32API.HWND_MESSAGE,  # 杂鱼♡～使用message-only窗口父级喵～
                None,  # hMenu
                Win32API.kernel32.GetModuleHandleW(None),  # hInstance
                None,  # lpParam
            )

            if hwnd:
                logger.debug(f"杂鱼♡～创建message-only窗口成功，句柄：{hwnd}")

                # 杂鱼♡～设置窗口过程函数喵～
                GWLP_WNDPROC = -4
                window_proc = Win32API.WNDPROC(cls._window_proc)

                # 杂鱼♡～根据系统架构使用正确的API喵～
                import sys

                if sys.maxsize > 2**32:
                    # 杂鱼♡～64位系统喵～
                    Win32API.user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, window_proc)
                else:
                    # 杂鱼♡～32位系统喵～
                    Win32API.user32.SetWindowLongW(hwnd, GWLP_WNDPROC, window_proc)

                # 杂鱼♡～保持窗口过程函数的引用，防止被垃圾回收喵～
                cls._window_callbacks[hwnd] = None
                setattr(
                    cls, f"_window_proc_{hwnd}", window_proc
                )  # 杂鱼♡～防止垃圾回收喵～

            return hwnd if hwnd else None
        except Exception as e:
            logger.error(f"杂鱼♡～创建隐藏窗口失败喵：{e}")
            return None

    @classmethod
    def destroy_window(cls, hwnd: w.HWND) -> bool:
        """杂鱼♡～销毁窗口喵～"""
        try:
            # 杂鱼♡～清理回调函数映射喵～
            if hwnd in cls._window_callbacks:
                del cls._window_callbacks[hwnd]

            # 杂鱼♡～清理窗口过程函数引用喵～
            proc_attr = f"_window_proc_{hwnd}"
            if hasattr(cls, proc_attr):
                delattr(cls, proc_attr)

            result = bool(Win32API.user32.DestroyWindow(hwnd))
            if result:
                logger.debug(f"杂鱼♡～成功销毁窗口喵～(窗口句柄: {hwnd})")
            return result
        except Exception as e:
            logger.error(f"杂鱼♡～销毁窗口失败喵：{e}")
            return False

    @classmethod
    def add_clipboard_listener(
        cls,
        hwnd: w.HWND,
        callback: Optional[Callable[[w.UINT, w.WPARAM, w.LPARAM], None]] = None,
    ) -> bool:
        """杂鱼♡～添加剪贴板监听器喵～"""
        try:
            # 杂鱼♡～设置回调函数喵～
            if callback:
                cls._window_callbacks[hwnd] = callback

            result = bool(Win32API.user32.AddClipboardFormatListener(hwnd))
            if result:
                logger.debug(f"杂鱼♡～成功添加剪贴板监听器喵～(窗口句柄: {hwnd})")
            return result
        except Exception as e:
            logger.error(f"杂鱼♡～添加剪贴板监听器失败喵：{e}")
            return False

    @classmethod
    def remove_clipboard_listener(cls, hwnd: w.HWND) -> bool:
        """杂鱼♡～移除剪贴板监听器喵～"""
        try:
            return bool(Win32API.user32.RemoveClipboardFormatListener(hwnd))
        except Exception as e:
            logger.error(f"杂鱼♡～移除剪贴板监听器失败喵：{e}")
            return False

    @classmethod
    def _window_proc(
        cls, hwnd: w.HWND, msg: w.UINT, wParam: w.WPARAM, lParam: w.LPARAM
    ) -> w.LPARAM:
        """杂鱼♡～窗口过程函数，处理Windows消息喵～"""
        try:
            # 杂鱼♡～检查是否有自定义回调函数喵～
            if hwnd in cls._window_callbacks and cls._window_callbacks[hwnd]:
                try:
                    cls._window_callbacks[hwnd](msg, wParam, lParam)
                except Exception as e:
                    logger.error(f"杂鱼♡～窗口回调函数执行失败喵：{e}")

            # 杂鱼♡～不在窗口过程中重复打印消息，避免双重处理喵～
            # 杂鱼♡～让回调函数负责具体的消息处理逻辑喵～

            # 杂鱼♡～调用默认窗口过程喵～
            return Win32API.user32.DefWindowProcW(hwnd, msg, wParam, lParam)
        except Exception as e:
            logger.error(f"杂鱼♡～窗口过程函数异常喵：{e}")
            return Win32API.user32.DefWindowProcW(hwnd, msg, wParam, lParam)

    @classmethod
    def pump_messages(
        cls,
        hwnd: w.HWND,
        callback: Optional[Callable[[w.UINT, w.WPARAM, w.LPARAM], None]] = None,
        timeout_ms: int = 100,
    ) -> bool:
        """
        杂鱼♡～处理Windows消息泵，支持事件驱动的剪贴板监控喵～

        Args:
            hwnd: 窗口句柄
            callback: 消息回调函数 (message, wParam, lParam) -> None（可选，优先使用窗口过程）
            timeout_ms: 超时时间（毫秒），0表示不等待，-1表示无限等待

        Returns:
            bool: True表示处理了消息，False表示超时或退出
        """
        try:
            msg = Win32Structures.MSG()

            if timeout_ms == 0:
                # 杂鱼♡～非阻塞模式，只检查是否有消息喵～
                PM_REMOVE = 0x0001
                if Win32API.user32.PeekMessageW(
                    ctypes.byref(msg), hwnd, 0, 0, PM_REMOVE
                ):
                    if msg.message == 0x0012:  # WM_QUIT
                        return False

                    # 杂鱼♡～使用窗口过程来处理消息（推荐）喵～
                    Win32API.user32.TranslateMessage(ctypes.byref(msg))
                    Win32API.user32.DispatchMessageW(
                        ctypes.byref(msg)
                    )  # 杂鱼♡～这会调用窗口过程喵～
                    return True
                return False
            else:
                # 杂鱼♡～阻塞模式，等待消息喵～
                result = Win32API.user32.GetMessageW(ctypes.byref(msg), hwnd, 0, 0)

                if result == -1:  # 杂鱼♡～错误喵～
                    error_code = Win32API.kernel32.GetLastError()
                    logger.error(f"杂鱼♡～GetMessage失败，错误码：{error_code}")
                    return False
                elif result == 0:  # 杂鱼♡～WM_QUIT消息喵～
                    return False
                else:
                    # 杂鱼♡～处理消息喵～
                    Win32API.user32.TranslateMessage(ctypes.byref(msg))
                    Win32API.user32.DispatchMessageW(ctypes.byref(msg))
                    return True
        except Exception as e:
            logger.error(f"杂鱼♡～消息泵处理异常喵：{e}")
            return False

    @classmethod
    def wait_for_clipboard_message(cls, hwnd: w.HWND, timeout_ms: int = 1000) -> bool:
        """杂鱼♡～等待剪贴板更新消息喵～"""
        start_time = ctypes.windll.kernel32.GetTickCount()

        while True:
            current_time = ctypes.windll.kernel32.GetTickCount()
            if current_time - start_time > timeout_ms:
                return False

            def message_callback(
                message: w.UINT, wParam: w.WPARAM, lParam: w.LPARAM
            ) -> None:
                if message == Win32API.WM_CLIPBOARDUPDATE:
                    logger.debug("杂鱼♡～收到剪贴板更新消息喵～")
                    # 杂鱼♡～这里可以处理剪贴板更新逻辑喵～

            # 杂鱼♡～临时设置回调喵～
            original_callback = cls._window_callbacks.get(hwnd)
            cls._window_callbacks[hwnd] = message_callback

            try:
                # 杂鱼♡～非阻塞式检查消息喵～
                if cls.pump_messages(hwnd, timeout_ms=0):
                    # 杂鱼♡～检查是否收到了剪贴板更新消息喵～
                    return True

                # 杂鱼♡～短暂休眠避免CPU占用过高喵～
                time.sleep(0.01)
            finally:
                # 杂鱼♡～恢复原始回调喵～
                cls._window_callbacks[hwnd] = original_callback

    @classmethod
    def get_clipboard_sequence_number(cls) -> int:
        """杂鱼♡～获取剪贴板序列号，用于检测变化喵～"""
        try:
            return Win32API.user32.GetClipboardSequenceNumber()
        except Exception:
            return -1

    @classmethod
    def post_quit_message(cls, exit_code: int = 0) -> None:
        """杂鱼♡～发送退出消息喵～"""
        try:
            Win32API.user32.PostQuitMessage(exit_code)
        except Exception as e:
            logger.error(f"杂鱼♡～发送退出消息失败喵：{e}")

    @classmethod
    def set_window_callback(
        cls,
        hwnd: w.HWND,
        callback: Optional[Callable[[w.UINT, w.WPARAM, w.LPARAM], None]],
    ) -> None:
        """杂鱼♡～设置窗口消息回调函数喵～"""
        cls._window_callbacks[hwnd] = callback

    @classmethod
    def get_window_callback(
        cls, hwnd: w.HWND
    ) -> Optional[Callable[[w.UINT, w.WPARAM, w.LPARAM], None]]:
        """杂鱼♡～获取窗口消息回调函数喵～"""
        return cls._window_callbacks.get(hwnd)
