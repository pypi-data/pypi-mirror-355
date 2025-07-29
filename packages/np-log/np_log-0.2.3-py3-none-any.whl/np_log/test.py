import threading
from np_log import log as print,setup_logging
logger = setup_logging()
# 线程测试
def _start_file_processing(file_path):


    def _task_wrapper():
        logger.info(f"file_path:{file_path}")
        print("你好")

    threading.Thread(target=_task_wrapper).start()

if __name__ == "__main__":

    _start_file_processing("hello")
