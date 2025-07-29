import datetime
import logging
import logging.handlers
import os
import sys
import time
import requests
import json
from pathlib import Path


# 创建多级目录
def mkdir_dir(path):
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        return True
    return False


# 获取项目根目录
def get_project_root():
    """向上搜索直到找到项目根目录（包含 .git 或 .project_root 标记）"""
    current_dir = Path(os.getcwd())

    # 向上搜索直到找到根标记
    while current_dir != current_dir.parent:
        if (current_dir / '.git').exists() or (current_dir / '.project_root').exists():
            return current_dir
        current_dir = current_dir.parent

    # 如果没找到，使用当前目录
    return Path(os.getcwd())


# 查找有效的环境文件
def find_valid_env_file(start_path=None):
    """
    递归向上查找包含机器人配置的有效.env文件
    :param start_path: 起始搜索路径，默认为当前目录
    :return: 找到的有效.env文件路径，或None
    """
    if start_path is None:
        start_path = Path.cwd()

    current_dir = Path(start_path).resolve()

    # 向上搜索直到根目录
    while current_dir != current_dir.parent:
        env_file = current_dir / '.env'

        # 检查文件是否存在且包含机器人配置
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检查是否包含机器人配置
                if "WECHAT_WEBHOOK_URL" in content or "FEISHU_WEBHOOK_URL" in content:
                    return env_file

        current_dir = current_dir.parent

    return None


# 自定义过滤器
class AbsolutePathFilter(logging.Filter):
    def filter(self, record):
        record.abspath = os.path.abspath(record.pathname)
        return True


# 自定义日志格式化器
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"


# 创建日志
def setup_logging(name=None, is_logfile=True, console_level="DEBUG", file_level="DEBUG",
                  log_max_days=7, log_max_size=50, project_root=None):
    """
    创建日志配置
    :param name: 日志器名称
    :param is_logfile: 是否创建日志文件
    :param console_level: 控制台日志级别
    :param file_level: 文件日志级别
    :param log_max_days: 日志保存天数
    :param log_max_size: 日志文件最大大小(MB)
    :param project_root: 项目根目录路径
    :return: 配置好的日志器
    """
    # 确定项目根目录
    if project_root is None:
        project_root = get_project_root()
    else:
        project_root = Path(project_root).resolve()

    # 查找有效的.env文件
    env_file = find_valid_env_file(project_root)

    # 如果没找到有效的.env文件，在项目根目录创建
    if env_file is None:
        env_file = project_root / '.env'
        if not env_file.exists():
            with open(env_file, 'w', encoding="UTF-8") as f:
                f.write("# 企业微信机器人Webhook的URL或Key\nWECHAT_WEBHOOK_URL=\n")
                f.write("# 飞书机器人Webhook的URL或Key\nFEISHU_WEBHOOK_URL=\n")

    # 设置日志目录路径
    log_dir = project_root / 'logs'

    # 创建日志目录（如果不存在）
    if not log_dir.exists():
        mkdir_dir(log_dir)

    # 日志级别处理
    console_level = console_level.upper()
    if console_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        console_level = "INFO"

    file_level = file_level.upper()
    if file_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        file_level = "INFO"

    # 确定日志器名称
    if name is None:
        frame = sys._getframe(1)
        caller_filename = os.path.basename(frame.f_code.co_filename)
        name = os.path.splitext(caller_filename)[0]

    # 创建或获取日志器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 清理现有处理器
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.getLevelName(console_level))
    formatter = ColorFormatter(
        "%(asctime)s [%(levelname)s] [ \"%(filename)s:%(lineno)d\" ] %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 添加自定义过滤器
    logger.addFilter(AbsolutePathFilter())

    # 创建文件处理器
    if is_logfile:
        now = datetime.datetime.now().strftime("%Y%m%d")
        daily_log_dir = log_dir / now
        mkdir_dir(daily_log_dir)

        log_file = daily_log_dir / f'{name}.log'
        fh = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_max_size * 1024 * 1024,
            backupCount=log_max_days,
            encoding='utf-8'
        )
        fh.setLevel(logging.getLevelName(file_level))
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

    # 添加机器人处理器
    logger.propagate = False
    robot = Robot(robot_type='all', env_file=env_file)

    # 只有在配置了至少一个机器人时才添加处理器
    if robot.has_configured_bots():
        robot_handler = RobotHandler(robot)
        logger.addHandler(robot_handler)
    else:
        print("未配置任何机器人Webhook，可以在.env文件添加机器人信息")

    return logger


# 机器人日志处理器
class RobotHandler(logging.Handler):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        # 设置级别为WARNING，只处理警告及以上级别的日志
        self.setLevel(logging.WARNING)

    def emit(self, record):
        if hasattr(record, 'bot') and record.bot:
            log_entry = self.format(record)
            self.robot.send_message(log_entry)


