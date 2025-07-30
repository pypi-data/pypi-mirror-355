from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from formica.models.constant import UserRole
from formica.models.models import FlowModel
from formica.models.models import FlowRunModel
from formica.models.models import FlowVersionModel
from formica.models.models import GroupModel
from formica.models.models import User
from formica.models.request_models import FlowFilters
from formica.models.request_models import ResponseFlow
from formica.models.request_models import UpdateFlow
from formica.utils.session import get_session
from formica.web.users import current_active_user
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_204_NO_CONTENT
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN
from starlette.status import HTTP_404_NOT_FOUND

SessionDep = Annotated[AsyncSession, Depends(get_session)]
flow_router = APIRouter()


@flow_router.post(
    path="",
    description="Create a new flow",
    status_code=HTTP_201_CREATED,
)
async def add_flow(
    new_flow: FlowModel, session: SessionDep, user: User = Depends(current_active_user)
) -> FlowModel:
    if await FlowModel.flow_existed(new_flow.flow_id, session):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Flow existed")

    group_model = await GroupModel.get_by_key(new_flow.group_id, session)

    if group_model is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Group not existed")

    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a flow",
        )

    # Check if user is in the group
    if user not in group_model.members:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"User {user.email} is not a member of group {new_flow.group_id}",
        )

    new_flow.owner_id = user.id
    session.add(new_flow)
    await session.commit()
    await session.refresh(new_flow)

    return new_flow


@flow_router.get(path="", description="Get flows", status_code=HTTP_200_OK)
async def get_flows(
    filters: Annotated[FlowFilters, Query()],
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> list[FlowModel]:
    return await FlowModel.filter(user, filters, session)


@flow_router.get(
    path="/{flow_id}", description="Lấy flow theo flow id", status_code=HTTP_200_OK
)
async def get_flow(
    flow_id: str, session: SessionDep, user: User = Depends(current_active_user)
) -> ResponseFlow:
    flow = await FlowModel.get_by_key(flow_id, session)

    if flow is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Flow not found")

    if flow.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this flow",
        )

    return ResponseFlow.model_validate(flow.model_dump())


@flow_router.get(
    path="/{flow_id}/versions/{version}",
    description="Get a flow version",
    status_code=HTTP_200_OK,
)
async def get_flow_version(
    flow_id: str,
    version,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> FlowVersionModel:
    flow_version = await FlowVersionModel.get_by_key(flow_id, version, session)
    if not flow_version:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Version not found")

    if flow_version.flow.group_id not in user.get_group_ids(session):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this flow",
        )

    return flow_version


@flow_router.get(
    path="/{flow_id}/versions/{version}/flow-runs/{flow_run_id}",
    description="Get a flow run",
    status_code=HTTP_200_OK,
)
async def get_flow_run(
    flow_id: str,
    version: str,
    flow_run_id: str,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> FlowRunModel:
    flow_run = await FlowRunModel.get_by_key(flow_id, version, flow_run_id, session)
    if not flow_run:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Flow run not found")

    if flow_run.flow_version.flow_id.group_id not in user.get_group_ids(session):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this flow",
        )

    return flow_run


@flow_router.patch(path="/{target_flow_id}", description="Update flow")
async def update_flow(
    target_flow_id: Annotated[str, Path(title="The target flow id to update")],
    update: UpdateFlow,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    flow = await FlowModel.get_by_key(target_flow_id, session)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Only the owner or superuser can update the flow
    if flow.owner_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this flow",
        )

    update_data = update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(flow, key, value)

    session.add(flow)
    await session.commit()
    await session.refresh(flow)
    return flow


@flow_router.delete(
    path="/{flow_id}",
    description="Delete a flow",
    status_code=HTTP_204_NO_CONTENT,
)
async def remove_device(
    flow_id: str,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> None:
    if not (user.is_superuser or user.role == UserRole.ADMIN):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete a flow",
        )

    flow = await FlowModel.get_by_key(flow_id, session)

    if flow.group_id not in (await user.get_group_ids(session)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Your groups do not have this flow: {flow_id}",
        )

    if flow is not None:
        await session.delete(flow)
        await session.commit()
