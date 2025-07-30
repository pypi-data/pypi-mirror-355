import asyncio
import logging
import multiprocessing
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from formica.models.models import DeviceRunModel
from formica.utils.workload import execute_device_run

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Workload:
    device_run_db_id: int


class Executor(ABC):
    def __init__(self):
        self._work_queue: list[Workload] = []
        self._process_list: list[multiprocessing.Process] = []

    @abstractmethod
    def run(self):
        pass

    def enqueue_device_run(self, device_run: DeviceRunModel) -> None:
        """
        Enqueue the DeviceRun to the work queue.
        :param device_run: DeviceRunModel instance to be added to the queue.
        :return: None
        :raises ValueError: RetryRun exists in the work queue
        """
        new_workload = Workload(device_run.device_run_db_id)
        if new_workload in self._work_queue:
            raise ValueError(f"DeviceRun existed: '{device_run.retry_run_db_id}'")
        self._work_queue.append(new_workload)


class LocalExecutor(Executor):
    def __init__(self):
        super().__init__()
        pass

    async def run(self, session=None):
        logger.debug(f"Executor running, found {len(self._work_queue)} workloads")
        tasks = [
            asyncio.create_task(execute_device_run(work_load.device_run_db_id))
            for work_load in self._work_queue
        ]
        await asyncio.gather(*tasks)

        # Clear the queue
        self._work_queue.clear()


class CeleryExecutor(Executor):
    def __init__(self):
        super().__init__()
        pass

    def run(self):
        pass
