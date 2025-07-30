from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from formica.models.constant import UserRole
from formica.models.models import DeviceModel
from formica.models.models import DeviceSetModel
from formica.models.models import User
from formica.models.request_models import CreateDeviceSet
from formica.models.request_models import DeviceSetFilters
from formica.models.request_models import DeviceSetResponse
from formica.models.request_models import ResponseDeviceSet
from formica.models.request_models import UpdateDevicesOfDeviceSet
from formica.utils.session import get_session
from formica.web.users import current_active_user
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN

SessionDep = Annotated[AsyncSession, Depends(get_session)]
device_set_router = APIRouter()


@device_set_router.get(
    path="/{device_set_id}", description="Get a device set", status_code=HTTP_200_OK
)
async def get_device_set(
    device_set_id: str, session: SessionDep, user: User = Depends(current_active_user)
) -> ResponseDeviceSet:
    device_set = await DeviceSetModel.get_by_key(device_set_id, session)

    if device_set is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Device set not found"
        )

    if device_set.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Can't get device set in group {device_set.group_id} because you are not a member of this group",
        )

    return ResponseDeviceSet(
        device_set_id=device_set.device_set_id,
        description=device_set.description,
        devices=[device.device_id for device in device_set.devices],
        group_id=device_set.group_id,
    )


@device_set_router.get(path="", description="Get device sets", status_code=HTTP_200_OK)
async def get_device_sets(
    filters: Annotated[DeviceSetFilters, Query()],
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> list[ResponseDeviceSet]:
    db_device_sets = await DeviceSetModel.filter(user, filters, session)
    return [
        ResponseDeviceSet(
            device_set_id=device_set.device_set_id,
            description=device_set.description,
            devices=[device.device_id for device in device_set.devices],
            group_id=device_set.group_id,
        )
        for device_set in db_device_sets
    ]


@device_set_router.post(
    path="", description="Create a device set", status_code=HTTP_201_CREATED
)
async def add_device_set(
    new_device_set: CreateDeviceSet,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> CreateDeviceSet:
    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a device set",
        )

    if new_device_set.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Can't create device set in group {new_device_set.group_id} because you are not a member of this group",
        )

    db_device_set = DeviceSetModel(
        device_set_id=new_device_set.device_set_id,
        description=new_device_set.description,
        group_id=new_device_set.group_id,
    )
    not_found_devices = []

    for device_id in new_device_set.devices:
        device = await DeviceModel.get_by_key(new_device_set.group_id, device_id)
        if device is None:
            not_found_devices.append(device_id)
        else:
            db_device_set.devices.append(device)

    if not_found_devices:
        raise HTTPException(
            status_code=400,
            detail=f"Devices with these ids not found: {'\n'.join(not_found_devices)}",
        )

    session.add(db_device_set)
    await session.commit()
    await session.refresh(db_device_set)

    return new_device_set


# @device_set_router.patch(
#     path="",
#     description="Thêm một hoặc nhiều device vào một device set có sẵn",
# )
# async def update_device_set(
#     update_device_set: UpdateDeviceSet, session: SessionDep
# ) -> DeviceSetModel:
#     db_device_set = await DeviceSetModel.get_device_set_by_id(
#         update_device_set.device_set_id
#     )
#
#     for device_id in update_device_set.device_id_list:
#         device = DeviceModel.get_device_by_device_id(device_id)
#         if device is None:
#             raise HTTPException(
#                 status_code=400, detail=f"Device with this id not found: {device_id}"
#             )
#
#         db_device_set.devices.append(device)
#
#     session.add(db_device_set)
#     await session.commit()
#     await session.refresh(db_device_set)
#
#     return db_device_set


@device_set_router.delete(
    path="/{device_set_id}",
    description="Delete a device set",
    status_code=HTTP_204_NO_CONTENT,
)
async def remove_device_set(
    device_set_id: str, session: SessionDep, user: User = Depends(current_active_user)
) -> None:
    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete a device",
        )

    device_set = await DeviceSetModel.get_by_key(device_set_id, session)

    if device_set.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Your groups do not have this device set: {device_set_id}",
        )

    if device_set is not None:
        await session.delete(device_set)
        await session.commit()


@device_set_router.post(
    path="/{device_set_id}/devices",
    description="Update devices of a device set",
    status_code=HTTP_200_OK,
)
async def update_devices(
    device_set_id: Annotated[str, Path(title="The target group id to update")],
    update_devices_request: UpdateDevicesOfDeviceSet,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> DeviceSetResponse:
    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to update devices of a device set",
        )

    db_device_set: DeviceSetModel = await DeviceSetModel.get_by_key(
        device_set_id, session
    )
    if db_device_set is None:
        raise HTTPException(status_code=400, detail="Device set not existed")

    if db_device_set.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Can't update devices in device set {device_set_id} because you are not a member of the group it belongs to",
        )

    devices = await DeviceModel.get_devices_by_id(
        update_devices_request.devices, session
    )
    db_device_set.devices = devices
    session.add(db_device_set)
    await session.commit()

    response = DeviceSetResponse(
        device_set_id=db_device_set.group_id,
        description=db_device_set.description,
        devices=[device.device_id for device in db_device_set.devices],
    )

    return response
