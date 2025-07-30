# 杂鱼♡～本喵的图片类型定义喵～
from dataclasses import dataclass
from typing import Union


@dataclass
class BMPData:
    """杂鱼♡～BMP格式的图片数据喵～"""

    success: bool
    data: Union[bytes, None]
    width: int
    height: int
    bit_count: int
    timestamp: str
