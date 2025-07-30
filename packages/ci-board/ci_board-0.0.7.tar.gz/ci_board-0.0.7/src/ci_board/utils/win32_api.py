# 杂鱼♡～本喵为杂鱼主人分离的Windows API封装层喵～
import ctypes
import ctypes.wintypes as w
from enum import Enum
from typing import Optional


class ClipboardFormat(Enum):
    """杂鱼♡～剪贴板格式枚举喵～"""

    TEXT = 1
    BITMAP = 2
    CF_DIB = 8
    UNICODETEXT = 13
    CF_DIBV5 = 17
    HDROP = 15


class ClipboardError(Exception):
    """杂鱼♡～剪贴板操作异常喵～"""

    def __init__(self, message: str, error_code: int = None):
        super().__init__(message)
        self.error_code = error_code


class ClipboardTimeout(ClipboardError):
    """杂鱼♡～剪贴板操作超时异常喵～"""


class ClipboardAccessDenied(ClipboardError):
    """杂鱼♡～剪贴板访问被拒绝异常喵～"""


class Win32Structures:
    """杂鱼♡～Windows结构体定义喵～"""

    class BITMAPINFOHEADER(ctypes.Structure):
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

    class BITMAP(ctypes.Structure):
        _fields_ = [
            ("bmType", w.LONG),
            ("bmWidth", w.LONG),
            ("bmHeight", w.LONG),
            ("bmWidthBytes", w.LONG),
            ("bmPlanes", w.WORD),
            ("bmBitsPixel", w.WORD),
            ("bmBits", w.LPVOID),
        ]

    class MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd", w.HWND),
            ("message", w.UINT),
            ("wParam", w.WPARAM),
            ("lParam", w.LPARAM),
            ("time", w.DWORD),
            ("pt", w.POINT),
        ]


class Win32API:
    """杂鱼♡～Windows API封装类，只负责API调用喵～"""

    # 杂鱼♡～Windows DLL引用喵～
    user32 = ctypes.WinDLL("user32")
    kernel32 = ctypes.WinDLL("kernel32")
    gdi32 = ctypes.WinDLL("gdi32")
    psapi = ctypes.WinDLL("psapi")

    # 杂鱼♡～常量定义喵～
    WM_CLIPBOARDUPDATE = 0x031D
    HWND_MESSAGE = w.HWND(-3)

    # 杂鱼♡～窗口过程函数类型定义喵～
    WNDPROC = ctypes.WINFUNCTYPE(w.LPARAM, w.HWND, w.UINT, w.WPARAM, w.LPARAM)

    @classmethod
    def setup_function_signatures(cls):
        """杂鱼♡～设置Windows API函数签名，确保64位兼容性喵～"""
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
        cls.kernel32.GlobalSize.argtypes = [w.HGLOBAL]
        cls.kernel32.GlobalSize.restype = ctypes.c_size_t

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

        # 杂鱼♡～窗口状态检查函数喵～
        cls.user32.IsWindow.argtypes = [w.HWND]
        cls.user32.IsWindow.restype = w.BOOL

        # 杂鱼♡～事件钩子相关函数喵～
        WINEVENTPROC = ctypes.WINFUNCTYPE(
            None, w.HANDLE, w.DWORD, w.HWND, w.LONG, w.LONG, w.DWORD, w.DWORD
        )
        cls.user32.SetWinEventHook.argtypes = [
            w.DWORD,
            w.DWORD,
            w.HANDLE,
            WINEVENTPROC,
            w.DWORD,
            w.DWORD,
            w.DWORD,
        ]
        cls.user32.SetWinEventHook.restype = w.HANDLE
        cls.user32.UnhookWinEvent.argtypes = [w.HANDLE]
        cls.user32.UnhookWinEvent.restype = w.BOOL

        # 杂鱼♡～进程路径查询函数喵～
        cls.kernel32.QueryFullProcessImageNameW.argtypes = [
            w.HANDLE,
            w.DWORD,
            w.LPWSTR,
            ctypes.POINTER(w.DWORD),
        ]
        cls.kernel32.QueryFullProcessImageNameW.restype = w.BOOL

        # 杂鱼♡～Windows消息泵相关函数喵～
        cls.user32.GetMessageW.argtypes = [
            ctypes.POINTER(Win32Structures.MSG),
            w.HWND,
            w.UINT,
            w.UINT,
        ]
        cls.user32.GetMessageW.restype = w.BOOL
        cls.user32.PeekMessageW.argtypes = [
            ctypes.POINTER(Win32Structures.MSG),
            w.HWND,
            w.UINT,
            w.UINT,
            w.UINT,
        ]
        cls.user32.PeekMessageW.restype = w.BOOL
        cls.user32.TranslateMessage.argtypes = [ctypes.POINTER(Win32Structures.MSG)]
        cls.user32.TranslateMessage.restype = w.BOOL
        cls.user32.DispatchMessageW.argtypes = [ctypes.POINTER(Win32Structures.MSG)]
        cls.user32.DispatchMessageW.restype = w.LPARAM
        cls.user32.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        cls.user32.PostMessageW.restype = w.BOOL

        # 杂鱼♡～窗口过程相关函数喵～
        cls.user32.DefWindowProcW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        cls.user32.DefWindowProcW.restype = w.LPARAM
        cls.user32.IsWindowVisible.argtypes = [w.HWND]
        cls.user32.IsWindowVisible.restype = w.BOOL

        # 杂鱼♡～64位兼容性函数喵～
        import sys

        if sys.maxsize > 2**32:
            cls.user32.SetWindowLongPtrW.argtypes = [w.HWND, ctypes.c_int, cls.WNDPROC]
            cls.user32.SetWindowLongPtrW.restype = cls.WNDPROC
        else:
            cls.user32.SetWindowLongW.argtypes = [w.HWND, ctypes.c_int, cls.WNDPROC]
            cls.user32.SetWindowLongW.restype = cls.WNDPROC

    @classmethod
    def get_window_title(cls, hwnd: w.HWND) -> Optional[str]:
        """杂鱼♡～获取窗口标题喵～"""
        try:
            length = cls.user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return None

            buffer = ctypes.create_unicode_buffer(length + 1)
            result = cls.user32.GetWindowTextW(hwnd, buffer, length + 1)

            if result > 0:
                return buffer.value
        except Exception:
            pass
        return None

    @classmethod
    def get_window_class(cls, hwnd: w.HWND) -> Optional[str]:
        """杂鱼♡～获取窗口类名喵～"""
        try:
            buffer = ctypes.create_unicode_buffer(256)
            result = cls.user32.GetClassNameW(hwnd, buffer, 256)

            if result > 0:
                return buffer.value
        except Exception:
            pass
        return None

    @classmethod
    def get_process_path(cls, process_id: int) -> Optional[str]:
        """杂鱼♡～获取进程路径喵～"""
        try:
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010

            hProcess = cls.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, process_id
            )

            if not hProcess:
                return None

            try:
                buffer = ctypes.create_unicode_buffer(260)
                result = cls.psapi.GetModuleFileNameExW(hProcess, None, buffer, 260)

                if result > 0:
                    return buffer.value
            finally:
                cls.kernel32.CloseHandle(hProcess)

        except Exception:
            pass
        return None


# 杂鱼♡～启动时初始化API签名喵～
Win32API.setup_function_signatures()
