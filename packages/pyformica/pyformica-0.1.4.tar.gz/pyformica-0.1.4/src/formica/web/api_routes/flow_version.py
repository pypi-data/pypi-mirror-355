from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from formica.models.models import FlowModel
from formica.models.models import FlowVersionModel
from formica.models.models import User
from formica.models.request_models import FlowVersionFilters
from formica.utils.session import get_session
from formica.web.users import current_active_user
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN
from starlette.status import HTTP_404_NOT_FOUND

SessionDep = Annotated[AsyncSession, Depends(get_session)]
flow_version_router = APIRouter()


@flow_version_router.post(
    path="", description="Tạo một FlowVersion", status_code=HTTP_201_CREATED
)
async def add_flow_version(
    new_flow_version: FlowVersionModel,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> FlowVersionModel:
    new_flow_version = FlowVersionModel.model_validate(new_flow_version)
    flow = await FlowModel.get_by_key(new_flow_version.flow_id, session)

    if flow is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Flow not found")

    # Only the owner or superuser can create new flow version
    if flow.owner_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to create flow version on this flow",
        )

    if await FlowVersionModel.flow_version_existed(
        new_flow_version.flow_id, new_flow_version.version
    ):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Flow version existed"
        )

    # valid, message = validate_flow_json(new_flow_version.structure)
    # if not valid:
    #     raise HTTPException(status_code=400, detail=f"Flow syntax error: {message}")

    new_flow_version.flow = flow
    session.add(new_flow_version)
    await session.commit()
    await session.refresh(new_flow_version)
    return new_flow_version


@flow_version_router.get(
    path="", description="Get flow versions", status_code=HTTP_200_OK
)
async def get_flow_versions(
    filters: Annotated[FlowVersionFilters, Query()],
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> list[FlowVersionModel]:
    return await FlowVersionModel.filter(user, filters, session)
