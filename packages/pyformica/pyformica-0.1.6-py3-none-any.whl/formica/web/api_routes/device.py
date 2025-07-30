from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from formica.models.constant import DeviceType
from formica.models.constant import UserRole
from formica.models.models import DeviceModel
from formica.models.models import User
from formica.models.request_models import DeviceFilters
from formica.utils.session import get_session
from formica.web.users import current_active_user
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN

SessionDep = Annotated[AsyncSession, Depends(get_session)]
device_router = APIRouter()


@device_router.post(
    path="", description="Create a device", status_code=HTTP_201_CREATED
)
async def add_device(
    new_device: DeviceModel,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> DeviceModel:
    if not DeviceType.is_valid(new_device.device_type):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Device type is not valid: {new_device.device_type}",
        )

    if await DeviceModel.device_existed(new_device.device_id, session):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Device existed")

    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a device",
        )

    if new_device.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Can't create device in group {new_device.group_id} because you are not a member of this group",
        )

    session.add(new_device)
    await session.commit()
    await session.refresh(new_device)

    return new_device


@device_router.get(path="", description="Get devices", status_code=HTTP_200_OK)
async def get_devices(
    filters: Annotated[DeviceFilters, Query()],
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> list[DeviceModel]:
    return await DeviceModel.filter(user, filters, session)


@device_router.delete(
    path="/{group_id}/{device_id}",
    description="Delete a device",
    status_code=HTTP_204_NO_CONTENT,
)
async def remove_device(
    group_id: str,
    device_id: str,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> None:
    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete a device",
        )

    device = await DeviceModel.get_by_key(group_id, device_id, session)

    if device.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Your groups do not have this device: {device_id}",
        )

    if device is not None:
        await session.delete(device)
        await session.commit()
