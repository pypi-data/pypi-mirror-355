from pathlib import Path
from typing import NamedTuple, Optional

from tqsdk_zq_server import get_zq_server_path
from tqsdk_zq_pgserver import get_zq_pgserver_path
from tqsdk_zq_proxy import get_zq_proxy_path
from tqsdk_zq_history import get_zq_history_path


class ZqConfig(NamedTuple):
    kq_name: str
    kq_password: str
    interpreter: str
    web_url: str
    td_url: str


cfg: Optional[ZqConfig] = None

DB_NAME = "zq"
DB_UID = "zq"
DB_PASSWORD = "12345678"

DEFAULT_WEB_IP = "localhost"
DEFAULT_WEB_PORT = 8342

ZQ_DIR = Path.home() / ".tqsdk" / "zq"
ZQ_LOG_DIR = ZQ_DIR / "log"
ZQ_SOCK_DIR = ZQ_DIR / "sock"
ZQ_CONFIG_DIR = ZQ_DIR / "config"
ZQ_DATA_DIR = ZQ_DIR / "data"
ZQ_LOCK_DIR = ZQ_DIR / "lock"

ZQ_LOG_ZQ_SERVER_DIR = ZQ_LOG_DIR / "zq-server"
ZQ_LOG_ZQ_HISTORY_DIR = ZQ_LOG_DIR / "zq-history"
ZQ_SOCK_ZQ_PG_DIR = ZQ_SOCK_DIR / "zq-pg"
ZQ_SOCK_ZQ_SERVER_DIR = ZQ_SOCK_DIR / "zq-server"
ZQ_SOCK_ZQ_HISTORY_DIR = ZQ_SOCK_DIR / "zq-history"
ZQ_DATA_ZQ_PG_DIR = ZQ_DATA_DIR / "zq-pg"
ZQ_DATA_ZQ_SERVER_DIR = ZQ_DATA_DIR / "zq-server"

ZQ_LOG_ZQ_HISTORY_FILE = ZQ_LOG_ZQ_HISTORY_DIR / "zq-history.log"
ZQ_CONFIG_ZQ_PROXY_FILE = ZQ_CONFIG_DIR / "zq-proxy.json"
ZQ_CONFIG_ZQ_SERVER_FILE = ZQ_CONFIG_DIR / "zq-server.json"
ZQ_CONFIG_ZQ_HISTORY_FILE = ZQ_CONFIG_DIR / "zq-history.json"
ZQ_CONFIG_ZQ_FILE = ZQ_CONFIG_DIR / "zq.json"
ZQ_SOCK_ZQ_SERVER_ADMIN_FILE = ZQ_SOCK_ZQ_SERVER_DIR / "admin.sock"
ZQ_SOCK_ZQ_SERVER_TRADE_FILE = ZQ_SOCK_ZQ_SERVER_DIR / "trade.sock"
ZQ_SOCK_ZQ_HISTORY_FILE = ZQ_SOCK_ZQ_HISTORY_DIR / "history.sock"
ZQ_LOCK_ZQ_FILE = ZQ_LOCK_DIR / "zq.lock"

ZQ_SERVER_DIR = get_zq_server_path()
ZQ_PG_DIR = get_zq_pgserver_path()
ZQ_PROXY_DIR = get_zq_proxy_path()
ZQ_HISTORY_DIR = get_zq_history_path()

ZQ_SERVER_EXE_FILE = ZQ_SERVER_DIR / "bin" / "zq_server"
ZQ_PROXY_EXE_FILE = ZQ_PROXY_DIR / "sock-proxy"
ZQ_PG_CTL_EXE_FILE = ZQ_PG_DIR / "bin" / "pg_ctl"
ZQ_PG_POSTGRES_EXE_FILE = ZQ_PG_DIR / "bin" / "postgres"
ZQ_PG_PSQL_EXE_FILE = ZQ_PG_DIR / "bin" / "psql"
ZQ_PG_IS_READY_EXE_FILE = ZQ_PG_DIR / "bin" / "pg_isready"
ZQ_HISTORY_EXE_FILE = ZQ_HISTORY_DIR / "zq_server_history_go"
