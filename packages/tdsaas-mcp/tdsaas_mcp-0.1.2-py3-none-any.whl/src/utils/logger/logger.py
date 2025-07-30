import os
import sys
import time
import functools
from loguru import logger

# 全局日志对象
_logger = None
_log_level = "INFO"  # 默认日志级别

def get_root_dir():
    """获取项目根目录"""
    # 当前文件路径
    current_file = os.path.abspath(__file__)
    # logger目录 -> utils目录 -> src目录 -> 项目根目录
    logger_dir = os.path.dirname(current_file)
    utils_dir = os.path.dirname(logger_dir)
    src_dir = os.path.dirname(utils_dir)
    root_dir = os.path.dirname(src_dir)
    return root_dir

def setup_logger(level=None, log_dir=None, log_name=None, console_output=True):
    """初始化日志系统
    
    Args:
        level: 日志级别，默认为INFO
        log_dir: 日志目录，默认为项目根目录下的logs目录
        log_name: 日志文件名前缀，默认为app
        console_output: 是否在控制台输出日志，默认为True
        
    Returns:
        logger: 日志对象
    """
    global _logger, _log_level
    
    # 如果已经初始化过，直接返回
    if _logger is not None:
        return _logger
    
    # 设置日志级别
    if level:
        _log_level = level
    
    # 创建日志目录
    if log_dir is None:
        # 使用辅助函数获取项目根目录
        root_dir = get_root_dir()
        log_dir = os.path.join(root_dir, "logs")
    
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成日志文件名，格式为 前缀_年月日.log
    log_prefix = log_name or "app"
    log_filename = os.path.join(log_dir, f"{log_prefix}_{time.strftime('%Y%m%d')}.log")
    
    # 配置日志
    logger.remove()  # 移除默认处理器
    
    # 添加控制台处理器（如果console_output为True）
    if console_output:
        logger.add(
            sys.stdout, 
            level=_log_level, 
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
    
    # 添加文件处理器
    logger.add(
        log_filename, 
        rotation="00:00",  # 每天零点创建新文件
        retention="30 days",  # 保留30天的日志
        level="DEBUG", 
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}", 
        encoding="utf-8",
        compression="zip"  # 压缩历史日志
    )
    
    _logger = logger
    
    return logger

def get_logger(console_output=True):
    """获取日志对象，如果未初始化则初始化
    
    Args:
        console_output: 是否在控制台输出日志，默认为True
        
    Returns:
        logger: 日志对象
    """
    global _logger
    if _logger is None:
        return setup_logger(console_output=console_output)
    return _logger

def set_level(level, console_output=None):
    """设置日志级别
    
    Args:
        level: 日志级别，可以是DEBUG, INFO, WARNING, ERROR, CRITICAL
        console_output: 是否在控制台输出日志，None表示保持当前设置
    """
    global _log_level, _logger
    _log_level = level
    
    # 重新初始化日志系统
    if _logger is not None:
        # 如果console_output为None，获取当前设置
        current_console_output = True
        # 目前没有直接方法获取当前设置，所以我们在这里默认为True
        # 如果要精确控制，应该由调用者指定
        if console_output is not None:
            current_console_output = console_output
        
        setup_logger(level=level, console_output=current_console_output)

# 快捷日志函数
def debug(msg, *args, **kwargs):
    console_output = kwargs.pop('console_output', True) if 'console_output' in kwargs else True
    return get_logger(console_output=console_output).debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    console_output = kwargs.pop('console_output', True) if 'console_output' in kwargs else True
    return get_logger(console_output=console_output).info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    console_output = kwargs.pop('console_output', True) if 'console_output' in kwargs else True
    return get_logger(console_output=console_output).warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    console_output = kwargs.pop('console_output', True) if 'console_output' in kwargs else True
    return get_logger(console_output=console_output).error(msg, *args, **kwargs)
    
def critical(msg, *args, **kwargs):
    console_output = kwargs.pop('console_output', True) if 'console_output' in kwargs else True
    return get_logger(console_output=console_output).critical(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    console_output = kwargs.pop('console_output', True) if 'console_output' in kwargs else True
    return get_logger(console_output=console_output).exception(msg, *args, **kwargs)

# 日志装饰器
def log_function(func=None, *, level="DEBUG", console_output=True):
    """函数调用日志装饰器
    
    用法:
        @log_function
        def my_function(args):
            pass
            
        @log_function(level="INFO")
        def my_function(args):
            pass
            
        @log_function(level="INFO", console_output=False)
        def my_function(args):
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(console_output=console_output)
            log_method = getattr(logger, level.lower())
            
            # 记录函数开始调用
            log_method(f"开始调用函数: {func.__name__}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                # 记录函数结束调用
                log_method(f"函数调用成功: {func.__name__}, 耗时: {end_time - start_time:.4f}秒")
                return result
            except Exception as e:
                end_time = time.time()
                # 记录函数调用异常
                logger.exception(f"函数调用异常: {func.__name__}, 耗时: {end_time - start_time:.4f}秒, 异常: {str(e)}")
                raise
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func) 