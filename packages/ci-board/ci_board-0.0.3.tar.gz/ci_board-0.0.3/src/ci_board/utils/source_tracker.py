# 杂鱼♡～本喵为杂鱼主人创建的源应用追踪器喵～
import ctypes
import ctypes.wintypes as w
import os
from typing import Any, Dict, Optional

from .win32_api import Win32API


class SourceTracker:
    """杂鱼♡～专门负责追踪剪贴板内容来源的类喵～"""

    # 杂鱼♡～系统进程列表喵～
    SYSTEM_PROCESSES = {
        "dwm.exe",
        "explorer.exe",
        "winlogon.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "dllhost.exe",
        "rundll32.exe",
        "taskhostw.exe",
        "audiodg.exe",
    }

    # 杂鱼♡～截图工具列表喵～
    SCREENSHOT_TOOLS = {
        "snippingtool.exe",
        "screensketch.exe",
        "lightshot.exe",
        "snagit32.exe",
        "picpick.exe",
        "greenshot.exe",
        "sharex.exe",
    }

    @classmethod
    def get_source_application_info(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板内容源应用信息喵～"""
        source_info = {
            "process_name": None,
            "process_path": None,
            "process_id": None,
            "window_title": None,
            "window_class": None,
            "detection_method": "unknown",
            "is_system_process": False,
            "is_screenshot_tool": False,
        }

        # 杂鱼♡～方法1：获取剪贴板拥有者信息（最准确）喵～
        owner_info = cls._get_clipboard_owner_info()
        if owner_info and owner_info.get("process_name"):
            source_info.update(owner_info)
            source_info["detection_method"] = "clipboard_owner"
            return source_info

        # 杂鱼♡～方法2：获取前台窗口信息（备用）喵～
        foreground_info = cls._get_foreground_window_info()
        if foreground_info and foreground_info.get("process_name"):
            source_info.update(foreground_info)
            source_info["detection_method"] = "foreground_window"
            return source_info

        # 杂鱼♡～方法3：尝试Alt+Tab窗口信息（最后备用）喵～
        alt_tab_info = cls._get_alt_tab_window_info()
        if alt_tab_info and alt_tab_info.get("process_name"):
            source_info.update(alt_tab_info)
            source_info["detection_method"] = "alt_tab_window"
            return source_info

        return source_info

    @classmethod
    def _get_clipboard_owner_info(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板拥有者信息喵～"""
        try:
            hwnd = Win32API.user32.GetClipboardOwner()
            if not hwnd:
                return {}

            return cls._get_window_process_info(hwnd)
        except Exception as e:
            print(f"杂鱼♡～获取剪贴板拥有者信息失败喵：{e}")
            return {}

    @classmethod
    def _get_foreground_window_info(cls) -> Optional[Dict[str, Any]]:
        """杂鱼♡～获取前台窗口信息喵～"""
        try:
            hwnd = Win32API.user32.GetForegroundWindow()
            if not hwnd:
                return None

            return cls._get_window_process_info(hwnd)
        except Exception as e:
            print(f"杂鱼♡～获取前台窗口信息失败喵：{e}")
            return None

    @classmethod
    def _get_alt_tab_window_info(cls) -> Optional[Dict[str, Any]]:
        """杂鱼♡～获取Alt+Tab窗口信息喵～"""
        try:
            # 杂鱼♡～枚举所有窗口，找到最可能的候选者喵～
            windows = []

            def enum_windows_proc(hwnd, lParam):
                # 杂鱼♡～检查窗口是否可见且不是工具窗口喵～
                if Win32API.user32.IsWindowVisible(hwnd):
                    title = Win32API.get_window_title(hwnd)
                    if title and len(title.strip()) > 0:
                        process_info = cls._get_window_process_info(hwnd)
                        if process_info.get("process_name"):
                            windows.append(
                                {"hwnd": hwnd, "title": title, **process_info}
                            )
                return True

            # 杂鱼♡～枚举窗口函数类型喵～
            ENUMWINDOWSPROC = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
            enum_func = ENUMWINDOWSPROC(enum_windows_proc)

            # 杂鱼♡～设置API签名喵～
            Win32API.user32.EnumWindows.argtypes = [ENUMWINDOWSPROC, w.LPARAM]
            Win32API.user32.EnumWindows.restype = w.BOOL
            Win32API.user32.EnumWindows(enum_func, 0)

            # 杂鱼♡～过滤系统进程和工具窗口喵～
            filtered_windows = []
            for window in windows:
                process_name = window.get("process_name", "").lower()
                if not cls._is_system_process(process_name) and process_name not in [
                    "explorer.exe"
                ]:
                    filtered_windows.append(window)

            # 杂鱼♡～返回第一个非系统窗口喵～
            if filtered_windows:
                return filtered_windows[0]

        except Exception as e:
            print(f"杂鱼♡～获取Alt+Tab窗口信息失败喵：{e}")

        return None

    @classmethod
    def _get_window_process_info(cls, hwnd: w.HWND) -> Dict[str, Any]:
        """杂鱼♡～获取窗口对应的进程信息喵～"""
        info = {
            "process_name": None,
            "process_path": None,
            "process_id": None,
            "window_title": None,
            "window_class": None,
            "is_system_process": False,
            "is_screenshot_tool": False,
        }

        try:
            # 杂鱼♡～获取进程ID喵～
            process_id = w.DWORD()
            Win32API.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            process_id = process_id.value

            if process_id:
                info["process_id"] = process_id

                # 杂鱼♡～获取进程路径喵～
                process_path = Win32API.get_process_path(process_id)
                if process_path:
                    info["process_path"] = process_path
                    info["process_name"] = os.path.basename(process_path).lower()

                    # 杂鱼♡～检查是否为系统进程或截图工具喵～
                    info["is_system_process"] = cls._is_system_process(
                        info["process_name"]
                    )
                    info["is_screenshot_tool"] = cls._is_screenshot_tool(
                        info["process_name"]
                    )

            # 杂鱼♡～获取窗口标题和类名喵～
            info["window_title"] = Win32API.get_window_title(hwnd)
            info["window_class"] = Win32API.get_window_class(hwnd)

        except Exception as e:
            print(f"杂鱼♡～获取窗口进程信息失败喵：{e}")

        return info

    @classmethod
    def _is_system_process(cls, process_name: Optional[str]) -> bool:
        """杂鱼♡～检查是否为系统进程喵～"""
        if not process_name:
            return False

        process_name = process_name.lower()

        # 杂鱼♡～检查已知系统进程喵～
        if process_name in cls.SYSTEM_PROCESSES:
            return True

        # 杂鱼♡～检查Windows系统路径喵～
        system_keywords = ["system32", "syswow64", "windows", "microsoft"]
        for keyword in system_keywords:
            if keyword in process_name:
                return True

        return False

    @classmethod
    def _is_screenshot_tool(cls, process_name: Optional[str]) -> bool:
        """杂鱼♡～检查是否为截图工具喵～"""
        if not process_name:
            return False

        process_name = process_name.lower()

        # 杂鱼♡～检查已知截图工具喵～
        if process_name in cls.SCREENSHOT_TOOLS:
            return True

        # 杂鱼♡～检查截图工具关键词喵～
        screenshot_keywords = ["screen", "capture", "shot", "snip", "grab"]
        for keyword in screenshot_keywords:
            if keyword in process_name:
                return True

        return False

    @classmethod
    def _get_process_main_window(cls, process_id: int) -> Optional[Dict[str, Any]]:
        """杂鱼♡～获取进程的主窗口信息喵～"""
        try:
            main_window = None

            def enum_windows_proc(hwnd, lParam):
                # 杂鱼♡～获取窗口的进程ID喵～
                window_process_id = w.DWORD()
                Win32API.user32.GetWindowThreadProcessId(
                    hwnd, ctypes.byref(window_process_id)
                )

                if window_process_id.value == process_id:
                    # 杂鱼♡～检查是否为可见的主窗口喵～
                    if Win32API.user32.IsWindowVisible(hwnd):
                        title = Win32API.get_window_title(hwnd)
                        if title and len(title.strip()) > 0:
                            nonlocal main_window
                            main_window = {
                                "hwnd": hwnd,
                                "title": title,
                                "class": Win32API.get_window_class(hwnd),
                            }
                            return False  # 杂鱼♡～找到主窗口，停止枚举喵～

                return True

            # 杂鱼♡～枚举窗口函数类型喵～
            ENUMWINDOWSPROC = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
            enum_func = ENUMWINDOWSPROC(enum_windows_proc)

            # 杂鱼♡～设置API签名喵～
            Win32API.user32.EnumWindows.argtypes = [ENUMWINDOWSPROC, w.LPARAM]
            Win32API.user32.EnumWindows.restype = w.BOOL
            Win32API.user32.EnumWindows(enum_func, 0)

            return main_window

        except Exception as e:
            print(f"杂鱼♡～获取进程主窗口失败喵：{e}")
            return None
