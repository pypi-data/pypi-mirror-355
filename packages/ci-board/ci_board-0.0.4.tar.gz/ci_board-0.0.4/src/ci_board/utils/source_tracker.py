# 杂鱼♡～本喵的源追踪系统喵～
"""
杂鱼♡～专业的剪贴板源应用程序追踪模块喵～
本模块提供对剪贴板数据来源的精确识别和追踪功能。
"""

import ctypes
import time
from ctypes import wintypes
from typing import Dict, Any

from .logger import get_logger

logger = get_logger(__name__)

# 杂鱼♡～Windows API常量喵～
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOREDRAW = 0x0008
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080
SWP_NOCOPYBITS = 0x0100
SWP_NOOWNERZORDER = 0x0200
SWP_NOSENDCHANGING = 0x0400

HWND_TOP = 0
HWND_BOTTOM = 1
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

GW_HWNDFIRST = 0
GW_HWNDLAST = 1
GW_HWNDNEXT = 2
GW_HWNDPREV = 3
GW_OWNER = 4
GW_CHILD = 5

SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_NORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3
SW_MAXIMIZE = 3
SW_SHOWNOACTIVATE = 4
SW_SHOW = 5
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_SHOWNA = 8
SW_RESTORE = 9

# 杂鱼♡～Windows消息常量喵～
WM_SETFOCUS = 0x0007
WM_KILLFOCUS = 0x0008
WM_ACTIVATE = 0x0006
WM_MOUSEACTIVATE = 0x0021
WM_NCACTIVATE = 0x0086
WM_ACTIVATEAPP = 0x001C

# 杂鱼♡～激活状态常量喵～
WA_INACTIVE = 0
WA_ACTIVE = 1
WA_CLICKACTIVE = 2

# 杂鱼♡～鼠标激活返回值常量喵～
MA_ACTIVATE = 1
MA_ACTIVATEANDEAT = 2
MA_NOACTIVATE = 3
MA_NOACTIVATEANDEAT = 4

# 杂鱼♡～获取窗口信息的常量喵～
GWL_STYLE = -16
GWL_EXSTYLE = -20
GWL_WNDPROC = -4
GWL_HINSTANCE = -6
GWL_HWNDPARENT = -8
GWL_ID = -12
GWL_USERDATA = -21

# 杂鱼♡～窗口样式常量喵～
WS_OVERLAPPED = 0x00000000
WS_POPUP = 0x80000000
WS_CHILD = 0x40000000
WS_MINIMIZE = 0x20000000
WS_VISIBLE = 0x10000000
WS_DISABLED = 0x08000000
WS_CLIPSIBLINGS = 0x04000000
WS_CLIPCHILDREN = 0x02000000
WS_MAXIMIZE = 0x01000000
WS_CAPTION = 0x00C00000
WS_BORDER = 0x00800000
WS_DLGFRAME = 0x00400000
WS_VSCROLL = 0x00200000
WS_HSCROLL = 0x00100000
WS_SYSMENU = 0x00080000
WS_THICKFRAME = 0x00040000
WS_GROUP = 0x00020000
WS_TABSTOP = 0x00010000

# 杂鱼♡～扩展窗口样式常量喵～
WS_EX_DLGMODALFRAME = 0x00000001
WS_EX_NOPARENTNOTIFY = 0x00000004
WS_EX_TOPMOST = 0x00000008
WS_EX_ACCEPTFILES = 0x00000010
WS_EX_TRANSPARENT = 0x00000020
WS_EX_MDICHILD = 0x00000040
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_WINDOWEDGE = 0x00000100
WS_EX_CLIENTEDGE = 0x00000200
WS_EX_CONTEXTHELP = 0x00000400
WS_EX_RIGHT = 0x00001000
WS_EX_LEFT = 0x00000000
WS_EX_RTLREADING = 0x00002000
WS_EX_LTRREADING = 0x00000000
WS_EX_LEFTSCROLLBAR = 0x00004000
WS_EX_RIGHTSCROLLBAR = 0x00000000
WS_EX_CONTROLPARENT = 0x00010000
WS_EX_STATICEDGE = 0x00020000
WS_EX_APPWINDOW = 0x00040000

# 杂鱼♡～进程访问权限常量喵～
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

