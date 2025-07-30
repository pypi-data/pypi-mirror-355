import logging
from pathlib import Path

from sqlmodel.ext.asyncio.session import AsyncSession

from formica.execution.context import Context
from formica.execution.device_run import DeviceRun
from formica.models.models import DeviceRunModel
from formica.node.flow import Flow
from formica.settings import FORMICA_HOME
from formica.utils.session import NEW_SESSION
from formica.utils.session import provide_session

logger = logging.getLogger(__name__)


def _prepare_log_file_path(device_run: DeviceRunModel) -> Path:
    log_file_dir = (
        FORMICA_HOME
        / "logs"
        / f"flow_id={device_run.flow_id}"
        / f"version={device_run.version}"
        / f"flow_run={device_run.flow_run_id}"
    )
    log_file_dir.mkdir(parents=True, exist_ok=True)

    return log_file_dir / f"{device_run.device.device_id}.log"


@provide_session
async def execute_device_run(retry_run_db_id: int, session: AsyncSession = NEW_SESSION):
    print("Executing retry run...")
    print("another one", retry_run_db_id, session)
    try:
        device_run_model = await session.get(DeviceRunModel, retry_run_db_id)
        print(
            "Got device run model: ",
            device_run_model.flow_run_id,
            device_run_model.device_id,
        )

        flow = Flow(
            flow_version=device_run_model.flow_run.flow_version,
            arguments=device_run_model.flow_run.args,
        )
        print("Creating context...")
        log_file_path = _prepare_log_file_path(device_run_model)
        context = Context(flow, session, log_file_path, device_run_model.device)
        print("Creating context done")
        # TODO: Nếu None thì sao?
        if device_run_model is not None:
            device_run = DeviceRun(device_run_model, context)
            await device_run.run()
    except Exception as e:
        print("Error: ", e)
