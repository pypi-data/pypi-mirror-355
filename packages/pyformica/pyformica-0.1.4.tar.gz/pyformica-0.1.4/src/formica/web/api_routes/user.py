from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from formica.models.models import User
from formica.models.request_models import UpdateUser
from formica.utils.session import get_session
from formica.web.users import current_active_user
from sqlmodel.ext.asyncio.session import AsyncSession

SessionDep = Annotated[AsyncSession, Depends(get_session)]
user_router = APIRouter()


@user_router.get(path="", description="Get all users")
async def get_all_users(
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    if not user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to view all users"
        )
    return await User.get_all(session)


@user_router.get(path="/me", description="Get current user")
async def get_current_user(
    user: User = Depends(current_active_user),
):
    return user


@user_router.patch(path="/{target_user_id}", description="Update user")
async def update_user(
    target_user_id: Annotated[str, Path(title="The target user id to update")],
    update: UpdateUser,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    if not user.is_superuser and user.id != target_user_id:
        raise HTTPException(
            status_code=403, detail="You do not have permission to update this user"
        )

    if update.role is not None and not user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Only superusers can change user roles"
        )

    target_user = await session.get(User, target_user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(target_user, key, value)

    session.add(target_user)
    await session.commit()
    await session.refresh(target_user)
    return target_user
