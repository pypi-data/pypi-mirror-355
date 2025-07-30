# 杂鱼♡～本喵的核心剪贴板监控器喵～
import threading
import time
import hashlib
import json
from typing import Dict, Optional, Any, List, Union, Callable, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from ..utils.clipboard_utils import ClipboardUtils
from ..interfaces.callback_interface import BaseClipboardHandler

class ClipboardMonitor:
    """杂鱼♡～本喵设计的高扩展性剪贴板监控器喵～"""
    
    def __init__(self, async_processing: bool = True, max_workers: int = 4, handler_timeout: float = 30.0, event_driven: bool = True):
        """
        杂鱼♡～初始化监控器喵～
        
        Args:
            async_processing: 是否启用异步处理模式
            max_workers: 处理器线程池最大工作线程数
            handler_timeout: 单个处理器超时时间（秒）
            event_driven: 是否启用事件驱动模式（推荐，更高效）
        """
        self._handlers: Dict[str, List[BaseClipboardHandler]] = {
            'text': [],
            'image': [], 
            'files': [],
            'update': []
        }
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._hwnd = None
        self._window_creation_success = None  # 杂鱼♡～窗口创建成功事件喵～
        # self._polling_interval = 0.5
        self._last_content = None
        self._last_sequence_number = 0  # 杂鱼♡～添加序列号跟踪喵～
        self._last_content_hash = None  # 杂鱼♡～添加内容哈希值跟踪，避免重复处理喵～
        self._is_running = False
        self._content_cache = {}  # 杂鱼♡～内容缓存，用于去重喵～
        self._cache_max_size = 10  # 杂鱼♡～最大缓存数量喵～
        self._enable_source_tracking = True  # 杂鱼♡～启用源应用程序追踪喵～
        
        # 杂鱼♡～事件驱动相关配置喵～
        self._event_driven = event_driven
        self._monitoring_mode = 'event' if event_driven else 'polling'
        
        # 杂鱼♡～异步处理相关配置喵～
        self._async_processing = async_processing
        self._max_workers = max_workers
        self._handler_timeout = handler_timeout
        self._executor: Optional[ThreadPoolExecutor] = None
        self._task_queue = queue.Queue()
        self._executor_thread: Optional[threading.Thread] = None
        self._executor_stop_event = threading.Event()
        
        # 杂鱼♡～异步处理统计信息喵～
        self._async_stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_timeout': 0,
            'active_tasks': 0
        }
    
    def enable_async_processing(self) -> None:
        """杂鱼♡～启用异步处理模式喵～"""
        self._async_processing = True
    
    def disable_async_processing(self) -> None:
        """杂鱼♡～禁用异步处理模式（回到同步模式）喵～"""
        self._async_processing = False
    
    def set_async_config(self, max_workers: int = 4, handler_timeout: float = 30.0) -> None:
        """杂鱼♡～设置异步处理配置喵～"""
        self._max_workers = max_workers
        self._handler_timeout = handler_timeout
        
        # 杂鱼♡～如果正在运行，重新初始化线程池喵～
        if self._is_running and self._async_processing:
            self._restart_async_executor()
    
    def _restart_async_executor(self) -> None:
        """杂鱼♡～重启异步执行器喵～"""
        if self._executor:
            print("杂鱼♡～重新启动异步执行器喵～")
            self._shutdown_async_executor()
            self._init_async_executor()
    
    def _init_async_executor(self) -> None:
        """杂鱼♡～初始化异步执行器喵～"""
        if not self._async_processing:
            return
            
        print(f"杂鱼♡～初始化异步执行器，最大工作线程：{self._max_workers}，超时：{self._handler_timeout}s喵～")
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="NekoHandler")
        self._executor_stop_event.clear()
        self._executor_thread = threading.Thread(target=self._async_executor_loop, daemon=True)
        self._executor_thread.start()
    
    def _shutdown_async_executor(self) -> None:
        """杂鱼♡～关闭异步执行器喵～"""
        if not self._executor:
            return
            
        print("杂鱼♡～正在关闭异步执行器喵～")
        self._executor_stop_event.set()
        
        # 杂鱼♡～等待执行器线程结束喵～
        if self._executor_thread and self._executor_thread.is_alive():
            self._executor_thread.join(timeout=2.0)
        
        # 杂鱼♡～关闭线程池喵～
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
    
    def _async_executor_loop(self) -> None:
        """杂鱼♡～异步执行器循环喵～"""
        futures = {}
        
        while not self._executor_stop_event.is_set():
            try:
                # 杂鱼♡～从任务队列获取新任务喵～
                try:
                    task = self._task_queue.get(timeout=0.1)
                    if task is None:  # 杂鱼♡～关闭信号喵～
                        break
                    
                    handler, content, source_info, content_type = task
                    future = self._executor.submit(self._execute_handler_safely, handler, content, source_info, content_type)
                    futures[future] = (handler, content_type, time.time())
                    self._async_stats['tasks_submitted'] += 1
                    self._async_stats['active_tasks'] += 1
                    
                except queue.Empty:
                    pass
                
                # 杂鱼♡～检查已完成的任务喵～
                completed_futures = []
                for future in list(futures.keys()):
                    if future.done():
                        completed_futures.append(future)
                    else:
                        # 杂鱼♡～检查超时喵～
                        handler, content_type, start_time = futures[future]
                        if time.time() - start_time > self._handler_timeout:
                            print(f"杂鱼♡～处理器超时了喵：{type(handler).__name__} ({content_type})")
                            future.cancel()
                            completed_futures.append(future)
                            self._async_stats['tasks_timeout'] += 1
                
                # 杂鱼♡～处理已完成的任务喵～
                for future in completed_futures:
                    try:
                        if not future.cancelled():
                            result = future.result()
                            if result:
                                self._async_stats['tasks_completed'] += 1
                            else:
                                self._async_stats['tasks_failed'] += 1
                    except Exception as e:
                        handler, content_type, _ = futures[future]
                        print(f"杂鱼♡～异步处理器出错了喵：{type(handler).__name__} ({content_type}) - {e}")
                        self._async_stats['tasks_failed'] += 1
                    finally:
                        del futures[future]
                        self._async_stats['active_tasks'] -= 1
                        self._task_queue.task_done()
                
                # 杂鱼♡～适当休息喵～
                time.sleep(0.01)
                
            except Exception as e:
                print(f"杂鱼♡～异步执行器循环出错了喵：{e}")
                time.sleep(0.1)
        
        # 杂鱼♡～清理剩余任务喵～
        print("杂鱼♡～异步执行器循环结束，清理剩余任务喵～")
        for future in futures.keys():
            future.cancel()
    
    def _execute_handler_safely(self, handler: BaseClipboardHandler, content: Any, 
                               source_info: Optional[Dict[str, Any]], content_type: str) -> bool:
        """杂鱼♡～安全执行处理器喵～"""
        try:
            if self._enable_source_tracking:
                handler.handle(content, source_info)
            else:
                # 杂鱼♡～检查处理器是否支持源信息参数，向后兼容喵～
                import inspect
                if hasattr(handler, 'handle'):
                    sig = inspect.signature(handler.handle)
                    if len(sig.parameters) >= 2:
                        handler.handle(content, None)
                    else:
                        handler.handle(content)
                else:
                    handler.handle(content)
            return True
        except Exception as e:
            print(f"杂鱼♡～{content_type}处理器出错了喵：{type(handler).__name__} - {e}")
            return False
    
    def get_async_stats(self) -> Dict[str, Any]:
        """杂鱼♡～获取异步处理统计信息喵～"""
        return {
            'async_enabled': self._async_processing,
            'max_workers': self._max_workers,
            'handler_timeout': self._handler_timeout,
            'executor_running': self._executor is not None,
            'queue_size': self._task_queue.qsize(),
            **self._async_stats
        }

    def enable_source_tracking(self) -> None:
        """杂鱼♡～启用源应用程序追踪功能喵～"""
        self._enable_source_tracking = True
    
    def disable_source_tracking(self) -> None:
        """杂鱼♡～禁用源应用程序追踪功能喵～"""
        self._enable_source_tracking = False
    
    def enable_event_driven_mode(self) -> None:
        """杂鱼♡～启用事件驱动监控模式（推荐）喵～"""
        self._event_driven = True
        self._monitoring_mode = 'event'
        print("杂鱼♡～已切换到事件驱动模式，更高效喵～")
    
    def disable_event_driven_mode(self) -> None:
        """杂鱼♡～禁用事件驱动模式，回到轮询模式喵～"""
        self._event_driven = False
        self._monitoring_mode = 'polling'
        print("杂鱼♡～已切换到轮询模式，杂鱼主人确定要这样做吗？喵～")
    
    def add_handler(self, content_type: Literal['text', 'image', 'files', 'update'], handler: Union[BaseClipboardHandler, Callable]) -> BaseClipboardHandler:
        """
        杂鱼♡～添加处理器喵～
        
        Args:
            content_type: 内容类型 ('text', 'image', 'files', 'update')
            handler: 处理器实例或回调函数
            
        Returns:
            BaseClipboardHandler: 处理器实例（如果传入回调函数会自动创建）
        """
        if content_type not in self._handlers:
            raise ValueError(f"杂鱼♡～不支持的内容类型：{content_type}")
        
        # 杂鱼♡～如果传入的是回调函数，自动创建对应的处理器喵～
        if callable(handler) and not isinstance(handler, BaseClipboardHandler):
            handler = self._create_handler_from_callback(content_type, handler)
        
        self._handlers[content_type].append(handler)
        return handler
    
    def _create_handler_from_callback(self, content_type: str, callback: Callable) -> BaseClipboardHandler:
        """杂鱼♡～根据回调函数创建对应的处理器喵～"""
        # 杂鱼♡～延迟导入避免循环引用喵～
        if content_type == 'text':
            from ..handlers.text_handler import TextHandler
            return TextHandler(callback)
        elif content_type == 'image':
            from ..handlers.image_handler import ImageHandler
            return ImageHandler(callback)
        elif content_type == 'files':
            from ..handlers.file_handler import FileHandler
            return FileHandler(callback)
        elif content_type == 'update':
            return SimpleUpdateHandler(callback)
        else:
            raise ValueError(f"杂鱼♡～无法为类型 {content_type} 创建处理器喵～")
    
    def remove_handler(self, content_type: str, handler: BaseClipboardHandler) -> None:
        """杂鱼♡～移除处理器喵～"""
        if content_type in self._handlers and handler in self._handlers[content_type]:
            self._handlers[content_type].remove(handler)
    
    def clear_handlers(self, content_type: Optional[str] = None) -> None:
        """杂鱼♡～清空处理器喵～"""
        if content_type:
            self._handlers[content_type].clear()
        else:
            for handlers in self._handlers.values():
                handlers.clear()
    
    def _calculate_content_hash(self, content_data) -> str:
        """杂鱼♡～计算内容哈希值，用于去重喵～"""
        content_type, content = content_data
        
        try:
            if content_type == 'text' and isinstance(content, str):
                # 杂鱼♡～文本内容直接哈希喵～
                return hashlib.md5(content.encode('utf-8')).hexdigest()
            elif content_type == 'image' and isinstance(content, dict):
                # 杂鱼♡～图片内容根据关键信息哈希喵～
                key_info = {
                    'type': content.get('type'),
                    'width': content.get('width'),
                    'height': content.get('height'), 
                    'bit_count': content.get('bit_count'),
                    'data_size': len(content.get('data', b'')) if content.get('data') else 0
                }
                # 杂鱼♡～如果有数据，取前1024字节参与哈希计算喵～
                if content.get('data') and len(content['data']) > 0:
                    data_sample = content['data'][:1024]
                    key_info['data_sample'] = hashlib.md5(data_sample).hexdigest()
                
                return hashlib.md5(json.dumps(key_info, sort_keys=True).encode('utf-8')).hexdigest()
            elif content_type == 'files' and isinstance(content, list):
                # 杂鱼♡～文件列表哈希喵～
                file_list = sorted(content)  # 杂鱼♡～排序确保一致性喵～
                return hashlib.md5(json.dumps(file_list).encode('utf-8')).hexdigest()
            else:
                # 杂鱼♡～其他类型转字符串哈希喵～
                return hashlib.md5(str(content).encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"杂鱼♡～计算内容哈希失败喵：{e}")
            # 杂鱼♡～如果哈希计算失败，返回时间戳确保不会误判重复喵～
            return hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()
    
    def _is_content_duplicate(self, content_data) -> bool:
        """杂鱼♡～检查内容是否重复喵～"""
        content_hash = self._calculate_content_hash(content_data)
        
        # 杂鱼♡～检查是否与上次内容相同喵～
        if content_hash == self._last_content_hash:
            return True
        
        # 杂鱼♡～检查缓存中是否存在喵～
        if content_hash in self._content_cache:
            # 杂鱼♡～检查时间间隔，避免短时间内重复处理喵～
            last_time = self._content_cache[content_hash]
            if time.time() - last_time < 1.0:  # 杂鱼♡～1秒内的重复内容忽略喵～
                # print(f"杂鱼♡～检测到重复内容，已跳过处理喵～")
                return True
        
        # 杂鱼♡～更新缓存喵～
        self._content_cache[content_hash] = time.time()
        self._last_content_hash = content_hash
        
        # 杂鱼♡～清理过期缓存喵～
        if len(self._content_cache) > self._cache_max_size:
            self._cleanup_cache()
        
        return False
    
    def _cleanup_cache(self) -> None:
        """杂鱼♡～清理过期的内容缓存喵～"""
        current_time = time.time()
        expired_keys = []
        
        for content_hash, timestamp in self._content_cache.items():
            if current_time - timestamp > 10.0:  # 杂鱼♡～10秒后过期喵～
                expired_keys.append(content_hash)
        
        for key in expired_keys:
            del self._content_cache[key]
    
    def start(self) -> bool:
        """杂鱼♡～启动监控器喵～"""
        if self._is_running:
            print("杂鱼♡～监控器已经在运行了喵～")
            return False
        
        # 杂鱼♡～初始化异步执行器喵～
        self._init_async_executor()
        
        # 杂鱼♡～启动监控线程，在线程内创建窗口和设置监听器喵～
        self._stop_event.clear()
        self._window_creation_success = threading.Event()
        # 杂鱼♡～不使用daemon线程，确保消息循环能正确接收Windows消息喵～
        self._thread = threading.Thread(target=self._monitor_loop, daemon=False)
        self._thread.start()
        
        # 杂鱼♡～等待窗口创建完成喵～
        if not self._window_creation_success.wait(timeout=5.0):
            print("杂鱼♡～窗口创建超时了喵！")
            self.stop()
            return False
        
        if not self._hwnd:
            print("杂鱼♡～窗口创建失败了喵！")
            return False
        
        self._is_running = True
        print(f"杂鱼♡～剪贴板监控已启动喵～(异步模式：{self._async_processing}, 监控模式：{self._monitoring_mode})")
        return True
    
    def stop(self) -> None:
        """杂鱼♡～停止监控器喵～"""
        if not self._is_running:
            return
        
        print("杂鱼♡～正在停止监控器喵～")
        self._stop_event.set()
        
        # 杂鱼♡～如果窗口存在，发送WM_QUIT消息中断消息循环喵～
        if self._hwnd:
            try:
                # 杂鱼♡～发送WM_QUIT消息来中断GetMessageW的阻塞喵～
                from ci_board.utils.win32_api import Win32API
                Win32API.user32.PostMessageW(self._hwnd, 0x0012, 0, 0)  # WM_QUIT = 0x0012
            except Exception as e:
                print(f"杂鱼♡～发送退出消息失败喵：{e}")
        
        # 杂鱼♡～关闭异步执行器喵～
        self._shutdown_async_executor()
        
        # 杂鱼♡～等待线程退出，现在应该能正常退出了喵～
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)  # 杂鱼♡～增加超时时间喵～
            if self._thread.is_alive():
                print("杂鱼♡～线程在3秒内未能正常退出喵～")
        
        # 杂鱼♡～清理窗口资源喵～
        if self._hwnd:
            ClipboardUtils.remove_clipboard_listener(self._hwnd)
            ClipboardUtils.destroy_window(self._hwnd)
            self._hwnd = None
        
        self._is_running = False
        print("杂鱼♡～剪贴板监控已停止喵～")
    
    def wait(self) -> None:
        """杂鱼♡～等待监控器结束喵～"""
        if not self._is_running:
            return
        
        try:
            while self._is_running:
                if self._thread and self._thread.is_alive():
                    self._thread.join(0.25)
                else:
                    break
        except KeyboardInterrupt:
            print("杂鱼♡～被用户中断了喵～")
            self.stop()
            raise
    
    def _monitor_loop(self) -> None:
        """杂鱼♡～监控循环喵～"""
        try:
            # 杂鱼♡～在消息循环线程中创建窗口和设置监听器喵～
            print("杂鱼♡～在监控线程中创建窗口喵～")
            self._hwnd = ClipboardUtils.create_hidden_window("NekoClipboardMonitor")
            if not self._hwnd:
                print("杂鱼♡～创建监控窗口失败了喵！")
                self._window_creation_success.set()
                return
            
            # 杂鱼♡～定义剪贴板更新回调函数喵～
            def clipboard_callback(message: int, wParam: int, lParam: int) -> None:
                from ci_board.utils.win32_api import Win32API
                if message == Win32API.WM_CLIPBOARDUPDATE:
                    print("杂鱼♡～收到剪贴板更新消息喵～")
                    self._on_clipboard_update()
            
            # 杂鱼♡～添加剪贴板监听器和回调喵～
            if not ClipboardUtils.add_clipboard_listener(self._hwnd, clipboard_callback):
                print("杂鱼♡～添加剪贴板监听器失败了喵！")
                ClipboardUtils.destroy_window(self._hwnd)
                self._hwnd = None
                self._window_creation_success.set()
                return
            
            # 杂鱼♡～通知主线程窗口创建成功喵～
            self._window_creation_success.set()
            
            print(f"杂鱼♡～开始监控剪贴板变化喵～(模式：{self._monitoring_mode})")
            
            if self._event_driven:
                self._event_driven_monitor_loop()
            else:
                self._polling_monitor_loop()
                
        except Exception as e:
            print(f"杂鱼♡～监控循环初始化出错喵：{e}")
            self._window_creation_success.set()
        finally:
            print("杂鱼♡～停止监控剪贴板变化喵～")
    
    def _on_clipboard_update(self) -> None:
        """杂鱼♡～处理剪贴板更新事件喵～"""
        try:
            # 杂鱼♡～获取新内容和源信息喵～
            if self._enable_source_tracking:
                content_type, content, source_info = ClipboardUtils.get_clipboard_content(with_source=True)
                current_content = (content_type, content)
            else:
                content_type, content, source_info = ClipboardUtils.get_clipboard_content(with_source=False)
                current_content = (content_type, content)
                source_info = None
            
            if current_content[0] is not None:  # 杂鱼♡～确保有有效内容喵～
                # 杂鱼♡～检查是否为重复内容喵～
                if not self._is_content_duplicate(current_content):
                    self._handle_clipboard_change(current_content, source_info)
                    self._last_content = current_content
                    
        except Exception as e:
            print(f"杂鱼♡～处理剪贴板更新时出错喵：{e}")
    
    def _event_driven_monitor_loop(self) -> None:
        """杂鱼♡～事件驱动监控循环（推荐）喵～"""
        print("杂鱼♡～使用事件驱动模式，等待剪贴板更新消息喵～")
        print("杂鱼♡～现在使用混合模式：阻塞等待消息但定期检查停止事件喵～")
        
        # 杂鱼♡～混合事件驱动循环：使用短超时的阻塞消息等待+定期检查停止事件喵～
        while not self._stop_event.is_set():
            try:
                # 杂鱼♡～使用短超时阻塞等待消息，这样可以更好地接收剪贴板消息喵～
                # 杂鱼♡～timeout_ms=50表示最多等待50毫秒，然后检查停止事件喵～
                message_received = ClipboardUtils.pump_messages(self._hwnd, None, 50)
                
                # 杂鱼♡～如果没有收到消息，稍微休息一下再继续喵～
                if not message_received:
                    time.sleep(0.01)  # 杂鱼♡～10毫秒喵～
                
            except Exception as e:
                print(f"杂鱼♡～事件驱动循环出错了喵：{e}")
                time.sleep(0.1)
    
    def _polling_monitor_loop(self) -> None:
        """杂鱼♡～轮询监控循环（兼容模式）喵～"""
        print("杂鱼♡～使用轮询模式，定期检查剪贴板变化喵～")
        
        # 杂鱼♡～获取初始序列号喵～
        current_seq = ClipboardUtils.get_clipboard_sequence_number()
        self._last_sequence_number = current_seq
        
        while not self._stop_event.is_set():
            try:
                # 杂鱼♡～使用序列号检测变化，更高效更准确喵～
                current_seq = ClipboardUtils.get_clipboard_sequence_number()
                
                if current_seq != self._last_sequence_number:
                    # 杂鱼♡～序列号变化了，获取新内容和源信息喵～
                    if self._enable_source_tracking:
                        # 杂鱼♡～使用增强版本获取内容和源信息喵～
                        content_type, content, source_info = ClipboardUtils.get_clipboard_content(with_source=True)
                        current_content = (content_type, content)
                    else:
                        # 杂鱼♡～只获取内容，不获取源信息喵～
                        content_type, content, source_info = ClipboardUtils.get_clipboard_content(with_source=False)
                        current_content = (content_type, content)
                        source_info = None
                    
                    if current_content[0] is not None:  # 杂鱼♡～确保有有效内容喵～
                        # 杂鱼♡～检查是否为重复内容喵～
                        if not self._is_content_duplicate(current_content):
                            self._handle_clipboard_change(current_content, source_info)
                            self._last_content = current_content
                        
                        self._last_sequence_number = current_seq
                
                # 杂鱼♡～适当休息，避免CPU过度占用喵～
                time.sleep(0.05)  # 杂鱼♡～50ms检查间隔喵～
                
            except Exception as e:
                print(f"杂鱼♡～轮询循环出错了喵：{e}")
                time.sleep(0.1)  # 杂鱼♡～出错后稍微等久一点喵～
    
    def _handle_clipboard_change(self, content_data, source_info=None) -> None:
        """杂鱼♡～处理剪贴板变化喵～"""
        content_type, content = content_data
        
        # 杂鱼♡～触发更新处理器喵～
        for handler in self._handlers['update']:
            if self._async_processing:
                # 杂鱼♡～异步模式：将任务加入队列喵～
                self._task_queue.put((handler, content_data, source_info, 'update'))
            else:
                # 杂鱼♡～同步模式：直接执行喵～
                self._execute_handler_safely(handler, content_data, source_info, 'update')
        
        # 杂鱼♡～根据内容类型触发相应处理器喵～
        if content_type in self._handlers and content is not None:
            for handler in self._handlers[content_type]:
                if self._async_processing:
                    # 杂鱼♡～异步模式：将任务加入队列，每个处理器独立执行喵～
                    self._task_queue.put((handler, content, source_info, content_type))
                else:
                    # 杂鱼♡～同步模式：直接执行（保持向后兼容）喵～
                    self._execute_handler_safely(handler, content, source_info, content_type)
    
    def get_status(self) -> dict:
        """杂鱼♡～获取监控器状态喵～"""
        return {
            'is_running': self._is_running,
            'monitoring_mode': self._monitoring_mode,  # 杂鱼♡～显示监控模式喵～
            'event_driven': self._event_driven,
            'handlers_count': {k: len(v) for k, v in self._handlers.items()},
            'last_content_type': self._last_content[0] if self._last_content else None,
            'last_sequence_number': self._last_sequence_number,
            'current_sequence_number': ClipboardUtils.get_clipboard_sequence_number() if self._is_running else None,
            'thread_alive': self._thread.is_alive() if self._thread else False,
            'last_content_hash': self._last_content_hash[:8] if self._last_content_hash else None,  # 杂鱼♡～显示哈希前8位喵～
            'cache_size': len(self._content_cache),
            'source_tracking_enabled': self._enable_source_tracking,  # 杂鱼♡～显示源追踪状态喵～
            'async_stats': self.get_async_stats()
        }
    
    def get_current_clipboard(self) -> tuple:
        """杂鱼♡～获取当前剪贴板内容喵～"""
        if self._enable_source_tracking:
            return ClipboardUtils.get_clipboard_content(with_source=True)
        else:
            content_type, content, source_info = ClipboardUtils.get_clipboard_content(with_source=False)
            return (content_type, content, source_info)
    
    def is_running(self) -> bool:
        """杂鱼♡～检查监控器是否在运行喵～"""
        return self._is_running

class SimpleUpdateHandler(BaseClipboardHandler):
    """杂鱼♡～简单的更新处理器喵～"""
    
    def __init__(self, callback=None):
        super().__init__(callback)
    
    def is_valid(self, data: Any) -> bool:
        return True
    
    def _default_handle(self, data: Any, source_info: Optional[Dict[str, Any]] = None) -> None:
        """杂鱼♡～默认的更新处理方法喵～"""
        content_type, content = data
        print(f"杂鱼♡～剪贴板内容更新了喵～类型：{content_type}")
        
        # 杂鱼♡～显示源应用程序信息喵～
        if source_info and self._include_source_info:
            print(f"  源应用程序：{source_info.get('process_name', 'Unknown')}")
            if source_info.get('process_path'):
                print(f"  程序路径：{source_info['process_path']}")
            if source_info.get('window_title'):
                print(f"  窗口标题：{source_info['window_title']}") 