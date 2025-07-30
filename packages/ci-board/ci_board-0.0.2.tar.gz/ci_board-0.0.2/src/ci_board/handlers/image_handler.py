# 杂鱼♡～本喵的图片处理器喵～
from typing import Optional, Callable, Any, Dict, Union, Tuple
from ..interfaces.callback_interface import BaseClipboardHandler
import datetime
import ctypes
import ctypes.wintypes as w

class BITMAP(ctypes.Structure):
    _fields_ = [
        ('bmType', w.LONG),
        ('bmWidth', w.LONG),
        ('bmHeight', w.LONG),
        ('bmWidthBytes', w.LONG),
        ('bmPlanes', w.WORD),
        ('bmBitsPixel', w.WORD),
        ('bmBits', ctypes.POINTER(ctypes.c_void_p))
    ]

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
    

    
    def handle(self, data: Any, source_info: Optional[Dict[str, Any]] = None) -> None:
        """杂鱼♡～重写handle方法，转换为BMP格式数据喵～"""
        if not self._enabled:
            return
            
        if not self.is_valid(data):
            return
            
        if not self._apply_filters(data):
            return
        
        # 杂鱼♡～转换为BMP格式数据喵～
        processed_data = self._convert_to_bmp_format(data)
        
        if self._callback:
            # 杂鱼♡～检查回调函数是否支持源信息参数喵～
            import inspect
            sig = inspect.signature(self._callback)
            if len(sig.parameters) >= 2:
                # 杂鱼♡～新格式回调：(data, source_info)喵～
                self._callback(processed_data, source_info if self._include_source_info else None)
            else:
                # 杂鱼♡～旧格式回调：只有data参数喵～
                self._callback(processed_data)
        else:
            self._default_handle(processed_data, source_info)
    

    
    def _convert_to_bmp_format(self, data: Any) -> Dict[str, Any]:
        """杂鱼♡～转换为BMP格式数据喵～"""
        if not isinstance(data, dict) or data.get('type') != 'DIB':
            return data
        
        bmp_bytes = self._get_bmp_bytes(data)
        if bmp_bytes:
            # 杂鱼♡～返回BMP格式的数据结构喵～
            return {
                'format': 'BMP',
                'type': 'BMP',
                'data': bmp_bytes,
                'size': (data.get('width', 0), data.get('height', 0)),
                'bit_count': data.get('bit_count', 0),
                'file_size': len(bmp_bytes),
                'timestamp': str(datetime.datetime.now())
            }
        else:
            # 杂鱼♡～BMP转换失败，返回原始数据喵～
            print("杂鱼♡～BMP转换失败，返回原始数据喵～")
            return data
    

    
    def is_valid(self, data: Any) -> bool:
        """杂鱼♡～检查图片数据是否有效喵～"""
        if data is None:
            return False
            
        # 杂鱼♡～检查是否是字典格式的图片数据喵～
        if isinstance(data, dict):
            if 'type' in data and data['type'] in ['DIB', 'BITMAP']:
                # 杂鱼♡～检查尺寸是否合理喵～
                width = data.get('width', 0)
                height = data.get('height', 0)
                if width <= 0 or height <= 0:
                    return False
                
                return True
        
        return False
    
    def _default_handle(self, data: Any, source_info: Optional[Dict[str, Any]] = None) -> None:
        """杂鱼♡～默认的图片处理方法喵～"""
        if not self.is_valid(data):
            print("杂鱼♡～无效的图片数据喵～")
            return
            
        print("杂鱼♡～检测到图片变化喵～")
        
        # 杂鱼♡～显示BMP格式图片信息喵～
        if isinstance(data, dict):
            if data.get('format') == 'BMP':
                print(f"杂鱼♡～BMP格式图片：{data['size'][0]}x{data['size'][1]}喵～")
                print(f"杂鱼♡～BMP文件大小：{data.get('file_size', 0)}字节喵～")
            else:
                # 杂鱼♡～原始格式或未知格式喵～
                image_info = self.get_image_info(data, source_info)
                print(f"杂鱼♡～原始图片信息：{image_info['width']}x{image_info['height']} {image_info['format']}喵～")
        
        # 杂鱼♡～显示源应用程序信息喵～
        if source_info and self._include_source_info:
            print(f"  源应用程序：{source_info.get('process_name', 'Unknown')}")
            if source_info.get('process_path'):
                print(f"  程序路径：{source_info['process_path']}")
            if source_info.get('window_title'):
                print(f"  窗口标题：{source_info['window_title']}")
            if source_info.get('error'):
                print(f"  错误信息：{source_info['error']}")
        
        print("-" * 50)
    
    def get_image_info(self, data: Any, source_info: Optional[Dict[str, Any]] = None) -> Dict[str, Union[str, int, bool, None]]:
        """杂鱼♡～获取图片信息喵～"""
        default_info = {
            'format': 'unknown',
            'width': 0,
            'height': 0,
            'bit_count': 0,
            'size_bytes': 0,
            'size_kb': 0,
            'size_mb': 0,
            'timestamp': str(datetime.datetime.now()),
            'type': 'unknown'
        }
        
        if not isinstance(data, dict):
            return default_info
            
        # 杂鱼♡～提取实际的图片信息喵～
        info = default_info.copy()
        info.update({
            'format': data.get('format', 'unknown'),
            'width': data.get('width', 0),
            'height': data.get('height', 0),
            'bit_count': data.get('bit_count', 0),
            'size_bytes': data.get('size', 0),
            'type': data.get('type', 'unknown')
        })
        
        # 杂鱼♡～计算文件大小喵～
        if info['size_bytes'] > 0:
            info['size_kb'] = round(info['size_bytes'] / 1024, 2)
            info['size_mb'] = round(info['size_kb'] / 1024, 2)
        
        # 杂鱼♡～添加源应用程序信息喵～
        if source_info:
            info['source'] = {
                'process_name': source_info.get('process_name'),
                'process_path': source_info.get('process_path'),
                'window_title': source_info.get('window_title'),
                'window_class': source_info.get('window_class'),
                'process_id': source_info.get('process_id'),
                'timestamp': source_info.get('timestamp')
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
            if (current_sequence is not None and 
                self._cached_sequence == current_sequence and 
                self._cached_dib_data is not None):
                
                # 杂鱼♡～对于大图片，验证缓存数据是否仍然有效喵～
                cached_data = self._cached_dib_data
                width = cached_data.get('width', 0)
                height = cached_data.get('height', 0)
                
                # 杂鱼♡～如果是大图片（超过50万像素），重新获取数据以确保安全喵～
                if width * height > 500000:  # 杂鱼♡～约700x700像素喵～
                    pass  # 杂鱼♡～跳过缓存，重新获取喵～
                else:
                    # 杂鱼♡～小图片可以安全使用缓存喵～
                    return self._cached_dib_data
        except:
            pass  # 杂鱼♡～获取序列号失败时继续喵～
        
        # 杂鱼♡～获取新数据并缓存喵～
        fresh_data = ClipboardUtils.get_image_content()
        if fresh_data and fresh_data.get('type') == 'DIB':
            width = fresh_data.get('width', 0)
            height = fresh_data.get('height', 0)
            
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
        if not isinstance(data, dict) or data.get('type') != 'DIB':
            return None
            
        try:
            # 杂鱼♡～从剪贴板重新获取数据喵～
            from ..utils.clipboard_utils import ClipboardUtils
            fresh_data = ClipboardUtils.get_image_content()
            
            if not fresh_data or fresh_data.get('type') != 'DIB':
                return None
            
            # 杂鱼♡～重构后的数据结构使用'data'字段而不是'data_pointer'喵～
            dib_bytes = fresh_data.get('data')
            if not dib_bytes:
                print("杂鱼♡～没有找到DIB数据字节喵～")
                return None
            
            # 杂鱼♡～检查DIB数据大小喵～
            if len(dib_bytes) < 40:
                print("杂鱼♡～DIB数据太小，无法解析头部喵～")
                return None
                
            # 杂鱼♡～读取BITMAPINFOHEADER信息喵～
            header_size = int.from_bytes(dib_bytes[0:4], 'little')
            width = int.from_bytes(dib_bytes[4:8], 'little', signed=True)
            height = int.from_bytes(dib_bytes[8:12], 'little', signed=True)
            bit_count = int.from_bytes(dib_bytes[14:16], 'little')
            compression = int.from_bytes(dib_bytes[16:20], 'little') if len(dib_bytes) >= 20 else 0
            clr_used = int.from_bytes(dib_bytes[32:36], 'little') if len(dib_bytes) >= 36 else 0
            
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
            bmp_bytes.extend(b'BM')  # BMP签名
            bmp_bytes.extend(file_size.to_bytes(4, 'little'))  # 文件大小
            bmp_bytes.extend(b'\x00\x00\x00\x00')  # 保留字段  
            bmp_bytes.extend(pixel_offset.to_bytes(4, 'little'))  # 像素数据偏移
            bmp_bytes.extend(dib_bytes)  # DIB数据
            
            print(f"杂鱼♡～BMP转换成功：{width}x{abs(height)}，{bit_count}位，文件大小{len(bmp_bytes)}字节喵～")
            return bytes(bmp_bytes)
            
        except Exception as e:
            print(f"杂鱼♡～获取BMP字节数据失败喵：{e}")
            import traceback
            traceback.print_exc()
            return None

class ImageSizeFilter:
    """杂鱼♡～图片尺寸过滤器类喵～"""
    
    def __init__(self, min_width: int = 0, min_height: int = 0, 
                 max_width: Optional[int] = None, max_height: Optional[int] = None):
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height
    
    def __call__(self, data: Any) -> bool:
        """杂鱼♡～检查图片尺寸是否符合要求喵～"""
        if not isinstance(data, dict):
            return False
            
        width = data.get('width', 0)
        height = data.get('height', 0)
        
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
            'cf_dib': 'CF_DIB',
            'cf_dibv5': 'CF_DIBV5', 
            'cf_bitmap': 'CF_BITMAP',
            'dib': 'CF_DIB',
            'dibv5': 'CF_DIBV5',
            'bitmap': 'CF_BITMAP'
        }
        
        self.allowed_formats = []
        for fmt in allowed_formats:
            normalized = format_mapping.get(fmt.lower(), fmt.upper())
            self.allowed_formats.append(normalized)
    
    def __call__(self, data: Any) -> bool:
        """杂鱼♡～检查图片格式是否允许喵～"""
        if not isinstance(data, dict):
            return False
            
        image_format = data.get('format', '').upper()
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
            
        bit_count = data.get('bit_count', 0)
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
            
        width = data.get('width', 0)
        height = data.get('height', 0)
        area = width * height
        
        if area < self.min_area:
            return False
        if self.max_area is not None and area > self.max_area:
            return False
            
        return True

class SourceApplicationImageFilter:
    """杂鱼♡～图片源应用程序过滤器类喵～"""
    
    def __init__(self, allowed_processes: Optional[list] = None, blocked_processes: Optional[list] = None):
        """
        杂鱼♡～初始化图片源应用程序过滤器喵～
        
        Args:
            allowed_processes: 允许的进程名列表
            blocked_processes: 禁止的进程名列表
        """
        self.allowed_processes = [p.lower() for p in (allowed_processes or [])]
        self.blocked_processes = [p.lower() for p in (blocked_processes or [])]
    
    def __call__(self, data: Any, source_info: Optional[Dict[str, Any]] = None) -> bool:
        """杂鱼♡～根据源应用程序过滤图片喵～"""
        if not source_info or not source_info.get('process_name'):
            # 杂鱼♡～如果没有源信息，默认允许喵～
            return True
        
        process_name = source_info['process_name'].lower()
        
        # 杂鱼♡～检查是否在禁止列表中喵～
        if self.blocked_processes and process_name in self.blocked_processes:
            return False
        
        # 杂鱼♡～如果有允许列表，检查是否在其中喵～
        if self.allowed_processes:
            return process_name in self.allowed_processes
        
        return True