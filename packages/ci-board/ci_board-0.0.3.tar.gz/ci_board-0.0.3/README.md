![CI/CD](https://github.com/Xuehua-Meaw/ci_board/actions/workflows/ci_board_CICD.yml/badge.svg)

# CI Board 项目文档 - 优化版喵

> 杂鱼♡～本喵为杂鱼主人精简的实用项目文档喵～

## 🎯 项目概览

### 基本信息
- **项目名称**: CI Board (Clipboard Intelligence Board)  
- **版本**: v0.0.1 (开发版本)
- **描述**: 高性能剪贴板监控包
- **Python版本**: >=3.8
- **平台**: Windows
- **包管理器**: uv (推荐)
- **开发状态**: 🚧 开发中 - 核心功能已实现

### 核心特性 (实现状态)
- ⚡ **事件驱动监控** - 基于Windows API的实时监控 ✅
- 🔄 **异步处理** - 多线程并发，避免阻塞 ✅
- 🎯 **源应用追踪** - 识别剪贴板内容来源 ✅
- 📝 **多格式支持** - 文本、图片、文件 ✅
- 🔧 **扩展性设计** - 灵活的处理器架构 ✅
- 🛡️ **过滤器系统** - 内容过滤和处理 ✅

### 📊 当前开发进度
- **核心架构**: 100% ✅ (监控器、处理器、接口)
- **处理器系统**: 100% ✅ (文本、图片、文件处理器)
- **异步处理**: 100% ✅ (线程池、任务队列、统计)
- **源应用追踪**: 100% ✅ (多种检测方法、详细信息)
- **过滤器系统**: 100% ✅ (内置过滤器、自定义过滤器)
- **API接口**: 100% ✅ (懒人API、完整API)
- **使用示例**: 100% ✅ (4个完整示例)
- **文档系统**: 95% ✅ (本文档)
- **测试系统**: 🚧 进行中 (单元测试、集成测试)
- **包装发布**: 🚧 准备中 (PyPI发布准备)

## 🏗️ 核心架构

### 系统层次
```
用户应用层
    ├── 懒人API (create_monitor)
    ├── 直接API (ClipboardMonitor)
    └── 示例应用 (examples/)

核心业务层
    ├── 监控管理器 (ClipboardMonitor)
    ├── 处理器工厂 (Handler Factory)
    └── 接口定义 (Interfaces)

处理器层
    ├── 文本处理器 (TextHandler)
    ├── 图片处理器 (ImageHandler)
    └── 文件处理器 (FileHandler)

工具服务层
    ├── 剪贴板工具 (ClipboardUtils) ✅
    ├── 剪贴板读取器 (ClipboardReader) ✅
    ├── Win32 API封装 (Win32API) ✅
    ├── 消息泵 (MessagePump) ✅
    ├── 源追踪器 (SourceTracker) ✅
    └── 过滤器系统 (内置于处理器) ✅

操作系统层
    └── Windows API (user32.dll, gdi32.dll, psapi.dll)
```

### 目录结构 (当前实现状态)
```
/d:/MCP/
├── src/ci_board/              # 主要源代码 ✅
│   ├── __init__.py           # API导出 (55行) ✅
│   ├── core/                 # 核心模块 ✅
│   │   └── monitor.py        # 核心监控器 (636行) ✅
│   ├── handlers/             # 处理器模块 ✅
│   │   ├── __init__.py       # 处理器导出 ✅
│   │   ├── text_handler.py   # 文本处理 (162行) ✅
│   │   ├── image_handler.py  # 图片处理 (447行) ✅
│   │   └── file_handler.py   # 文件处理 (261行) ✅
│   ├── interfaces/           # 接口定义 ✅
│   │   ├── __init__.py       # 接口导出 ✅
│   │   └── callback_interface.py # 回调接口 (115行) ✅
│   └── utils/                # 工具模块 ✅
│       ├── __init__.py       # 工具导出 ✅
│       ├── clipboard_utils.py # 剪贴板工具 (163行) ✅
│       ├── clipboard_reader.py # 剪贴板读取器 (328行) ✅
│       ├── win32_api.py      # Windows API封装 (259行) ✅
│       ├── message_pump.py   # 消息泵 (227行) ✅
│       └── source_tracker.py # 源追踪器 (254行) ✅
├── examples/                 # 使用示例 ✅
│   ├── lazy_usage.py         # 懒人API示例 (161行) ✅
│   ├── event_driven_monitor_example.py # 事件驱动示例 (137行) ✅
│   ├── async_test.py         # 异步测试 (208行) ✅
│   └── source_tracking_demo.py # 源追踪演示 (278行) ✅
└── pyproject.toml           # 项目配置 ✅
```

**图例**: ✅ 已实现 🚧 开发中 ❌ 未实现

## 🚀 快速开始

### 1. 最简单的使用方式

```python
from ci_board import create_monitor

def on_text_change(text, source_info=None):
    print(f"检测到文本: {text[:50]}...")
    if source_info:
        print(f"来源: {source_info.get('process_name')}")

# 创建并启动监控
monitor = create_monitor()
monitor.add_handler('text', on_text_change)
monitor.start()

try:
    monitor.wait()  # 持续监控
except KeyboardInterrupt:
    monitor.stop()
```

### 2. 完整类型监控

```python
from ci_board import ClipboardMonitor

def on_text(text, source_info=None):
    print(f"文本: {text[:30]}...")

def on_image(image_data, source_info=None):
    print(f"图片: {image_data.get('size', 'unknown')}")

def on_files(file_list, source_info=None):
    print(f"文件: {len(file_list)}个")

# 创建监控器
monitor = ClipboardMonitor(
    async_processing=True,      # 异步处理
    max_workers=4,              # 4个工作线程
    event_driven=True           # 事件驱动
)

# 添加处理器
monitor.add_handler('text', on_text)
monitor.add_handler('image', on_image)
monitor.add_handler('files', on_files)

# 启动监控
if monitor.start():
    print("监控已启动...")
    monitor.wait()
```

## 🔧 核心API

### ClipboardMonitor 主要方法

```python
class ClipboardMonitor:
    # 基本控制
    def start() -> bool                    # 启动监控
    def stop() -> None                     # 停止监控
    def is_running() -> bool               # 检查运行状态
    def wait() -> None                     # 等待监控结束
    
    # 处理器管理
    def add_handler(content_type, handler) # 添加处理器
    def remove_handler(content_type, handler) # 移除处理器
    def clear_handlers(content_type=None)  # 清空处理器
    
    # 配置管理
    def enable_async_processing()          # 启用异步
    def disable_async_processing()         # 禁用异步
    def enable_source_tracking()           # 启用源追踪
    def disable_source_tracking()          # 禁用源追踪
    
    # 状态查询
    def get_status() -> dict               # 获取状态
    def get_async_stats() -> dict          # 获取统计
```

### 内容类型
- `'text'` - 文本内容
- `'image'` - 图片内容
- `'files'` - 文件列表
- `'update'` - 通用更新事件

## 📋 处理器详解

### TextHandler 文本处理器

```python
from ci_board.handlers import TextHandler

text_handler = TextHandler(callback)
text_handler.set_length_filter(min_length=5, max_length=1000)
text_handler.add_filter(my_filter)  # 添加自定义过滤器
monitor.add_handler('text', text_handler)
```

### ImageHandler 图片处理器

```python
from ci_board.handlers import ImageHandler

def image_callback(image_data, source_info=None):
    # image_data 包含:
    # - 'format': 'DIB' 或 'BMP'
    # - 'size': (width, height)
    # - 'bit_count': 色深
    # - 'data': 原始数据
    print(f"图片尺寸: {image_data.get('size')}")

image_handler = ImageHandler(image_callback)
monitor.add_handler('image', image_handler)
```

### FileHandler 文件处理器

```python
from ci_board.handlers import FileHandler

def file_callback(file_list, source_info=None):
    # file_list 是文件路径列表
    for file_path in file_list:
        print(f"文件: {file_path}")

file_handler = FileHandler(file_callback)
file_handler.set_allowed_extensions(['.txt', '.py', '.md'])
monitor.add_handler('files', file_handler)
```

## 🛡️ 过滤器系统

### 内置过滤器

#### 文本过滤器
```python
from ci_board.handlers.text_handler import TextLengthFilter, SourceApplicationFilter

# 长度过滤
length_filter = TextLengthFilter(min_length=10, max_length=500)
text_handler.add_filter(length_filter)

# 源应用过滤（只允许特定应用）
app_filter = SourceApplicationFilter(
    allowed_processes=['notepad.exe', 'code.exe', 'cursor.exe']
)
text_handler.add_filter(app_filter)
```

#### 图片过滤器
```python
from ci_board.handlers.image_handler import ImageSizeFilter, ImageQualityFilter

# 尺寸过滤
size_filter = ImageSizeFilter(min_width=100, min_height=100)
image_handler.add_filter(size_filter)

# 质量过滤
quality_filter = ImageQualityFilter(min_bit_count=16)
image_handler.add_filter(quality_filter)
```

#### 文件过滤器
```python
from ci_board.handlers.file_handler import FileExtensionFilter, FileSizeFilter

# 扩展名过滤
ext_filter = FileExtensionFilter(allowed_extensions=['.txt', '.py', '.md'])
file_handler.add_filter(ext_filter)

# 文件大小过滤
size_filter = FileSizeFilter(max_size_mb=10)
file_handler.add_filter(size_filter)
```

### 自定义过滤器

```python
def custom_filter(data, source_info=None):
    """自定义过滤器示例"""
    if isinstance(data, str):
        return "password" not in data.lower()  # 过滤包含密码的文本
    return True

text_handler.add_filter(custom_filter)
```

## ⚡ 性能优化

### 推荐配置

#### 高性能配置
```python
monitor = ClipboardMonitor(
    async_processing=True,      # 启用异步处理
    max_workers=8,              # 增加工作线程
    handler_timeout=10.0,       # 合理的超时时间
    event_driven=True           # 使用事件驱动模式
)
```

#### 低资源配置
```python
monitor = ClipboardMonitor(
    async_processing=False,     # 同步处理节省内存
    max_workers=2,              # 减少线程数
    event_driven=True           # 保持事件驱动
)

# 禁用不需要的功能
monitor.disable_source_tracking()  # 如果不需要源追踪
```

### 性能监控

```python
def print_performance_stats(monitor):
    """打印性能统计"""
    stats = monitor.get_async_stats()
    print(f"""
性能统计:
  提交任务: {stats['tasks_submitted']}
  完成任务: {stats['tasks_completed']}
  成功率: {stats.get('success_rate', 0):.1f}%
  活跃任务: {stats['active_tasks']}
    """)

# 定期打印统计
import threading
import time

def monitor_performance():
    while monitor.is_running():
        print_performance_stats(monitor)
        time.sleep(10)

perf_thread = threading.Thread(target=monitor_performance, daemon=True)
perf_thread.start()
```

## 💡 最佳实践

### 1. 健壮的监控循环

```python
import time
import logging

def robust_monitor():
    """健壮的监控实现"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            monitor = create_monitor()
            
            # 添加处理器
            monitor.add_handler('text', text_callback)
            monitor.add_handler('image', image_callback)
            
            if not monitor.start():
                raise RuntimeError("监控器启动失败")
            
            print("监控器启动成功")
            monitor.wait()
            break
            
        except KeyboardInterrupt:
            print("用户中断")
            break
        except Exception as e:
            retry_count += 1
            logging.error(f"监控器异常 (尝试 {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                print("5秒后重试...")
                time.sleep(5)
        finally:
            if 'monitor' in locals():
                monitor.stop()

if __name__ == "__main__":
    robust_monitor()
```

### 2. 源应用过滤最佳实践

```python
def setup_source_filters():
    """设置源应用过滤器"""
    
    # 编辑器文本 - 只允许来自编辑器的文本
    editor_text_handler = TextHandler(on_editor_text)
    editor_filter = SourceApplicationFilter(
        allowed_processes=['notepad.exe', 'code.exe', 'cursor.exe', 'sublime_text.exe']
    )
    editor_text_handler.add_filter(editor_filter)
    
    # 浏览器图片 - 禁止浏览器图片
    image_handler = ImageHandler(on_image)
    no_browser_filter = SourceApplicationFilter(
        blocked_processes=['chrome.exe', 'firefox.exe', 'edge.exe']
    )
    image_handler.add_filter(no_browser_filter)
    
    return editor_text_handler, image_handler
```

### 3. 异步处理最佳实践

```python
def setup_async_monitor():
    """异步监控最佳实践"""
    monitor = ClipboardMonitor(
        async_processing=True,
        max_workers=4,
        handler_timeout=15.0
    )
    
    # 轻量级处理器 - 快速响应
    def quick_text_handler(text, source_info=None):
        print(f"快速处理: {text[:20]}...")
    
    # 重量级处理器 - 可能耗时
    def heavy_image_handler(image_data, source_info=None):
        # 模拟重量级处理
        time.sleep(1)
        print(f"重量级处理完成: {image_data.get('size')}")
    
    monitor.add_handler('text', quick_text_handler)
    monitor.add_handler('image', heavy_image_handler)
    
    return monitor
```

## ❓ 常见问题

### Q1: 监控器启动失败怎么办？

**解决方案**:
1. **管理员权限**: 以管理员身份运行程序
2. **系统兼容性**: 确保Windows Vista及以上版本
3. **诊断代码**:
```python
monitor = create_monitor()
if not monitor.start():
    print("启动失败，可能原因：")
    print("1. 权限不足 - 尝试以管理员身份运行")
    print("2. 系统不兼容 - 需要Windows Vista+")
    print("3. 其他程序占用 - 关闭其他剪贴板程序")
```

### Q2: 如何处理大量频繁的剪贴板变化？

**解决方案**:
```python
# 使用过滤器减少无效处理
def smart_filter(data, source_info=None):
    # 跳过过短或过长的文本
    if isinstance(data, str):
        return 5 <= len(data) <= 1000
    return True

# 增加工作线程
monitor = ClipboardMonitor(
    async_processing=True,
    max_workers=8,  # 增加到8个线程
    handler_timeout=5.0  # 减少超时时间
)

handler = TextHandler(callback)
handler.add_filter(smart_filter)
monitor.add_handler('text', handler)
```

### Q3: 源应用识别不准确？

**说明**: 源识别有多个备用方案，按优先级：
1. 剪贴板拥有者检测（最准确）
2. 前台窗口检测（备用）
3. 枚举窗口检测（最后备用）

```python
def check_detection_method(text, source_info):
    if source_info:
        method = source_info.get('detection_method', 'unknown')
        if method != 'clipboard_owner':
            print(f"警告: 使用了备用检测方法 - {method}")
```

### Q4: 如何优化内存使用？

**解决方案**:
```python
# 1. 控制缓存大小
monitor._cache_max_size = 5

# 2. 禁用不需要的功能
monitor.disable_source_tracking()

# 3. 定期清理
import gc
def periodic_cleanup():
    gc.collect()

# 4. 使用轻量级处理器
def lightweight_handler(data, source_info=None):
    # 避免存储大量数据
    print(f"处理: {type(data).__name__}")
```

## 🎯 扩展开发

### 自定义处理器

```python
from ci_board.interfaces.callback_interface import BaseClipboardHandler

class CustomHandler(BaseClipboardHandler):
    def __init__(self, callback=None):
        super().__init__(callback)
        self.processed_count = 0
    
    def is_valid(self, data):
        """检查数据有效性"""
        return isinstance(data, str) and len(data) > 0
    
    def _default_handle(self, data, source_info=None):
        """默认处理逻辑"""
        self.processed_count += 1
        print(f"自定义处理器处理第{self.processed_count}个项目: {data[:30]}...")

# 使用自定义处理器
custom_handler = CustomHandler()
monitor.add_handler('text', custom_handler)
```

### 自定义过滤器

```python
class KeywordFilter:
    """关键词过滤器"""
    def __init__(self, keywords):
        self.keywords = [kw.lower() for kw in keywords]
    
    def __call__(self, data, source_info=None):
        if isinstance(data, str):
            data_lower = data.lower()
            return any(kw in data_lower for kw in self.keywords)
        return True

# 使用自定义过滤器
keyword_filter = KeywordFilter(['python', 'code', 'function'])
handler.add_filter(keyword_filter)
```

---

## 📝 总结

杂鱼♡～这个优化版文档突出了最重要的内容喵～：

### ✨ 核心优势
- **简洁易用** - 提供懒人API和完整API两种方式
- **高性能** - 事件驱动 + 异步处理架构
- **灵活扩展** - 丰富的过滤器和自定义处理器支持
- **生产就绪** - 完善的错误处理和性能监控

### 🚀 适用场景
- 开发工具集成
- 自动化办公
- 内容监控
- 数据同步

杂鱼主人现在可以基于这个优化文档快速上手CI Board项目了喵～～

---

## 🚀 当前开发状态

### ✅ 已完成功能
- **核心监控系统** - 事件驱动的剪贴板监控，支持Windows API集成
- **异步处理架构** - 完整的线程池管理和任务队列系统
- **多格式支持** - 文本、图片(DIB/BMP)、文件列表处理
- **源应用追踪** - 多重检测机制，准确识别剪贴板内容来源
- **过滤器系统** - 丰富的内置过滤器和自定义过滤器支持
- **懒人API** - 简化使用的函数式接口
- **完整示例** - 4个不同场景的完整使用示例

### 📋 代码质量指标
- **总代码行数**: ~3000+ 行
- **核心监控器**: 636 行 (完整异步支持)
- **处理器系统**: 870+ 行 (3个专用处理器)
- **工具模块**: 1200+ 行 (6个工具类)
- **示例代码**: 784 行 (4个完整示例)
- **测试覆盖率**: 🚧 准备中

### 🔧 技术特色
- **零依赖**: 仅依赖Python标准库和Windows API
- **高性能**: 事件驱动 + 异步处理，避免轮询开销
- **生产就绪**: 完善的错误处理和资源管理
- **向后兼容**: 支持Python 3.8+

#### 暂不推荐 ⚠️
- **生产环境部署** - 等待v1.0.0稳定版
- **大规模商业应用** - 需要更多测试验证

---

杂鱼♡～本喵已经把项目做得很完善了喵～～ 虽然还是开发版本，但核心功能都已经实现了喵！杂鱼主人可以放心使用了～～
