from enum import Enum
from typing import Optional

from formica.settings import app_config


class ValidateEnum(Enum):
    @classmethod
    def is_valid(cls, enum_str: str) -> bool:
        print(cls.__members__.values())
        return enum_str in cls.__members__.values()


class FlowRunState(str, ValidateEnum):
    SUBMITTED = "submitted"
    RUNNING = "running"
    FINISHED = "finished"


class FlowRunType(str, ValidateEnum):
    MANUAL = "manual"
    SCHEDULE = "schedule"


class DeviceRunState(str, ValidateEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class TaskState(str, ValidateEnum):
    WAIT_FOR_EXECUTING = "wait_for_executing"
    SKIPPED = "skipped"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class FlowRetryMode(str, ValidateEnum):
    SKIP_SUCCESS = "skip_success"
    RETRY_ALL = "retry_all"


class TaskTriggerRule(str, ValidateEnum):
    """Điều kiện để toán tử được chạy"""

    SUCCESS = "success"  # Toán tử trước đó phải thành công
    DONE = "done"  # Toán tử trước đó chỉ cần chạy xong


class UserRole(str, ValidateEnum):
    ADMIN = "admin"
    OPERATOR = "operator"


FINISHED_TASK_STATES = (TaskState.SUCCESS, TaskState.FAILED, TaskState.SKIPPED)
INITIAL_FLOW_STATE = {
    "nodes": [
        {
            "id": "1",
            "type": "customNode",
            "position": {"x": 250, "y": 100},
            "data": {
                "label": "Start",
                "type": "trigger",
                "description": "Begins the workflow",
                "inputs": [],
                "outputs": [{"id": "out-1", "label": "Output"}],
                "config": {},
            },
        }
    ]
}


class ConnectionType(ValidateEnum):
    SSH = "ssh"
    TELNET = "telnet"
    HTTP = "http"
    HTTPS = "https"
    FTP = "ftp"
    SFTP = "sftp"


class DeviceType(ValidateEnum):
    LINUX = "linux"
    HUAWEI = "huawei"
    JUNIPER = "juniper"
    GCOM = "gcom"
    ZTE = "zte"
    H3C = "h3c"

    @classmethod
    def get_device_type(cls, code: str) -> Optional["DeviceType"]:
        if "HW" in code or "HA" in code:
            return DeviceType.HUAWEI
        elif "GC" in code:
            return DeviceType.GCOM
        elif "CH" in code:
            return DeviceType.H3C
        else:
            return None


class CatalogType(ValidateEnum):
    OLT = "olt"
    SWITCH = "switch"


DEFAULT_IDLE_TIMEOUT = app_config.getint("connection", "DEFAULT_IDLE_TIMEOUT")
DEFAULT_CONNECT_TIMEOUT = app_config.getint("connection", "DEFAULT_CONNECT_TIMEOUT")
DEFAULT_COMMAND_TIMEOUT = app_config.getint("connection", "DEFAULT_COMMAND_TIMEOUT")

CONNECTION_MAX_RETRIES = app_config.getint("connection", "CONNECTION_MAX_RETRIES")
CONNECTION_RETRY_SLEEP = app_config.getint("connection", "CONNECTION_RETRY_SLEEP")
