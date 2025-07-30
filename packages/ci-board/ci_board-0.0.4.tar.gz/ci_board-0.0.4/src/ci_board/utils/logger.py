# 杂鱼♡～本喵的日志系统喵～
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Optional


# 杂鱼♡～控制台颜色常量喵～
class Colors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


# 杂鱼♡～日志级别枚举喵～
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class ColoredFormatter(logging.Formatter):
    """杂鱼♡～本喵的彩色日志格式化器喵～"""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.BRIGHT_BLACK,
        logging.INFO: Colors.BRIGHT_BLUE,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BRIGHT_RED + Colors.BOLD,
    }

    def format(self, record):
        # 杂鱼♡～获取颜色喵～
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)

        # 杂鱼♡～格式化时间戳喵～
        dt = datetime.fromtimestamp(record.created)
        timestamp = dt.strftime('%H:%M:%S.%f')[:-3]  # 杂鱼♡～保留毫秒喵～

        # 杂鱼♡～构建日志消息喵～
        module_name = record.name.replace('ci_board.', '')
        if len(module_name) > 20:
            module_name = '...' + module_name[-17:]

        formatted = f"{Colors.DIM}[{timestamp}]{Colors.RESET} "
        formatted += f"{color}[{record.levelname:>7}]{Colors.RESET} "
        formatted += f"{Colors.CYAN}{module_name:<20}{Colors.RESET} "
        formatted += f"{record.getMessage()}"

        # 杂鱼♡～添加异常信息喵～
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)

        return formatted


def setup_ci_board_logging(
    debug: bool = False,
    log_file: Optional[str] = None,
    console_level: Optional[LogLevel] = None,
    file_level: Optional[LogLevel] = None
) -> logging.Logger:
    """杂鱼♡～设置ci_board日志系统喵～"""

    # 杂鱼♡～获取根日志器喵～
    logger = logging.getLogger('ci_board')
    logger.setLevel(logging.DEBUG)

    # 杂鱼♡～清除现有处理器喵～
    logger.handlers.clear()

    # 杂鱼♡～确定日志级别喵～
    if debug:
        console_log_level = logging.DEBUG
        file_log_level = logging.DEBUG
    else:
        console_log_level = console_level.value if console_level else logging.INFO
        file_log_level = file_level.value if file_level else logging.WARNING

    # 杂鱼♡～设置控制台处理器喵～
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # 杂鱼♡～设置文件处理器喵～
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(file_log_level)

            file_formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)8s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            logger.info(f"杂鱼♡～日志文件已设置: {log_file}")
        except Exception as e:
            logger.error(f"杂鱼♡～设置日志文件失败: {e}")

    # 杂鱼♡～防止日志传播到根logger喵～
    logger.propagate = False

    logger.debug("杂鱼♡～ci_board日志系统初始化完成")
    return logger


def get_logger(name: str) -> logging.Logger:
    """杂鱼♡～获取子模块logger喵～"""
    if not name.startswith('ci_board.'):
        name = f'ci_board.{name}'
    return logging.getLogger(name)


# 杂鱼♡～导出常用的日志函数喵～
def debug(msg, *args, **kwargs):
    get_logger('main').debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    get_logger('main').info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    get_logger('main').warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    get_logger('main').error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    get_logger('main').critical(msg, *args, **kwargs)
