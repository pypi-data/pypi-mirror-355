import logging

import pytest
from formica.executor.executor import LocalExecutor
from formica.node.flow import Flow

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def executor():
    executor = LocalExecutor()
    return executor


@pytest.fixture(scope="module")
def ssh_2_commands_flow_mock(sample_flow_structures):
    return Flow(
        flow_id="mock_flow_for_ssh_test",
        structure=sample_flow_structures["test_ssh_2_commands"],
    )


# def test_executor_run(
#         executor,
#         queued_retry_run_mock,
#         resource_mock_data,
#         session
# ):
#     assert len(queued_retry_run_mock.tasks) == 4
#     assert all(
#         [
#             task.state == TaskState.WAIT_FOR_EXECUTING
#             for task in queued_retry_run_mock.tasks
#         ]
#     )
#     assert queued_retry_run_mock.state == RetryRunState.RUNNING
#     # context = Context(ssh_2_commands_flow_mock, session)
#     # retry_run = RetryRun(queued_retry_run_mock, context)
#     executor.enqueue_retryrun(queued_retry_run_mock)
#     executor.run()
#     sleep(2)
#
#     logger.debug(f"Finish executing retry run")
#     session.add(queued_retry_run_mock)
#
#     session.refresh(queued_retry_run_mock)
#
#     assert len(queued_retry_run_mock.tasks) == 4
#     assert queued_retry_run_mock.state in [RetryRunState.SUCCESS, RetryRunState.FAILED]
#     assert all(
#         [task.state in FINISHED_TASK_STATES for task in queued_retry_run_mock.tasks]
#     )
