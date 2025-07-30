import subprocess
import platform
import json
import sys
import os
from pathlib import Path

import psutil

from tqsdk_zq import config


def check_subprocess_running(process_exe):
    username = psutil.Process().username()
    if platform.system() == "Windows":
        process_exe += ".exe"
    for process in psutil.process_iter(['username', 'exe']):
        if process.info['exe'] == process_exe and process.info['username'] == username:
            return True
    return False


def kill_subprocess(process_exe):
    username = psutil.Process().username()
    if platform.system() == "Windows":
        process_exe += ".exe"
    for process in psutil.process_iter(['username', 'exe']):
        if process.info['exe'] == process_exe and process.info['username'] == username:
            process.terminate()
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                process.kill()


def run_subprocess_async(cmd, env=None):
    if platform.system() == "Windows":
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
            env=env
        )
    else:
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env
        )


def run_subprocess(cmd, env=None, check=False):
    return subprocess.run(cmd,
                          env=env,
                          check=check,
                          stdin=subprocess.DEVNULL,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL,
                          )


def load_zq_config():
    try:
        if platform.system() != "Windows":
            assert os.stat(config.ZQ_CONFIG_ZQ_FILE).st_uid == os.getuid(), "当前用户和初始化用户不一致，请保证在同一个用户下运行"
        with config.ZQ_CONFIG_ZQ_FILE.open("r") as f:
            config.cfg = config.ZqConfig(**json.load(f))
            assert config.cfg.interpreter == sys.executable, "运行环境与初始化环境(tqsdk-zq init)不一致，请保证在同一个环境下运行"
    except (FileNotFoundError, json.JSONDecodeError):
        raise Exception("未找到配置文件，请先使用 tqsdk-zq init 初始化") from None


def write_json_config_atomically(data: dict, config_file: Path):
    """Atomically writes a dictionary to a JSON config file."""
    temp_file = config_file.with_suffix('.tmp')
    with temp_file.open('w') as f:
        json.dump(data, f, indent=4)
    os.replace(temp_file, config_file)


def get_common_db_config() -> dict:
    """Returns a dictionary with common database configuration settings."""
    return {
        "db_uid": config.DB_UID,
        "db_password": config.DB_PASSWORD,
        "db_name": config.DB_NAME,
        "db_unix_socket_directories": str(config.ZQ_SOCK_ZQ_PG_DIR),
    }
