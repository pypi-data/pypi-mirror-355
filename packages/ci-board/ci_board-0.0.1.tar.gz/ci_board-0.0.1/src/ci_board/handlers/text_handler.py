# 杂鱼♡～本喵的文本处理器喵～
from typing import Optional, Callable, Dict, Any
from ..interfaces.callback_interface import BaseClipboardHandler

class TextHandler(BaseClipboardHandler):
    """杂鱼♡～专门处理文本的处理器喵～"""
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        杂鱼♡～初始化文本处理器喵～
        
        Args:
            callback: 处理文本的回调函数，可以是：
                      - callback(text) - 旧格式，只接收文本
                      - callback(text, source_info) - 新格式，接收文本和源信息
        """
        super().__init__(callback)
        self._min_length = 0
        self._max_length = float('inf')
        self._encoding = 'utf-8'
    
    def set_length_filter(self, min_length: int = 0, max_length: Optional[int] = None) -> None:
        """杂鱼♡～设置文本长度过滤器喵～"""
        self._min_length = min_length
        self._max_length = max_length if max_length is not None else float('inf')
    
    def set_encoding(self, encoding: str) -> None:
        """杂鱼♡～设置文本编码喵～"""
        self._encoding = encoding
    
    def is_valid(self, data: str) -> bool:
        """杂鱼♡～检查文本数据是否有效喵～"""
        if not isinstance(data, str):
            return False
        
        if not data.strip():  # 杂鱼♡～空字符串不处理喵～
            return False
        
        text_length = len(data)
        if text_length < self._min_length or text_length > self._max_length:
            return False
        
        return True
    
    def _default_handle(self, data: str, source_info: Optional[Dict[str, Any]] = None) -> None:
        """杂鱼♡～默认的文本处理方法喵～"""
        print(f"杂鱼♡～检测到文本变化喵：")
        print(f"  内容长度：{len(data)} 字符")
        print(f"  前50个字符：{data[:50]}...")
        
        # 杂鱼♡～显示源应用程序信息喵～
        if source_info and self._include_source_info:
            process_name = source_info.get('process_name', 'Unknown')
            detection_method = source_info.get('detection_method', 'unknown')
            is_fallback = source_info.get('is_fallback', False)
            
            # 杂鱼♡～根据不同情况显示不同的信息喵～
            if process_name == 'Unknown':
                print(f"  源应用程序：❓ 未知 (无法获取)")
                if source_info.get('error'):
                    print(f"    原因：{source_info['error']}")
            elif is_fallback:
                print(f"  源应用程序：🔄 {process_name} (推测)")
                print(f"    检测方法：{detection_method}")
                if source_info.get('note'):
                    print(f"    说明：{source_info['note']}")
            else:
                print(f"  源应用程序：{process_name}")
            
            # 杂鱼♡～显示其他详细信息喵～
            if source_info.get('process_path') and process_name != 'Unknown':
                print(f"  程序路径：{source_info['process_path']}")
            if source_info.get('window_title'):
                print(f"  窗口标题：{source_info['window_title']}")
            if source_info.get('process_id'):
                print(f"  进程ID：{source_info['process_id']}")
        
        print("-" * 50)
    
    def get_text_info(self, data: str, source_info: Optional[Dict[str, Any]] = None) -> dict:
        """杂鱼♡～获取文本信息喵～"""
        text_info = {
            'length': len(data),
            'lines': len(data.splitlines()),
            'words': len(data.split()),
            'encoding': self._encoding,
            'is_empty': not data.strip(),
            'preview': data[:100] + ('...' if len(data) > 100 else '')
        }
        
        # 杂鱼♡～添加源应用程序信息喵～
        if source_info:
            text_info['source'] = {
                'process_name': source_info.get('process_name'),
                'process_path': source_info.get('process_path'),
                'window_title': source_info.get('window_title'),
                'window_class': source_info.get('window_class'),
                'process_id': source_info.get('process_id'),
                'timestamp': source_info.get('timestamp')
            }
        
        return text_info

class TextLengthFilter:
    """杂鱼♡～文本长度过滤器类喵～"""
    
    def __init__(self, min_length: int = 0, max_length: Optional[int] = None):
        self.min_length = min_length
        self.max_length = max_length if max_length is not None else float('inf')
    
    def __call__(self, text: str) -> bool:
        """杂鱼♡～检查文本长度是否符合要求喵～"""
        return self.min_length <= len(text) <= self.max_length

class TextPatternFilter:
    """杂鱼♡～文本模式过滤器类喵～"""
    
    def __init__(self, pattern: str, use_regex: bool = False):
        self.pattern = pattern
        self.use_regex = use_regex
        if use_regex:
            import re
            self.regex = re.compile(pattern)
    
    def __call__(self, text: str) -> bool:
        """杂鱼♡～检查文本是否匹配模式喵～"""
        if self.use_regex:
            return bool(self.regex.search(text))
        else:
            return self.pattern in text

class SourceApplicationFilter:
    """杂鱼♡～源应用程序过滤器类喵～"""
    
    def __init__(self, allowed_processes: Optional[list] = None, blocked_processes: Optional[list] = None):
        """
        杂鱼♡～初始化源应用程序过滤器喵～
        
        Args:
            allowed_processes: 允许的进程名列表（例如：['notepad.exe', 'cursor.exe']）
            blocked_processes: 禁止的进程名列表
        """
        self.allowed_processes = [p.lower() for p in (allowed_processes or [])]
        self.blocked_processes = [p.lower() for p in (blocked_processes or [])]
    
    def __call__(self, text: str, source_info: Optional[Dict[str, Any]] = None) -> bool:
        """杂鱼♡～根据源应用程序过滤文本喵～"""
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