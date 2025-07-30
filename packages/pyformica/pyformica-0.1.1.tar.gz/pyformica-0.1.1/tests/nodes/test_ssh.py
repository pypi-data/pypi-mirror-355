import pytest
from formica.execution.context import Context
from formica.node.flow import Flow
from formica.node.nodes import SSHNode
from paramiko.client import SSHClient


@pytest.fixture(scope="module")
def ssh_2_commands_flow_mock(sample_flow_structures):
    return Flow(
        flow_id="mock_flow_for_ssh_test",
        structure=sample_flow_structures["test_ssh_2_commands"],
    )


def test_ssh_node(
    ssh_2_commands_flow_mock, session, resource_mock_data, clean_up_remote_test_files
):
    context = Context(ssh_2_commands_flow_mock, session)
    context.resources[resource_mock_data.rs_id] = resource_mock_data
    ssh_op = ssh_2_commands_flow_mock.node_dict["ssh_init"]
    ssh_touch = ssh_2_commands_flow_mock.node_dict["ssh_touch"]
    ssh_ls = ssh_2_commands_flow_mock.node_dict["ssh_ls"]
    ssh_exit = ssh_2_commands_flow_mock.node_dict["ssh_exit"]

    assert isinstance(ssh_op, SSHNode)
    ssh_op.execute(context)
    assert context.connection is not None
    assert isinstance(context.connection, SSHClient)
    ssh_touch.execute(context)
    ssh_ls.execute(context)
    assert ".bash_history" in ssh_ls.output
    assert ".ssh" in ssh_ls.output

    ssh_exit.execute(context)
    assert context.connection is None
