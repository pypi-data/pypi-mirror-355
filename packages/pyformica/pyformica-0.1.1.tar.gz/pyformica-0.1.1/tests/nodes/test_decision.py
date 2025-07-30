import pathlib
import shutil

import pytest
from formica.execution.context import Context
from formica.node.flow import Flow
from formica.node.nodes import CommandNode
from formica.node.nodes import DecisionNode


@pytest.fixture(scope="function", autouse=True)
def test_dir():
    test_dir = pathlib.Path.cwd() / "test_formica"
    if not test_dir.exists():
        test_dir.mkdir()

    yield test_dir

    shutil.rmtree(test_dir)


@pytest.fixture(scope="function")
def test_file(test_dir):
    test_file = test_dir / "test_file.txt"
    if not test_file.exists():
        test_file.touch()

    return test_file


@pytest.fixture(scope="module")
def decision_flow_mock(sample_flow_structures):
    return Flow(
        flow_id="mock_flow_for_decision_test",
        structure=sample_flow_structures["test_decision_node"],
    )


def test_decision_node_true_branch(
    decision_flow_mock, session, resource_mock_data, clean_up_remote_test_files
):
    context = Context(decision_flow_mock, session)
    context.resources[resource_mock_data.rs_id] = resource_mock_data
    ls_op = decision_flow_mock.node_dict["ssh_command_ls"]
    decision_op = decision_flow_mock.node_dict["dummy_decision"]
    rm_op = decision_flow_mock.node_dict["remove_dummy"]
    create_op = decision_flow_mock.node_dict["create_dummy"]

    assert isinstance(ls_op, CommandNode)
    assert isinstance(decision_op, DecisionNode)
    ls_op.execute(context)
    # assert context.connection is not None
    decision_op.execute(context)
    assert decision_op.output == "create_dummy"
    assert decision_op.skip_task == "remove_dummy"

    # ssh_exit.execute(context)
    # assert context.connection is None
