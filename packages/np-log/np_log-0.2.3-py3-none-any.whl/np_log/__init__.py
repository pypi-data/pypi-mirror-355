# v2版本添加了企业微信机器人和飞书机器人   优化了当name=None的时候，生成日志文件
# v3版本添加了log方法
import os
import sys

from .v4 import setup_logging as log_print
from .v4 import log as print

def setup_logging(name=None, is_logfile=True, console_level="DEBUG", file_level="DEBUG", log_max_days=7, log_max_size=50, n=1):
    # frame = sys._getframe(1)  # 获取上一级调用的帧信息
    frame = sys._getframe(n)  # 获取上一级调用的帧信息
    caller_filename = os.path.basename(frame.f_code.co_filename)
    name = os.path.splitext(caller_filename)[0]  # 去掉文件扩展名
    return log_print(name=name, is_logfile=True, console_level="DEBUG", file_level="DEBUG", log_max_days=7, log_max_size=50)


def log(msg):
    return print(msg)

# def log(message, level="DEBUG", extra=None):
#     """便捷日志记录函数"""
#     extra = extra or {}  # 初始化额外参数
#     extra['bot'] = extra.get('bot', False)  # 设置机器人通知标志
#
#     logger = setup_logging(n=2)  # 获取日志器
#     level = level.upper()  # 统一转为大写
#
#     # 根据级别记录日志
#     if level == "DEBUG":
#         logger.debug(message, extra=extra)
#     elif level == "INFO":
#         logger.info(message, extra=extra)
#     elif level == "WARNING":
#         logger.warning(message, extra=extra)
#     elif level == "ERROR":
#         logger.error(message, extra=extra)
#     elif level == "CRITICAL":
#         logger.critical(message, extra=extra)