# 杂鱼♡～本喵为杂鱼主人创建的优化版源应用追踪器喵～
"""
杂鱼♡～修复版：解决双重消息循环冲突问题喵～
将焦点跟踪整合到主监控线程中，避免资源竞争喵～
"""
import ctypes
import ctypes.wintypes as w
import os
import threading
import time
from typing import Any, Dict

from ..utils.win32_api import Win32API
from ..utils.logger import get_component_logger


class OptimizedSourceTracker:
    """杂鱼♡～优化版智能源应用程序追踪器，解决消息循环冲突问题喵～"""

    # 杂鱼♡～类级别变量，跟踪焦点变化喵～
    _focus_lock = threading.Lock()
    _current_focus_info = None
    _focus_history = []
    _last_clipboard_owner = None
    _clipboard_owner_cache = {}  # 杂鱼♡～缓存剪贴板拥有者信息，减少API调用喵～
    _logger = get_component_logger("optimized_source_tracker")

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
    def initialize_integrated_tracking(cls, message_pump_callback) -> bool:
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
                print("杂鱼♡～集成式焦点跟踪钩子设置成功喵～")

                # 杂鱼♡～初始化当前焦点信息喵～
                current_hwnd = Win32API.user32.GetForegroundWindow()
                if current_hwnd:
                    cls._winevent_proc(None, cls.EVENT_SYSTEM_FOREGROUND, current_hwnd, 0, 0, 0, 0)

                return True
            else:
                print(f"杂鱼♡～设置集成式焦点钩子失败喵！错误码：{Win32API.kernel32.GetLastError()}")
                return False

        except Exception as e:
            print(f"杂鱼♡～初始化集成式焦点跟踪器时出错喵～：{str(e)}")
            return False

    @classmethod
    def cleanup_integrated_tracking(cls):
        """杂鱼♡～清理集成式焦点跟踪功能喵～"""
        print("杂鱼♡～清理集成式焦点跟踪器喵～")

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

            print("杂鱼♡～集成式焦点跟踪器已清理喵～")

        except Exception as e:
            print(f"杂鱼♡～清理集成式焦点跟踪器时出错喵～：{str(e)}")

    @staticmethod
    def _winevent_proc(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        """杂鱼♡～窗口事件钩子回调函数喵～"""
        if event == OptimizedSourceTracker.EVENT_SYSTEM_FOREGROUND and hwnd:
            try:
                window_info = OptimizedSourceTracker._get_window_info(hwnd)
                if isinstance(window_info, dict):
                    # 杂鱼♡～过滤系统窗口和无效窗口喵～
                    exe_name = window_info['exe_info']['name'].lower()
                    title = window_info['title']
                    if (exe_name not in OptimizedSourceTracker.SYSTEM_PROCESSES and
                            title != "杂鱼♡～无标题" and len(title.strip()) > 0):

                        with OptimizedSourceTracker._focus_lock:
                            OptimizedSourceTracker._current_focus_info = window_info.copy()
                            OptimizedSourceTracker._current_focus_info['focus_time'] = time.time()

                            # 杂鱼♡～更新焦点历史，避免重复喵～
                            OptimizedSourceTracker._focus_history = [
                                f for f in OptimizedSourceTracker._focus_history
                                if f['exe_info']['name'].lower() != window_info['exe_info']['name'].lower()
                            ]
                            OptimizedSourceTracker._focus_history.insert(0, OptimizedSourceTracker._current_focus_info)

                            # 杂鱼♡～只保留最近10个喵～
                            OptimizedSourceTracker._focus_history = OptimizedSourceTracker._focus_history[:10]

            except Exception as e:
                print(f"杂鱼♡～焦点钩子回调出错喵～：{str(e)}")

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
    def get_optimized_source_info(cls, avoid_clipboard_access: bool = True) -> Dict[str, Any]:
        """杂鱼♡～获取优化的源应用程序信息，避免剪贴板访问竞争喵～"""
        try:
            # 杂鱼♡～获取当前焦点信息喵～
            with cls._focus_lock:
                current_focus = cls._current_focus_info.copy() if cls._current_focus_info else None
                recent_focus = cls._focus_history[:5] if cls._focus_history else []

            # 杂鱼♡～如果避免剪贴板访问，直接使用焦点信息喵～
            if avoid_clipboard_access:
                real_source = current_focus
                confidence_level = "中等"
                detection_method = "focus_based_safe"
            else:
                # 杂鱼♡～谨慎获取剪贴板拥有者（可能失败）喵～
                owner_hwnd = None
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
                    # 杂鱼♡～剪贴板被占用时，忽略错误，使用焦点信息喵～
                    pass

                # 杂鱼♡～智能分析源应用程序喵～
                real_source = None
                confidence_level = "未知"
                detection_method = "unknown"

                if current_focus:
                    # 杂鱼♡～检查当前焦点是否就是剪贴板拥有者喵～
                    if (owner_info and isinstance(owner_info, dict) and
                            current_focus['pid'] == owner_info['pid']):
                        real_source = current_focus
                        confidence_level = "高"
                        detection_method = "focus_and_owner_match"

                    # 杂鱼♡～检查最近焦点切换时间喵～
                    elif current_focus.get('focus_time', 0) > time.time() - 3:  # 杂鱼♡～3秒内的焦点切换喵～
                        real_source = current_focus
                        confidence_level = "中等"
                        detection_method = "recent_focus"

                    # 杂鱼♡～如果剪贴板拥有者是系统进程，使用当前焦点喵～
                    elif (owner_info and isinstance(owner_info, dict) and
                          owner_info['exe_info']['name'].lower() in cls.SYSTEM_PROCESSES):
                        real_source = current_focus
                        confidence_level = "中等"
                        detection_method = "system_owner_fallback"

                # 杂鱼♡～如果还是没有，使用剪贴板拥有者喵～
                if not real_source and owner_info and isinstance(owner_info, dict):
                    real_source = owner_info
                    confidence_level = "低"
                    detection_method = "clipboard_owner_only"

                # 杂鱼♡～如果还是没有，使用最近的焦点应用程序喵～
                if not real_source and recent_focus:
                    real_source = recent_focus[0]
                    confidence_level = "低"
                    detection_method = "focus_history_fallback"

            # 杂鱼♡～构建返回结果喵～
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

        except Exception as e:
            return {
                "process_name": None,
                "process_path": None,
                "process_id": None,
                "window_title": None,
                "window_class": None,
                "detection_method": "error",
                "confidence_level": "无",
                "error": f"杂鱼♡～优化分析时出错喵～：{str(e)}",
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


# 杂鱼♡～保持向后兼容性喵～
__all__ = ["OptimizedSourceTracker"]
