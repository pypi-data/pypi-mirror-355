from time import sleep

import requests
from formica.db.models import FlowRunModel
from formica.utils.constant import DeviceRunState
from formica.utils.constant import FlowRunState
from formica.utils.constant import FlowRunType


def test_integrate(
    host,
    sample_flow_structures,
    resource_mock_data,
    session,
    formica_standalone,
    clean_up_remote_test_files,
):
    """
    Chạy formica standalone, sau đó đẩy một FlowRun vào để chạy thử
    Kiểm tra trạng thái của RetryRun và các Task, kiểm tra xem lệnh có thực sự được chạy không
    """
    insert_test_data(sample_flow_structures, "test_ssh_2_commands", host)
    flow_id = "test_ssh_2_commands"
    version = "v1"
    flow_run_id = "test_run"

    # Kiểm tra các object trong DB xem có đúng ko
    flow_run: FlowRunModel = FlowRunModel.get_by_key(
        flow_id, version, flow_run_id, session
    )
    assert flow_run is not None
    assert flow_run.state in [FlowRunState.SUBMITTED]

    # Chờ scheuduler chạy
    sleep(3)

    # Kiểm tra các object trong DB xem có đúng ko
    session.refresh(flow_run)
    assert flow_run is not None
    # assert flow_run.state == FlowRunState.FINISHED

    assert len(flow_run.retry_runs) == 1
    assert flow_run.state == FlowRunState.FINISHED
    assert flow_run.retry_runs[0].state == DeviceRunState.SUCCESS
    assert len(flow_run.retry_runs[0].tasks) == 4
    assert all(
        task.state == DeviceRunState.SUCCESS for task in flow_run.retry_runs[0].tasks
    )


def insert_test_data(flow_structures: dict, structure_id: str, host: str):
    """Đẩy flow,"""
    flow_id = "test_ssh_2_commands"
    version = "v1"
    flow_run_id = "test_run"

    # Chờ cho api server start lên
    # Code logic check xem api server đã start chưa, để chạy, không phải chờ một khoảng thời gian cố định
    sleep(3)

    # POST flow
    url = f"{host}/flow"
    body = {
        "flow_id": flow_id,
        "description": "post new flow for testing",
    }
    requests.post(url, json=body)

    # POST flow version
    url = f"{host}/flow_version"
    body = {
        "flow_id": flow_id,
        "version": version,
        "description": "version for testing",
        "structure": flow_structures[structure_id],
    }
    requests.post(url, json=body)

    # POST flow run
    url = f"{host}/flow_run"
    body = {
        "flow_id": flow_id,
        "version": version,
        "flow_run_id": flow_run_id,
        "description": "test run",
        "run_type": FlowRunType.MANUAL,
    }
    requests.post(url, json=body)
