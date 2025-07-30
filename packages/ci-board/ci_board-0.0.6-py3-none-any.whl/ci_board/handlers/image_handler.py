# 杂鱼♡～本喵的图片处理器喵～
import datetime
from typing import Any, Callable, Dict, Optional, Union
from ..types import ProcessInfo, BMPData

from ..interfaces.callback_interface import BaseClipboardHandler
from ..utils.logger import get_component_logger

# 杂鱼♡～获取组件专用logger喵～
logger = get_component_logger('handlers.image_handler')

# 杂鱼♡～Windows GDI常量喵～
DIB_RGB_COLORS = 0
BI_RGB = 0


class ImageHandler(BaseClipboardHandler):
    """杂鱼♡～专门处理图片的处理器喵～"""

    def __init__(self, callback: Optional[Callable] = None):
        """
        杂鱼♡～初始化图片处理器喵～

        Args:
            callback: 处理图片的回调函数，可以是：
                      - callback(data) - 旧格式，只接收图片数据
                      - callback(data, source_info) - 新格式，接收图片数据和源信息
        """
        super().__init__(callback)
        self._cached_dib_data = None  # 杂鱼♡～缓存DIB数据喵～
        self._cached_sequence = None  # 杂鱼♡～缓存序列号喵～

    def handle(self, data: Any, source_info: Optional[ProcessInfo] = None) -> None:
        """杂鱼♡～重写handle方法，转换为BMP格式数据喵～"""
        bData = BMPData(
            success=False,
            data=None,
            width=0,
            height=0,
            bit_count=0,
            timestamp=str(datetime.datetime.now()),
        )
        if not self._enabled:
            return

        # 杂鱼♡～增强数据验证，避免处理None或无效数据喵～
        if data is None:
            # 杂鱼♡～数据为None，直接返回，不调用回调喵～
            return

        if not self.is_valid(data):
            return

        if not self._apply_filters(data):
            return

        # 杂鱼♡～将原始数据赋值给BMPData喵～
        bData.data = data

        # 杂鱼♡～转换为BMP格式数据喵～
        try:
            processed_data = self._convert_to_bmp_format(bData)

            # 杂鱼♡～如果转换失败，不调用回调函数喵～
            if not processed_data or (hasattr(processed_data, 'success') and not processed_data.success):
                return

        except Exception as e:
            logger.error(f"杂鱼♡～BMP转换过程出错喵：{e}")
            return

        if self._callback:
            try:
                # 杂鱼♡～检查回调函数是否支持源信息参数喵～
                self._callback(
                    processed_data, source_info
                )
            except Exception as e:
                logger.error(f"杂鱼♡～图片处理回调函数出错喵：{e}")
        else:
            self._default_handle(processed_data, source_info)

    def _convert_to_bmp_format(self, bData: BMPData) -> BMPData:
        """杂鱼♡～转换为BMP格式数据喵～"""
        if not isinstance(bData.data, dict) or bData.data.get("type") != "DIB":
            return bData

        bmp_bytes = self._get_bmp_bytes(bData.data)
        if bmp_bytes:
            # 杂鱼♡～返回BMP格式的数据结构喵～
            bData.success = True
            bData.data = bmp_bytes
            bData.width = int.from_bytes(bmp_bytes[18:22], "little", signed=True)
            bData.height = int.from_bytes(bmp_bytes[22:26], "little", signed=True)
            bData.bit_count = int.from_bytes(bmp_bytes[28:30], "little")
            return bData
        else:
            # 杂鱼♡～BMP转换失败，返回原始数据喵～
            logger.warning("杂鱼♡～BMP转换失败，返回原始数据喵～")
            return bData

    def is_valid(self, data: Any) -> bool:
        """杂鱼♡～检查图片数据是否有效喵～"""
        if data is None:
            return False

        # 杂鱼♡～检查是否是字典格式的图片数据喵～
        if isinstance(data, dict):
            if "type" in data and data["type"] in ["DIB", "BITMAP"]:
                # 杂鱼♡～检查尺寸是否合理喵～
                width = data.get("width", 0)
                height = data.get("height", 0)
                if width <= 0 or height <= 0:
                    return False

                return True

        return False

    def _default_handle(
        self, bData: BMPData, source_info: Optional[ProcessInfo] = None
    ) -> None:
        """杂鱼♡～默认的图片处理方法喵～"""
        logger.info("杂鱼♡～检测到图片变化喵～")

        # 杂鱼♡～显示BMP格式图片信息喵～
        if bData.success:
            logger.info(f"杂鱼♡～BMP格式图片：{bData.width}x{bData.height}喵～")
            logger.info(f"杂鱼♡～BMP文件大小：{len(bData.data)}字节喵～")
        else:
            logger.warning("杂鱼♡～BMP转换失败，返回原始数据喵～")
            return

        # 杂鱼♡～显示源应用程序信息喵～
        if source_info and self._include_source_info:
            logger.info(f"  源应用程序：{source_info.process_name}")
            if source_info.process_path:
                logger.debug(f"  程序路径：{source_info.process_path}")
            if source_info.window_title:
                logger.debug(f"  窗口标题：{source_info.window_title}")

        logger.info("-" * 50)

    def get_image_info(
        self, data: Any, source_info: Optional[ProcessInfo] = None
    ) -> Dict[str, Union[str, int, bool, None]]:
        """杂鱼♡～获取图片信息喵～"""
        default_info = {
            "format": "unknown",
            "width": 0,
            "height": 0,
            "bit_count": 0,
            "size_bytes": 0,
            "size_kb": 0,
            "size_mb": 0,
            "timestamp": str(datetime.datetime.now()),
            "type": "unknown",
        }

        if not isinstance(data, dict):
            return default_info

        # 杂鱼♡～提取实际的图片信息喵～
        info = default_info.copy()
        info.update(
            {
                "format": data.get("format", "unknown"),
                "width": data.get("width", 0),
                "height": data.get("height", 0),
                "bit_count": data.get("bit_count", 0),
                "size_bytes": data.get("size", 0),
                "type": data.get("type", "unknown"),
            }
        )

        # 杂鱼♡～计算文件大小喵～
        if info["size_bytes"] > 0:
            info["size_kb"] = round(info["size_bytes"] / 1024, 2)
            info["size_mb"] = round(info["size_kb"] / 1024, 2)

        # 杂鱼♡～添加源应用程序信息喵～
        if source_info:
            info["source"] = {
                "process_name": source_info.process_name,
                "process_path": source_info.process_path,
                "window_title": source_info.window_title,
                "window_class": source_info.window_class,
                "process_id": source_info.process_id,
                "timestamp": source_info.timestamp,
            }

        return info

    def clear_cache(self) -> None:
        """杂鱼♡～清理缓存的DIB数据喵～"""
        self._cached_dib_data = None
        self._cached_sequence = None

    def _get_fresh_dib_data(self) -> Optional[Dict]:
        """杂鱼♡～获取新鲜的DIB数据，带智能缓存优化喵～"""
        from ..utils.clipboard_utils import ClipboardUtils

        # 杂鱼♡～检查剪贴板序列号是否变化喵～
        current_sequence = None
        try:
            current_sequence = ClipboardUtils.get_clipboard_sequence_number()
            if (
                current_sequence is not None
                and self._cached_sequence == current_sequence
                and self._cached_dib_data is not None
            ):

                # 杂鱼♡～对于大图片，验证缓存数据是否仍然有效喵～
                cached_data = self._cached_dib_data
                width = cached_data.get("width", 0)
                height = cached_data.get("height", 0)

                # 杂鱼♡～如果是大图片（超过50万像素），重新获取数据以确保安全喵～
                if width * height > 500000:  # 杂鱼♡～约700x700像素喵～
                    pass  # 杂鱼♡～跳过缓存，重新获取喵～
                else:
                    # 杂鱼♡～小图片可以安全使用缓存喵～
                    return self._cached_dib_data
        except Exception:
            pass  # 杂鱼♡～获取序列号失败时继续喵～

        # 杂鱼♡～获取新数据并缓存喵～
        fresh_data = ClipboardUtils.get_image_content()
        if fresh_data and fresh_data.get("type") == "DIB":
            width = fresh_data.get("width", 0)
            height = fresh_data.get("height", 0)

            # 杂鱼♡～只为小图片启用缓存喵～
            if width * height <= 500000:
                self._cached_dib_data = fresh_data
                self._cached_sequence = current_sequence
            else:
                # 杂鱼♡～大图片不缓存，每次都重新获取喵～
                self._cached_dib_data = None
                self._cached_sequence = None

            return fresh_data

        return None

    def get_image_bytes(self, data: Dict) -> Optional[bytes]:
        """
        杂鱼♡～返回BMP格式图片字节数据喵～

        Args:
            data: 图片数据

        Returns:
            BMP格式字节数据
        """
        return self._get_bmp_bytes(data)

    def _get_bmp_bytes(self, data: Dict) -> Optional[bytes]:
        """杂鱼♡～获取BMP格式字节数据喵～"""
        if not isinstance(data, dict) or data.get("type") != "DIB":
            return None

        try:
            # 杂鱼♡～从剪贴板重新获取数据喵～
            from ..utils.clipboard_utils import ClipboardUtils

            fresh_data = ClipboardUtils.get_image_content()

            if not fresh_data or fresh_data.get("type") != "DIB":
                return None

            # 杂鱼♡～重构后的数据结构使用'data'字段而不是'data_pointer'喵～
            dib_bytes = fresh_data.get("data")
            if not dib_bytes:
                logger.warning("杂鱼♡～没有找到DIB数据字节喵～")
                return None

            # 杂鱼♡～检查DIB数据大小喵～
            if len(dib_bytes) < 40:
                logger.warning("杂鱼♡～DIB数据太小，无法解析头部喵～")
                return None

            # 杂鱼♡～读取BITMAPINFOHEADER信息喵～
            header_size = int.from_bytes(dib_bytes[0:4], "little")
            width = int.from_bytes(dib_bytes[4:8], "little", signed=True)
            height = int.from_bytes(dib_bytes[8:12], "little", signed=True)
            bit_count = int.from_bytes(dib_bytes[14:16], "little")
            compression = (
                int.from_bytes(dib_bytes[16:20], "little")
                if len(dib_bytes) >= 20
                else 0
            )
            clr_used = (
                int.from_bytes(dib_bytes[32:36], "little")
                if len(dib_bytes) >= 36
                else 0
            )

            # 杂鱼♡～计算像素数据偏移喵～
            pixel_offset = 14 + header_size  # 文件头(14) + DIB头

            # 杂鱼♡～如果有调色板或位字段掩码，需要加上大小喵～
            if bit_count <= 8:
                # 杂鱼♡～调色板模式喵～
                if clr_used > 0:
                    color_table_size = clr_used * 4
                else:
                    color_table_size = (1 << bit_count) * 4
                pixel_offset += color_table_size
            elif compression == 3:  # BI_BITFIELDS
                # 杂鱼♡～位字段掩码，通常是3个DWORD喵～
                pixel_offset += 12  # 3 * 4字节

            # 杂鱼♡～创建BMP文件头喵～
            file_header_size = 14
            file_size = file_header_size + len(dib_bytes)

            # 杂鱼♡～构建完整的BMP字节数据喵～
            bmp_bytes = bytearray()
            bmp_bytes.extend(b"BM")  # BMP签名
            bmp_bytes.extend(file_size.to_bytes(4, "little"))  # 文件大小
            bmp_bytes.extend(b"\x00\x00\x00\x00")  # 保留字段
            bmp_bytes.extend(pixel_offset.to_bytes(4, "little"))  # 像素数据偏移
            bmp_bytes.extend(dib_bytes)  # DIB数据

            logger.info(
                f"杂鱼♡～BMP转换成功：{width}x{abs(height)}，{bit_count}位，文件大小{len(bmp_bytes)}字节喵～"
            )
            return bytes(bmp_bytes)

        except Exception as e:
            logger.error(f"杂鱼♡～获取BMP字节数据失败喵：{e}")
            import traceback

            traceback.print_exc()
            return None


