import uuid
from datetime import datetime
from typing import Optional

from fastapi_users import schemas
from formica.models.constant import DeviceRunState
from formica.models.constant import FlowRunState
from formica.models.constant import FlowRunType
from formica.models.constant import UserRole
from pydantic import BaseModel


class CreateDeviceSet(BaseModel):
    device_set_id: str
    description: str
    devices: list[str]
    group_id: str


class UpdateUser(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    email: Optional[str] = None
    is_active: Optional[str] = None


class UpdateFlow(BaseModel):
    flow_id: Optional[str] = None
    description: Optional[str] = None
    saved_state: dict


class UpdateUsersOfGroup(BaseModel):
    users: list[str]


class UpdateDevicesOfDeviceSet(BaseModel):
    devices: list[str]


class CreateFlowRun(BaseModel):
    flow_id: str
    version: str
    description: str
    device_set_id: str
    run_type: FlowRunType
    args: Optional[dict[str, str]] = None


class ResponseFlow(BaseModel):
    flow_id: str
    description: str
    saved_state: dict
    group_id: str


class Log(BaseModel):
    timestamp: str
    level: str
    message: str


class ResponseDeviceRun(BaseModel):
    id: int
    flow_id: str
    version: str
    flow_run_id: str
    device_id: str
    state: DeviceRunState
    logical_start_time: datetime
    actual_start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    logs: list[Log]


class ResponseFlowRun(BaseModel):
    flow_run_id: str
    flow_id: str
    version: str
    description: str
    device_set_id: str
    args: Optional[dict[str, str]] = None
    run_type: FlowRunType
    start_time: datetime
    end_time: Optional[datetime]
    state: FlowRunState
    created_at: datetime
    device_runs: list[ResponseDeviceRun]


class ResponseDeviceSet(BaseModel):
    device_set_id: str
    description: str
    devices: list[str]
    group_id: str


class UpdateDeviceSet(BaseModel):
    device_set_id: str
    devices: list[str]


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    name: str


class UserUpdate(schemas.BaseUserUpdate):
    pass


class ResponseUser(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    is_superuser: bool


class GroupResponse(BaseModel):
    group_id: str
    description: str
    members: list[uuid.UUID]  # list of user ids


class DeviceSetResponse(BaseModel):
    device_set_id: str
    description: str
    devices: list[str]


# ============================= FILTERS ================================
class DeviceFilters(BaseModel):
    group_id: Optional[str] = None


class CredentialFilters(BaseModel):
    group_id: Optional[str] = None


class DeviceSetFilters(BaseModel):
    group_id: Optional[str] = None


class FlowFilters(BaseModel):
    group_id: Optional[str] = None


class FlowVersionFilters(BaseModel):
    flow_id: Optional[str] = None
    group_id: Optional[str] = None


class FlowRunFilters(BaseModel):
    flow_id: Optional[str] = None
    flow_version_id: Optional[str] = None
    group_id: Optional[str] = None


class GroupFilters(BaseModel):
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    group_description: Optional[str] = None
