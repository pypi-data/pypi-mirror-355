from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from formica.models.constant import UserRole
from formica.models.models import CredentialModel
from formica.models.models import DeviceModel
from formica.models.models import User
from formica.models.request_models import DeviceFilters
from formica.utils.session import get_session
from formica.web.users import current_active_user
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN

SessionDep = Annotated[AsyncSession, Depends(get_session)]
credential_router = APIRouter()


@credential_router.post(
    path="",
    description="Create a credential to connect to a device",
    status_code=HTTP_201_CREATED,
)
async def add_credential(
    new_credential: CredentialModel,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> CredentialModel:
    # if not ConnectionType.is_valid(new_credential.connection_type):
    #     raise HTTPException(
    #         status_code=HTTP_400_BAD_REQUEST,
    #         detail=f"Connection type is not valid: {new_credential.connection_type}",
    #     )

    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a credential",
        )

    device = await DeviceModel.get_by_key(
        new_credential.group_id, new_credential.device_id, session
    )

    if device is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Device not found")

    if device.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Can't create credential of device in group that you are not a member of",
        )

    session.add(new_credential)
    await session.commit()
    await session.refresh(new_credential)

    return new_credential


@credential_router.get(path="", description="Get credentials")
async def get_credentials(
    session: SessionDep,
    filters: Annotated[DeviceFilters, Query()],
    user: User = Depends(current_active_user),
) -> list[CredentialModel]:
    return await CredentialModel.filter(user, filters, session)


@credential_router.delete(path="/{credential_id}", description="Delete a credential")
async def remove_credential(
    credential_id: str, session: SessionDep, user: User = Depends(current_active_user)
) -> None:
    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete a credential",
        )

    credential = await CredentialModel.get_by_key(credential_id, session)

    if credential.device.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Can't delete credential of device in group that you are not a member of",
        )

    if credential is not None:
        await session.delete(credential)
        await session.commit()
