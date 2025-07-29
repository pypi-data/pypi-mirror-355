import re
from typing import Optional

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

# Security
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def validate_flow_json(json: dict) -> tuple[bool, str]:
    """
    Check xem định nghĩa json của flow đã đúng cú pháp chưa
    :param json: JSON cần check
    :return: `True` nếu đúng cú pháp, không thì `False`, kèm theo một chuỗi msg chứa thông tin lỗi
    """
    # Check xem có các trường cần thiết không: flow_version, flow_id, nodes, directed_link
    required_fields = [
        "ff_version",
        "params",
        "globals",
        "nodes",
        "directed_links",
    ]
    for field in required_fields:
        if field not in json:
            return False, f"Missing required field: {field}"

    # Check flow_version có hỗ trợ không
    supported_versions = ["0.1"]

    if json["ff_version"] not in supported_versions:
        return False, f"Flow version {json['ff_version']} not supported."

    # Check flow_id có trùng với cái nào đã tồn tại chưa (cần kết nối DB)

    # Check device_set có tồn tại không (Cần check DB)

    # Check xem biến globals có phải dạng dictionary không, và các value có phải dạng str không
    if isinstance(json["globals"], dict):
        for key, value in json["globals"].items():
            if not isinstance(value, str):
                return False, f"Global variable {key}: {value} is not a string."
    else:
        return False, "globals must be an object"

    # Check các nodes

    # Check các liên kết giữa các operator
    for link in json["directed_links"]:
        pass

    return True, "Success"


def camel_to_snake(name):
    # Converts camelCase or PascalCase to snake_case
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def convert_keys_to_snake_case(obj):
    if isinstance(obj, dict):
        return {
            camel_to_snake(k): convert_keys_to_snake_case(v) for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_keys_to_snake_case(i) for i in obj]
    else:
        return obj


# def convert_react_flow_to_formica(react_flow: dict):
#     return react_flow["structure"]["version"]
