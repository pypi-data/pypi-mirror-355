from time import sleep
import urllib.request
import subprocess
import json

from tqsdk_zq import config
from tqsdk_zq.utils import check_subprocess_running, run_subprocess_async, kill_subprocess, write_json_config_atomically, get_common_db_config
from tqsdk_zq import config
from tqsdk_zq.exceptions import TqZqHealthCheckError


def ensure_start_zq_server():
    zq_server_executable = str(config.ZQ_SERVER_EXE_FILE)

    if check_subprocess_running(zq_server_executable):
        if not check_zq_server():
            ensure_stop_zq_server()
            ensure_start_zq_server()
    else:
        start_zq_server()
        # 启动有延时，会导致后续 tqsdk 连接失败，触发重试循环
        count = 0
        while not check_zq_server():
            sleep(1)
            count += 1
            if count > 10:
                raise TqZqHealthCheckError("tqsdk-zq-server 服务启动失败，请重试")


def ensure_stop_zq_server():
    zq_server_executable = str(config.ZQ_SERVER_EXE_FILE)
    kill_subprocess(zq_server_executable)


def check_zq_server():
    data = {
        'password': 'admin',
        'user_name': 'admin'
    }

    json_data = json.dumps(data).encode('utf-8')

    url = f'{config.cfg.web_url}v1/login'
    req = urllib.request.Request(url, data=json_data, method='POST')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            return status_code == 200
    except (Exception):
        return False


def init_zq_server():
    cmd = [
        str(config.ZQ_SERVER_EXE_FILE),
        "--init",
        "--adminid", "admin",
        "--adminpwd", "admin",
        "--config", str(config.ZQ_CONFIG_ZQ_SERVER_FILE)
    ]

    with subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True) as process:
        process.communicate(input="Y\n")
        if process.returncode != 0:
            raise Exception("tqsdk-zq-server 初始化失败，请重试")


def start_zq_server():
    cmd = [
        str(config.ZQ_SERVER_EXE_FILE),
        "--config",
        str(config.ZQ_CONFIG_ZQ_SERVER_FILE)
    ]
    run_subprocess_async(cmd)


def init_zq_server_config():
    common_db_config = get_common_db_config()
    zq_server_config = {
        **common_db_config,
        "log_file_path": str(config.ZQ_LOG_ZQ_SERVER_DIR),
        "app_data_path": str(config.ZQ_DATA_ZQ_SERVER_DIR),
        "db_driver": "PostgreSQL",
        "db_server": "localhost",
        "admin_unix_socket_path": str(config.ZQ_SOCK_ZQ_SERVER_ADMIN_FILE),
        "trade_unix_socket_path": str(config.ZQ_SOCK_ZQ_SERVER_TRADE_FILE),
        "secret_key": "ABCDEFG1234",
        "islp_mode": False,
        "log_compressed": True,
        "enable_authorization": False,
        "shinny_id": config.cfg.kq_name,
        "shinny_password": config.cfg.kq_password,
        "individual_mode": True,
    }
    write_json_config_atomically(zq_server_config, config.ZQ_CONFIG_ZQ_SERVER_FILE)
