# 杂鱼♡～本喵为杂鱼主人创建的剪贴板数据读取器喵～
import ctypes
import ctypes.wintypes as w
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from .win32_api import (ClipboardError, ClipboardFormat, ClipboardTimeout,
                        Win32API, Win32Structures)


class ClipboardReader:
    """杂鱼♡～专门负责读取剪贴板数据的类喵～"""

    # 杂鱼♡～操作配置喵～
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 0.01  # 杂鱼♡～10毫秒喵～
    DEFAULT_TIMEOUT = 2.0  # 杂鱼♡～2秒超时喵～

    # 杂鱼♡～线程安全锁喵～
    _clipboard_lock = threading.RLock()

    @classmethod
    def _with_retry(
        cls,
        operation: Callable,
        retry_count: int = None,
        retry_delay: float = None,
        timeout: float = None,
    ) -> Any:
        """杂鱼♡～带重试的操作执行喵～"""
        retry_count = retry_count or cls.DEFAULT_RETRY_COUNT
        retry_delay = retry_delay or cls.DEFAULT_RETRY_DELAY
        timeout = timeout or cls.DEFAULT_TIMEOUT

        start_time = time.time()
        last_exception = None

        for attempt in range(retry_count):
            if time.time() - start_time > timeout:
                raise ClipboardTimeout(f"杂鱼♡～操作超时喵～ ({timeout}s)")

            try:
                return operation()
            except Exception as e:
                last_exception = e
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue
                break

        if last_exception:
            raise last_exception

    @classmethod
    def _safe_open_clipboard(cls, hwnd: w.HWND = None) -> bool:
        """杂鱼♡～安全打开剪贴板喵～"""
        try:
            return bool(Win32API.user32.OpenClipboard(hwnd))
        except Exception as e:
            print(f"杂鱼♡～打开剪贴板失败喵：{e}")
            return False

    @classmethod
    def _safe_close_clipboard(cls) -> None:
        """杂鱼♡～安全关闭剪贴板喵～"""
        try:
            Win32API.user32.CloseClipboard()
        except Exception as e:
            print(f"杂鱼♡～关闭剪贴板失败喵：{e}")

    @classmethod
    def _check_memory_validity(cls, handle: w.HANDLE, min_size: int = 1) -> bool:
        """杂鱼♡～检查内存句柄有效性喵～"""
        if not handle:
            return False
        try:
            size = Win32API.kernel32.GlobalSize(handle)
            return size >= min_size
        except Exception:
            return False

    @classmethod
    def is_format_available(cls, format_type: ClipboardFormat) -> bool:
        """杂鱼♡～检查剪贴板格式是否可用喵～"""
        try:
            return bool(Win32API.user32.IsClipboardFormatAvailable(format_type.value))
        except Exception:
            return False

    @classmethod
    def get_available_formats(cls) -> List[str]:
        """杂鱼♡～获取可用的剪贴板格式列表喵～"""
        formats = []
        try:
            if cls.is_format_available(ClipboardFormat.UNICODETEXT):
                formats.append("text")
            if cls.is_format_available(
                ClipboardFormat.BITMAP
            ) or Win32API.user32.IsClipboardFormatAvailable(
                8
            ):  # CF_DIB
                formats.append("image")
            if cls.is_format_available(ClipboardFormat.HDROP):
                formats.append("files")
        except Exception:
            pass
        return formats

    @classmethod
    def detect_content_type(cls) -> Optional[str]:
        """杂鱼♡～检测剪贴板内容类型喵～"""
        try:
            # 杂鱼♡～检查各种图片格式喵～
            CF_DIB = 8
            CF_DIBV5 = 17
            if (
                cls.is_format_available(ClipboardFormat.BITMAP)
                or Win32API.user32.IsClipboardFormatAvailable(CF_DIB)
                or Win32API.user32.IsClipboardFormatAvailable(CF_DIBV5)
            ):
                return "image"
            elif cls.is_format_available(ClipboardFormat.UNICODETEXT):
                return "text"
            elif cls.is_format_available(ClipboardFormat.HDROP):
                return "files"
        except Exception:
            pass
        return None

    @classmethod
    def get_text_content(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[str]:
        """杂鱼♡～获取剪贴板文本内容喵～"""

        def _get_text():
            with cls._clipboard_lock:
                if not cls._safe_open_clipboard():
                    raise ClipboardError("杂鱼♡～无法打开剪贴板喵～")

                try:
                    handle = Win32API.user32.GetClipboardData(
                        ClipboardFormat.UNICODETEXT.value
                    )
                    if not cls._check_memory_validity(handle):
                        return None

                    text_ptr = Win32API.kernel32.GlobalLock(handle)
                    if not text_ptr:
                        return None

                    try:
                        text = ctypes.wstring_at(text_ptr)
                        return text if text else None
                    finally:
                        Win32API.kernel32.GlobalUnlock(handle)
                finally:
                    cls._safe_close_clipboard()

        return cls._with_retry(_get_text, retry_count, timeout=timeout)

    @classmethod
    def get_image_content(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[Any]:
        """杂鱼♡～获取剪贴板图片内容喵～"""

        def _get_image():
            # 杂鱼♡～首先尝试DIB格式喵～
            CF_DIB = 8
            CF_DIBV5 = 17

            image_data = None
            if Win32API.user32.IsClipboardFormatAvailable(CF_DIB):
                image_data = cls._get_dib_data(CF_DIB)
            elif Win32API.user32.IsClipboardFormatAvailable(CF_DIBV5):
                image_data = cls._get_dib_data(CF_DIBV5)
            elif cls.is_format_available(ClipboardFormat.BITMAP):
                image_data = cls._get_bitmap_data()

            return image_data

        return cls._with_retry(_get_image, retry_count, timeout=timeout)

    @classmethod
    def _get_dib_data(cls, format_type: int) -> Optional[dict]:
        """杂鱼♡～获取DIB格式图片数据，返回ImageHandler期望的格式喵～"""
        with cls._clipboard_lock:
            if not cls._safe_open_clipboard():
                raise ClipboardError("杂鱼♡～无法打开剪贴板喵～")

            try:
                handle = Win32API.user32.GetClipboardData(format_type)
                if not cls._check_memory_validity(
                    handle, 40
                ):  # 杂鱼♡～BITMAPINFOHEADER至少40字节喵～
                    return None

                data_ptr = Win32API.kernel32.GlobalLock(handle)
                if not data_ptr:
                    return None

                try:
                    # 杂鱼♡～读取BITMAPINFOHEADER喵～
                    header = Win32Structures.BITMAPINFOHEADER.from_address(data_ptr)

                    data_size = Win32API.kernel32.GlobalSize(handle)
                    raw_data = ctypes.string_at(data_ptr, data_size)

                    # 杂鱼♡～返回ImageHandler期望的格式喵～
                    return {
                        "type": "DIB",  # 杂鱼♡～ImageHandler检查这个字段喵～
                        "format": "DIB",
                        "width": header.biWidth,
                        "height": abs(header.biHeight),
                        "size": (header.biWidth, abs(header.biHeight)),
                        "bit_count": header.biBitCount,
                        "compression": header.biCompression,
                        "data": raw_data,
                        "header": header,
                    }
                finally:
                    Win32API.kernel32.GlobalUnlock(handle)
            finally:
                cls._safe_close_clipboard()

    @classmethod
    def _get_bitmap_data(cls) -> Optional[dict]:
        """杂鱼♡～获取位图数据，返回ImageHandler期望的格式喵～"""
        with cls._clipboard_lock:
            if not cls._safe_open_clipboard():
                raise ClipboardError("杂鱼♡～无法打开剪贴板喵～")

            try:
                handle = Win32API.user32.GetClipboardData(ClipboardFormat.BITMAP.value)
                if not handle:
                    return None

                # 杂鱼♡～获取位图信息喵～
                bitmap_info = Win32Structures.BITMAP()
                result = Win32API.gdi32.GetObjectW(
                    handle, ctypes.sizeof(bitmap_info), ctypes.byref(bitmap_info)
                )

                if result > 0:
                    # 杂鱼♡～返回ImageHandler期望的格式喵～
                    return {
                        "type": "BITMAP",  # 杂鱼♡～ImageHandler检查这个字段喵～
                        "format": "BMP",
                        "width": bitmap_info.bmWidth,
                        "height": bitmap_info.bmHeight,
                        "size": (bitmap_info.bmWidth, bitmap_info.bmHeight),
                        "bit_count": bitmap_info.bmBitsPixel,
                        "data": handle,  # 杂鱼♡～返回句柄，让调用者决定如何处理喵～
                    }
            finally:
                cls._safe_close_clipboard()
        return None

    @classmethod
    def get_file_list(
        cls, retry_count: int = None, timeout: float = None
    ) -> Optional[List[str]]:
        """杂鱼♡～获取剪贴板文件列表喵～"""

        def _get_files():
            with cls._clipboard_lock:
                if not cls._safe_open_clipboard():
                    raise ClipboardError("杂鱼♡～无法打开剪贴板喵～")

                try:
                    handle = Win32API.user32.GetClipboardData(
                        ClipboardFormat.HDROP.value
                    )
                    if not cls._check_memory_validity(handle):
                        return None

                    # 杂鱼♡～现在实现HDROP格式解析喵～
                    return cls._parse_hdrop_data(handle)
                finally:
                    cls._safe_close_clipboard()

        return cls._with_retry(_get_files, retry_count, timeout=timeout)

    @classmethod
    def _parse_hdrop_data(cls, handle: w.HANDLE) -> List[str]:
        """杂鱼♡～解析HDROP格式的文件列表数据喵～"""
        try:
            data_ptr = Win32API.kernel32.GlobalLock(handle)
            if not data_ptr:
                return []

            try:
                # 杂鱼♡～HDROP结构：
                # UINT uSize;        // 结构大小
                # POINT pt;          // 鼠标位置
                # BOOL fNC;          // 是否在客户区
                # BOOL fWide;        // 是否宽字符
                # 然后是以null结尾的文件路径列表

                # 杂鱼♡～跳过HDROP头部（20字节）喵～
                files_data_ptr = data_ptr + 20

                files = []
                current_offset = 0

                while True:
                    # 杂鱼♡～读取宽字符字符串喵～
                    try:
                        file_path = ctypes.wstring_at(files_data_ptr + current_offset)
                        if not file_path:  # 杂鱼♡～空字符串表示结束喵～
                            break

                        files.append(file_path)
                        # 杂鱼♡～移动到下一个字符串（+1是为了跳过null终止符）喵～
                        current_offset += (
                            len(file_path) + 1
                        ) * 2  # 杂鱼♡～宽字符是2字节喵～

                    except Exception:
                        # 杂鱼♡～读取出错，可能到了数据末尾喵～
                        break

                return files

            finally:
                Win32API.kernel32.GlobalUnlock(handle)

        except Exception as e:
            print(f"杂鱼♡～解析HDROP数据失败喵：{e}")
            return []

    @classmethod
    def get_clipboard_content(
        cls, retry_count: int = None, timeout: float = None
    ) -> tuple[Optional[str], Any]:
        """杂鱼♡～获取剪贴板内容和类型喵～"""
        content_type = cls.detect_content_type()
        content = None

        try:
            if content_type == "text":
                content = cls.get_text_content(retry_count, timeout)
            elif content_type == "image":
                content = cls.get_image_content(retry_count, timeout)
            elif content_type == "files":
                content = cls.get_file_list(retry_count, timeout)
        except Exception as e:
            print(f"杂鱼♡～获取剪贴板内容时出错喵：{e}")
            content = None

        return (content_type, content)

    @classmethod
    def get_clipboard_stats(cls) -> Dict[str, Any]:
        """杂鱼♡～获取剪贴板统计信息喵～"""
        return {
            "available_formats": cls.get_available_formats(),
            "sequence_number": Win32API.user32.GetClipboardSequenceNumber(),
            "content_type": cls.detect_content_type(),
        }
