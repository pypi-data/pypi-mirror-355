from time import sleep
import urllib.request
import urllib.parse
import socket

from tqsdk_zq import config
from tqsdk_zq.exceptions import TqZqHealthCheckError
from tqsdk_zq.utils import run_subprocess_async, check_subprocess_running, kill_subprocess
from tqsdk_zq.utils import write_json_config_atomically


def ensure_start_zq_proxy():
    web_url = config.cfg.web_url
    proxy_server_executable = str(config.ZQ_PROXY_EXE_FILE)

    if check_subprocess_running(proxy_server_executable):
        if not check_zq_proxy():
            ensure_stop_zq_proxy()
            ensure_start_zq_proxy()
    else:
        start_zq_proxy()
        count = 0
        while not check_zq_proxy():
            sleep(1)
            count += 1
            if count > 10:
                raise TqZqHealthCheckError("tqsdk-zq-proxy 服务启动失败，请重试")


def ensure_stop_zq_proxy():
    proxy_server_executable = str(config.ZQ_PROXY_EXE_FILE)
    kill_subprocess(proxy_server_executable)


def check_zq_proxy():
    try:
        with urllib.request.urlopen(config.cfg.web_url) as response:
            return response.status == 200
    except (urllib.error.URLError, socket.timeout):
        return False


def start_zq_proxy():
    cmd = [
        str(config.ZQ_PROXY_EXE_FILE),
        "-a", urllib.parse.urlparse(config.cfg.web_url).netloc,
        "-p", str(config.ZQ_CONFIG_ZQ_PROXY_FILE)
    ]
    run_subprocess_async(cmd)


def init_zq_proxy_config():
    zq_proxy_config = [
        {
            "Pattern": "/",
            "Static": str(config.ZQ_SERVER_DIR)
        },
        {
            "Pattern": "/trade",
            "Unix": str(config.ZQ_SOCK_ZQ_SERVER_TRADE_FILE)
        },
        {
            "Pattern": "/v1/",
            "Unix": str(config.ZQ_SOCK_ZQ_SERVER_ADMIN_FILE)
        },
        {
            "Pattern": "/history/v1/",
            "Unix": str(config.ZQ_SOCK_ZQ_HISTORY_FILE)
        }
    ]
    write_json_config_atomically(zq_proxy_config, config.ZQ_CONFIG_ZQ_PROXY_FILE)
