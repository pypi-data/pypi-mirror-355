# 杂鱼♡～本喵的核心剪贴板监控器喵～
import hashlib
import json
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from ..interfaces.callback_interface import BaseClipboardHandler
from ..types.t_source import ProcessInfo
from ..utils.clipboard_utils import ClipboardUtils
from ..utils.logger import get_component_logger
from .source_tracker_ import SourceTracker


class ClipboardMonitor:
    """杂鱼♡～本喵设计的高扩展性剪贴板监控器喵～"""

    def __init__(
        self,
        async_processing: bool = True,
        max_workers: int = 4,
        handler_timeout: float = 30.0,
        event_driven: bool = True,
    ):
        # 杂鱼♡～初始化日志器喵～
        self.logger = get_component_logger("monitor")
        """
        杂鱼♡～初始化监控器喵～

        Args:
            async_processing: 是否启用异步处理模式
            max_workers: 处理器线程池最大工作线程数
            handler_timeout: 单个处理器超时时间（秒）
            event_driven: 是否启用事件驱动模式（推荐，更高效）
        """
        self._handlers: Dict[str, List[BaseClipboardHandler]] = {
            "text": [],
            "image": [],
            "files": [],
            "update": [],
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
        self._monitoring_mode = "event" if event_driven else "polling"

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
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_timeout": 0,
            "active_tasks": 0,
        }

    def enable_async_processing(self) -> None:
        """杂鱼♡～启用异步处理模式喵～"""
        self._async_processing = True

    def disable_async_processing(self) -> None:
        """杂鱼♡～禁用异步处理模式（回到同步模式）喵～"""
        self._async_processing = False

    def set_async_config(
        self, max_workers: int = 4, handler_timeout: float = 30.0
    ) -> None:
        """杂鱼♡～设置异步处理配置喵～"""
        self._max_workers = max_workers
        self._handler_timeout = handler_timeout

        # 杂鱼♡～如果正在运行，重新初始化线程池喵～
        if self._is_running and self._async_processing:
            self._restart_async_executor()

    def _restart_async_executor(self) -> None:
        """杂鱼♡～重启异步执行器喵～"""
        if self._executor:
            self.logger.info("杂鱼♡～重新启动异步执行器喵～")
            self._shutdown_async_executor()
            self._init_async_executor()

    def _init_async_executor(self) -> None:
        """杂鱼♡～初始化异步执行器喵～"""
        if not self._async_processing:
            return

        self.logger.info(
            f"杂鱼♡～初始化异步执行器，最大工作线程：{self._max_workers}，超时：{self._handler_timeout}s喵～"
        )
        self._executor = ThreadPoolExecutor(
            max_workers=self._max_workers, thread_name_prefix="NekoHandler"
        )
        self._executor_stop_event.clear()
        self._executor_thread = threading.Thread(
            target=self._async_executor_loop, daemon=True
        )
        self._executor_thread.start()

    def _shutdown_async_executor(self) -> None:
        """杂鱼♡～关闭异步执行器喵～"""
        if not self._executor:
            return

        self.logger.info("杂鱼♡～正在关闭异步执行器喵～")
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
                # 杂鱼♡～处理新任务喵～
                self._process_new_tasks(futures)

                # 杂鱼♡～检查并清理已完成的任务喵～
                self._check_and_cleanup_completed_tasks(futures)

                # 杂鱼♡～适当休息喵～
                time.sleep(0.01)

            except Exception as e:
                self.logger.error(f"杂鱼♡～异步执行器循环出错了喵：{e}")
                time.sleep(0.1)

        # 杂鱼♡～清理剩余任务喵～
        self._cleanup_remaining_futures(futures)

    def _process_new_tasks(self, futures: dict) -> None:
        """杂鱼♡～处理新任务喵～"""
        try:
            task = self._task_queue.get(timeout=0.1)
            if task is None:  # 杂鱼♡～关闭信号喵～
                return

            handler, content, source_info, content_type = task
            future = self._executor.submit(
                self._execute_handler_safely,
                handler,
                content,
                source_info,
                content_type,
            )
            futures[future] = (handler, content_type, time.time())
            self._async_stats["tasks_submitted"] += 1
            self._async_stats["active_tasks"] += 1

        except queue.Empty:
            pass

    def _check_and_cleanup_completed_tasks(self, futures: dict) -> None:
        """杂鱼♡～检查并清理已完成的任务喵～"""
        completed_futures = self._find_completed_and_timeout_futures(futures)

        for future in completed_futures:
            self._handle_completed_future(future, futures)

    def _find_completed_and_timeout_futures(self, futures: dict) -> list:
        """杂鱼♡～查找已完成和超时的任务喵～"""
        completed_futures = []

        for future in list(futures.keys()):
            if future.done():
                completed_futures.append(future)
            else:
                # 杂鱼♡～检查超时喵～
                handler, content_type, start_time = futures[future]
                if time.time() - start_time > self._handler_timeout:
                    self.logger.warning(f"杂鱼♡～处理器超时了喵：{type(handler).__name__} ({content_type})")
                    future.cancel()
                    completed_futures.append(future)
                    self._async_stats["tasks_timeout"] += 1

        return completed_futures

    def _handle_completed_future(self, future, futures: dict) -> None:
        """杂鱼♡～处理单个已完成的任务喵～"""
        try:
            if not future.cancelled():
                result = future.result()
                if result:
                    self._async_stats["tasks_completed"] += 1
                else:
                    self._async_stats["tasks_failed"] += 1
        except Exception as e:
            handler, content_type, _ = futures[future]
            self.logger.error(f"杂鱼♡～异步处理器出错了喵：{type(handler).__name__} ({content_type}) - {e}")
            self._async_stats["tasks_failed"] += 1
        finally:
            del futures[future]
            self._async_stats["active_tasks"] -= 1
            self._task_queue.task_done()

    def _cleanup_remaining_futures(self, futures: dict) -> None:
        """杂鱼♡～清理剩余任务喵～"""
        self.logger.info("杂鱼♡～异步执行器循环结束，清理剩余任务喵～")
        for future in futures.keys():
            future.cancel()

    def _convert_source_info_to_process_info(self, source_info: Optional[Dict[str, Any]]) -> Optional[ProcessInfo]:
        """杂鱼♡～将dict格式的source_info转换为ProcessInfo实例喵～"""
        if not source_info or not isinstance(source_info, dict):
            return None

        try:
            # 杂鱼♡～创建ProcessInfo实例，提供所有必需字段的默认值喵～
            return ProcessInfo(
                process_name=source_info.get('process_name', 'Unknown'),
                process_path=source_info.get('process_path', ''),
                process_id=source_info.get('process_id', 0),
                window_title=source_info.get('window_title', ''),
                window_class=source_info.get('window_class', ''),
                detection_method=source_info.get('detection_method', 'unknown'),
                confidence_level=source_info.get('confidence_level', 'unknown'),
                is_system_process=source_info.get('is_system_process', False),
                is_screenshot_tool=source_info.get('is_screenshot_tool', False),
                timestamp=source_info.get('timestamp', time.time())
            )
        except Exception as e:
            self.logger.error(f"杂鱼♡～转换source_info为ProcessInfo失败喵：{e}")
            return None

    def _execute_handler_safely(
        self,
        handler: BaseClipboardHandler,
        content: Any,
        source_info: Optional[Dict[str, Any]],
        content_type: str,
    ) -> bool:
        """杂鱼♡～安全执行处理器喵～"""
        try:
            if self._enable_source_tracking:
                # 杂鱼♡～将dict格式的source_info转换为ProcessInfo实例喵～
                process_info = self._convert_source_info_to_process_info(source_info)
                handler.handle(content, process_info)
            else:
                # 杂鱼♡～检查处理器是否支持源信息参数，向后兼容喵～
                import inspect

                if hasattr(handler, "handle"):
                    sig = inspect.signature(handler.handle)
                    if len(sig.parameters) >= 2:
                        handler.handle(content, None)
                    else:
                        handler.handle(content)
                else:
                    handler.handle(content)
            return True
        except Exception as e:
            self.logger.error(
                f"杂鱼♡～{content_type}处理器出错了喵：{type(handler).__name__} - {e}"
            )
            return False

    def get_async_stats(self) -> Dict[str, Any]:
        """杂鱼♡～获取异步处理统计信息喵～"""
        return {
            "async_enabled": self._async_processing,
            "max_workers": self._max_workers,
            "handler_timeout": self._handler_timeout,
            "executor_running": self._executor is not None,
            "queue_size": self._task_queue.qsize(),
            **self._async_stats,
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
        self._monitoring_mode = "event"
        self.logger.info("杂鱼♡～已切换到事件驱动模式，更高效喵～")

    def disable_event_driven_mode(self) -> None:
        """杂鱼♡～禁用事件驱动模式，回到轮询模式喵～"""
        self._event_driven = False
        self._monitoring_mode = "polling"
        self.logger.info("杂鱼♡～已切换到轮询模式，杂鱼主人确定要这样做吗？喵～")

    def add_handler(
        self,
        content_type: Literal["text", "image", "files", "update"],
        handler: Optional[Union[BaseClipboardHandler, Callable]] = None,
    ) -> BaseClipboardHandler:
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

        if handler is None:
            handler = self._create_handler_from_callback(content_type, None)

        self._handlers[content_type].append(handler)
        return handler

    def _create_handler_from_callback(
        self, content_type: str, callback: Optional[Callable] = None
    ) -> BaseClipboardHandler:
        """杂鱼♡～根据回调函数创建对应的处理器喵～"""
        # 杂鱼♡～延迟导入避免循环引用喵～
        if content_type == "text":
            from ..handlers.text_handler import TextHandler

            return TextHandler(callback)
        elif content_type == "image":
            from ..handlers.image_handler import ImageHandler

            return ImageHandler(callback)
        elif content_type == "files":
            from ..handlers.file_handler import FileHandler

            return FileHandler(callback)
        elif content_type == "update":
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
            if content_type == "text" and isinstance(content, str):
                # 杂鱼♡～文本内容直接哈希喵～
                return hashlib.md5(content.encode("utf-8")).hexdigest()
            elif content_type == "image" and isinstance(content, dict):
                # 杂鱼♡～图片内容使用更精确的指纹算法，专门处理多步骤重复问题喵～
                return self._calculate_image_fingerprint(content)
            elif content_type == "files" and isinstance(content, list):
                # 杂鱼♡～文件列表哈希喵～
                file_list = sorted(content)  # 杂鱼♡～排序确保一致性喵～
                return hashlib.md5(json.dumps(file_list).encode("utf-8")).hexdigest()
            else:
                # 杂鱼♡～其他类型转字符串哈希喵～
                return hashlib.md5(str(content).encode("utf-8")).hexdigest()
        except Exception as e:
            self.logger.error(f"杂鱼♡～计算内容哈希失败喵：{e}")
            # 杂鱼♡～如果哈希计算失败，返回时间戳确保不会误判重复喵～
            return hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()

    def _calculate_image_fingerprint(self, content: dict) -> str:
        """杂鱼♡～计算图片内容的精确指纹，专门用于识别多步骤处理的重复图片喵～"""
        try:
            # 杂鱼♡～基础特征：尺寸、位深度、格式喵～
            basic_features = {
                "width": content.get("width", 0),
                "height": content.get("height", 0),
                "bit_count": content.get("bit_count", 0),
                "type": content.get("type", ""),
                "format": content.get("format", ""),
            }

            # 杂鱼♡～快速特征哈希（用于第一阶段过滤）喵～
            basic_hash = hashlib.md5(
                json.dumps(basic_features, sort_keys=True).encode("utf-8")
            ).hexdigest()

            # 杂鱼♡～如果没有实际数据，只用基础特征喵～
            if not content.get("data"):
                return f"basic_{basic_hash}"

            data = content["data"]
            data_size = len(data) if isinstance(data, (bytes, bytearray)) else 0

            # 杂鱼♡～对于小图片，使用完整数据哈希喵～
            if data_size <= 4096:  # 杂鱼♡～4KB以下直接全量哈希喵～
                if isinstance(data, (bytes, bytearray)):
                    data_hash = hashlib.md5(data).hexdigest()
                else:
                    data_hash = hashlib.md5(str(data).encode()).hexdigest()
                return f"small_{basic_hash}_{data_hash}"

            # 杂鱼♡～对于大图片，使用多点采样策略避免多步骤处理的细微差异喵～
            sample_points = []

            # 杂鱼♡～采样策略：头部、中部、尾部 + 几个随机点喵～
            if isinstance(data, (bytes, bytearray)):
                # 杂鱼♡～头部样本（前512字节）喵～
                sample_points.append(data[:512])

                # 杂鱼♡～中部样本喵～
                mid_start = data_size // 2 - 256
                mid_end = data_size // 2 + 256
                if mid_start >= 0 and mid_end <= data_size:
                    sample_points.append(data[mid_start:mid_end])

                # 杂鱼♡～尾部样本（后512字节）喵～
                sample_points.append(data[-512:])

                # 杂鱼♡～固定位置采样（避免随机性导致不一致）喵～
                quarter_pos = data_size // 4
                three_quarter_pos = data_size * 3 // 4
                sample_points.append(data[quarter_pos:quarter_pos+256])
                sample_points.append(data[three_quarter_pos:three_quarter_pos+256])

                # 杂鱼♡～计算所有样本的组合哈希喵～
                combined_samples = b"".join(sample_points)
                data_fingerprint = hashlib.md5(combined_samples).hexdigest()

                # 杂鱼♡～加入数据大小作为额外特征喵～
                size_info = {"data_size": data_size, "sample_count": len(sample_points)}
                size_hash = hashlib.md5(json.dumps(size_info).encode()).hexdigest()

                return f"large_{basic_hash}_{data_fingerprint}_{size_hash}"
            else:
                # 杂鱼♡～非字节数据，转换为字符串处理喵～
                data_str = str(data)
                if len(data_str) > 2048:
                    # 杂鱼♡～长字符串也采用采样策略喵～
                    samples = [
                        data_str[:512],
                        data_str[len(data_str)//2-256:len(data_str)//2+256],
                        data_str[-512:]
                    ]
                    combined = "".join(samples)
                    data_hash = hashlib.md5(combined.encode()).hexdigest()
                else:
                    data_hash = hashlib.md5(data_str.encode()).hexdigest()

                return f"other_{basic_hash}_{data_hash}"

        except Exception as e:
            self.logger.error(f"计算图片指纹时出错: {e}")
            # 杂鱼♡～出错时回退到基础哈希喵～
            fallback = f"{content.get('width', 0)}x{content.get('height', 0)}_{content.get('bit_count', 0)}"
            return hashlib.md5(fallback.encode()).hexdigest()

    def _is_content_duplicate(self, content_data) -> bool:
        """杂鱼♡～检查内容是否重复喵～"""
        content_hash = self._calculate_content_hash(content_data)
        content_type, content = content_data

        # 杂鱼♡～检查是否与上次内容相同喵～
        if content_hash == self._last_content_hash:
            return True

        # 杂鱼♡～检查缓存中是否存在喵～
        if content_hash in self._content_cache:
            # 杂鱼♡～针对不同内容类型使用不同的时间窗口喵～
            last_time = self._content_cache[content_hash]
            current_time = time.time()
            time_diff = current_time - last_time

            # 杂鱼♡～图片内容使用更长的去重窗口，因为多步骤处理可能延迟较久喵～
            if content_type == "image":
                threshold = 3.0  # 杂鱼♡～图片3秒内的重复内容忽略喵～
                if time_diff < threshold:
                    self.logger.debug(f"检测到重复图片内容，时间差{time_diff:.2f}s < {threshold}s，已跳过处理")
                    return True
            else:
                threshold = 1.0  # 杂鱼♡～其他内容1秒内的重复内容忽略喵～
                if time_diff < threshold:
                    self.logger.debug(f"检测到重复{content_type}内容，时间差{time_diff:.2f}s < {threshold}s，已跳过处理")
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
            # 杂鱼♡～根据内容类型决定过期时间喵～
            if content_hash.startswith(("small_", "large_", "basic_", "other_")):
                # 杂鱼♡～图片内容缓存保留更久，应对多步骤处理的延迟喵～
                expire_time = 15.0  # 杂鱼♡～图片15秒后过期喵～
            else:
                # 杂鱼♡～其他内容10秒后过期喵～
                expire_time = 10.0

            if current_time - timestamp > expire_time:
                expired_keys.append(content_hash)

        if expired_keys:
            self.logger.debug(f"清理了{len(expired_keys)}个过期缓存项")
            for key in expired_keys:
                del self._content_cache[key]

    def start(self) -> bool:
        """杂鱼♡～启动监控器喵～"""
        if self._is_running:
            self.logger.warning("监控器已经在运行了")
            return False

        # 杂鱼♡～初始化智能源追踪器喵～
        if self._enable_source_tracking:
            self.logger.info("正在初始化集成式智能源追踪功能")

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
            self.logger.error("窗口创建超时了")
            self.stop()
            return False

        if not self._hwnd:
            self.logger.error("窗口创建失败了")
            return False

        self._is_running = True
        self.logger.info(
            f"剪贴板监控已启动 (异步模式：{self._async_processing}, 监控模式：{self._monitoring_mode})"
        )
        return True

    def stop(self) -> None:
        """杂鱼♡～停止监控器喵～"""
        if not self._is_running:
            return

        self.logger.info("正在停止监控器")
        self._stop_event.set()

        # 杂鱼♡～如果窗口存在，发送WM_QUIT消息中断消息循环喵～
        if self._hwnd:
            try:
                # 杂鱼♡～发送WM_QUIT消息来中断GetMessageW的阻塞喵～
                from ci_board.utils.win32_api import Win32API

                Win32API.user32.PostMessageW(
                    self._hwnd, 0x0012, 0, 0
                )  # WM_QUIT = 0x0012
            except Exception as e:
                self.logger.error(f"杂鱼♡～发送退出消息失败喵：{e}")

        # 杂鱼♡～关闭异步执行器喵～
        self._shutdown_async_executor()

        # 杂鱼♡～等待线程退出，现在应该能正常退出了喵～
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)  # 杂鱼♡～增加超时时间喵～
            if self._thread.is_alive():
                self.logger.warning("杂鱼♡～线程在3秒内未能正常退出喵～")

        # 杂鱼♡～清理智能源追踪器喵～
        if self._enable_source_tracking:
            self.logger.info("杂鱼♡～正在清理集成式智能源追踪功能喵～")
            SourceTracker.cleanup_focus_tracking()

        # 杂鱼♡～清理窗口资源喵～
        if self._hwnd:
            ClipboardUtils.remove_clipboard_listener(self._hwnd)
            ClipboardUtils.destroy_window(self._hwnd)
            self._hwnd = None

        self._is_running = False
        self.logger.info("杂鱼♡～剪贴板监控已停止喵～")

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
            self.logger.info("杂鱼♡～被用户中断了喵～")
            self.stop()
            raise

    def _monitor_loop(self) -> None:
        """杂鱼♡～监控循环喵～"""
        try:
            # 杂鱼♡～在消息循环线程中创建窗口和设置监听器喵～
            self.logger.info("杂鱼♡～在监控线程中创建窗口喵～")
            self._hwnd = ClipboardUtils.create_hidden_window("NekoClipboardMonitor")
            if not self._hwnd:
                self.logger.error("杂鱼♡～创建监控窗口失败了喵！")
                self._window_creation_success.set()
                return

            # 杂鱼♡～定义剪贴板更新回调函数喵～
            def clipboard_callback(message: int, wParam: int, lParam: int) -> None:
                from ci_board.utils.win32_api import Win32API

                if message == Win32API.WM_CLIPBOARDUPDATE:
                    self.logger.debug("收到剪贴板更新消息")
                    self._on_clipboard_update()

            # 杂鱼♡～添加剪贴板监听器和回调喵～
            if not ClipboardUtils.add_clipboard_listener(
                self._hwnd, clipboard_callback
            ):
                self.logger.error("杂鱼♡～添加剪贴板监听器失败了喵！")
                ClipboardUtils.destroy_window(self._hwnd)
                self._hwnd = None
                self._window_creation_success.set()
                return

            # 杂鱼♡～设置集成式焦点跟踪喵～
            if self._enable_source_tracking:
                if not SourceTracker.initialize_integrated_tracking(None):
                    self.logger.warning("杂鱼♡～警告：集成式焦点跟踪初始化失败喵～")

            # 杂鱼♡～通知主线程窗口创建成功喵～
            self._window_creation_success.set()

            self.logger.info(f"杂鱼♡～开始监控剪贴板变化喵～(模式：{self._monitoring_mode})")

            if self._event_driven:
                self._event_driven_monitor_loop()
            else:
                self._polling_monitor_loop()

        except Exception as e:
            self.logger.error(f"杂鱼♡～监控循环初始化出错喵：{e}")
            self._window_creation_success.set()
        finally:
            self.logger.info("杂鱼♡～停止监控剪贴板变化喵～")

    def _on_clipboard_update(self) -> None:
        """杂鱼♡～处理剪贴板更新事件喵～"""
        try:
            # 杂鱼♡～检查序列号变化，避免处理重复消息喵～
            current_seq = ClipboardUtils.get_clipboard_sequence_number()
            if current_seq == self._last_sequence_number:
                # 杂鱼♡～序列号没变化，可能是重复消息，跳过处理喵～
                return

            # 杂鱼♡～检测内容类型，为图片内容增加额外延迟喵～
            content_type_detected = ClipboardUtils.detect_content_type()
            if content_type_detected == "image":
                # 杂鱼♡～图片内容需要更多时间准备，稍微等待一下喵～
                time.sleep(0.05)  # 杂鱼♡～50ms延迟，让剪贴板完全准备好喵～

            # 杂鱼♡～获取新内容和源信息喵～
            if self._enable_source_tracking:
                # 杂鱼♡～使用统一的源追踪器，避免剪贴板访问竞争喵～
                content_type, content, source_info = ClipboardUtils.get_clipboard_content(with_source=True)
                current_content = (content_type, content)
            else:
                content_type, content, source_info = (
                    ClipboardUtils.get_clipboard_content(with_source=False)
                )
                current_content = (content_type, content)
                source_info = None

            if current_content[0] is not None:  # 杂鱼♡～确保有有效内容喵～
                # 杂鱼♡～检查是否为重复内容喵～
                if not self._is_content_duplicate(current_content):
                    self._handle_clipboard_change(current_content, source_info)
                    self._last_content = current_content
                    self._last_sequence_number = current_seq

        except Exception as e:
            self.logger.error(f"杂鱼♡～处理剪贴板更新时出错喵：{e}")

    def _event_driven_monitor_loop(self) -> None:
        """杂鱼♡～事件驱动监控循环（推荐）喵～"""
        self.logger.info("杂鱼♡～使用事件驱动模式，等待剪贴板更新消息喵～")
        self.logger.info("杂鱼♡～现在使用混合模式：阻塞等待消息但定期检查停止事件喵～")

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
                self.logger.error(f"杂鱼♡～事件驱动循环出错了喵：{e}")
                time.sleep(0.1)

    def _polling_monitor_loop(self) -> None:
        """杂鱼♡～轮询监控循环（兼容模式）喵～"""
        self.logger.info("杂鱼♡～使用轮询模式，定期检查剪贴板变化喵～")

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
                        # 杂鱼♡～使用统一的源追踪器，避免剪贴板访问竞争喵～
                        content_type, content, _ = ClipboardUtils.get_clipboard_content(with_source=False)
                        current_content = (content_type, content)
                        # 杂鱼♡～安全获取源信息，避免剪贴板访问冲突喵～
                        source_info = SourceTracker.get_source_info(avoid_clipboard_access=True)
                    else:
                        # 杂鱼♡～只获取内容，不获取源信息喵～
                        content_type, content, source_info = (
                            ClipboardUtils.get_clipboard_content(with_source=False)
                        )
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
                self.logger.error(f"杂鱼♡～轮询循环出错了喵：{e}")
                time.sleep(0.1)  # 杂鱼♡～出错后稍微等久一点喵～

    def _handle_clipboard_change(self, content_data, source_info=None) -> None:
        """杂鱼♡～处理剪贴板变化喵～"""
        content_type, content = content_data

        # 杂鱼♡～触发更新处理器喵～
        for handler in self._handlers["update"]:
            if self._async_processing:
                # 杂鱼♡～异步模式：将任务加入队列喵～
                self._task_queue.put((handler, content_data, source_info, "update"))
            else:
                # 杂鱼♡～同步模式：直接执行喵～
                self._execute_handler_safely(
                    handler, content_data, source_info, "update"
                )

        # 杂鱼♡～根据内容类型触发相应处理器喵～
        if content_type in self._handlers and content is not None:
            for handler in self._handlers[content_type]:
                if self._async_processing:
                    # 杂鱼♡～异步模式：将任务加入队列，每个处理器独立执行喵～
                    self._task_queue.put((handler, content, source_info, content_type))
                else:
                    # 杂鱼♡～同步模式：直接执行（保持向后兼容）喵～
                    self._execute_handler_safely(
                        handler, content, source_info, content_type
                    )

    def get_status(self) -> dict:
        """杂鱼♡～获取监控器状态喵～"""
        return {
            "is_running": self._is_running,
            "monitoring_mode": self._monitoring_mode,  # 杂鱼♡～显示监控模式喵～
            "event_driven": self._event_driven,
            "handlers_count": {k: len(v) for k, v in self._handlers.items()},
            "last_content_type": self._last_content[0] if self._last_content else None,
            "last_sequence_number": self._last_sequence_number,
            "current_sequence_number": (
                ClipboardUtils.get_clipboard_sequence_number()
                if self._is_running
                else None
            ),
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "last_content_hash": (
                self._last_content_hash[:8] if self._last_content_hash else None
            ),  # 杂鱼♡～显示哈希前8位喵～
            "cache_size": len(self._content_cache),
            "source_tracking_enabled": self._enable_source_tracking,  # 杂鱼♡～显示源追踪状态喵～
            "focus_tracking_status": (
                SourceTracker.get_focus_status()
            ),  # 杂鱼♡～显示焦点跟踪状态喵～
            "async_stats": self.get_async_stats(),
        }

    def get_current_clipboard(self) -> tuple:
        """杂鱼♡～获取当前剪贴板内容喵～"""
        if self._enable_source_tracking:
            # 杂鱼♡～使用统一的源追踪器，避免剪贴板访问竞争喵～
            content_type, content, _ = ClipboardUtils.get_clipboard_content(with_source=False)
            source_info = SourceTracker.get_source_info(avoid_clipboard_access=True)
            return (content_type, content, source_info)
        else:
            content_type, content, source_info = ClipboardUtils.get_clipboard_content(
                with_source=False
            )
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

    def _default_handle(
        self, data: Any, source_info: Optional[ProcessInfo] = None
    ) -> None:
        """杂鱼♡～默认的更新处理方法喵～"""
        content_type, content = data
        self.logger.info(f"杂鱼♡～剪贴板内容更新了喵～类型：{content_type}")

        # 杂鱼♡～显示源应用程序信息喵～
        if source_info and self._include_source_info:
            self.logger.info(f"  源应用程序：{source_info.process_name or 'Unknown'}")
            if source_info.process_path:
                self.logger.info(f"  程序路径：{source_info.process_path}")
            if source_info.window_title:
                self.logger.info(f"  窗口标题：{source_info.window_title}")
