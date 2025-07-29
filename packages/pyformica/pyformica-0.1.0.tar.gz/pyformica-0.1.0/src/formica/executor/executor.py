import logging
import multiprocessing
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from formica.db.models import DeviceRunModel
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
        Đẩy DeviceRunModel vào trong work queue
        :param device_run: Đối tượng RetryRun cần được thực thi
        :return: None
        :raises ValueError: RetryRun này đã tồn tại trong work queue rồi
        """
        new_workload = Workload(device_run.device_run_db_id)
        if new_workload in self._work_queue:
            raise ValueError(
                f"DeviceRun này đã tồn tại trong work queue rồi: '{device_run.retry_run_db_id}'"
            )
        self._work_queue.append(new_workload)


class LocalExecutor(Executor):
    def __init__(self):
        super().__init__()
        pass

    async def run(self, session=None):
        # logger.debug(f"Executor running, found {len(self._work_queue)} workloads")
        for work_load in self._work_queue:
            # Pop workload ra trước
            self._work_queue.remove(work_load)

            print("Processing workload: ", work_load.device_run_db_id)
            # process = multiprocessing.Process(
            #     target=execute_device_run, args=[work_load.device_run_db_id], daemon=True
            # )
            # logger.debug(
            #     f"Running retry run using local executor: {work_load.device_run_db_id}"
            # )
            # process.start()
            # self._process_list.append(process)
            await execute_device_run(work_load.device_run_db_id)


class CeleryExecutor(Executor):
    def __init__(self):
        super().__init__()
        pass

    def run(self):
        pass
