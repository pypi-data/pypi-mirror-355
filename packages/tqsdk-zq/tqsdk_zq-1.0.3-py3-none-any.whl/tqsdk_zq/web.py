from filelock import FileLock, Timeout

from tqsdk_zq import config
from tqsdk_zq.exceptions import TqZqTimeoutError
from tqsdk_zq.utils import load_zq_config
from tqsdk_zq.start import ensure_start


def web_cmd(args):
    try:
        with FileLock(str(config.ZQ_LOCK_ZQ_FILE), timeout=10):
            load_zq_config()
            print("正在启动进程...")
            ensure_start()
            print(f"Web 管理页 URL: {config.cfg.web_url}")
    except Timeout:
        raise TqZqTimeoutError("tqsdk-zq 启动超时，请稍后重试")
