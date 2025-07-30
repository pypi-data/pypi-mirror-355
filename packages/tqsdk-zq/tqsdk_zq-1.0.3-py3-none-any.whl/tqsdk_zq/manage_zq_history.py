from tqsdk_zq.utils import check_subprocess_running, run_subprocess_async, kill_subprocess, write_json_config_atomically, get_common_db_config
from tqsdk_zq import config
from tqsdk_zq.exceptions import TqZqHealthCheckError


def ensure_start_zq_history():
    zq_history_executable = str(config.ZQ_HISTORY_EXE_FILE)
    if not check_subprocess_running(zq_history_executable):
        start_zq_history()


def ensure_stop_zq_history():
    zq_history_executable = str(config.ZQ_HISTORY_EXE_FILE)
    kill_subprocess(zq_history_executable)


def start_zq_history():
    # 后期添加的业务，对于老用户需要提醒其再次进行初始化操作
    if not config.ZQ_CONFIG_ZQ_HISTORY_FILE.exists():
        raise TqZqHealthCheckError("tqsdk-zq-history 服务还未初始化，请再次执行：tqsdk-zq init")

    cmd = [
        str(config.ZQ_HISTORY_EXE_FILE),
        "-config",
        str(config.ZQ_CONFIG_ZQ_HISTORY_FILE)
    ]
    run_subprocess_async(cmd)


def init_zq_history_config():
    common_db_config = get_common_db_config()
    zq_history_config = {
        **common_db_config,
        "log_file_path": str(config.ZQ_LOG_ZQ_HISTORY_FILE),
        "db_search_path": "public",
        "server_unix_socket_directories": str(config.ZQ_SOCK_ZQ_HISTORY_FILE),
        "server_mode": "unix"
    }
    write_json_config_atomically(zq_history_config, config.ZQ_CONFIG_ZQ_HISTORY_FILE)
