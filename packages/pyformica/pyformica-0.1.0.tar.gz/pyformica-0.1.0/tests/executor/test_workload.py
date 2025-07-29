import logging

from formica.utils.constant import DeviceRunState
from formica.utils.constant import FINISHED_TASK_STATES
from formica.utils.constant import TaskState
from formica.utils.workload import execute_device_run

logger = logging.getLogger(__name__)


def test_wl(queued_retry_run_mock, session, resource_mock_data):
    """Chạy hàm thực thi workload, sau đó check xem các Task có trạng thái SUCCESS không"""
    assert len(queued_retry_run_mock.tasks) == 4
    assert all(
        [
            task.state == TaskState.WAIT_FOR_EXECUTING
            for task in queued_retry_run_mock.tasks
        ]
    )
    assert queued_retry_run_mock.state == DeviceRunState.RUNNING

    # Không dùng Session mới, vì sqlite không hỗ trợ nhiều connection
    session.expunge_all()
    execute_device_run(queued_retry_run_mock.retry_run_db_id, session=session)

    logger.debug("Finish executing retry run")
    session.add(queued_retry_run_mock)

    session.refresh(queued_retry_run_mock)

    assert len(queued_retry_run_mock.tasks) == 4
    assert queued_retry_run_mock.state in [
        DeviceRunState.SUCCESS,
        DeviceRunState.FAILED,
    ]
    assert all(
        [task.state in FINISHED_TASK_STATES for task in queued_retry_run_mock.tasks]
    )
