import datetime
import logging
import logging.handlers
import os
import sys
import time
import requests
import json

# 创建多级目录
def mkdir_dir(path):
    # 判断路径是否存在
    isExists = os.path.exists(path)

    if not isExists:
        # 如果不存在，则创建目录（多层）
        os.makedirs(path)
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        return False

# 自定义过滤器，用于替换 filename 为绝对路径
class AbsolutePathFilter(logging.Filter):
    def filter(self, record):
        record.abspath = os.path.abspath(record.pathname)
        return True

# 自定义日志格式化器，用于添加颜色
class ColorFormatter(logging.Formatter):
    # 定义不同日志等级的颜色
    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"  # Reset color

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, "")
        message = logging.Formatter.format(self, record)
        return f"{log_color}{message}{self.RESET}"

# 创建日志
def setup_logging(name=None, is_logfile=True, console_level="DEBUG", file_level="DEBUG", log_max_days=7, log_max_size=50):
    """
    创建日志配置
    :param name: 日志器名称，默认为调用者的文件名
    :param is_logfile: 是否创建日志文件，默认为 True
    :param console_level: 控制台日志输出级别，默认为 "DEBUG"
    :param file_level: 文件日志输出级别，默认为 "DEBUG"
    :param log_max_days: 日志文件保存天数，默认为 7 天
    :param log_max_size: 单个日志文件最大大小（单位：MB），默认为 50MB
    :return: 配置好的日志器
    """
    console_level = console_level.upper()
    if console_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        console_level = "INFO"
    file_level = file_level.upper()
    if file_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        file_level = "INFO"
    # 如果没有传入 name，则获取调用者的文件名
    if name is None:
        frame = sys._getframe(1)  # 获取上一级调用的帧信息
        caller_filename = os.path.basename(frame.f_code.co_filename)
        name = os.path.splitext(caller_filename)[0]  # 去掉文件扩展名
    # 使用固定的日志器名称
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 清理现有处理器
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建流处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.getLevelName(console_level.upper()))  # 将字符串转换为日志级别
    formatter = ColorFormatter(
        "%(asctime)s [%(levelname)s] [ \"%(filename)s:%(lineno)d\" ] %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 添加自定义过滤器
    logger.addFilter(AbsolutePathFilter())

    # 根据 is_logfile 参数决定是否创建文件处理器
    if is_logfile:
        now = datetime.datetime.now().strftime("%Y%m%d")
        log_dir = f'logs/{now}'
        mkdir_dir(log_dir)
        log_file = os.path.join(log_dir, f'{name}.log')
        # 创建 RotatingFileHandler，设置最大文件大小和备份文件数量
        fh = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_max_size * 1024 * 1024,  # 将MB转换为字节
            backupCount=log_max_days,
            encoding='utf-8'
        )
        fh.setLevel(logging.getLevelName(file_level.upper()))  # 将字符串转换为日志级别
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

    # 禁止日志传播
    logger.propagate = False
    # 初始化机器人
    robot = Robot(robot_type='all')
    # 添加机器人日志处理器
    robot_handler = RobotHandler(robot)
    logger.addHandler(robot_handler)

    return logger

# 机器人日志处理器
class RobotHandler(logging.Handler):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot

    def emit(self, record):
        # 检查是否需要发送到机器人
        if hasattr(record, 'bot') and record.bot:
            log_entry = self.format(record)
            self.robot.send_message(log_entry)