class Robot:
    def __init__(self, robot_type, env_file, max_retries=3, retry_delay=3):
        """
        初始化机器人
        :param robot_type: 机器人类型 ('wechat', 'feishu', 'all')
        :param env_file: .env文件路径
        :param max_retries: 最大重试次数
        :param retry_delay: 重试间隔(秒)
        """
        self.robot_type = robot_type.lower()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.env_file = Path(env_file)
        self.webhook_urls = self._load_webhook_urls()

    def has_configured_bots(self):
        """检查是否配置了至少一个机器人"""
        return bool(self.webhook_urls.get('wechat') or self.webhook_urls.get('feishu'))

    def _load_webhook_urls(self):
        """从.env文件加载Webhook地址"""
        webhook_urls = {}

        if not self.env_file.exists():
            return webhook_urls

        with open(self.env_file, 'r', encoding="UTF-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith('WECHAT_WEBHOOK_URL='):
                    value = line.split('WECHAT_WEBHOOK_URL=', 1)[1]
                    if value:  # 只添加非空值
                        webhook_urls['wechat'] = value
                elif line.startswith('FEISHU_WEBHOOK_URL='):
                    value = line.split('FEISHU_WEBHOOK_URL=', 1)[1]
                    if value:  # 只添加非空值
                        webhook_urls['feishu'] = value

        return webhook_urls

    def _construct_webhook_url(self, robot_type, webhook_url_or_key):
        """构造完整的Webhook地址"""
        if robot_type == 'wechat':
            base_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key="
        elif robot_type == 'feishu':
            base_url = "https://open.feishu.cn/open-apis/bot/v2/hook/"
        else:
            raise ValueError("不支持的机器人类型")

        if webhook_url_or_key.startswith("https://"):
            return webhook_url_or_key
        return f"{base_url}{webhook_url_or_key}"

    def send_message(self, content):
        """向机器人发送文本消息"""
        headers = {"Content-Type": "application/json; charset=utf-8"}
        results = {}

        if self.robot_type in ['wechat', 'all'] and self.webhook_urls.get('wechat'):
            wechat_url = self._construct_webhook_url('wechat', self.webhook_urls['wechat'])
            wechat_data = {"msgtype": "text", "text": {"content": content}}
            wechat_response = self._send_request(wechat_url, headers, wechat_data)
            results['wechat'] = wechat_response

        if self.robot_type in ['feishu', 'all'] and self.webhook_urls.get('feishu'):
            feishu_url = self._construct_webhook_url('feishu', self.webhook_urls['feishu'])
            feishu_data = {"msg_type": "text", "content": {"text": content}}
            feishu_response = self._send_request(feishu_url, headers, feishu_data)
            results['feishu'] = feishu_response

        return results

    def _send_request(self, url, headers, data):
        """发送HTTP请求"""
        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
                if response.status_code == 200:
                    # 企业微信
                    if 'errcode' in response.json() and response.json()['errcode'] == 0:
                        return True, "消息发送成功"
                    # 飞书
                    elif 'code' in response.json() and response.json()['code'] == 0:
                        return True, "消息发送成功"
                    return False, "消息发送失败，key失效"
                return False, f"HTTP请求失败，状态码：{response.status_code}"
            except Exception as e:
                retries += 1
                time.sleep(self.retry_delay)
        return False, f"消息发送失败，已达到最大重试次数"


def log(msg, level="info"):
    # 创建日志器（使用统一的项目根目录）
    logger = setup_logging(
        console_level="INFO",
        file_level="ERROR",
        log_max_days=10,
        log_max_size=50,
        # project_root=project_root
    )
    if level.upper() == "DEBUG":
        logger.debug(msg)
    elif level.upper() == "INFO":
        logger.info(msg)
    elif level.upper() == "WARNING":
        logger.warning(msg)
    elif level.upper() == "ERROR":
        logger.error(msg)
    elif level.upper() == "CRITICAL":
        logger.critical(msg)
    else:
        print(msg)



# 示例使用
if __name__ == "__main__":
    # 指定项目根目录（可选）
    # project_root = get_project_root()

    # 创建日志器（使用统一的项目根目录）
    logger = setup_logging(
        console_level="INFO",
        file_level="WARNING",
        log_max_days=10,
        log_max_size=50,
        # project_root=project_root
    )

    # 日志记录
    logger.debug("这是一条 debug 日志")
    logger.info("这是一条 info 日志", extra={"bot": True})
    logger.warning("这是一条 warning 日志")
    logger.error("这是一条 error 日志", extra={"bot": True})
    logger.critical("这是一条 critical 日志")