from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from formica.models.models import GroupModel
from formica.models.models import User
from formica.models.request_models import DeviceSetFilters
from formica.models.request_models import GroupResponse
from formica.models.request_models import ResponseUser
from formica.models.request_models import UpdateUsersOfGroup
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
group_router = APIRouter()


@group_router.post(path="", description="Create a group", status_code=HTTP_201_CREATED)
async def add_group(
    new_group: GroupModel,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> GroupResponse:
    if not user.is_superuser:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a group",
        )

    if await GroupModel.group_existed(new_group.group_id, session):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Group existed")

    new_group.members.append(user)
    session.add(new_group)
    await session.commit()
    inserted_group = await session.get(GroupModel, new_group.group_id)

    response = GroupResponse(
        group_id=inserted_group.group_id,
        description=inserted_group.description,
        members=[member.id for member in inserted_group.members],
    )

    return response


@group_router.post(
    path="/{group_id}/users",
    description="Update members of a group",
    status_code=HTTP_200_OK,
)
async def update_users(
    group_id: Annotated[str, Path(title="The target group id to update")],
    add_user_request: UpdateUsersOfGroup,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> GroupResponse:
    if not user.is_superuser:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to update group members",
        )

    db_group: GroupModel = await GroupModel.get_by_key(group_id, session)

    if db_group is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Group not existed"
        )

    users = await User.get_user_by_ids(add_user_request.users, session)

    # Should always have the current user (superuser) in the group
    if user not in db_group.members:
        users.extend([user])
    print(f"users are: {users}")
    db_group.members = users
    session.add(db_group)
    await session.commit()

    response = GroupResponse(
        group_id=db_group.group_id,
        description=db_group.description,
        members=[member.id for member in db_group.members],
    )

    return response


@group_router.delete(
    path="/{group_id}", description="Delete a group", status_code=HTTP_204_NO_CONTENT
)
async def remove_group(
    group_id: str, session: SessionDep, user: User = Depends(current_active_user)
) -> None:
    if not user.is_superuser:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete a group",
        )

    group = await GroupModel.get_by_key(group_id, session)

    if group is not None:
        await session.delete(group)
        await session.commit()


@group_router.get(path="", description="Get groups")
async def get_groups(
    filters: Annotated[DeviceSetFilters, Query()],
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> list[GroupResponse]:
    groups = await GroupModel.filter(user, filters, session)
    group_responses = []

    groups = [group for group in groups if user in group.members]

    for group in groups:
        group_response = GroupResponse(
            group_id=group.group_id,
            description=group.description,
            members=[member.id for member in group.members],
        )
        group_responses.append(group_response)

    return group_responses


@group_router.get(path="/{group_id}/members", description="Get groups")
async def get_members_of_group(
    group_id: str,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> list[ResponseUser]:
    group = await GroupModel.get_by_key(group_id, session)

    if group is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Group not found")

    if user not in group.members:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this group's members",
        )

    return [
        ResponseUser(
            id=member.id,
            name=member.name,
            email=member.email,
            role=member.role,
            is_superuser=member.is_superuser,
        )
        for member in group.members
    ]


@group_router.get(
    path="/{group_id}", description="Get a group", status_code=HTTP_200_OK
)
async def get_flow(
    group_id: str, session: SessionDep, user: User = Depends(current_active_user)
) -> GroupResponse:
    group = await GroupModel.get_by_key(group_id, session)

    if group is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Flow not found")

    if user not in group.members:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this group",
        )

    return GroupResponse(
        group_id=group.group_id,
        description=group.description,
        members=[member.id for member in group.members],
    )
