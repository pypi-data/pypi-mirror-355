# 杂鱼♡～本喵的追踪器类型定义喵～
from dataclasses import dataclass


@dataclass
class ProcessInfo:
    """杂鱼♡～进程信息数据类喵～"""

    process_name: str
    process_path: str
    process_id: int
    window_title: str
    window_class: str
    detection_method: str
    confidence_level: str
    is_system_process: bool
    is_screenshot_tool: bool
    timestamp: float
