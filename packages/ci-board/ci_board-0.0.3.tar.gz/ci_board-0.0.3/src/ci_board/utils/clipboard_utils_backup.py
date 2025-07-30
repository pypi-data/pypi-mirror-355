# 杂鱼♡～本喵的剪贴板工具类喵～（备份版本）
import ctypes
import ctypes.wintypes as w
import os
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class ClipboardFormat(Enum):
    """杂鱼♡～剪贴板格式枚举喵～"""

    TEXT = 1
    BITMAP = 2
    UNICODETEXT = 13
    HDROP = 15


class ClipboardError(Exception):
    """杂鱼♡～剪贴板操作异常喵～"""

    pass


class ClipboardTimeout(ClipboardError):
    """杂鱼♡～剪贴板操作超时异常喵～"""

    pass


class ClipboardAccessDenied(ClipboardError):
    """杂鱼♡～剪贴板访问被拒绝异常喵～"""

    pass


class ClipboardUtils:
    """杂鱼♡～剪贴板工具类，封装了所有底层操作喵～"""

    # 杂鱼♡～Windows DLL引用喵～
    user32 = ctypes.WinDLL("user32")
    kernel32 = ctypes.WinDLL("kernel32")
    gdi32 = ctypes.WinDLL("gdi32")
    psapi = ctypes.WinDLL("psapi")  # 杂鱼♡～添加psapi用于获取进程信息喵～

    # 杂鱼♡～消息常量喵～
    WM_CLIPBOARDUPDATE = 0x031D
    HWND_MESSAGE = w.HWND(-3)  # 杂鱼♡～Message-only窗口常量喵～

    # 杂鱼♡～操作配置喵～
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 0.01  # 杂鱼♡～10毫秒喵～
    DEFAULT_TIMEOUT = 2.0  # 杂鱼♡～2秒超时喵～

    # 杂鱼♡～Windows结构体定义喵～
    class _BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", w.DWORD),
            ("biWidth", w.LONG),
            ("biHeight", w.LONG),
            ("biPlanes", w.WORD),
            ("biBitCount", w.WORD),
            ("biCompression", w.DWORD),
            ("biSizeImage", w.DWORD),
            ("biXPelsPerMeter", w.LONG),
            ("biYPelsPerMeter", w.LONG),
            ("biClrUsed", w.DWORD),
            ("biClrImportant", w.DWORD),
        ]

    class _BITMAP(ctypes.Structure):
        _fields_ = [
            ("bmType", w.LONG),
            ("bmWidth", w.LONG),
            ("bmHeight", w.LONG),
            ("bmWidthBytes", w.LONG),
            ("bmPlanes", w.WORD),
            ("bmBitsPixel", w.WORD),
            ("bmBits", w.LPVOID),
        ]

    # 杂鱼♡～Windows消息结构体喵～
    class _MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd", w.HWND),
            ("message", w.UINT),
            ("wParam", w.WPARAM),
            ("lParam", w.LPARAM),
            ("time", w.DWORD),
            ("pt", w.POINT),
        ]

    # 杂鱼♡～线程安全锁喵～
    _clipboard_lock = threading.RLock()

    # 杂鱼♡～全局消息处理器映射喵～
    _window_callbacks = {}

    # 杂鱼♡～窗口过程函数类型定义喵～
    WNDPROC = ctypes.WINFUNCTYPE(w.LPARAM, w.HWND, w.UINT, w.WPARAM, w.LPARAM)

    @classmethod
    def _setup_function_signatures(cls):
        """杂鱼♡～设置Windows API函数签名喵～"""
        # 杂鱼♡～剪贴板相关函数喵～
        cls.user32.OpenClipboard.argtypes = [w.HWND]
        cls.user32.OpenClipboard.restype = w.BOOL
        cls.user32.CloseClipboard.restype = w.BOOL
        cls.user32.IsClipboardFormatAvailable.argtypes = [w.UINT]
        cls.user32.IsClipboardFormatAvailable.restype = w.BOOL
        cls.user32.GetClipboardData.argtypes = [w.UINT]
        cls.user32.GetClipboardData.restype = w.HANDLE

        # 杂鱼♡～内存操作函数喵～
        cls.kernel32.GlobalLock.argtypes = [w.HGLOBAL]
        cls.kernel32.GlobalLock.restype = w.LPVOID
        cls.kernel32.GlobalUnlock.argtypes = [w.HGLOBAL]
        cls.kernel32.GlobalUnlock.restype = w.BOOL

        # 杂鱼♡～监听器相关函数喵～
        cls.user32.AddClipboardFormatListener.argtypes = [w.HWND]
        cls.user32.AddClipboardFormatListener.restype = w.BOOL
        cls.user32.RemoveClipboardFormatListener.argtypes = [w.HWND]
        cls.user32.RemoveClipboardFormatListener.restype = w.BOOL

        # 杂鱼♡～窗口相关函数喵～
        cls.user32.CreateWindowExW.argtypes = [
            w.DWORD,
            w.LPCWSTR,
            w.LPCWSTR,
            w.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            w.HWND,
            w.HMENU,
            w.HINSTANCE,
            w.LPVOID,
        ]
        cls.user32.CreateWindowExW.restype = w.HWND
        cls.user32.DestroyWindow.argtypes = [w.HWND]
        cls.user32.DestroyWindow.restype = w.BOOL

        cls.kernel32.GetModuleHandleW.argtypes = [w.LPCWSTR]
        cls.kernel32.GetModuleHandleW.restype = w.HMODULE

        # 杂鱼♡～内存大小获取函数喵～
        cls.kernel32.GlobalSize.argtypes = [w.HGLOBAL]
        cls.kernel32.GlobalSize.restype = ctypes.c_size_t

        # 杂鱼♡～剪贴板序列号函数喵～
        cls.user32.GetClipboardSequenceNumber.argtypes = []
        cls.user32.GetClipboardSequenceNumber.restype = w.DWORD

        # 杂鱼♡～GDI相关函数喵～
        cls.gdi32.GetObjectW.argtypes = [w.HANDLE, ctypes.c_int, w.LPVOID]
        cls.gdi32.GetObjectW.restype = ctypes.c_int

        # 杂鱼♡～错误处理函数喵～
        cls.kernel32.GetLastError.argtypes = []
        cls.kernel32.GetLastError.restype = w.DWORD

        # 杂鱼♡～剪贴板拥有者函数喵～
        cls.user32.GetClipboardOwner.argtypes = []
        cls.user32.GetClipboardOwner.restype = w.HWND

        # 杂鱼♡～进程相关函数喵～
        cls.user32.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
        cls.user32.GetWindowThreadProcessId.restype = w.DWORD

        # 杂鱼♡～进程句柄相关函数喵～
        cls.kernel32.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        cls.kernel32.OpenProcess.restype = w.HANDLE
        cls.kernel32.CloseHandle.argtypes = [w.HANDLE]
        cls.kernel32.CloseHandle.restype = w.BOOL

        # 杂鱼♡～获取进程模块路径函数喵～
        cls.psapi.GetModuleFileNameExW.argtypes = [
            w.HANDLE,
            w.HMODULE,
            w.LPWSTR,
            w.DWORD,
        ]
        cls.psapi.GetModuleFileNameExW.restype = w.DWORD

        # 杂鱼♡～获取窗口文本相关函数喵～
        cls.user32.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
        cls.user32.GetWindowTextW.restype = ctypes.c_int
        cls.user32.GetWindowTextLengthW.argtypes = [w.HWND]
        cls.user32.GetWindowTextLengthW.restype = ctypes.c_int

        # 杂鱼♡～获取窗口类名函数喵～
        cls.user32.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
        cls.user32.GetClassNameW.restype = ctypes.c_int

        # 杂鱼♡～获取前台窗口函数喵～
        cls.user32.GetForegroundWindow.argtypes = []
        cls.user32.GetForegroundWindow.restype = w.HWND

        # 杂鱼♡～Windows消息泵相关函数喵～
        cls.user32.GetMessageW.argtypes = [
            ctypes.POINTER(cls._MSG),
            w.HWND,
            w.UINT,
            w.UINT,
        ]
        cls.user32.GetMessageW.restype = w.BOOL
        cls.user32.PeekMessageW.argtypes = [
            ctypes.POINTER(cls._MSG),
            w.HWND,
            w.UINT,
            w.UINT,
            w.UINT,
        ]
        cls.user32.PeekMessageW.restype = w.BOOL
        cls.user32.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        cls.user32.PostMessageW.restype = w.BOOL
        cls.user32.TranslateMessage.argtypes = [ctypes.POINTER(cls._MSG)]
        cls.user32.TranslateMessage.restype = w.BOOL
        cls.user32.DispatchMessageW.argtypes = [ctypes.POINTER(cls._MSG)]
        cls.user32.DispatchMessageW.restype = w.LPARAM

        # 杂鱼♡～添加关键的API函数签名，确保64位兼容性喵～
        cls.user32.DefWindowProcW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        cls.user32.DefWindowProcW.restype = w.LPARAM
        cls.user32.IsClipboardFormatAvailable.argtypes = [w.UINT]
        cls.user32.IsClipboardFormatAvailable.restype = w.BOOL
        cls.user32.IsWindowVisible.argtypes = [w.HWND]
        cls.user32.IsWindowVisible.restype = w.BOOL
        cls.user32.GetParent.argtypes = [w.HWND]
        cls.user32.GetParent.restype = w.HWND
        cls.user32.GetWindowLongW.argtypes = [w.HWND, ctypes.c_int]
        cls.user32.GetWindowLongW.restype = w.LONG

        # 杂鱼♡～注意：SetWindowLongPtrW的签名会在使用时动态设置喵～

    # ============= 杂鱼♡～底层函数喵～ =============

    @classmethod
    def _window_proc(
        cls, hwnd: w.HWND, msg: w.UINT, wParam: w.WPARAM, lParam: w.LPARAM
    ) -> w.LPARAM:
        """杂鱼♡～窗口过程函数，处理剪贴板消息喵～"""
        try:
            # 杂鱼♡～检查是否是剪贴板更新消息喵～
            if msg == cls.WM_CLIPBOARDUPDATE:
                # 杂鱼♡～调用注册的回调函数喵～
                if hwnd in cls._window_callbacks:
                    callback = cls._window_callbacks[hwnd]
                    if callback:
                        try:
                            callback(msg, wParam, lParam)
                        except Exception as e:
                            print(f"杂鱼♡～窗口过程回调函数出错喵：{e}")
                return 0

            # 杂鱼♡～其他消息使用默认处理喵～
            return cls.user32.DefWindowProcW(hwnd, msg, wParam, lParam)

        except Exception as e:
            print(f"杂鱼♡～窗口过程函数出错喵：{e}")
            return cls.user32.DefWindowProcW(hwnd, msg, wParam, lParam)

    @classmethod
    def _with_retry(
        cls,
        operation: Callable,
        retry_count: int = None,
        retry_delay: float = None,
        timeout: float = None,
    ) -> Any:
        """杂鱼♡～带重试机制的操作执行器喵～"""
        retry_count = retry_count or cls.DEFAULT_RETRY_COUNT
        retry_delay = retry_delay or cls.DEFAULT_RETRY_DELAY
        timeout = timeout or cls.DEFAULT_TIMEOUT

        start_time = time.time()
        last_exception = None

        for attempt in range(retry_count):
            if time.time() - start_time > timeout:
                raise ClipboardTimeout(f"杂鱼♡～操作超时了喵～({timeout}s)")

            try:
                return operation()
            except Exception as e:
                last_exception = e
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    break

        # 杂鱼♡～所有重试都失败了喵～
        if isinstance(last_exception, ClipboardError):
            raise last_exception
        else:
            raise ClipboardError(f"杂鱼♡～操作失败了喵：{last_exception}")

    @classmethod
    def _safe_open_clipboard(cls, hwnd: w.HWND = None) -> bool:
        """杂鱼♡～安全打开剪贴板喵～"""
        result = cls.user32.OpenClipboard(hwnd)
        if not result:
            error_code = cls.kernel32.GetLastError()
            if error_code == 5:  # 杂鱼♡～ERROR_ACCESS_DENIED喵～
                raise ClipboardAccessDenied("杂鱼♡～剪贴板被其他程序占用了喵～")
            else:
                raise ClipboardError(f"杂鱼♡～打开剪贴板失败喵～(错误码: {error_code})")
        return True

    @classmethod
    def _safe_close_clipboard(cls) -> None:
        """杂鱼♡～安全关闭剪贴板喵～"""
        if not cls.user32.CloseClipboard():
            error_code = cls.kernel32.GetLastError()

            # 杂鱼♡～常见的非致命错误码，只在调试时显示喵～
            non_critical_errors = {
                1418: "ERROR_THREAD_MODE_NOT_SUPPORTED",  # 杂鱼♡～线程模式不支持，但不影响功能喵～
                1400: "ERROR_INVALID_WINDOW_HANDLE",  # 杂鱼♡～无效窗口句柄喵～
                1413: "ERROR_INVALID_HOOK_HANDLE",  # 杂鱼♡～无效钩子句柄喵～
            }

            if error_code in non_critical_errors:
                # 杂鱼♡～对于非致命错误，只在debug模式下显示详细信息喵～
                # print(f"杂鱼♡～剪贴板关闭时的轻微警告喵～({non_critical_errors[error_code]}: {error_code})")
                pass  # 杂鱼♡～静默处理，不影响用户体验喵～
            else:
                # 杂鱼♡～其他错误需要显示喵～
                print(f"杂鱼♡～关闭剪贴板时出现警告喵～(错误码: {error_code})")

    @classmethod
    def _check_memory_validity(cls, handle: w.HANDLE, min_size: int = 1) -> bool:
        """杂鱼♡～检查内存句柄有效性喵～"""
        if not handle:
            return False

        try:
            size = cls.kernel32.GlobalSize(handle)
            return size >= min_size
        except Exception:
            return False

    @classmethod
    def _get_clipboard_owner_info(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板拥有者信息喵～"""
        try:
            owner_hwnd = cls.user32.GetClipboardOwner()
            if not owner_hwnd:
                return {"owner": None, "process_id": None}

            process_id = w.DWORD()
            thread_id = cls.user32.GetWindowThreadProcessId(
                owner_hwnd, ctypes.byref(process_id)
            )

            return {
                "owner": owner_hwnd,
                "process_id": process_id.value,
                "thread_id": thread_id,
            }
        except Exception:
            return {"owner": None, "process_id": None}

    @classmethod
    def get_source_application_info(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板源应用程序详细信息喵～"""
        try:
            # 杂鱼♡～获取剪贴板拥有者窗口喵～
            owner_hwnd = cls.user32.GetClipboardOwner()
            if not owner_hwnd:
                # 杂鱼♡～没有剪贴板拥有者时，尝试使用前台窗口作为fallback喵～
                print("杂鱼♡～没有剪贴板拥有者，尝试使用前台窗口作为备选喵～")
                fallback_info = cls._get_foreground_window_info()

                if fallback_info and fallback_info.get("process_name"):
                    # 杂鱼♡～如果前台窗口有效，使用它作为源信息喵～
                    return {
                        "window_handle": fallback_info.get("window_handle"),
                        "process_id": fallback_info.get("process_id"),
                        "thread_id": fallback_info.get("thread_id"),
                        "process_path": fallback_info.get("process_path"),
                        "process_name": fallback_info.get("process_name"),
                        "window_title": fallback_info.get("window_title"),
                        "window_class": fallback_info.get("window_class"),
                        "timestamp": time.time(),
                        "detection_method": "foreground_window_fallback",
                        "note": "No clipboard owner found, using foreground window as fallback",
                        "is_fallback": True,
                    }
                else:
                    # 杂鱼♡～前台窗口也不可用，尝试Alt+Tab window fallback喵～
                    alt_tab_info = cls._get_alt_tab_window_info()
                    if alt_tab_info and alt_tab_info.get("process_name"):
                        return {
                            "window_handle": alt_tab_info.get("window_handle"),
                            "process_id": alt_tab_info.get("process_id"),
                            "thread_id": alt_tab_info.get("thread_id"),
                            "process_path": alt_tab_info.get("process_path"),
                            "process_name": alt_tab_info.get("process_name"),
                            "window_title": alt_tab_info.get("window_title"),
                            "window_class": alt_tab_info.get("window_class"),
                            "timestamp": time.time(),
                            "detection_method": "alt_tab_fallback",
                            "note": "No clipboard owner or foreground window found, using active application as fallback",
                            "is_fallback": True,
                        }

                # 杂鱼♡～所有fallback都失败了，返回特殊的"Unknown"信息喵～
                return {
                    "window_handle": None,
                    "process_id": None,
                    "process_path": None,
                    "process_name": "Unknown",  # 杂鱼♡～不再返回None，而是"Unknown"喵～
                    "window_title": None,
                    "window_class": None,
                    "timestamp": time.time(),
                    "detection_method": "unknown",
                    "error": "No clipboard owner found and all fallback methods failed",
                    "is_fallback": True,
                }

            # 杂鱼♡～获取进程ID喵～
            process_id = w.DWORD()
            thread_id = cls.user32.GetWindowThreadProcessId(
                owner_hwnd, ctypes.byref(process_id)
            )

            if not process_id.value:
                # 杂鱼♡～无法获取进程ID时也使用fallback喵～
                fallback_info = cls._get_foreground_window_info()
                if fallback_info and fallback_info.get("process_name"):
                    fallback_info["detection_method"] = "foreground_window_fallback"
                    fallback_info["note"] = (
                        "Failed to get process ID from clipboard owner, using foreground window"
                    )
                    fallback_info["is_fallback"] = True
                    fallback_info["timestamp"] = time.time()
                    return fallback_info

                return {
                    "window_handle": owner_hwnd,
                    "process_id": None,
                    "process_path": None,
                    "process_name": "Unknown",  # 杂鱼♡～同样不返回None喵～
                    "window_title": cls._get_window_title(owner_hwnd),
                    "window_class": cls._get_window_class(owner_hwnd),
                    "timestamp": time.time(),
                    "detection_method": "clipboard_owner",
                    "error": "Failed to get process ID",
                    "is_fallback": True,
                }

            # 杂鱼♡～获取进程路径喵～
            process_path = cls._get_process_path(process_id.value)
            process_name = (
                os.path.basename(process_path) if process_path else "Unknown"
            )  # 杂鱼♡～不返回None喵～

            # 杂鱼♡～检查是否为系统进程，如果是则尝试获取前台窗口信息喵～
            is_system_process = cls._is_system_process(process_name)
            fallback_info = None
            detection_method = "clipboard_owner"
            note = None

            if is_system_process:
                # 杂鱼♡～第一级fallback：尝试获取前台窗口信息喵～
                fallback_info = cls._get_foreground_window_info()

                # 杂鱼♡～检查前台窗口是否为截图工具或系统进程喵～
                if fallback_info and fallback_info.get("process_name"):

                    fg_process_name = fallback_info.get("process_name")

                    # 杂鱼♡～如果前台窗口也是截图工具，继续fallback喵～
                    if cls._is_screenshot_tool(fg_process_name):
                        # 杂鱼♡～第二级fallback：尝试获取用户应用程序窗口喵～
                        alt_tab_info = cls._get_alt_tab_window_info()

                        if alt_tab_info and alt_tab_info.get("process_name"):
                            # 杂鱼♡～使用Alt+Tab窗口信息喵～
                            return {
                                "window_handle": alt_tab_info.get("window_handle"),
                                "process_id": alt_tab_info.get("process_id"),
                                "thread_id": alt_tab_info.get("thread_id"),
                                "process_path": alt_tab_info.get("process_path"),
                                "process_name": alt_tab_info.get("process_name"),
                                "window_title": alt_tab_info.get("window_title"),
                                "window_class": alt_tab_info.get("window_class"),
                                "timestamp": time.time(),
                                "detection_method": "alt_tab_window",
                                "clipboard_owner_process": process_name,
                                "foreground_process": fg_process_name,
                                "note": f"Detected system process {process_name} and screenshot tool {fg_process_name}, using active user application instead",
                            }
                        else:
                            # 杂鱼♡～如果Alt+Tab fallback也失败，还是使用截图工具信息喵～
                            detection_method = "foreground_window"
                            note = f"Detected system process {process_name} and screenshot tool {fg_process_name}, no better alternative found"

                    # 杂鱼♡～如果前台窗口不是系统进程且不是截图工具，使用它喵～
                    elif not cls._is_system_process(fg_process_name):
                        detection_method = "foreground_window"
                        note = f"Detected system process {process_name}, using foreground window instead"
                    else:
                        # 杂鱼♡～前台窗口也是系统进程，尝试其他fallback喵～
                        alt_tab_info = cls._get_alt_tab_window_info()
                        if alt_tab_info and alt_tab_info.get("process_name"):
                            return {
                                "window_handle": alt_tab_info.get("window_handle"),
                                "process_id": alt_tab_info.get("process_id"),
                                "thread_id": alt_tab_info.get("thread_id"),
                                "process_path": alt_tab_info.get("process_path"),
                                "process_name": alt_tab_info.get("process_name"),
                                "window_title": alt_tab_info.get("window_title"),
                                "window_class": alt_tab_info.get("window_class"),
                                "timestamp": time.time(),
                                "detection_method": "alt_tab_window",
                                "clipboard_owner_process": process_name,
                                "foreground_process": fg_process_name,
                                "note": f"Both clipboard owner ({process_name}) and foreground ({fg_process_name}) are system processes, using active user application",
                            }
                        else:
                            detection_method = "foreground_window"
                            note = f"Detected system process {process_name}, foreground also system process {fg_process_name}"

                # 杂鱼♡～如果有有效的fallback信息，使用它喵～
                if fallback_info and fallback_info.get("process_name"):
                    return {
                        "window_handle": fallback_info.get("window_handle"),
                        "process_id": fallback_info.get("process_id"),
                        "thread_id": fallback_info.get("thread_id"),
                        "process_path": fallback_info.get("process_path"),
                        "process_name": fallback_info.get("process_name"),
                        "window_title": fallback_info.get("window_title"),
                        "window_class": fallback_info.get("window_class"),
                        "timestamp": time.time(),
                        "detection_method": detection_method,
                        "clipboard_owner_process": process_name,
                        "note": note,
                    }

            # 杂鱼♡～获取窗口信息，如果没有标题则尝试查找同进程的其他窗口喵～
            window_title = cls._get_window_title(owner_hwnd)
            window_class = cls._get_window_class(owner_hwnd)

            # 杂鱼♡～如果剪贴板拥有者窗口没有标题，尝试查找同进程的主窗口喵～
            if not window_title or not window_title.strip():
                main_window_info = cls._get_process_main_window(process_id.value)
                if main_window_info and main_window_info.get("window_title"):
                    window_title = main_window_info["window_title"]
                    # 杂鱼♡～可以选择是否更新窗口类和句柄喵～
                    if main_window_info.get("window_class"):
                        window_class = main_window_info["window_class"]

            return {
                "window_handle": owner_hwnd,
                "process_id": process_id.value,
                "thread_id": thread_id,
                "process_path": process_path,
                "process_name": process_name,
                "window_title": window_title,
                "window_class": window_class,
                "timestamp": time.time(),
                "detection_method": "clipboard_owner",
                "is_system_process": is_system_process,
            }

        except Exception as e:
            return {
                "window_handle": None,
                "process_id": None,
                "process_path": None,
                "process_name": None,
                "window_title": None,
                "window_class": None,
                "error": f"Exception: {str(e)}",
            }

    @classmethod
    def _is_system_process(cls, process_name: Optional[str]) -> bool:
        """杂鱼♡～检查是否为系统进程喵～"""
        if not process_name:
            return False

        system_processes = {
            "svchost.exe",  # 杂鱼♡～系统服务主机喵～
            "dwm.exe",  # 杂鱼♡～桌面窗口管理器喵～
            "winlogon.exe",  # 杂鱼♡～Windows登录进程喵～
            "csrss.exe",  # 杂鱼♡～客户端/服务器运行时进程喵～
            "wininit.exe",  # 杂鱼♡～Windows初始化进程喵～
            "services.exe",  # 杂鱼♡～服务控制管理器喵～
            "lsass.exe",  # 杂鱼♡～本地安全认证服务器喵～
            "smss.exe",  # 杂鱼♡～会话管理器喵～
            "conhost.exe",  # 杂鱼♡～控制台主机进程喵～
            "explorer.exe",  # 杂鱼♡～资源管理器喵～（虽然是系统进程但通常有意义）
        }

        # 杂鱼♡～explorer.exe 虽然是系统进程，但通常表示用户操作，所以不视为需要fallback的系统进程喵～
        if process_name.lower() == "explorer.exe":
            return False

        return process_name.lower() in {p.lower() for p in system_processes}

    @classmethod
    def _is_screenshot_tool(cls, process_name: Optional[str]) -> bool:
        """杂鱼♡～检查是否为截图工具喵～"""
        if not process_name:
            return False

        screenshot_tools = {
            "screenclippinghost.exe",  # 杂鱼♡～Windows截图工具喵～
            "snippingtool.exe",  # 杂鱼♡～截图工具喵～
            "screensketch.exe",  # 杂鱼♡～屏幕草图喵～
            "sharex.exe",  # 杂鱼♡～第三方截图工具喵～
            "lightshot.exe",  # 杂鱼♡～Lightshot截图工具喵～
            "greenshot.exe",  # 杂鱼♡～Greenshot截图工具喵～
            "picpick.exe",  # 杂鱼♡～PicPick截图工具喵～
            "snagit32.exe",  # 杂鱼♡～Snagit截图工具喵～
            "snagiteditor.exe",  # 杂鱼♡～Snagit编辑器喵～
            "screentogif.exe",  # 杂鱼♡～屏幕录制工具喵～
        }

        return process_name.lower() in {p.lower() for p in screenshot_tools}

    @classmethod
    def _get_foreground_window_info(cls) -> Optional[Dict[str, Any]]:
        """杂鱼♡～获取前台窗口信息作为fallback喵～"""
        try:
            # 杂鱼♡～获取前台窗口句柄喵～
            fg_hwnd = cls.user32.GetForegroundWindow()
            if not fg_hwnd:
                return None

            # 杂鱼♡～获取前台窗口的进程ID喵～
            fg_process_id = w.DWORD()
            fg_thread_id = cls.user32.GetWindowThreadProcessId(
                fg_hwnd, ctypes.byref(fg_process_id)
            )

            if not fg_process_id.value:
                return None

            # 杂鱼♡～获取前台窗口的进程信息喵～
            fg_process_path = cls._get_process_path(fg_process_id.value)
            fg_process_name = (
                os.path.basename(fg_process_path) if fg_process_path else None
            )

            return {
                "window_handle": fg_hwnd,
                "process_id": fg_process_id.value,
                "thread_id": fg_thread_id,
                "process_path": fg_process_path,
                "process_name": fg_process_name,
                "window_title": cls._get_window_title(fg_hwnd),
                "window_class": cls._get_window_class(fg_hwnd),
            }

        except Exception as e:
            print(f"杂鱼♡～获取前台窗口信息失败喵：{e}")
            return None

    @classmethod
    def _get_process_path(cls, process_id: int) -> Optional[str]:
        """杂鱼♡～通过进程ID获取进程路径喵～"""
        try:
            # 杂鱼♡～进程访问权限常量喵～
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010

            # 杂鱼♡～打开进程句柄喵～
            process_handle = cls.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process_id
            )

            if not process_handle:
                return None

            try:
                # 杂鱼♡～准备路径缓冲区喵～
                path_buffer = ctypes.create_unicode_buffer(1024)

                # 杂鱼♡～获取进程模块文件名喵～
                result = cls.psapi.GetModuleFileNameExW(
                    process_handle,
                    None,  # 杂鱼♡～主模块喵～
                    path_buffer,
                    len(path_buffer),
                )

                if result > 0:
                    return path_buffer.value
                else:
                    return None

            finally:
                cls.kernel32.CloseHandle(process_handle)

        except Exception as e:
            print(f"杂鱼♡～获取进程路径失败喵：{e}")
            return None

    @classmethod
    def _get_window_title(cls, hwnd: w.HWND) -> Optional[str]:
        """杂鱼♡～获取窗口标题喵～"""
        try:
            # 杂鱼♡～获取窗口标题长度喵～
            title_length = cls.user32.GetWindowTextLengthW(hwnd)
            if title_length <= 0:
                return None

            # 杂鱼♡～创建缓冲区并获取标题喵～
            title_buffer = ctypes.create_unicode_buffer(title_length + 1)
            result = cls.user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))

            if result > 0:
                return title_buffer.value
            else:
                return None

        except Exception:
            return None

    @classmethod
    def _get_window_class(cls, hwnd: w.HWND) -> Optional[str]:
        """杂鱼♡～获取窗口类名喵～"""
        try:
            class_buffer = ctypes.create_unicode_buffer(256)
            result = cls.user32.GetClassNameW(hwnd, class_buffer, len(class_buffer))

            if result > 0:
                return class_buffer.value
            else:
                return None

        except Exception:
            return None

    # ============= 杂鱼♡～中级函数喵～ =============

    @classmethod
    def is_format_available(cls, format_type: ClipboardFormat) -> bool:
        """杂鱼♡～检查指定格式是否可用喵～"""
        try:
            return bool(cls.user32.IsClipboardFormatAvailable(format_type.value))
        except Exception:
            return False

    @classmethod
    def get_available_formats(cls) -> List[str]:
        """杂鱼♡～获取所有可用的剪贴板格式喵～"""
        formats = []

        # 杂鱼♡～检查常见格式喵～
        format_names = {
            1: "CF_TEXT",
            2: "CF_BITMAP",
            3: "CF_METAFILEPICT",
            8: "CF_DIB",
            13: "CF_UNICODETEXT",
            15: "CF_HDROP",
            17: "CF_DIBV5",
        }

        for format_id, format_name in format_names.items():
            if cls.user32.IsClipboardFormatAvailable(format_id):
                formats.append(format_name)

        return formats

    @classmethod
    def get_clipboard_stats(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板统计信息喵～"""
        stats = {
            "sequence_number": cls.get_clipboard_sequence_number(),
            "available_formats": cls.get_available_formats(),
            "owner_info": cls._get_clipboard_owner_info(),
            "content_type": cls.detect_content_type(),
            "timestamp": time.time(),
        }
        return stats

    @classmethod
    def get_text_content(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[str]:
        """杂鱼♡～获取文本内容（带错误处理）喵～"""

        def _get_text():
            with cls._clipboard_lock:
                cls._safe_open_clipboard()
                try:
                    if cls.user32.IsClipboardFormatAvailable(
                        ClipboardFormat.UNICODETEXT.value
                    ):
                        h_clip_mem = cls.user32.GetClipboardData(
                            ClipboardFormat.UNICODETEXT.value
                        )
                        if h_clip_mem and cls._check_memory_validity(h_clip_mem):
                            p_clip_mem = cls.kernel32.GlobalLock(h_clip_mem)
                            if p_clip_mem:
                                try:
                                    # 杂鱼♡～UTF-16LE字符串处理喵～
                                    text_data = ctypes.c_wchar_p(p_clip_mem).value
                                    return text_data
                                finally:
                                    cls.kernel32.GlobalUnlock(h_clip_mem)
                finally:
                    cls._safe_close_clipboard()
            return None

        try:
            return cls._with_retry(_get_text, retry_count, timeout=timeout)
        except ClipboardError:
            return None

    @classmethod
    def get_image_content(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[Any]:
        """杂鱼♡～使用Windows API直接获取图片内容（带错误处理）喵～"""

        def _get_image():
            with cls._clipboard_lock:
                cls._safe_open_clipboard()
                try:
                    # 杂鱼♡～优先尝试CF_DIBV5格式喵～ (Comment for testing)
                    CF_DIBV5 = 17
                    if cls.user32.IsClipboardFormatAvailable(CF_DIBV5):
                        result = cls._get_dib_data(CF_DIBV5)
                        if result:
                            return result

                    # 杂鱼♡～尝试CF_DIB格式喵～
                    CF_DIB = 8
                    if cls.user32.IsClipboardFormatAvailable(CF_DIB):
                        result = cls._get_dib_data(CF_DIB)
                        if result:
                            return result

                    # 杂鱼♡～最后尝试CF_BITMAP格式喵～
                    if cls.user32.IsClipboardFormatAvailable(
                        ClipboardFormat.BITMAP.value
                    ):
                        return cls._get_bitmap_data()

                    return None
                finally:
                    cls._safe_close_clipboard()

        try:
            return cls._with_retry(_get_image, retry_count, timeout=timeout)
        except ClipboardError:
            return None

    @classmethod
    def _get_dib_data(cls, format_type: int) -> Optional[dict]:
        """杂鱼♡～获取DIB格式的图片数据（增强版）喵～"""
        h_dib = cls.user32.GetClipboardData(format_type)
        if not h_dib or not cls._check_memory_validity(
            h_dib, 40
        ):  # 杂鱼♡～至少需要BITMAPINFOHEADER大小喵～
            return None

        # 杂鱼♡～锁定内存获取DIB数据喵～
        p_dib = cls.kernel32.GlobalLock(h_dib)
        if not p_dib:
            return None

        try:
            # 杂鱼♡～获取DIB大小喵～
            dib_size = cls.kernel32.GlobalSize(h_dib)

            # 杂鱼♡～读取DIB头信息喵～
            bih = ctypes.cast(p_dib, ctypes.POINTER(cls._BITMAPINFOHEADER)).contents

            # 杂鱼♡～验证DIB头的合理性喵～
            if (
                bih.biSize < 40  # 杂鱼♡～头大小至少40字节喵～
                or bih.biWidth <= 0
                or bih.biWidth > 32767  # 杂鱼♡～宽度范围检查喵～
                or abs(bih.biHeight) > 32767  # 杂鱼♡～高度范围检查喵～
                or bih.biBitCount not in [1, 4, 8, 16, 24, 32]
            ):  # 杂鱼♡～支持的位深度喵～
                print("杂鱼♡～DIB头数据无效喵～")
                return None

            image_info = {
                "type": "DIB",
                "format": f'CF_DIB{"V5" if format_type == 17 else ""}',
                "width": bih.biWidth,
                "height": abs(bih.biHeight),  # 杂鱼♡～高度可能是负数喵～
                "bit_count": bih.biBitCount,
                "compression": bih.biCompression,
                "size_image": bih.biSizeImage,
                "size": dib_size,
                "data_pointer": p_dib,  # 杂鱼♡～原始数据指针喵～
                "is_top_down": bih.biHeight < 0,  # 杂鱼♡～是否是自顶向下的图片喵～
            }

            return image_info

        except Exception as e:
            print(f"杂鱼♡～解析DIB数据时出错喵：{e}")
            return None
        finally:
            cls.kernel32.GlobalUnlock(h_dib)

    @classmethod
    def _get_bitmap_data(cls) -> Optional[dict]:
        """杂鱼♡～获取BITMAP格式的图片数据（增强版）喵～"""
        h_bitmap = cls.user32.GetClipboardData(ClipboardFormat.BITMAP.value)
        if not h_bitmap:
            return None

        # 杂鱼♡～获取位图信息喵～
        bitmap_info = cls._BITMAP()
        result = cls.gdi32.GetObjectW(
            h_bitmap, ctypes.sizeof(bitmap_info), ctypes.byref(bitmap_info)
        )

        if result and bitmap_info.bmWidth > 0 and bitmap_info.bmHeight > 0:
            return {
                "type": "BITMAP",
                "format": "CF_BITMAP",
                "width": bitmap_info.bmWidth,
                "height": bitmap_info.bmHeight,
                "bit_count": bitmap_info.bmBitsPixel,
                "planes": bitmap_info.bmPlanes,
                "width_bytes": bitmap_info.bmWidthBytes,
                "handle": h_bitmap,  # 杂鱼♡～位图句柄喵～
            }

        return None

    @classmethod
    def detect_content_type(cls) -> Optional[str]:
        """杂鱼♡～检测剪贴板内容类型喵～"""
        try:
            # 杂鱼♡～检查各种图片格式喵～
            CF_DIB = 8
            CF_DIBV5 = 17
            if (
                cls.is_format_available(ClipboardFormat.BITMAP)
                or cls.user32.IsClipboardFormatAvailable(CF_DIB)
                or cls.user32.IsClipboardFormatAvailable(CF_DIBV5)
            ):
                return "image"
            elif cls.is_format_available(ClipboardFormat.UNICODETEXT):
                return "text"
            elif cls.is_format_available(ClipboardFormat.HDROP):
                return "files"
        except Exception:
            pass
        return None

    # ============= 杂鱼♡～高级函数喵～ =============

    @classmethod
    def get_clipboard_content(
        cls, retry_count: int = None, timeout: float = None, with_source: bool = False
    ) -> Tuple[Optional[str], Any, Optional[Dict[str, Any]]]:
        """杂鱼♡～获取剪贴板内容和类型（增强版）喵～"""
        content_type = cls.detect_content_type()
        content = None
        source_info = None

        try:
            if content_type == "text":
                content = cls.get_text_content(retry_count, timeout)
            elif content_type == "image":
                content = cls.get_image_content(retry_count, timeout)
            elif content_type == "files":
                # 杂鱼♡～文件列表处理太复杂，杂鱼主人自己想办法喵～
                content = []
        except Exception as e:
            print(f"杂鱼♡～获取剪贴板内容时出错喵：{e}")
            content = None

        # 杂鱼♡～如果需要源信息，则获取源应用信息喵～
        if with_source:
            source_info = cls.get_source_application_info()

        return (content_type, content, source_info)

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
                content_type, content, _ = cls.get_clipboard_content()
                if callback:
                    try:
                        callback(content_type, content)
                    except Exception as e:
                        print(f"杂鱼♡～回调函数出错喵：{e}")
                return (content_type, content)

        raise ClipboardTimeout(f"杂鱼♡～等待剪贴板变化超时喵～({timeout}s)")

    @classmethod
    def create_hidden_window(
        cls, window_name: str = "ClipboardMonitor"
    ) -> Optional[w.HWND]:
        """杂鱼♡～创建隐藏窗口用于监听喵～"""
        try:
            hwnd = cls.user32.CreateWindowExW(
                0,  # dwExStyle
                "STATIC",  # 杂鱼♡～使用系统预定义的窗口类喵～
                window_name,  # lpWindowName
                0,  # dwStyle (隐藏窗口)
                0,
                0,
                0,
                0,  # x, y, width, height
                cls.HWND_MESSAGE,  # 杂鱼♡～使用message-only窗口父级喵～
                None,  # hMenu
                cls.kernel32.GetModuleHandleW(None),  # hInstance
                None,  # lpParam
            )

            if hwnd:
                print(f"杂鱼♡～创建message-only窗口成功，句柄：{hwnd}")

                # 杂鱼♡～设置窗口过程函数喵～
                GWLP_WNDPROC = -4
                window_proc = cls.WNDPROC(cls._window_proc)

                # 杂鱼♡～根据系统架构使用正确的API喵～
                import sys

                if sys.maxsize > 2**32:
                    # 杂鱼♡～64位系统喵～
                    cls.user32.SetWindowLongPtrW.argtypes = [
                        w.HWND,
                        ctypes.c_int,
                        cls.WNDPROC,
                    ]
                    cls.user32.SetWindowLongPtrW.restype = cls.WNDPROC
                    cls.user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, window_proc)
                else:
                    # 杂鱼♡～32位系统喵～
                    cls.user32.SetWindowLongW.argtypes = [
                        w.HWND,
                        ctypes.c_int,
                        cls.WNDPROC,
                    ]
                    cls.user32.SetWindowLongW.restype = cls.WNDPROC
                    cls.user32.SetWindowLongW(hwnd, GWLP_WNDPROC, window_proc)

                # 杂鱼♡～保持窗口过程函数的引用，防止被垃圾回收喵～
                cls._window_callbacks[hwnd] = None
                setattr(
                    cls, f"_window_proc_{hwnd}", window_proc
                )  # 杂鱼♡～防止垃圾回收喵～

            return hwnd if hwnd else None
        except Exception as e:
            print(f"杂鱼♡～创建隐藏窗口失败喵：{e}")
            return None

    @classmethod
    def add_clipboard_listener(
        cls, hwnd: w.HWND, callback: Callable[[w.UINT, w.WPARAM, w.LPARAM], None] = None
    ) -> bool:
        """杂鱼♡～添加剪贴板监听器喵～"""
        try:
            # 杂鱼♡～设置回调函数喵～
            if callback:
                cls._window_callbacks[hwnd] = callback

            result = bool(cls.user32.AddClipboardFormatListener(hwnd))
            if result:
                print(f"杂鱼♡～成功添加剪贴板监听器喵～(窗口句柄: {hwnd})")
            return result
        except Exception as e:
            print(f"杂鱼♡～添加剪贴板监听器失败喵：{e}")
            return False

    @classmethod
    def remove_clipboard_listener(cls, hwnd: w.HWND) -> bool:
        """杂鱼♡～移除剪贴板监听器喵～"""
        try:
            return bool(cls.user32.RemoveClipboardFormatListener(hwnd))
        except Exception as e:
            print(f"杂鱼♡～移除剪贴板监听器失败喵：{e}")
            return False

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

            result = bool(cls.user32.DestroyWindow(hwnd))
            if result:
                print(f"杂鱼♡～成功销毁窗口喵～(窗口句柄: {hwnd})")
            return result
        except Exception as e:
            print(f"杂鱼♡～销毁窗口失败喵：{e}")
            return False

    @classmethod
    def get_clipboard_sequence_number(cls) -> int:
        """杂鱼♡～获取剪贴板序列号，用于检测变化喵～"""
        try:
            return cls.user32.GetClipboardSequenceNumber()
        except Exception:
            return -1

    @classmethod
    def pump_messages(
        cls,
        hwnd: w.HWND,
        callback: Callable[[w.UINT, w.WPARAM, w.LPARAM], None] = None,
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
            msg = cls._MSG()

            if timeout_ms == 0:
                # 杂鱼♡～非阻塞模式，只检查是否有消息喵～
                PM_REMOVE = 0x0001
                if cls.user32.PeekMessageW(ctypes.byref(msg), hwnd, 0, 0, PM_REMOVE):
                    if msg.message == 0x0012:  # WM_QUIT
                        return False

                    # 杂鱼♡～使用窗口过程来处理消息（推荐）喵～
                    cls.user32.TranslateMessage(ctypes.byref(msg))
                    cls.user32.DispatchMessageW(
                        ctypes.byref(msg)
                    )  # 杂鱼♡～这会调用窗口过程喵～
                    return True
                return False
            else:
                # 杂鱼♡～阻塞模式，等待消息喵～
                # 杂鱼♡～使用像测试钩子那样的GetMessageW调用方式喵～
                result = cls.user32.GetMessageW(ctypes.byref(msg), hwnd, 0, 0)

                if result == -1:  # 杂鱼♡～错误喵～
                    error_code = cls.kernel32.GetLastError()
                    print(f"杂鱼♡～GetMessage失败喵：错误码 {error_code}")
                    return False
                elif result == 0:  # 杂鱼♡～WM_QUIT喵～
                    return False

                # 杂鱼♡～使用窗口过程来处理消息（推荐）喵～
                cls.user32.TranslateMessage(ctypes.byref(msg))
                cls.user32.DispatchMessageW(
                    ctypes.byref(msg)
                )  # 杂鱼♡～这会调用窗口过程喵～
                return True

        except Exception as e:
            print(f"杂鱼♡～处理消息泵时出错喵：{e}")
            return False

    @classmethod
    def wait_for_clipboard_message(cls, hwnd: w.HWND, timeout_ms: int = 1000) -> bool:
        """
        杂鱼♡～等待剪贴板更新消息喵～

        Args:
            hwnd: 窗口句柄
            timeout_ms: 超时时间（毫秒）

        Returns:
            bool: True表示收到剪贴板更新消息，False表示超时
        """
        import time

        start_time = time.time() * 1000  # 杂鱼♡～转换为毫秒喵～

        def message_callback(
            message: w.UINT, wParam: w.WPARAM, lParam: w.LPARAM
        ) -> None:
            nonlocal clipboard_updated
            if message == cls.WM_CLIPBOARDUPDATE:
                clipboard_updated = True

        clipboard_updated = False

        while True:
            # 杂鱼♡～非阻塞检查消息喵～
            if cls.pump_messages(hwnd, message_callback, 0):
                if clipboard_updated:
                    return True

            # 杂鱼♡～检查超时喵～
            current_time = time.time() * 1000
            if timeout_ms > 0 and (current_time - start_time) >= timeout_ms:
                break

            # 杂鱼♡～短暂休息避免CPU过度占用喵～
            time.sleep(0.001)  # 杂鱼♡～1毫秒喵～

        return False

    @classmethod
    def _get_alt_tab_window_info(cls) -> Optional[Dict[str, Any]]:
        """杂鱼♡～尝试获取Alt+Tab窗口列表中最近的用户应用程序喵～"""
        try:
            # 杂鱼♡～枚举所有顶级窗口喵～
            windows = []

            def enum_windows_proc(hwnd, lParam):
                # 杂鱼♡～检查窗口是否可见且不是工具窗口喵～
                if (
                    cls.user32.IsWindowVisible(hwnd) and cls.user32.GetParent(hwnd) == 0
                ):  # 杂鱼♡～顶级窗口喵～

                    # 杂鱼♡～获取窗口扩展样式喵～
                    ex_style = cls.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE

                    # 杂鱼♡～跳过工具窗口和无任务栏窗口喵～
                    if not (ex_style & 0x00000080):  # WS_EX_TOOLWINDOW
                        # 杂鱼♡～获取窗口进程信息喵～
                        process_id = w.DWORD()
                        cls.user32.GetWindowThreadProcessId(
                            hwnd, ctypes.byref(process_id)
                        )

                        if process_id.value:
                            process_path = cls._get_process_path(process_id.value)
                            process_name = (
                                os.path.basename(process_path) if process_path else None
                            )
                            window_title = cls._get_window_title(hwnd)

                            # 杂鱼♡～跳过系统进程和截图工具喵～
                            if (
                                process_name
                                and not cls._is_system_process(process_name)
                                and not cls._is_screenshot_tool(process_name)
                                and window_title
                                and window_title.strip()
                            ):  # 杂鱼♡～必须有标题喵～

                                windows.append(
                                    {
                                        "window_handle": hwnd,
                                        "process_id": process_id.value,
                                        "process_path": process_path,
                                        "process_name": process_name,
                                        "window_title": window_title,
                                        "window_class": cls._get_window_class(hwnd),
                                    }
                                )

                return True  # 杂鱼♡～继续枚举喵～

            # 杂鱼♡～枚举所有窗口喵～
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, w.HWND, w.LPARAM)
            enum_proc = EnumWindowsProc(enum_windows_proc)
            cls.user32.EnumWindows(enum_proc, 0)

            # 杂鱼♡～返回第一个找到的用户应用程序喵～
            if windows:
                # 杂鱼♡～优先选择有意义标题的窗口喵～
                meaningful_windows = [w for w in windows if len(w["window_title"]) > 1]
                if meaningful_windows:
                    return meaningful_windows[0]
                return windows[0]

            return None

        except Exception as e:
            print(f"杂鱼♡～获取Alt+Tab窗口信息失败喵：{e}")
            return None

    @classmethod
    def _get_process_main_window(cls, process_id: int) -> Optional[Dict[str, Any]]:
        """杂鱼♡～获取进程的主窗口信息（有标题的窗口）喵～"""
        try:
            # 杂鱼♡～存储找到的窗口喵～
            found_windows = []

            def enum_windows_proc(hwnd, lParam):
                # 杂鱼♡～获取窗口的进程ID喵～
                window_process_id = w.DWORD()
                cls.user32.GetWindowThreadProcessId(
                    hwnd, ctypes.byref(window_process_id)
                )

                # 杂鱼♡～如果是同一进程的窗口喵～
                if window_process_id.value == process_id:
                    # 杂鱼♡～检查窗口是否可见喵～
                    if cls.user32.IsWindowVisible(hwnd):
                        window_title = cls._get_window_title(hwnd)
                        window_class = cls._get_window_class(hwnd)

                        # 杂鱼♡～优先选择有标题的窗口喵～
                        if window_title and window_title.strip():
                            found_windows.append(
                                {
                                    "window_handle": hwnd,
                                    "window_title": window_title,
                                    "window_class": window_class,
                                    "has_title": True,
                                }
                            )
                        else:
                            # 杂鱼♡～没有标题的窗口作为备选喵～
                            found_windows.append(
                                {
                                    "window_handle": hwnd,
                                    "window_title": window_title,
                                    "window_class": window_class,
                                    "has_title": False,
                                }
                            )

                return True  # 杂鱼♡～继续枚举喵～

            # 杂鱼♡～枚举所有窗口喵～
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, w.HWND, w.LPARAM)
            enum_proc = EnumWindowsProc(enum_windows_proc)
            cls.user32.EnumWindows(enum_proc, 0)

            # 杂鱼♡～优先返回有标题的窗口喵～
            titled_windows = [w for w in found_windows if w["has_title"]]
            if titled_windows:
                return titled_windows[0]

            # 杂鱼♡～如果没有有标题的窗口，返回第一个找到的窗口喵～
            if found_windows:
                return found_windows[0]

            return None

        except Exception as e:
            print(f"杂鱼♡～获取进程主窗口失败喵：{e}")
            return None


# 杂鱼♡～初始化函数签名喵～
ClipboardUtils._setup_function_signatures()
