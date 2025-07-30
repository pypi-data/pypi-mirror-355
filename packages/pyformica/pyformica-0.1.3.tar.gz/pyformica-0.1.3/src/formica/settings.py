from __future__ import annotations

import configparser
import json
import logging.config
import os
import pathlib
from importlib.resources import files

from sqlalchemy.ext.asyncio import create_async_engine

# print("Set start method")
# multiprocessing.set_start_method("spawn")

_DEFAULT_CONFIG = {
    "webserver": {
        "HOST": "127.0.0.1",
        "PORT": 8000
    },
    "scheduler": {
        "POLLING_INTERVAL": 1,
    },
    "executor": {"TYPE": "local"},
    "database": {"CONNECTION_POOL_SIZE": 1},
    "connection": {
        "DEFAULT_IDLE_TIMEOUT": 3000,
        "DEFAULT_CONNECT_TIMEOUT": 30,
        "DEFAULT_COMMAND_TIMEOUT": 30,
        "CONNECTION_MAX_RETRIES": 2,
        "CONNECTION_RETRY_SLEEP": 1,
    },
    "security": {
        "SECRET_KEY": "SECRET",
        "TOKEN_LIFETIME": 3600,  # 1 hour
    }
}

# ------------ PATHS -----------------------------------------------------------------------------------

_DEFAULT_FORMICA_HOME = pathlib.Path.home() / "formica"
FORMICA_HOME = (
    pathlib.Path(os.getenv("FORMICA_HOME"))
    if os.getenv("FORMICA_HOME") is not None
    else _DEFAULT_FORMICA_HOME
)

_CONFIG = FORMICA_HOME / "formica.ini"
_TEST_CONFIG = "src/formica/config_templates/test.ini"
_LOGS = FORMICA_HOME / "logs"
_SCHEDULER_LOGS = _LOGS / "scheduler"
_FLOW_LOGS = _LOGS / "flow"

# ------------ CONNECTIONS ------------------------------------------------------------------------------

_SQLITE_DB_TEST_FILE = "test_formica.db"
_SQLITE_DB_FILE = "formica.db"
_SQLITE_DEFAULT_CONNECTION_URL = f"sqlite+aiosqlite:///{FORMICA_HOME / _SQLITE_DB_FILE}"
_SQLITE_TEST_CONNECTION_URL = (
    f"sqlite+aiosqlite:///{FORMICA_HOME / _SQLITE_DB_TEST_FILE}"
)

# ------------- OBJECTS ---------------------------------------------------------------------------------

config = configparser.ConfigParser()
config.read_dict(_DEFAULT_CONFIG)
engine = None
_logger = logging.getLogger(__name__)
_init_already = False

# -------------------------------------------------------------------------------------------------------


def init() -> None:
    """
    Khởi tạo thư mục dữ liệu ở đường dẫn `FORMICA_HOME.

    Khi bắt đầu chạy bất cứ thành phần nào thì hàm này cần được gọi để khởi tạo các tài nguyên cần thiết

    Nhưng hàm này chưa khởi tạo DB (vì circular import), caller phải sau đó gọi create_all của SQLModel

    :return: None
    """
    global _init_already
    global FORMICA_HOME

    if not _init_already:
        print("Init already:", _init_already)
        formica_home_env = os.getenv("FORMICA_HOME", None)
        if formica_home_env is None:
            print(
                f"Environment variable FORMICA_HOME not found, default to {FORMICA_HOME}"
            )
        else:
            FORMICA_HOME = formica_home_env

        _create_formica_home()
        _init_config()
        _init_engine()

        print("Setting init_already to False...")
        _init_already = True


def _create_formica_home():
    if _formica_home_existed():
        return

    # Tạo các thư mục logs
    FORMICA_HOME.mkdir(parents=True)
    _SCHEDULER_LOGS.mkdir(parents=True, exist_ok=True)
    _FLOW_LOGS.mkdir(parents=True, exist_ok=True)

    # Tạo file config từ mẫu nếu chưa có
    if not _CONFIG.exists():
        default_config_data = files("formica.config_templates").joinpath("default_formica.ini").read_bytes()

        # Write it to destination
        pathlib.Path(_CONFIG).write_bytes(default_config_data)


def _formica_home_existed():
    return FORMICA_HOME.exists() and FORMICA_HOME.is_dir()


def _init_config():
    _setup_logging()
    global config
    config.read(_CONFIG, encoding="utf-8")

    # Đọc testing config và ghi đè giá trị của test config lên config chính (nếu trùng key)
    if os.getenv("TESTING", "") == "true":
        config.read(_TEST_CONFIG)


def _setup_logging():
    _logger.info("Setting up logging")
    config_file = pathlib.Path("logging_config.json")
    with open(config_file) as f:
        logging_config = json.loads(f.read())

    # Set log file path
    logging_config["handlers"]["file"]["filename"] = str(
        _SCHEDULER_LOGS / "formica.log"
    )
    logging.config.dictConfig(config=logging_config)
    _logger.info("Done setting up logging")


def _init_engine():
    global engine
    connection_url = config.get(
        "database", "DATABASE_URL", fallback=_SQLITE_DEFAULT_CONNECTION_URL
    )
    print("connection_url:", connection_url)

    # Tạo engine dựa trên môi trường chạy hiện tại,
    # nếu là môi trường TESTING thì tạo một engine in-memory sqlite
    if os.environ.get("TESTING", "") == "true":
        engine = create_async_engine(_SQLITE_TEST_CONNECTION_URL, echo=False)
    else:
        engine = create_async_engine(
            connection_url,
            pool_size=config.getint("database", "CONNECTION_POOL_SIZE"),
            echo=False,
        )


init()
