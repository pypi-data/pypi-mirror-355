from __future__ import annotations

import configparser
import json
import logging.config
import os
import pathlib
import shutil

from sqlalchemy.ext.asyncio import create_async_engine

# print("Set start method")
# multiprocessing.set_start_method("spawn")

# ------------ PATHS -----------------------------------------------------------------------------------

DEFAULT_FORMICA_HOME = pathlib.Path.home() / "formica"
FORMICA_HOME = (
    pathlib.Path(os.getenv("FORMICA_HOME"))
    if os.getenv("FORMICA_HOME") is not None
    else DEFAULT_FORMICA_HOME
)

CONFIG = FORMICA_HOME / "formica.conf"
TEST_CONFIG = "src/formica/config_templates/test.conf"
LOGS = FORMICA_HOME / "logs"
SCHEDULER_LOGS = LOGS / "scheduler"
FLOW_LOGS = LOGS / "flow"

# ------------ CONNECTIONS ------------------------------------------------------------------------------

SQLITE_DB_TEST_FILE = "test_formica.db"
SQLITE_DB_FILE = "formica.db"
SQLITE_DEFAULT_CONNECTION_URL = f"sqlite+aiosqlite:///{FORMICA_HOME / SQLITE_DB_FILE}"
SQLITE_TEST_CONNECTION_URL = f"sqlite+aiosqlite:///{FORMICA_HOME / SQLITE_DB_TEST_FILE}"

# ------------- OBJECTS ---------------------------------------------------------------------------------

config = configparser.ConfigParser()
engine = None
logger = logging.getLogger(__name__)
init_already = False

# -------------------------------------------------------------------------------------------------------


def init() -> None:
    """
    Khởi tạo thư mục dữ liệu ở đường dẫn `FORMICA_HOME.

    Khi bắt đầu chạy bất cứ thành phần nào thì hàm này cần được gọi để khởi tạo các tài nguyên cần thiết

    Nhưng hàm này chưa khởi tạo DB (vì circular import), caller phải sau đó gọi create_all của SQLModel

    :return: None
    """
    global init_already
    global FORMICA_HOME

    if not init_already:
        print("Init already:", init_already)
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

        print("Setting init_already to False...", os.getpid())
        init_already = True


def _create_formica_home():
    if _formica_home_existed():
        return

    # Tạo các thư mục logs
    FORMICA_HOME.mkdir(parents=True)
    SCHEDULER_LOGS.mkdir(parents=True, exist_ok=True)
    FLOW_LOGS.mkdir(parents=True, exist_ok=True)

    # Tạo file config từ mẫu nếu chưa có
    if not CONFIG.exists():
        default_config = pathlib.Path(
            "src/formica/config_templates/default_formica.conf"
        )
        shutil.copy(default_config, CONFIG)


def _formica_home_existed():
    return FORMICA_HOME.exists() and FORMICA_HOME.is_dir()


def _init_config():
    _setup_logging()
    global config
    config.read(CONFIG, encoding="utf-8")

    # Đọc testing config và ghi đè giá trị của test config lên config chính (nếu trùng key)
    if os.getenv("TESTING", "") == "true":
        config.read(TEST_CONFIG)


def _setup_logging():
    logger.info("Setting up logging")
    config_file = pathlib.Path("logging_config.json")
    with open(config_file) as f:
        logging_config = json.loads(f.read())

    # Set đường dẫn log file của
    logging_config["handlers"]["file"]["filename"] = str(SCHEDULER_LOGS / "formica.log")
    logging.config.dictConfig(config=logging_config)
    logger.info("Done setting up logging")


def _init_engine():
    global engine
    connection_url = (
        config["database"]["DATABASE_URL"]
        if "DATABASE_URL" in config["database"]
        else SQLITE_DEFAULT_CONNECTION_URL
    )
    print("connection_url:", connection_url)

    # Tạo engine dựa trên môi trường chạy hiện tại,
    # nếu là môi trường TESTING thì tạo một engine in-memory sqlite
    if os.environ.get("TESTING", "") == "true":
        engine = create_async_engine(SQLITE_TEST_CONNECTION_URL, echo=False)
    else:
        engine = create_async_engine(
            connection_url,
            pool_size=int(config["database"]["CONNECTION_POOL_SIZE"]),
            echo=False,
        )


init()
