from time import sleep
import os

from tqsdk_zq.utils import check_subprocess_running, run_subprocess_async, kill_subprocess, run_subprocess
from tqsdk_zq.manage_zq_server import ensure_stop_zq_server
from tqsdk_zq import config
from tqsdk_zq.exceptions import TqZqHealthCheckError
from tqsdk_zq.manage_zq_history import ensure_stop_zq_history

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = str(config.ZQ_PG_DIR / "lib")


def ensure_start_zq_pg():
    pg_server_executable = str(config.ZQ_PG_POSTGRES_EXE_FILE)

    if check_subprocess_running(pg_server_executable):
        if not check_zq_pg():
            ensure_stop_zq_pg()
            ensure_start_zq_pg()
    else:
        ensure_stop_zq_history()
        ensure_stop_zq_server()
        start_zq_pg()
        # 启动有延时，会导致后续众期进程连接数据库失败
        count = 0
        while not check_zq_pg():
            sleep(1)
            count += 1
            if count > 10:
                raise TqZqHealthCheckError("tqsdk-zq-pg 服务启动失败，请重试")


def ensure_stop_zq_pg(timeout=5):
    stop_zq_pg()
    count = 0
    pg_server_executable = str(config.ZQ_PG_POSTGRES_EXE_FILE)
    while check_subprocess_running(pg_server_executable):
        sleep(1)
        count += 1
        if count >= timeout:
            kill_subprocess(pg_server_executable)
            break


def init_zq_pg():
    cmd = [
        str(config.ZQ_PG_CTL_EXE_FILE),
        "init",
        "-D", str(config.ZQ_DATA_ZQ_PG_DIR)
    ]
    run_subprocess(cmd, env=env, check=True)


def config_zq_pg():
    cmd = [
        str(config.ZQ_PG_PSQL_EXE_FILE),
        "-d", "postgres",
        "-h", str(config.ZQ_SOCK_ZQ_PG_DIR),
        "-c", f"CREATE DATABASE {config.DB_NAME} ENCODING 'UTF8' TEMPLATE template0;"
    ]
    run_subprocess(cmd, env=env, check=True)

    cmd = [
        str(config.ZQ_PG_PSQL_EXE_FILE),
        "-d", "postgres",
        "-h", str(config.ZQ_SOCK_ZQ_PG_DIR),
        "-c", f"CREATE USER {config.DB_UID} WITH SUPERUSER PASSWORD '{config.DB_PASSWORD}';"
    ]
    run_subprocess(cmd, env=env, check=True)

    cmd = [
        str(config.ZQ_PG_PSQL_EXE_FILE),
        "-d", "postgres",
        "-h", str(config.ZQ_SOCK_ZQ_PG_DIR),
        "-c", f"GRANT ALL PRIVILEGES ON DATABASE {config.DB_NAME} TO {config.DB_UID};"
    ]
    run_subprocess(cmd, env=env, check=True)

    cmd = [
        str(config.ZQ_PG_PSQL_EXE_FILE),
        "-d", "postgres",
        "-h", str(config.ZQ_SOCK_ZQ_PG_DIR),
        "-c", f"ALTER DATABASE {config.DB_NAME} SET timezone TO 'Asia/Shanghai';"
    ]
    run_subprocess(cmd, env=env, check=True)

    cmd = [
        str(config.ZQ_PG_PSQL_EXE_FILE),
        "-d", "postgres",
        "-h", str(config.ZQ_SOCK_ZQ_PG_DIR),
        "-c", f"ALTER SYSTEM SET log_timezone TO 'Asia/Shanghai';"
    ]
    run_subprocess(cmd, env=env, check=True)


def check_zq_pg():
    check_cmd = [
        str(config.ZQ_PG_IS_READY_EXE_FILE),
        "-h", str(config.ZQ_SOCK_ZQ_PG_DIR)
    ]
    result = run_subprocess(check_cmd, env=env)
    return result.returncode == 0


def start_zq_pg():
    cmd = [
        str(config.ZQ_PG_CTL_EXE_FILE),
        "start",
        "-D", str(config.ZQ_DATA_ZQ_PG_DIR),
        "-o", f"-k {str(config.ZQ_SOCK_ZQ_PG_DIR)}"
    ]
    run_subprocess_async(cmd, env=env)


def stop_zq_pg():
    cmd = [
        str(config.ZQ_PG_CTL_EXE_FILE),
        "stop",
        "-D", str(config.ZQ_DATA_ZQ_PG_DIR)
    ]
    run_subprocess(cmd, env=env)
