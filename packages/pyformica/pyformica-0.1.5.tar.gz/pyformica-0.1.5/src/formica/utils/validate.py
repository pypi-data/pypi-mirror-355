import re
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


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
