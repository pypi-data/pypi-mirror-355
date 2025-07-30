import asyncio
import logging
import time
from time import sleep
from typing import Optional

from formica.executor.executor import Executor
from formica.executor.executor import LocalExecutor
from formica.models.constant import DeviceRunState
from formica.models.constant import FlowRunState
from formica.models.constant import TaskState
from formica.models.models import DeviceRunModel
from formica.models.models import DeviceSetModel
from formica.models.models import FlowRunModel
from formica.models.models import TaskModel
from formica.node.flow import Flow
from formica.settings import app_config
from formica.utils.session import NEW_SESSION
from formica.utils.session import provide_session
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)


def _create_tasks_for_device_run(
    device_run_model: DeviceRunModel, session: AsyncSession
) -> None:
    """Tạo các TaskModel từ thông tin của flow và device_run truyền vào, add vào session luôn"""
    flow = Flow(
        flow_version=device_run_model.flow_run.flow_version,
        arguments=device_run_model.flow_run.args,
    )
    for node_id, op in flow.node_dict.items():
        new_task = TaskModel(
            device_run_db_id=device_run_model.device_run_db_id,
            node_id=node_id,
            state=TaskState.WAIT_FOR_EXECUTING,
        )
        session.add(new_task)


class Scheduler:
    def __init__(self, executor: Executor, multi_processing: bool = True):
        self.executor = executor
        self.multi_processing = multi_processing

    @provide_session
    async def run(
        self, max_iteration: Optional[int] = None, session: AsyncSession = NEW_SESSION
    ):
        if isinstance(self.executor, LocalExecutor):
            logger.debug("executor is local")
        iteration = 0
        while True:
            if max_iteration is not None and iteration >= max_iteration:
                break

            # print("db url is", engine.url)
            flowruns_to_schedule = await FlowRunModel.get_flowrun_to_schedule(session)
            # Expunge these out of the session in order to add the processed one back
            # session.expunge_all()

            processes_do_any_work = []
            for flowrun_model in flowruns_to_schedule:
                temp = await self._schedule_flowrun(flowrun_model, session)
                processes_do_any_work.append(temp)

            # print("Try run executor...", len(self.executor._work_queue))
            await self.executor.run(session)

            iteration += 1
            if not any(processes_do_any_work):
                # logger.info(
                #     f"Didn't schedule anything this time, sleep for 2 seconds..."
                # )
                sleep(app_config.getint("scheduler", "POLLING_INTERVAL"))

        # TODO: Thông báo lý do gì mà vòng lặp schedule dừng
        logger.info(f"Đã lặp đủ số lần lặp schedule: {max_iteration}")
        logger.info("Dừng scheduler...")

    @provide_session
    async def _schedule_flowrun(
        self, flowrun_model: FlowRunModel, session: AsyncSession = NEW_SESSION
    ) -> bool:
        """
        :param flowrun_model: flow_run to process
        :param session: DB session
        :return: Is anything scheduled in this loop?
        """
        if (
            flowrun_model.state == FlowRunState.SUBMITTED
        ):  # Flow submitted, not scheduled
            return await self._schedule_submitted_flowrun(flowrun_model, session)
        else:
            return await self._schedule_running_flowrun(flowrun_model, session)

    async def _schedule_submitted_flowrun(
        self, flowrun_model: FlowRunModel, session: AsyncSession = NEW_SESSION
    ) -> bool:
        # Find the device set and loop through all devices in that set
        device_set = await DeviceSetModel.get_by_key(flowrun_model.device_set_id)
        for device in device_set.devices:
            # create DeviceRunModel
            device_run_model = DeviceRunModel(
                flow_id=flowrun_model.flow_id,
                version=flowrun_model.version,
                device_id=device.device_id,
                flow_run_id=flowrun_model.flow_run_id,
                device_run_id=f"{flowrun_model.run_type}__{time.time()}",
                logical_start_time=flowrun_model.start_time,
            )

            session.add(device_run_model)
            flowrun_model.set_state(FlowRunState.RUNNING)

            # Commit to get device_run_db_id
            await session.commit()
            await session.refresh(device_run_model)

            _create_tasks_for_device_run(device_run_model, session)
            await session.commit()
            # print("Enqueue:", device_run_model.device_run_id)
            self.executor.enqueue_device_run(device_run_model)
            print("size of queue", len(self.executor._work_queue))
            return True

        await session.commit()
        return False

    async def _schedule_running_flowrun(
        self, flowrun_model: FlowRunModel, session: AsyncSession = NEW_SESSION
    ) -> bool:
        latest_device_run = await DeviceRunModel.get_latest_device_run_of_flowrun(
            flowrun_model, session
        )
        if latest_device_run is None:
            # TODO: Handle invalid state - this FlowRun is RUNNING but has no DeviceRun
            raise Exception(
                f"FlowRun: {flowrun_model.flow_id}.{flowrun_model.version}.{flowrun_model.flow_run_id} is RUNNING but has no deviceRun"
            )
        if latest_device_run.state == DeviceRunState.SUCCESS:
            flowrun_model.state = FlowRunState.FINISHED
            await session.commit()
            return True
        elif latest_device_run.state == DeviceRunState.FAILED:
            flowrun_model.state = FlowRunState.FINISHED
            await session.commit()
            return True

        return False


async def _scheduler():
    scheduler_ = Scheduler(LocalExecutor())
    await scheduler_.run()


def main():
    asyncio.run(_scheduler())


if __name__ == "__main__":
    main()
