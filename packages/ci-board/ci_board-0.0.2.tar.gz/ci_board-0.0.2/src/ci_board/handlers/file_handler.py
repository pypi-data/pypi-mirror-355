# 杂鱼♡～本喵的文件处理器喵～
from typing import Optional, Callable, List, Dict, Any
from ..interfaces.callback_interface import BaseClipboardHandler

class FileHandler(BaseClipboardHandler):
    """杂鱼♡～专门处理文件的处理器喵～"""
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        杂鱼♡～初始化文件处理器喵～
        
        Args:
            callback: 处理文件列表的回调函数，可以是：
                      - callback(files) - 旧格式，只接收文件列表
                      - callback(files, source_info) - 新格式，接收文件列表和源信息
        """
        super().__init__(callback)
        self._allowed_extensions = []
        self._blocked_extensions = []
        self._max_file_count = 100
        self._check_file_exists = True
    
    def set_allowed_extensions(self, extensions: List[str]) -> None:
        """杂鱼♡～设置允许的文件扩展名喵～"""
        self._allowed_extensions = [ext.lower() for ext in extensions]
    
    def set_blocked_extensions(self, extensions: List[str]) -> None:
        """杂鱼♡～设置禁止的文件扩展名喵～"""
        self._blocked_extensions = [ext.lower() for ext in extensions]
    
    def set_max_file_count(self, count: int) -> None:
        """杂鱼♡～设置最大文件数量限制喵～"""
        self._max_file_count = count
    
    def enable_file_exists_check(self) -> None:
        """杂鱼♡～启用文件存在性检查喵～"""
        self._check_file_exists = True
    
    def disable_file_exists_check(self) -> None:
        """杂鱼♡～禁用文件存在性检查喵～"""
        self._check_file_exists = False
    
    def is_valid(self, data: List[str]) -> bool:
        """杂鱼♡～检查文件数据是否有效喵～"""
        if not isinstance(data, list):
            return False
        
        if len(data) == 0:
            return False
        
        if len(data) > self._max_file_count:
            return False
        
        # 杂鱼♡～检查每个文件路径喵～
        for file_path in data:
            if not self._is_valid_file(file_path):
                return False
        
        return True
    
    def _is_valid_file(self, file_path: str) -> bool:
        """杂鱼♡～检查单个文件是否有效喵～"""
        import os
        
        # 杂鱼♡～检查文件是否存在喵～
        if self._check_file_exists and not os.path.exists(file_path):
            return False
        
        # 杂鱼♡～检查扩展名喵～
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # 杂鱼♡～检查是否在允许列表中喵～
        if self._allowed_extensions and ext not in self._allowed_extensions:
            return False
        
        # 杂鱼♡～检查是否在禁止列表中喵～
        if self._blocked_extensions and ext in self._blocked_extensions:
            return False
        
        return True
    
    def _default_handle(self, data: List[str], source_info: Optional[Dict[str, Any]] = None) -> None:
        """杂鱼♡～默认的文件处理方法喵～"""
        print(f"杂鱼♡～检测到文件变化喵：")
        print(f"  文件数量：{len(data)}")
        
        for i, file_path in enumerate(data, 1):
            file_info = self.get_file_info(file_path)
            print(f"  文件{i}：{file_info['name']} ({file_info['size']})")
        
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
    
    def get_file_info(self, file_path: str) -> dict:
        """杂鱼♡～获取文件信息喵～"""
        import os
        import datetime
        
        info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'directory': os.path.dirname(file_path),
            'extension': os.path.splitext(file_path)[1],
            'exists': os.path.exists(file_path),
            'size': 'unknown',
            'modified': 'unknown'
        }
        
        if info['exists']:
            try:
                stat = os.stat(file_path)
                info['size'] = self._format_file_size(stat.st_size)
                info['modified'] = str(datetime.datetime.fromtimestamp(stat.st_mtime))
            except Exception as e:
                info['error'] = str(e)
        
        return info
    
    def _format_file_size(self, size_bytes: int) -> str:
        """杂鱼♡～格式化文件大小喵～"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def get_files_summary(self, data: List[str], source_info: Optional[Dict[str, Any]] = None) -> dict:
        """杂鱼♡～获取文件列表汇总信息喵～"""
        summary = {
            'total_count': len(data),
            'valid_count': 0,
            'invalid_count': 0,
            'total_size': 0,
            'extensions': {},
            'directories': set()
        }
        
        for file_path in data:
            info = self.get_file_info(file_path)
            
            if info['exists']:
                summary['valid_count'] += 1
                
                # 杂鱼♡～统计扩展名喵～
                ext = info['extension'].lower()
                summary['extensions'][ext] = summary['extensions'].get(ext, 0) + 1
                
                # 杂鱼♡～记录目录喵～
                summary['directories'].add(info['directory'])
            else:
                summary['invalid_count'] += 1
        
        summary['directories'] = list(summary['directories'])
        
        # 杂鱼♡～添加源应用程序信息喵～
        if source_info:
            summary['source'] = {
                'process_name': source_info.get('process_name'),
                'process_path': source_info.get('process_path'),
                'window_title': source_info.get('window_title'),
                'window_class': source_info.get('window_class'),
                'process_id': source_info.get('process_id'),
                'timestamp': source_info.get('timestamp')
            }
        
        return summary

class FileExtensionFilter:
    """杂鱼♡～文件扩展名过滤器类喵～"""
    
    def __init__(self, allowed_extensions: List[str]):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
    
    def __call__(self, files: List[str]) -> bool:
        """杂鱼♡～检查文件扩展名是否允许喵～"""
        import os
        
        for file_path in files:
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in self.allowed_extensions:
                return False
        return True

class FileSizeFilter:
    """杂鱼♡～文件大小过滤器类喵～"""
    
    def __init__(self, max_size_mb: float):
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    def __call__(self, files: List[str]) -> bool:
        """杂鱼♡～检查文件大小是否符合要求喵～"""
        import os
        
        for file_path in files:
            if os.path.exists(file_path):
                if os.path.getsize(file_path) > self.max_size_bytes:
                    return False
        return True

class SourceApplicationFileFilter:
    """杂鱼♡～文件源应用程序过滤器类喵～"""
    
    def __init__(self, allowed_processes: Optional[List[str]] = None, blocked_processes: Optional[List[str]] = None):
        """
        杂鱼♡～初始化文件源应用程序过滤器喵～
        
        Args:
            allowed_processes: 允许的进程名列表
            blocked_processes: 禁止的进程名列表
        """
        self.allowed_processes = [p.lower() for p in (allowed_processes or [])]
        self.blocked_processes = [p.lower() for p in (blocked_processes or [])]
    
    def __call__(self, files: List[str], source_info: Optional[Dict[str, Any]] = None) -> bool:
        """杂鱼♡～根据源应用程序过滤文件喵～"""
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