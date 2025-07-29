import pytest
import requests
from formica.utils.constant import FlowRunType


@pytest.mark.asyncio
async def test_create_objects(host, api_server, session, sample_flow_structures):
    # Test POST device
    url = f"{host}/device"
    body = {"device_id": "new_dev_1", "host": "localhost", "device_type": "linux"}

    response = requests.post(url, json=body)
    data = response.json()

    assert response.status_code == 200

    assert data["device_id"] == "new_dev_1"
    assert data["host"] == "localhost"
    assert data["device_type"] == "linux"

    # Test POST credential
    url = f"{host}/credential"
    body = {
        "device_id": "new_dev_1",
        "conn_type": "ssh",
        "login": "minh",
        "port": 22,
        "priority": 1,
        "extra": {},
    }

    response = requests.post(url, json=body)
    data = response.json()

    assert response.status_code == 200

    assert data["device_id"] == "new_dev_1"
    assert data["conn_type"] == "ssh"
    assert data["login"] == "minh"
    assert data["password"] is None
    assert data["port"] == 22
    assert data["priority"] == 1
    assert not data["extra"]

    # Test POST device set
    url = f"{host}/device_set"
    body = {"device_set_id": "test_set", "device_id_list": ["new_dev_1"]}

    response = requests.post(url, json=body)
    data = response.json()

    assert response.status_code == 200

    assert data["device_set_id"] == "test_set"

    # Test POST flow
    url = f"{host}/flow"
    body = {
        "flow_id": "test_ssh_2_commands",
        "description": "post new flow for testing",
    }

    response = requests.post(url, json=body)
    data = response.json()

    assert response.status_code == 200

    assert data["flow_id"] == "test_ssh_2_commands"
    assert data["description"] == "post new flow for testing"

    # Test POST flow version
    url = f"{host}/flow_version"
    body = {
        "flow_id": "test_ssh_2_commands",
        "version": "v1",
        "description": "version for testing",
        "structure": sample_flow_structures["test_ssh_2_commands"],
    }

    response = requests.post(url, json=body)
    data = response.json()
    print("INFO: data is", data)

    assert response.status_code == 200

    assert data["flow_id"] == "test_ssh_2_commands"
    assert data["version"] == "v1"
    assert data["description"] == "version for testing"
    assert len(data["structure"]["nodes"]) == 4

    # Test POST flow run
    url = f"{host}/flow_run"
    body = {
        "flow_id": "test_ssh_2_commands",
        "version": "v1",
        "flow_run_id": "test_run",
        "device_set_id": "test_set",
        "description": "test run",
        "run_type": FlowRunType.MANUAL,
    }

    response = requests.post(url, json=body)
    data = response.json()

    assert response.status_code == 200
    assert data["flow_id"] == "test_ssh_2_commands"
    assert data["version"] == "v1"
    assert data["flow_run_id"] == "test_run"
    assert data["description"] == "test run"
    assert data["run_type"] == FlowRunType.MANUAL
    assert data["device_set_id"] == "test_set"
