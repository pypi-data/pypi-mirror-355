import logging
import time
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from formica.models.models import FlowRunModel
from formica.models.models import FlowVersionModel
from formica.models.models import User
from formica.models.request_models import CreateFlowRun
from formica.models.request_models import FlowRunFilters
from formica.models.request_models import Log
from formica.models.request_models import ResponseDeviceRun
from formica.models.request_models import ResponseFlowRun
from formica.settings import FORMICA_HOME
from formica.utils.session import get_session
from formica.web.users import current_active_user
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN
from starlette.status import HTTP_404_NOT_FOUND

SessionDep = Annotated[AsyncSession, Depends(get_session)]
flow_run_router = APIRouter()
logger = logging.getLogger(__name__)


@flow_run_router.post(
    path="", description="Create a FlowRun", status_code=HTTP_201_CREATED
)
async def add_flow_run(
    create_flow_run: CreateFlowRun,
    session: SessionDep,
    user: User = Depends(current_active_user),
) -> FlowRunModel:
    # new_flow_run = FlowRunModel.model_validate(new_flow_run)
    new_flow_run = FlowRunModel(
        flow_run_id=f"manual__{int(time.time())}",
        flow_id=create_flow_run.flow_id,
        version=create_flow_run.version,
        device_set_id=create_flow_run.device_set_id,
        description=create_flow_run.description,
        args=create_flow_run.args,
        run_type=create_flow_run.run_type,
        owner_id=user.id,
    )
    new_flow_run.flow_version = await FlowVersionModel.get_by_key(
        new_flow_run.flow_id, new_flow_run.version
    )

    flow_version = await FlowVersionModel.get_by_key(
        new_flow_run.flow_id, new_flow_run.version
    )

    if flow_version is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Flow version not found"
        )

    if await FlowRunModel.flow_run_existed(
        new_flow_run.flow_id, new_flow_run.version, new_flow_run.flow_run_id
    ):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Flow run existed")

    if flow_version.flow.group_id not in (await user.get_group_ids()):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="This flow version is not in your group, you cannot create a flow run for it",
        )
    session.expunge(user)
    session.add(new_flow_run)
    await session.commit()
    await session.refresh(new_flow_run)

    return new_flow_run


@flow_run_router.get(path="", description="Get flow runs", status_code=HTTP_200_OK)
async def get_flow_runs(
    session: SessionDep,
    filters: Annotated[FlowRunFilters, Query()],
    user: User = Depends(current_active_user),
) -> list[ResponseFlowRun]:
    db_flow_runs: list[FlowRunModel] = await FlowRunModel.filter(user, filters, session)
    response = []

    for db_flow_run in db_flow_runs:
        # Create the ResponseDeviceRun objects
        response_device_runs = []
        for device_run in db_flow_run.device_runs:
            # Get the logs
            log_file = (
                FORMICA_HOME
                / "logs"
                / f"flow_id={device_run.flow_id}"
                / f"version={device_run.version}"
                / f"flow_run={device_run.flow_run_id}"
                / f"{device_run.device_id}.log"
            )

            logs = []
            try:
                with open(log_file, "r") as f:
                    logs = f.readlines()
            except FileNotFoundError as e:
                logger.warning(f"Can't find log file at {log_file}, exception: {e}")

            response_device_run = ResponseDeviceRun(
                id=device_run.device_run_db_id,
                flow_id=device_run.flow_id,
                version=device_run.version,
                flow_run_id=device_run.flow_run_id,
                device_id=device_run.device_id,
                state=device_run.state,
                logical_start_time=device_run.logical_start_time,
                actual_start_time=device_run.actual_start_time,
                end_time=device_run.end_time,
                created_at=device_run.created_at,
                logs=[
                    Log(timestamp="", level="info", message=log) for log in logs
                ],  # Add logs to the response
            )
            response_device_runs.append(response_device_run)

        response_flow_run = ResponseFlowRun(
            flow_run_id=db_flow_run.flow_run_id,
            flow_id=db_flow_run.flow_id,
            version=db_flow_run.version,
            description=db_flow_run.description,
            device_set_id=db_flow_run.device_set_id,
            args=db_flow_run.args,
            run_type=db_flow_run.run_type,
            start_time=db_flow_run.start_time,
            end_time=db_flow_run.end_time,
            state=db_flow_run.state,
            created_at=db_flow_run.created_at,
            device_runs=response_device_runs,
        )

        response.append(response_flow_run)

    return response
