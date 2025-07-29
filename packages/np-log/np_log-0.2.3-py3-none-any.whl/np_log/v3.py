# 导入必要的模块
import datetime  # 日期时间处理
import logging  # Python标准日志模块
import logging.handlers  # 日志处理器
import os  # 操作系统接口
import sys  # 系统相关功能
import inspect  # 检查活动对象
import time  # 时间相关功能
import requests  # HTTP请求库
import json  # JSON处理


# 创建目录函数
def mkdir_dir(path):
    """创建多级目录"""
    if not os.path.exists(path):  # 检查路径是否存在
        os.makedirs(path)  # 创建目录
        return True  # 返回创建成功标志
    return False  # 目录已存在


# 自定义格式化器，能识别调用者信息
class CallerAwareFormatter(logging.Formatter):
    """自定义格式化器，自动识别真实调用者"""

    def format(self, record):
        """重写format方法，添加调用者信息"""
        # 获取当前调用栈帧
        frame = inspect.currentframe()
        try:
            # 遍历调用栈
            while frame:
                filename = frame.f_code.co_filename  # 获取当前帧文件名
                # 跳过logging模块、当前文件和__init__.py的帧
                if ('logging' not in filename and
                        'v3.py' not in filename and
                        not filename.endswith('__init__.py')):
                    # 设置记录的文件名和行号
                    record.filename = os.path.basename(filename)
                    record.lineno = frame.f_lineno
                    break
                frame = frame.f_back  # 获取上一帧
        finally:
            del frame  # 删除帧引用避免内存泄漏

        return super().format(record)  # 调用父类格式化方法


# 带颜色的格式化器，继承自CallerAwareFormatter
class ColorFormatter(CallerAwareFormatter):
    """带颜色的日志格式化器"""

    # 定义不同日志级别的颜色代码
    COLORS = {
        logging.DEBUG: "\033[36m",  # 青色
        logging.INFO: "\033[32m",  # 绿色
        logging.WARNING: "\033[33m",  # 黄色
        logging.ERROR: "\033[31m",  # 红色
        logging.CRITICAL: "\033[35m"  # 紫色
    }
    RESET = "\033[0m"  # 颜色重置代码

    def format(self, record):
        """重写format方法添加颜色"""
        message = super().format(record)  # 先获取格式化后的消息
        log_color = self.COLORS.get(record.levelno, "")  # 获取对应颜色
        return f"{log_color}{message}{self.RESET}"  # 添加颜色标记


# 机器人通知类
class Robot:
    """机器人通知类，支持微信和飞书"""

    def __init__(self, robot_type='all', max_retries=3, retry_delay=3):
        """初始化机器人"""
        self.robot_type = robot_type.lower()  # 机器人类型
        self.max_retries = max_retries  # 最大重试次数
        self.retry_delay = retry_delay  # 重试延迟(秒)
        self.webhook_urls = self._load_webhook_urls()  # 加载webhook地址

    def _load_webhook_urls(self):
        """从.env文件加载webhook地址"""
        env_file = '.env'  # 配置文件
        webhook_urls = {}  # 存储地址的字典

        if not os.path.exists(env_file):  # 如果文件不存在
            with open(env_file, 'w', encoding="utf-8") as f:
                # 写入默认配置
                f.write("WECHAT_WEBHOOK_URL=\nFEISHU_WEBHOOK_URL=\n")
        else:  # 文件存在则读取
            with open(env_file, 'r', encoding="utf-8") as f:
                for line in f:  # 逐行读取
                    if line.startswith('WECHAT_WEBHOOK_URL='):
                        webhook_urls['wechat'] = line.strip().split('=')[1]
                    elif line.startswith('FEISHU_WEBHOOK_URL='):
                        webhook_urls['feishu'] = line.strip().split('=')[1]
        return webhook_urls

    def send_message(self, content):
        """发送消息到机器人"""
        headers = {"Content-Type": "application/json"}  # 请求头
        results = {}  # 存储结果

        # 企业微信机器人
        if self.robot_type in ['wechat', 'all'] and self.webhook_urls.get('wechat'):
            url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.webhook_urls['wechat']}"
            data = {"msgtype": "text", "text": {"content": content}}
            results['wechat'] = self._send_request(url, headers, data)

        # 飞书机器人
        if self.robot_type in ['feishu', 'all'] and self.webhook_urls.get('feishu'):
            url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{self.webhook_urls['feishu']}"
            data = {"msg_type": "text", "content": {"text": content}}
            results['feishu'] = self._send_request(url, headers, data)

        return results  # 返回发送结果

    def _send_request(self, url, headers, data):
        """发送HTTP请求"""
        for _ in range(self.max_retries):  # 重试机制
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                if response.status_code == 200:  # 成功
                    return True, "发送成功"
                return False, f"HTTP错误: {response.status_code}"  # HTTP错误
            except Exception as e:
                time.sleep(self.retry_delay)  # 延迟后重试
        return False, "发送失败"  # 重试后仍失败


