from filelock import Timeout, FileLock
import sys
import shutil

from tqsdk_zq import config
from tqsdk_zq.exceptions import TqZqTimeoutError
from tqsdk_zq.utils import write_json_config_atomically
from tqsdk_zq.start import ensure_start
from tqsdk_zq.manage_zq_proxy import ensure_start_zq_proxy, init_zq_proxy_config, ensure_stop_zq_proxy
from tqsdk_zq.manage_zq_server import ensure_start_zq_server, init_zq_server_config, ensure_stop_zq_server, init_zq_server
from tqsdk_zq.manage_zq_pg import ensure_start_zq_pg, init_zq_pg, config_zq_pg, ensure_stop_zq_pg
from tqsdk_zq.manage_zq_history import ensure_start_zq_history, init_zq_history_config, ensure_stop_zq_history


def init_cmd(args):
    try:
        with FileLock(str(config.ZQ_LOCK_ZQ_FILE), timeout=10):
            if not args.kq_name:
                args.kq_name = input("请输入快期用户名: ").strip()

            if not args.kq_password:
                import getpass
                args.kq_password = getpass.getpass("请输入密码: ")

            print("正在初始化...")

            ensure_stop()
            config.cfg = config.ZqConfig(kq_name=args.kq_name, kq_password=args.kq_password, interpreter=sys.executable,
                                         web_url=f"http://{config.DEFAULT_WEB_IP}:{args.web_port if args.web_port else config.DEFAULT_WEB_PORT}/",
                                         td_url=f"ws://{config.DEFAULT_WEB_IP}:{args.web_port if args.web_port else config.DEFAULT_WEB_PORT}/trade")
            if not config.ZQ_CONFIG_ZQ_FILE.exists():
                init()
            else:
                update()

            print("初始化完成")
            print(f"快期用户名: {args.kq_name}")
            print("Web 管理页账户: admin")
            print("Web 管理页密码: admin")
            print(f"Web 管理页 URL: {config.cfg.web_url}")
    except Timeout:
        raise TqZqTimeoutError("tqsdk-zq 初始化超时，请稍后重试")


def init():
    clean_zq_dirs()
    init_zq_dirs()
    init_zq_pg()
    ensure_start_zq_pg()
    config_zq_pg()
    init_zq_proxy_config()
    ensure_start_zq_proxy()
    init_zq_server_config()
    init_zq_server()
    ensure_start_zq_server()
    init_zq_history_config()
    ensure_start_zq_history()
    init_zq_config()


def update():
    init_zq_dirs()
    init_zq_proxy_config()
    init_zq_history_config()
    init_zq_server_config()
    init_zq_config()
    ensure_start()


def ensure_stop():
    ensure_stop_zq_history()
    ensure_stop_zq_server()
    ensure_stop_zq_proxy()
    ensure_stop_zq_pg()


def init_zq_config():
    """原子操作，保存配置文件"""
    write_json_config_atomically(config.cfg._asdict(), config.ZQ_CONFIG_ZQ_FILE)


def clean_zq_dirs():
    if not config.ZQ_DIR.exists():
        return
    for item in config.ZQ_DIR.iterdir():
        if item.is_dir() and item != config.ZQ_LOCK_DIR:
            shutil.rmtree(item)


def init_zq_dirs():
    config.ZQ_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_LOG_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_SOCK_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_LOCK_DIR.mkdir(parents=True, exist_ok=True)

    config.ZQ_LOG_ZQ_SERVER_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_LOG_ZQ_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_LOG_ZQ_HISTORY_FILE.touch(exist_ok=True)
    config.ZQ_SOCK_ZQ_PG_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_SOCK_ZQ_SERVER_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_SOCK_ZQ_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_DATA_ZQ_PG_DIR.mkdir(parents=True, exist_ok=True)
    config.ZQ_DATA_ZQ_SERVER_DIR.mkdir(parents=True, exist_ok=True)
