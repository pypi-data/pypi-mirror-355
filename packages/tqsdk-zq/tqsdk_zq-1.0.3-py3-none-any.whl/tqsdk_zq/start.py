from filelock import Timeout, FileLock

from tqsdk_zq import config
from tqsdk_zq.exceptions import TqZqTimeoutError
from tqsdk_zq.utils import load_zq_config
from tqsdk_zq.manage_zq_proxy import ensure_start_zq_proxy
from tqsdk_zq.manage_zq_server import ensure_start_zq_server
from tqsdk_zq.manage_zq_pg import ensure_start_zq_pg
from tqsdk_zq.manage_zq_history import ensure_start_zq_history


def start_cmd(args):
    try:
        with FileLock(str(config.ZQ_LOCK_ZQ_FILE), timeout=10):
            load_zq_config()
            ensure_start()
    except Timeout:
        raise TqZqTimeoutError("tqsdk-zq 启动超时，请稍后重试")


def ensure_start():
    ensure_start_zq_pg()
    ensure_start_zq_proxy()
    ensure_start_zq_server()
    ensure_start_zq_history()
