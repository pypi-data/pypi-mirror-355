# 杂鱼♡～本喵的源信息类型定义喵～
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ProcessInfo:
    """杂鱼♡～进程信息喵～"""
    name: str
    pid: int
    path: str


@dataclass
class WindowInfo:
    """杂鱼♡～窗口信息喵～"""
    title: str
    hwnd: int
    class_name: str


@dataclass
class FocusEvent:
    """杂鱼♡～焦点事件喵～"""
    timestamp: float
    process_info: ProcessInfo
    window_info: WindowInfo


@dataclass
class SourceInfo:
    """杂鱼♡～剪贴板源信息喵～"""
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
    additional_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}