# 杂鱼♡～Windows API函数声明喵～
try:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi

    # 杂鱼♡～函数原型声明喵～
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    psapi.GetModuleBaseNameW.argtypes = [wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    psapi.GetModuleBaseNameW.restype = wintypes.DWORD
    psapi.GetProcessImageFileNameW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD]
    psapi.GetProcessImageFileNameW.restype = wintypes.DWORD

except Exception as e:
    logger.error(f"杂鱼♡～Windows API初始化失败: {e}")
    user32 = None
    kernel32 = None
    psapi = None


class SourceTracker:
    """杂鱼♡～剪贴板源追踪器喵～"""

    def __init__(self):
        self.last_foreground_window = None
        self.last_foreground_time = 0
        self.last_known_source = {}
        self.source_cache = {}
        self.cache_timeout = 2.0  # 杂鱼♡～缓存超时时间喵～

    def get_foreground_window_info(self) -> Dict[str, Any]:
        """杂鱼♡～获取前台窗口信息喵～"""
        if not user32:
            return {'error': '杂鱼♡～Windows API不可用'}

        try:
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return {'error': '杂鱼♡～无前台窗口'}

            # 杂鱼♡～检查缓存喵～
            current_time = time.time()
            cache_key = f"window_{hwnd}"
            if cache_key in self.source_cache:
                cached_data, cache_time = self.source_cache[cache_key]
                if current_time - cache_time < self.cache_timeout:
                    logger.debug("杂鱼♡～使用缓存的窗口信息")
                    return cached_data

            # 杂鱼♡～获取窗口标题喵～
            title_length = user32.GetWindowTextLengthW(hwnd)
            if title_length > 0:
                title_buffer = ctypes.create_unicode_buffer(title_length + 1)
                user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)
                window_title = title_buffer.value
            else:
                window_title = ""

            # 杂鱼♡～获取进程信息喵～
            process_id = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

            process_name = self._get_process_name(process_id.value)

            # 杂鱼♡～获取窗口属性喵～
            is_visible = bool(user32.IsWindowVisible(hwnd))
            window_style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            window_ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

            # 杂鱼♡～判断是否为有效的应用程序窗口喵～
            is_valid_app_window = self._is_valid_app_window(hwnd, window_style, window_ex_style)

            window_info = {
                'hwnd': hwnd,
                'window_title': window_title,
                'process_id': process_id.value,
                'process_name': process_name,
                'is_visible': is_visible,
                'is_valid_app': is_valid_app_window,
                'window_style': window_style,
                'window_ex_style': window_ex_style,
                'timestamp': current_time
            }

            # 杂鱼♡～缓存结果喵～
            self.source_cache[cache_key] = (window_info, current_time)

            # 杂鱼♡～清理过期缓存喵～
            self._cleanup_cache(current_time)

            return window_info

        except Exception as e:
            logger.error(f"杂鱼♡～获取窗口信息失败: {e}")
            return {'error': f'获取窗口信息失败: {str(e)}'}

    def _get_process_name(self, process_id: int) -> str:
        """杂鱼♡～根据进程ID获取进程名称喵～"""
        if not kernel32 or not psapi:
            return "Unknown"

        try:
            # 杂鱼♡～打开进程句柄喵～
            process_handle = kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                False,
                process_id
            )

            if not process_handle:
                return "Unknown"

            try:
                # 杂鱼♡～获取进程名称喵～
                buffer = ctypes.create_unicode_buffer(1024)
                if psapi.GetModuleBaseNameW(process_handle, None, buffer, 1024):
                    return buffer.value
                else:
                    # 杂鱼♡～尝试获取完整路径喵～
                    if psapi.GetProcessImageFileNameW(process_handle, buffer, 1024):
                        full_path = buffer.value
                        return full_path.split('\\')[-1] if '\\' in full_path else full_path
                    return "Unknown"

            finally:
                kernel32.CloseHandle(process_handle)

        except Exception as e:
            logger.debug(f"杂鱼♡～获取进程名称失败: {e}")
            return "Unknown"

    def _is_valid_app_window(self, hwnd: int, style: int, ex_style: int) -> bool:
        """杂鱼♡～判断是否为有效的应用程序窗口喵～"""
        try:
            # 杂鱼♡～基本可见性检查喵～
            if not user32.IsWindowVisible(hwnd):
                return False

            # 杂鱼♡～排除工具窗口喵～
            if ex_style & WS_EX_TOOLWINDOW:
                return False

            # 杂鱼♡～排除子窗口喵～
            if style & WS_CHILD:
                return False

            # 杂鱼♡～检查是否有父窗口喵～
            parent = user32.GetParent(hwnd)
            if parent:
                return False

            # 杂鱼♡～检查窗口标题喵～
            title_length = user32.GetWindowTextLengthW(hwnd)
            if title_length == 0:
                # 杂鱼♡～有些应用程序窗口可能没有标题喵～
                return style & (WS_CAPTION | WS_SYSMENU) != 0

            return True

        except Exception as e:
            logger.debug(f"杂鱼♡～窗口有效性检查失败: {e}")
            return False

    def _cleanup_cache(self, current_time: float):
        """杂鱼♡～清理过期缓存喵～"""
        expired_keys = []
        for key, (_, cache_time) in self.source_cache.items():
            if current_time - cache_time > self.cache_timeout:
                expired_keys.append(key)

        for key in expired_keys:
            del self.source_cache[key]

    def get_clipboard_source_info(self) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板数据源信息喵～"""
        current_window_info = self.get_foreground_window_info()

        if 'error' in current_window_info:
            # 杂鱼♡～如果获取失败，返回上次已知的源喵～
            if self.last_known_source:
                return {
                    **self.last_known_source,
                    'confidence': 'low',
                    'note': '使用上次已知源信息'
                }
            return current_window_info

        # 杂鱼♡～更新记录喵～
        current_time = time.time()
        hwnd = current_window_info.get('hwnd')

        if hwnd != self.last_foreground_window:
            self.last_foreground_window = hwnd
            self.last_foreground_time = current_time

        # 杂鱼♡～如果是有效的应用程序窗口，更新已知源喵～
        if current_window_info.get('is_valid_app', False):
            self.last_known_source = {
                'process_name': current_window_info.get('process_name', 'Unknown'),
                'window_title': current_window_info.get('window_title', ''),
                'process_id': current_window_info.get('process_id', 0),
                'hwnd': hwnd,
                'timestamp': current_time
            }

        # 杂鱼♡～计算置信度喵～
        time_since_focus = current_time - self.last_foreground_time
        if time_since_focus < 1.0:  # 杂鱼♡～1秒内的窗口切换喵～
            confidence = 'high'
        elif time_since_focus < 5.0:  # 杂鱼♡～5秒内的喵～
            confidence = 'medium'
        else:
            confidence = 'low'

        result = {
            **current_window_info,
            'confidence': confidence,
            'time_since_focus': time_since_focus
        }

        logger.debug(f"杂鱼♡～源追踪结果: {result.get('process_name', 'Unknown')} ({confidence} confidence)")

        return result

    def clear_cache(self):
        """杂鱼♡～清空所有缓存喵～"""
        self.source_cache.clear()
        logger.debug("杂鱼♡～源追踪缓存已清空")

    def get_cache_stats(self) -> Dict[str, Any]:
        """杂鱼♡～获取缓存统计信息喵～"""
        current_time = time.time()
        active_entries = 0
        expired_entries = 0

        for _, (_, cache_time) in self.source_cache.items():
            if current_time - cache_time < self.cache_timeout:
                active_entries += 1
            else:
                expired_entries += 1

        return {
            'total_entries': len(self.source_cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'cache_timeout': self.cache_timeout
        }


# 杂鱼♡～全局源追踪器实例喵～
_source_tracker = None


def get_source_tracker() -> SourceTracker:
    """杂鱼♡～获取全局源追踪器实例喵～"""
    global _source_tracker
    if _source_tracker is None:
        _source_tracker = SourceTracker()
        logger.debug("杂鱼♡～创建新的源追踪器实例")
    return _source_tracker


def get_clipboard_source() -> Dict[str, Any]:
    """杂鱼♡～便捷函数：获取剪贴板源信息喵～"""
    tracker = get_source_tracker()
    return tracker.get_clipboard_source_info()


def clear_source_cache():
    """杂鱼♡～便捷函数：清空源追踪缓存喵～"""
    tracker = get_source_tracker()
    tracker.clear_cache()


def get_source_cache_stats() -> Dict[str, Any]:
    """杂鱼♡～便捷函数：获取缓存统计信息喵～"""
    tracker = get_source_tracker()
    return tracker.get_cache_stats()


# 杂鱼♡～导出的公共接口喵～
__all__ = [
    'SourceTracker',
    'get_source_tracker',
    'get_clipboard_source',
    'clear_source_cache',
    'get_source_cache_stats'
]
