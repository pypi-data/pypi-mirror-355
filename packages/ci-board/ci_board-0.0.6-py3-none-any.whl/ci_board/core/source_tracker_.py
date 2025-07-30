# 杂鱼♡～本喵为杂鱼主人创建的统一源应用追踪器喵～
"""
杂鱼♡～统一版源追踪器：整合传统和优化版本的功能喵～
解决双重消息循环冲突问题，提供完整的源应用程序追踪功能喵～
"""
import ctypes
import ctypes.wintypes as w
import os
import threading
import time
from typing import Any, Dict

from ..utils.win32_api import Win32API
from ..utils.logger import get_component_logger


class SourceTracker:
    """杂鱼♡～统一智能源应用程序追踪器，整合所有功能喵～"""

    # 杂鱼♡～类级别变量，跟踪焦点变化喵～
    _focus_lock = threading.Lock()
    _current_focus_info = None
    _focus_history = []
    _last_clipboard_owner = None
    _clipboard_owner_cache = {}  # 杂鱼♡～缓存剪贴板拥有者信息，减少API调用喵～
    _logger = get_component_logger("source_tracker")

    # 杂鱼♡～系统进程黑名单喵～
    SYSTEM_PROCESSES = {
        'svchost.exe', 'dwm.exe', 'explorer.exe', 'winlogon.exe', 'csrss.exe',
        'screenclippinghost.exe', 'taskhostw.exe', 'runtimebroker.exe',
        'sihost.exe', 'shellexperiencehost.exe', 'searchui.exe', 'cortana.exe',
        'windowsinternal.composableshell.experiences.textinput.inputapp.exe',
        'applicationframehost.exe', 'searchapp.exe', 'startmenuexperiencehost.exe'
    }

    # 杂鱼♡～窗口事件常量喵～
    EVENT_SYSTEM_FOREGROUND = 0x0003
    WINEVENT_OUTOFCONTEXT = 0x0000
    WINEVENT_SKIPOWNPROCESS = 0x0002
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    @classmethod
    def initialize_integrated_tracking(cls, message_pump_callback=None) -> bool:
        """杂鱼♡～初始化集成的焦点跟踪，使用主消息循环喵～"""
        cls._logger.info("初始化集成式焦点跟踪器")

        try:
            # 杂鱼♡～设置Windows事件钩子，但不创建单独的消息循环喵～
            WINEVENTPROC = ctypes.WINFUNCTYPE(
                None, w.HANDLE, w.DWORD, w.HWND, w.LONG, w.LONG, w.DWORD, w.DWORD
            )
            cls._winevent_proc_func = WINEVENTPROC(cls._winevent_proc)

            # 杂鱼♡～设置Windows事件钩子喵～
            cls._focus_hook_handle = Win32API.user32.SetWinEventHook(
                cls.EVENT_SYSTEM_FOREGROUND,
                cls.EVENT_SYSTEM_FOREGROUND,
                None,
                cls._winevent_proc_func,
                0,
                0,
                cls.WINEVENT_OUTOFCONTEXT | cls.WINEVENT_SKIPOWNPROCESS
            )

            if cls._focus_hook_handle:
                cls._logger.info("集成式焦点跟踪钩子设置成功")

                # 杂鱼♡～初始化当前焦点信息喵～
                current_hwnd = Win32API.user32.GetForegroundWindow()
                if current_hwnd:
                    cls._winevent_proc(None, cls.EVENT_SYSTEM_FOREGROUND, current_hwnd, 0, 0, 0, 0)

                return True
            else:
                cls._logger.error(f"设置集成式焦点钩子失败，错误码：{Win32API.kernel32.GetLastError()}")
                return False

        except Exception as e:
            cls._logger.error(f"初始化集成式焦点跟踪器时出错：{str(e)}")
            return False

    @classmethod
    def cleanup_integrated_tracking(cls):
        """杂鱼♡～清理集成式焦点跟踪功能喵～"""
        cls._logger.info("清理集成式焦点跟踪器")

        try:
            # 杂鱼♡～清理钩子喵～
            if hasattr(cls, '_focus_hook_handle') and cls._focus_hook_handle:
                Win32API.user32.UnhookWinEvent(cls._focus_hook_handle)
                cls._focus_hook_handle = None

            # 杂鱼♡～清理状态喵～
            with cls._focus_lock:
                cls._current_focus_info = None
                cls._focus_history.clear()
                cls._clipboard_owner_cache.clear()

            cls._logger.info("集成式焦点跟踪器已清理")

        except Exception as e:
            cls._logger.error(f"清理集成式焦点跟踪器时出错：{str(e)}")

    @staticmethod
    def _winevent_proc(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        """杂鱼♡～窗口事件钩子回调函数喵～"""
        if event == SourceTracker.EVENT_SYSTEM_FOREGROUND and hwnd:
            try:
                window_info = SourceTracker._get_window_info(hwnd)
                if isinstance(window_info, dict):
                    # 杂鱼♡～过滤系统窗口和无效窗口喵～
                    exe_name = window_info['exe_info']['name'].lower()
                    title = window_info['title']
                    if (exe_name not in SourceTracker.SYSTEM_PROCESSES and
                            title != "杂鱼♡～无标题" and len(title.strip()) > 0):

                        with SourceTracker._focus_lock:
                            SourceTracker._current_focus_info = window_info.copy()
                            SourceTracker._current_focus_info['focus_time'] = time.time()

                            # 杂鱼♡～更新焦点历史，避免重复喵～
                            SourceTracker._focus_history = [
                                f for f in SourceTracker._focus_history
                                if f['exe_info']['name'].lower() != window_info['exe_info']['name'].lower()
                            ]
                            SourceTracker._focus_history.insert(0, SourceTracker._current_focus_info)

                            # 杂鱼♡～只保留最近10个喵～
                            SourceTracker._focus_history = SourceTracker._focus_history[:10]

            except Exception as e:
                SourceTracker._logger.debug(f"焦点钩子回调出错：{str(e)}")

    @classmethod
    def _get_window_info(cls, hwnd, description=""):
        """杂鱼♡～获取窗口详细信息的通用函数喵～"""
        if not hwnd or not Win32API.user32.IsWindow(hwnd):
            return f"杂鱼♡～{description}窗口无效喵～"

        try:
            # 杂鱼♡～获取窗口标题（改进版）喵～
            title_length = Win32API.user32.GetWindowTextLengthW(hwnd)
            if title_length > 0:
                window_title_buffer = ctypes.create_unicode_buffer(title_length + 1)
                actual_length = Win32API.user32.GetWindowTextW(hwnd, window_title_buffer, title_length + 1)
                window_title = window_title_buffer.value if actual_length > 0 else "杂鱼♡～无标题"
            else:
                window_title = "杂鱼♡～无标题"

            # 杂鱼♡～获取窗口类名喵～
            class_buffer = ctypes.create_unicode_buffer(256)
            class_length = Win32API.user32.GetClassNameW(hwnd, class_buffer, 256)
            window_class = class_buffer.value if class_length > 0 else "杂鱼♡～未知类名"

            # 杂鱼♡～获取进程信息喵～
            process_id = w.DWORD()
            Win32API.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

            if not process_id.value:
                return f"杂鱼♡～{description}无法获取进程ID喵～（窗口：{window_title}，类名：{window_class}）"

            # 杂鱼♡～获取可执行文件路径喵～
            exe_info = cls._get_process_path(process_id.value)

            return {
                'title': window_title,
                'class': window_class,
                'pid': process_id.value,
                'exe_info': exe_info,
                'hwnd': hwnd
            }

        except Exception as e:
            return f"杂鱼♡～获取{description}窗口信息时出错喵～：{str(e)}"

    @classmethod
    def _get_process_path(cls, process_id):
        """杂鱼♡～获取进程路径信息喵～"""
        try:
            # 杂鱼♡～打开进程获取详细信息喵～
            process_handle = Win32API.kernel32.OpenProcess(
                cls.PROCESS_QUERY_INFORMATION | cls.PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                process_id
            )

            if not process_handle:
                # 杂鱼♡～尝试较低权限喵～
                process_handle = Win32API.kernel32.OpenProcess(cls.PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)

            if not process_handle:
                return {'name': f'PID:{process_id}', 'path': '杂鱼♡～无法打开进程'}

            try:
                # 杂鱼♡～尝试获取完整进程路径喵～
                exe_path = None

                # 杂鱼♡～方法1：使用QueryFullProcessImageName（推荐）喵～
                path_buffer = ctypes.create_unicode_buffer(1024)
                path_size = w.DWORD(1024)
                if Win32API.kernel32.QueryFullProcessImageNameW(process_handle, 0, path_buffer, ctypes.byref(path_size)):
                    exe_path = path_buffer.value

                if exe_path:
                    exe_name = os.path.basename(exe_path)
                    return {'name': exe_name, 'path': exe_path}
                else:
                    return {'name': f'PID:{process_id}', 'path': '杂鱼♡～无法获取路径'}

            finally:
                Win32API.kernel32.CloseHandle(process_handle)

        except Exception as e:
            return {'name': f'PID:{process_id}', 'path': f'杂鱼♡～出错：{str(e)}'}

    @classmethod
    def get_source_info(cls, avoid_clipboard_access: bool = True) -> Dict[str, Any]:
        """杂鱼♡～获取优化的源应用程序信息，避免剪贴板访问竞争喵～"""
        try:
            # 杂鱼♡～获取当前焦点信息喵～
            current_focus, recent_focus = cls._get_focus_data()

            # 杂鱼♡～根据策略确定源应用程序喵～
            if avoid_clipboard_access:
                real_source, confidence_level, detection_method = cls._get_source_by_focus_safe(current_focus)
            else:
                real_source, confidence_level, detection_method = cls._get_source_by_clipboard_analysis(
                    current_focus, recent_focus
                )

            # 杂鱼♡～构建返回结果喵～
            return cls._build_source_result(real_source, detection_method, confidence_level)

        except Exception as e:
            return cls._build_error_result(e)

    @classmethod
    def _get_focus_data(cls) -> tuple:
        """杂鱼♡～获取焦点数据喵～"""
        with cls._focus_lock:
            current_focus = cls._current_focus_info.copy() if cls._current_focus_info else None
            recent_focus = cls._focus_history[:5] if cls._focus_history else []
        return current_focus, recent_focus

    @classmethod
    def _get_source_by_focus_safe(cls, current_focus) -> tuple:
        """杂鱼♡～安全模式：直接使用焦点信息喵～"""
        return current_focus, "中等", "focus_based_safe"

    @classmethod
    def _get_source_by_clipboard_analysis(cls, current_focus, recent_focus) -> tuple:
        """杂鱼♡～剪贴板分析模式：综合分析源应用程序喵～"""
        # 杂鱼♡～获取剪贴板拥有者信息喵～
        owner_info = cls._get_clipboard_owner_info()

        # 杂鱼♡～智能分析源应用程序喵～
        real_source, confidence_level, detection_method = cls._analyze_real_source(
            current_focus, owner_info, recent_focus
        )

        return real_source, confidence_level, detection_method

    @classmethod
    def _get_clipboard_owner_info(cls):
        """杂鱼♡～获取剪贴板拥有者信息喵～"""
        owner_info = None
        try:
            owner_hwnd = Win32API.user32.GetClipboardOwner()
            if owner_hwnd:
                # 杂鱼♡～检查缓存，减少重复查询喵～
                if owner_hwnd in cls._clipboard_owner_cache:
                    owner_info = cls._clipboard_owner_cache[owner_hwnd]
                else:
                    owner_info = cls._get_window_info(owner_hwnd, "剪贴板拥有者")
                    if isinstance(owner_info, dict):
                        cls._clipboard_owner_cache[owner_hwnd] = owner_info
        except Exception:
            # 杂鱼♡～剪贴板被占用时，忽略错误喵～
            pass
        return owner_info

    @classmethod
    def _analyze_real_source(cls, current_focus, owner_info, recent_focus) -> tuple:
        """杂鱼♡～分析真实源应用程序喵～"""
        if current_focus:
            # 杂鱼♡～优先检查各种匹配情况喵～
            result = cls._check_focus_owner_match(current_focus, owner_info)
            if result:
                return result

            result = cls._check_recent_focus(current_focus)
            if result:
                return result

            result = cls._check_system_owner_fallback(current_focus, owner_info)
            if result:
                return result

        # 杂鱼♡～降级策略喵～
        return cls._fallback_source_detection(owner_info, recent_focus)

    @classmethod
    def _check_focus_owner_match(cls, current_focus, owner_info) -> tuple:
        """杂鱼♡～检查焦点和剪贴板拥有者是否匹配喵～"""
        if (owner_info and isinstance(owner_info, dict) and
                current_focus['pid'] == owner_info['pid']):
            return current_focus, "高", "focus_and_owner_match"
        return None

    @classmethod
    def _check_recent_focus(cls, current_focus) -> tuple:
        """杂鱼♡～检查最近焦点切换时间喵～"""
        if current_focus.get('focus_time', 0) > time.time() - 3:  # 杂鱼♡～3秒内的焦点切换喵～
            return current_focus, "中等", "recent_focus"
        return None

    @classmethod
    def _check_system_owner_fallback(cls, current_focus, owner_info) -> tuple:
        """杂鱼♡～检查系统进程降级喵～"""
        if (owner_info and isinstance(owner_info, dict) and
                owner_info['exe_info']['name'].lower() in cls.SYSTEM_PROCESSES):
            return current_focus, "中等", "system_owner_fallback"
        return None

    @classmethod
    def _fallback_source_detection(cls, owner_info, recent_focus) -> tuple:
        """杂鱼♡～降级源检测喵～"""
        if owner_info and isinstance(owner_info, dict):
            return owner_info, "低", "clipboard_owner_only"

        if recent_focus:
            return recent_focus[0], "低", "focus_history_fallback"

        return None, "未知", "unknown"

    @classmethod
    def _build_source_result(cls, real_source, detection_method: str, confidence_level: str) -> dict:
        """杂鱼♡～构建源应用程序结果喵～"""
        result = {
            "process_name": None,
            "process_path": None,
            "process_id": None,
            "window_title": None,
            "window_class": None,
            "detection_method": detection_method,
            "confidence_level": confidence_level,
            "is_system_process": False,
            "is_screenshot_tool": False,
            "timestamp": time.time(),
        }

        if real_source:
            result.update({
                "process_name": real_source['exe_info']['name'],
                "process_path": real_source['exe_info']['path'],
                "process_id": real_source['pid'],
                "window_title": real_source['title'],
                "window_class": real_source['class'],
                "is_system_process": real_source['exe_info']['name'].lower() in cls.SYSTEM_PROCESSES,
            })

        return result

    @classmethod
    def _build_error_result(cls, error: Exception) -> dict:
        """杂鱼♡～构建错误结果喵～"""
        return {
            "process_name": None,
            "process_path": None,
            "process_id": None,
            "window_title": None,
            "window_class": None,
            "detection_method": "error",
            "confidence_level": "无",
            "error": f"杂鱼♡～分析时出错喵～：{str(error)}",
            "timestamp": time.time(),
        }

    @classmethod
    def get_focus_status(cls) -> Dict[str, Any]:
        """杂鱼♡～获取焦点跟踪状态喵～"""
        with cls._focus_lock:
            return {
                "is_tracking": hasattr(cls, '_focus_hook_handle') and cls._focus_hook_handle is not None,
                "current_focus": cls._current_focus_info.copy() if cls._current_focus_info else None,
                "focus_history_count": len(cls._focus_history),
                "has_hook": hasattr(cls, '_focus_hook_handle') and cls._focus_hook_handle is not None,
                "cache_size": len(cls._clipboard_owner_cache),
            }

    # 杂鱼♡～为向后兼容保留的旧接口喵～
    @classmethod
    def initialize_focus_tracking(cls) -> bool:
        """杂鱼♡～向后兼容接口：初始化焦点跟踪喵～"""
        return cls.initialize_integrated_tracking()

    @classmethod
    def cleanup_focus_tracking(cls):
        """杂鱼♡～向后兼容接口：清理焦点跟踪喵～"""
        cls.cleanup_integrated_tracking()

    @classmethod
    def get_optimized_source_info(cls, avoid_clipboard_access: bool = True) -> Dict[str, Any]:
        """杂鱼♡～向后兼容接口：获取优化源信息喵～"""
        return cls.get_source_info(avoid_clipboard_access)


# 杂鱼♡～保持向后兼容性喵～
__all__ = ["SourceTracker"]
