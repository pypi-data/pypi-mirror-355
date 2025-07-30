from fastapi import APIRouter
from formica.models.request_models import UserCreate
from formica.models.request_models import UserRead
from formica.web.api_routes.credential import credential_router
from formica.web.api_routes.device import device_router
from formica.web.api_routes.device_set import device_set_router
from formica.web.api_routes.flow import flow_router
from formica.web.api_routes.flow_run import flow_run_router
from formica.web.api_routes.flow_version import flow_version_router
from formica.web.api_routes.group import group_router
from formica.web.api_routes.user import user_router
from formica.web.users import auth_backend
from formica.web.users import fastapi_users


api_router = APIRouter()

api_router.include_router(credential_router, prefix="/credentials", tags=["credential"])
api_router.include_router(device_router, prefix="/devices", tags=["device"])
api_router.include_router(device_set_router, prefix="/device-sets", tags=["device-set"])
api_router.include_router(flow_router, prefix="/flows", tags=["flow"])
api_router.include_router(flow_run_router, prefix="/flow-runs", tags=["flow-run"])
api_router.include_router(
    flow_version_router, prefix="/flow-versions", tags=["flow-version"]
)
api_router.include_router(group_router, prefix="/groups", tags=["group"])
api_router.include_router(user_router, prefix="/users", tags=["user"])


# Authentication
api_router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
api_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
# api_router.include_router(
#     fastapi_users.get_reset_password_router(),
#     prefix="/auth",
#     tags=["auth"],
# )
# api_router.include_router(
#     fastapi_users.get_verify_router(UserRead),
#     prefix="/auth",
#     tags=["auth"],
# )
# api_router.include_router(
#     fastapi_users.get_users_router(UserRead, UserUpdate),
#     prefix="/users",
#     tags=["users"],
# )