class Robot:
    def __init__(self, robot_type, max_retries=3, retry_delay=3):
        """
        初始化机器人
        :param robot_type: 机器人类型，支持 'wechat', 'feishu', 'all'
        :param max_retries: 最大重试次数，默认为3次
        :param retry_delay: 重试间隔时间（秒），默认为3秒
        """
        self.robot_type = robot_type.lower()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.webhook_urls = self._load_webhook_urls()

    def _load_webhook_urls(self):
        """
        从.env文件中加载Webhook地址
        :return: 包含企业微信和飞书Webhook地址的字典
        """
        env_file = '.env'
        webhook_urls = {}

        if not os.path.exists(env_file):
            # 如果.env文件不存在，则创建并填充初始值
            with open(env_file, 'w', encoding="UTF-8") as f:
                f.write("# 企业微信机器人Webhook的URL或Key\nWECHAT_WEBHOOK_URL=\n")
                f.write("# 飞书机器人Webhook的URL或Key\nFEISHU_WEBHOOK_URL=\n")
        else:
            # 如果.env文件存在，则读取内容
            with open(env_file, 'r', encoding="UTF-8") as f:
                for line in f:
                    if line.startswith('WECHAT_WEBHOOK_URL='):
                        webhook_urls['wechat'] = line.strip().split('WECHAT_WEBHOOK_URL=')[1]
                    elif line.startswith('FEISHU_WEBHOOK_URL='):
                        webhook_urls['feishu'] = line.strip().split('FEISHU_WEBHOOK_URL=')[1]

        return webhook_urls

    def _construct_webhook_url(self, robot_type, webhook_url_or_key):
        """
        构造完整的Webhook地址
        :param robot_type: 机器人类型
        :param webhook_url_or_key: 机器人的Webhook地址或Key
        :return: 完整的Webhook地址
        """
        if robot_type == 'wechat':
            base_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key="
        elif robot_type == 'feishu':
            base_url = "https://open.feishu.cn/open-apis/bot/v2/hook/"
        else:
            raise ValueError("不支持的机器人类型")

        if webhook_url_or_key.startswith("https://"):
            return webhook_url_or_key
        else:
            return f"{base_url}{webhook_url_or_key}"

    def send_message(self, content):
        """
        向机器人发送文本消息
        :param content: 要发送的文本内容
        :return: 发送结果
        """
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

        results = {}

        if self.robot_type in ['wechat', 'all'] and self.webhook_urls.get('wechat'):
            wechat_url = self._construct_webhook_url('wechat', self.webhook_urls['wechat'])
            wechat_data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            wechat_response = self._send_request(wechat_url, headers, wechat_data)
            results['wechat'] = wechat_response
            # print(f"企业微信机器人发送结果：{wechat_response}")

        if self.robot_type in ['feishu', 'all'] and self.webhook_urls.get('feishu'):
            feishu_url = self._construct_webhook_url('feishu', self.webhook_urls['feishu'])
            feishu_data = {
                "msg_type": "text",
                "content": {
                    "text": content
                }
            }
            feishu_response = self._send_request(feishu_url, headers, feishu_data)
            results['feishu'] = feishu_response
            # print(f"飞书机器人发送结果：{feishu_response}")

        return results

    def _send_request(self, url, headers, data):
        """
        发送HTTP请求
        :param url: Webhook地址
        :param headers: 请求头
        :param data: 请求数据
        :return: 发送结果
        """
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data))
                # print(f"请求URL: {url}")
                # print(f"响应内容: {response.json()}")

                if response.status_code == 200:
                    # 企业微信
                    if 'errcode' in response.json() and response.json()['errcode'] == 0:
                        return True, "消息发送成功"
                    # 飞书
                    elif 'code' in response.json() and response.json()['code'] == 0:
                        return True, "消息发送成功"
                    else:
                        return False, "消息发送失败，key失效"
                else:
                    return False, f"HTTP请求失败，状态码：{response.status_code}"
            except Exception as e:
                # print(f"发送请求时发生错误: {e}")
                retries += 1
                # print(f"消息发送失败，正在重试...（第{retries}次）")
                time.sleep(self.retry_delay)
        return False, f"消息发送失败，已达到最大重试次数"

# 示例使用
if __name__ == "__main__":


    # 创建日志器
    logger = setup_logging(console_level="INFO", file_level="WARNING", log_max_days=10, log_max_size=50)
    # 日志记录
    logger.debug("这是一条 debug 日志")
    logger.info("这是一条 info 日志", extra={"bot": True})  # 通过机器人发送
    logger.warning("这是一条 warning 日志")
    logger.error("这是一条 error 日志", extra={"bot": True})  # 通过机器人发送
    logger.critical("这是一条 critical 日志")
