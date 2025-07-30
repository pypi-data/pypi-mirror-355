# CI Board - 高性能剪贴板监控库

![CI/CD](https://github.com/Xuehua-Meaw/ci_board/actions/workflows/ci_board_CICD.yml/badge.svg)

> 杂鱼♡～本喵为杂鱼主人精心设计的Windows剪贴板监控库喵～

## 🎯 项目概览

**CI Board** (Clipboard Intelligence Board) 是一个高性能的Windows剪贴板监控Python库，支持实时监控文本、图片、文件等剪贴板内容变化，并能追踪内容来源应用程序。

### ✨ 核心特性
- 🔄 **实时监控** - 基于Windows API的事件驱动监控
- 📋 **多格式支持** - 文本、图片、文件列表
- 🎯 **源应用追踪** - 识别剪贴板内容来源程序
- ⚡ **异步处理** - 多线程并发处理
- 🛡️ **过滤器系统** - 灵活的内容过滤
- 🔌 **扩展性强** - 易于扩展的处理器架构
- 😺 **懒人API** - 简单易用的快速接口

### 📊 项目信息
- **版本**: v0.0.7
- **Python版本**: >=3.8
- **平台**: Windows
- **依赖**: 纯Python，无第三方依赖
- **许可证**: MIT

## 🚀 快速开始

### 安装

```bash
# 杂鱼♡～推荐使用uv包管理器喵～
uv add ci-board

# 或者使用pip
pip install ci-board
```

### 懒人API - 30秒上手

```python
# 杂鱼♡～最简单的使用方式喵～
from ci_board import create_monitor

def on_text_change(text, source_info):
    print(f"文本变化: {text[:50]}...")
    print(f"来源: {source_info.process_name}")

def on_image_change(bmp_data, source_info):
    print(f"图片变化: {bmp_data.width}x{bmp_data.height}")

# 创建监控器
monitor = create_monitor()

# 添加处理器（懒人方式）
monitor.add_handler('text', on_text_change)
monitor.add_handler('image', on_image_change)

# 启动监控
monitor.start()
try:
    monitor.wait()  # 持续监控
except KeyboardInterrupt:
    monitor.stop()
    print("监控结束")
```

### 完整API示例

```python
from ci_board import ClipboardMonitor

# 创建配置完整的监控器
monitor = ClipboardMonitor(
    async_processing=True,      # 异步处理
    max_workers=4,              # 线程池大小
    event_driven=True,          # 事件驱动模式
    handler_timeout=10.0        # 处理器超时
)

def handle_text(text, source_info):
    """处理文本内容"""
    if source_info:
        print(f"[{source_info.process_name}] {text[:100]}")

def handle_image(bmp_data, source_info):
    """处理图片内容"""
    if bmp_data.success:
        print(f"图片: {bmp_data.width}x{bmp_data.height}, {len(bmp_data.data)}字节")
        # 可以保存图片
        # with open("clipboard.bmp", "wb") as f:
        #     f.write(bmp_data.data)

def handle_files(file_list, source_info):
    """处理文件列表"""
    print(f"文件: {len(file_list)}个")
    for file_path in file_list:
        print(f"  - {file_path}")

# 注册处理器
monitor.add_handler('text', handle_text)
monitor.add_handler('image', handle_image)
monitor.add_handler('files', handle_files)

# 启动监控
if monitor.start():
    print("监控已启动，复制内容进行测试...")
    monitor.wait()
```

## 📋 API文档

### ClipboardMonitor 核心类

```python
class ClipboardMonitor:
    def __init__(self, 
                 async_processing=True,     # 是否异步处理
                 max_workers=4,             # 线程池大小
                 event_driven=True,         # 事件驱动模式
                 handler_timeout=10.0):     # 处理器超时
    
    # 基本控制
    def start() -> bool                     # 启动监控
    def stop() -> None                      # 停止监控
    def is_running() -> bool                # 检查运行状态
    def wait() -> None                      # 等待监控结束
    
    # 处理器管理
    def add_handler(content_type, callback) # 添加处理器
    def remove_handler(content_type, handler) # 移除处理器
    def clear_handlers(content_type=None)   # 清空处理器
    
    # 配置管理
    def enable_source_tracking()            # 启用源追踪
    def disable_source_tracking()           # 禁用源追踪
    def get_status() -> dict                # 获取状态信息
```

### 内容类型

| 类型 | 描述 | 回调参数 |
|------|------|----------|
| `'text'` | 文本内容 | `(text: str, source_info: ProcessInfo)` |
| `'image'` | 图片内容 | `(bmp_data: BMPData, source_info: ProcessInfo)` |
| `'files'` | 文件列表 | `(file_list: List[str], source_info: ProcessInfo)` |

### 数据结构

```python
# 进程信息
class ProcessInfo:
    process_name: str       # 进程名称
    process_path: str       # 进程路径
    process_id: int         # 进程ID
    window_title: str       # 窗口标题

# BMP图片数据
class BMPData:
    success: bool           # 转换是否成功
    data: bytes            # BMP数据
    width: int             # 图片宽度
    height: int            # 图片高度
```

## 🛡️ 高级功能

### 过滤器系统

```python
from ci_board.handlers import TextHandler, ImageHandler

# 文本长度过滤
text_handler = TextHandler(callback)
text_handler.set_length_filter(min_length=10, max_length=1000)

# 源应用过滤
text_handler.set_source_filter(
    allowed_processes=['notepad.exe', 'code.exe']
)

# 图片尺寸过滤
image_handler = ImageHandler(callback)
image_handler.set_size_filter(min_width=100, min_height=100)

# 自定义过滤器
def custom_filter(data, source_info):
    return "password" not in data.lower()

text_handler.add_filter(custom_filter)
```

### 异步性能优化

```python
# 高性能配置
monitor = ClipboardMonitor(
    async_processing=True,
    max_workers=8,          # 更多工作线程
    handler_timeout=30.0    # 更长超时时间
)

# 查看性能统计
stats = monitor.get_async_stats()
print(f"处理任务: {stats['tasks_completed']}")
print(f"成功率: {stats.get('success_rate', 0):.1f}%")
```

## 📁 项目结构

```
ci_board/
├── core/                   # 核心模块
│   └── monitor.py         # 主监控器
├── handlers/              # 处理器
│   ├── text_handler.py    # 文本处理器
│   ├── image_handler.py   # 图片处理器
│   └── file_handler.py    # 文件处理器
├── interfaces/            # 接口定义
│   └── callback_interface.py
├── types/                 # 数据类型
│   ├── t_image.py         # 图片类型
│   └── t_source.py        # 源信息类型
└── utils/                 # 工具模块
    ├── clipboard_utils.py # 剪贴板工具
    ├── clipboard_reader.py # 剪贴板读取器
    ├── win32_api.py       # Windows API封装
    ├── message_pump.py    # 消息泵
    └── logger.py          # 日志工具
```

## 🔧 使用示例

### 保存剪贴板图片

```python
import os
from ci_board import create_monitor

def save_clipboard_image(bmp_data, source_info):
    if bmp_data.success:
        filename = f"clipboard_{int(time.time())}.bmp"
        with open(filename, "wb") as f:
            f.write(bmp_data.data)
        print(f"已保存图片: {filename}")

monitor = create_monitor()
monitor.add_handler('image', save_clipboard_image)
monitor.start()
monitor.wait()
```

### 文本内容记录

```python
from ci_board import create_monitor
import datetime

def log_text_content(text, source_info):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = source_info.process_name if source_info else "Unknown"
    
    with open("clipboard_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{source}] {text[:100]}\n")

monitor = create_monitor()
monitor.add_handler('text', log_text_content)
monitor.start()
monitor.wait()
```

## ❓ 常见问题

### Q: 监控器启动失败怎么办？
A: 确保以管理员权限运行，检查Windows版本兼容性（需要Vista及以上）。

### Q: 如何减少性能开销？
A: 使用过滤器减少不必要的处理，合理设置线程池大小。

### Q: 支持其他平台吗？
A: 目前只支持Windows平台，基于Windows API实现。

### Q: 如何处理大量剪贴板变化？
A: 启用异步处理，增加工作线程数，使用过滤器筛选内容。

## 📝 开发信息

- **作者**: StanleyUKN
- **邮箱**: stanley09537000@gmail.com
- **GitHub**: [ci_board](https://github.com/Xuehua-Meaw/ci_board)
- **许可证**: MIT License

## 💝 致谢

杂鱼♡～感谢所有使用本喵作品的杂鱼主人们喵～
如果觉得好用的话，给个Star吧～本喵会很开心的喵♡～