# 机器人日志处理器
class RobotHandler(logging.Handler):
    """机器人日志处理器"""

    def __init__(self, robot):
        """初始化处理器"""
        super().__init__()  # 调用父类初始化
        self.robot = robot  # 机器人实例

    def emit(self, record):
        """处理日志记录"""
        if getattr(record, 'bot', False):  # 检查是否需要机器人通知
            self.robot.send_message(self.format(record))  # 发送消息


# 日志配置函数
def setup_logging(name=None, is_logfile=True, console_level="DEBUG", file_level="DEBUG",
                  log_max_days=7, log_max_size=50):
    """配置日志系统"""
    # 获取调用者文件名作为日志名称
    if name is None:
        try:
            frame = inspect.currentframe()  # 获取当前帧
            while frame:  # 遍历调用栈
                filename = frame.f_code.co_filename  # 获取文件名
                # 跳过logging模块、当前文件和__init__.py
                if ('logging' not in filename and
                        'v3.py' not in filename and
                        not filename.endswith('__init__.py')):
                    # 提取文件名(不含扩展名)作为日志名
                    name = os.path.splitext(os.path.basename(filename))[0]
                    break
                frame = frame.f_back  # 上一帧
        except:
            name = "default"  # 出错使用默认名称

    logger = logging.getLogger(name)  # 获取日志器
    logger.setLevel(logging.DEBUG)  # 设置日志级别

    # 清理现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 配置控制台处理器
    ch = logging.StreamHandler()  # 创建控制台处理器
    ch.setLevel(logging.getLevelName(console_level.upper()))  # 设置级别
    ch.setFormatter(ColorFormatter(  # 设置带颜色的格式化器
        '%(asctime)s [%(levelname)s] [ "%(filename)s:%(lineno)d" ] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(ch)  # 添加处理器

    # 配置文件处理器
    if is_logfile:
        log_dir = f'logs/{datetime.datetime.now().strftime("%Y%m%d")}'  # 日志目录
        mkdir_dir(log_dir)  # 创建目录
        fh = logging.handlers.RotatingFileHandler(  # 创建轮转文件处理器
            os.path.join(log_dir, f'{name}.log'),  # 日志文件路径
            maxBytes=log_max_size * 1024 * 1024,  # 最大文件大小(MB转字节)
            backupCount=log_max_days,  # 保留天数
            encoding='utf-8'  # 文件编码
        )
        fh.setLevel(logging.getLevelName(file_level.upper()))  # 设置级别
        fh.setFormatter(CallerAwareFormatter(  # 设置格式化器
            '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(fh)  # 添加处理器

    # 配置机器人处理器
    robot_handler = RobotHandler(Robot())  # 创建机器人处理器
    robot_handler.setLevel(logging.ERROR)  # 只处理ERROR及以上级别
    logger.addHandler(robot_handler)  # 添加处理器

    return logger  # 返回配置好的日志器


# 便捷日志函数
def log(message, level="DEBUG", extra=None):
    """便捷日志记录函数"""
    extra = extra or {}  # 初始化额外参数
    extra['bot'] = extra.get('bot', False)  # 设置机器人通知标志

    logger = setup_logging()  # 获取日志器
    level = level.upper()  # 统一转为大写

    # 根据级别记录日志
    if level == "DEBUG":
        logger.debug(message, extra=extra)
    elif level == "INFO":
        logger.info(message, extra=extra)
    elif level == "WARNING":
        logger.warning(message, extra=extra)
    elif level == "ERROR":
        logger.error(message, extra=extra)
    elif level == "CRITICAL":
        logger.critical(message, extra=extra)


# 线程测试
def _start_file_processing(file_path):


    def _task_wrapper():
        log(f"file_path:{file_path}")

    threading.Thread(target=_task_wrapper).start()



import threading

def thread_function(name):
    log(f"Thread {name} is starting")
    # 执行任务
    log(f"Thread {name} is finishing")


if __name__ == '__main__':

    # 使用便捷函数
    log("Debug message")  # 默认DEBUG级别
    log("Info message", "INFO")  # INFO级别
    log("Warning with bot", "WARNING", {"bot": True})  # 带机器人通知

    # 直接使用logger
    logger = setup_logging()
    logger.info("Direct info call")
    logger.error("Error with bot", extra={"bot": True})

    #
    _start_file_processing("hello")
    # log("Main thread: before creating a thread")
    # # 创建线程对象
    # thread = threading.Thread(target=thread_function, args=(1,))
    # log("Main thread: before running the thread")
    # # 启动线程
    # thread.start()
    # log("Main thread: wait for the thread to finish")
    # # 等待线程完成
    # thread.join()
    # log("Main thread: all done")