class ImageSizeFilter:
    """杂鱼♡～图片尺寸过滤器类喵～"""

    def __init__(
        self,
        min_width: int = 0,
        min_height: int = 0,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
    ):
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height

    def __call__(self, data: Any) -> bool:
        """杂鱼♡～检查图片尺寸是否符合要求喵～"""
        if not isinstance(data, dict):
            return False

        width = data.get("width", 0)
        height = data.get("height", 0)

        # 杂鱼♡～检查最小尺寸喵～
        if width < self.min_width or height < self.min_height:
            return False

        # 杂鱼♡～检查最大尺寸喵～
        if self.max_width is not None and width > self.max_width:
            return False
        if self.max_height is not None and height > self.max_height:
            return False

        return True


class ImageFormatFilter:
    """杂鱼♡～图片格式过滤器类喵～"""

    def __init__(self, allowed_formats: list):
        # 杂鱼♡～标准化格式名称喵～
        format_mapping = {
            "cf_dib": "CF_DIB",
            "cf_dibv5": "CF_DIBV5",
            "cf_bitmap": "CF_BITMAP",
            "dib": "CF_DIB",
            "dibv5": "CF_DIBV5",
            "bitmap": "CF_BITMAP",
        }

        self.allowed_formats = []
        for fmt in allowed_formats:
            normalized = format_mapping.get(fmt.lower(), fmt.upper())
            self.allowed_formats.append(normalized)

    def __call__(self, data: Any) -> bool:
        """杂鱼♡～检查图片格式是否允许喵～"""
        if not isinstance(data, dict):
            return False

        image_format = data.get("format", "").upper()
        return image_format in self.allowed_formats


class ImageQualityFilter:
    """杂鱼♡～图片质量过滤器喵～"""

    def __init__(self, min_bit_count: int = 1, max_bit_count: int = 32):
        self.min_bit_count = min_bit_count
        self.max_bit_count = max_bit_count

    def __call__(self, data: Any) -> bool:
        """杂鱼♡～检查图片位深度是否符合要求喵～"""
        if not isinstance(data, dict):
            return False

        bit_count = data.get("bit_count", 0)
        return self.min_bit_count <= bit_count <= self.max_bit_count


class ImageAreaFilter:
    """杂鱼♡～图片面积过滤器喵～"""

    def __init__(self, min_area: int = 0, max_area: Optional[int] = None):
        self.min_area = min_area
        self.max_area = max_area

    def __call__(self, data: Any) -> bool:
        """杂鱼♡～检查图片面积是否符合要求喵～"""
        if not isinstance(data, dict):
            return False

        width = data.get("width", 0)
        height = data.get("height", 0)
        area = width * height

        if area < self.min_area:
            return False
        if self.max_area is not None and area > self.max_area:
            return False

        return True


class SourceApplicationImageFilter:
    """杂鱼♡～图片源应用程序过滤器类喵～"""

    def __init__(
        self,
        allowed_processes: Optional[list] = None,
        blocked_processes: Optional[list] = None,
    ):
        """
        杂鱼♡～初始化图片源应用程序过滤器喵～

        Args:
            allowed_processes: 允许的进程名列表
            blocked_processes: 禁止的进程名列表
        """
        self.allowed_processes = [p.lower() for p in (allowed_processes or [])]
        self.blocked_processes = [p.lower() for p in (blocked_processes or [])]

    def __call__(self, data: Any, source_info: Optional[ProcessInfo] = None) -> bool:
        """杂鱼♡～根据源应用程序过滤图片喵～"""
        if not source_info or not source_info.process_name:
            # 杂鱼♡～如果没有源信息，默认允许喵～
            return True

        process_name = source_info.process_name.lower()

        # 杂鱼♡～检查是否在禁止列表中喵～
        if self.blocked_processes and process_name in self.blocked_processes:
            return False

        # 杂鱼♡～如果有允许列表，检查是否在其中喵～
        if self.allowed_processes:
            return process_name in self.allowed_processes

        return True
