import pathlib
import shutil

import pytest
from formica.execution.context import Context
from formica.node.flow import Flow


@pytest.fixture(scope="function", autouse=True)
def test_dir():
    test_dir = pathlib.Path.cwd() / "test_formica"
    if not test_dir.exists():
        test_dir.mkdir()

    yield test_dir

    shutil.rmtree(test_dir)


@pytest.fixture(scope="function", autouse=True)
def test_file(test_dir):
    test_file = test_dir / "test_file.txt"
    if not test_file.exists():
        test_file.touch()

    return test_file


@pytest.fixture(scope="function")
def flow_2_commands_mock(sample_flow_structures):
    return Flow(
        flow_id="mock_flow_command_local",
        structure=sample_flow_structures["test_2_commands_local"],
    )


@pytest.fixture(scope="function")
def global_var_flow_mock(sample_flow_structures):
    return Flow(
        flow_id="global_var",
        structure=sample_flow_structures["test_global_var"],
    )


@pytest.fixture(scope="function")
def params_and_globals_flow_mock(sample_flow_structures):
    return Flow(
        flow_id="params_and_globals",
        structure=sample_flow_structures["test_params_and_global_vars"],
        arguments={"ls_option": "-la"},
    )


def test_command_local(flow_2_commands_mock, session):
    context = Context(flow_2_commands_mock, session)
    ssh_touch = flow_2_commands_mock.node_dict["ssh_touch"]
    ssh_ls = flow_2_commands_mock.node_dict["ssh_ls"]

    ssh_touch.execute(context)
    ssh_ls.execute(context)
    print(ssh_ls.output)
    assert "abcdef" in ssh_ls.output


def test_global_var(global_var_flow_mock, session):
    context = Context(global_var_flow_mock, session)
    create_file = global_var_flow_mock.node_dict["create_file"]
    cmd_ls = global_var_flow_mock.node_dict["cmd_ls"]

    create_file.execute(context)
    cmd_ls.execute(context)
    print(cmd_ls.output)
    assert "test_global_var" in cmd_ls.output


def test_params_and_globals(params_and_globals_flow_mock, session, test_file):
    context = Context(params_and_globals_flow_mock, session)
    create_file = params_and_globals_flow_mock.node_dict["create_file"]

    create_file.execute(context)
    print(create_file.output)
    assert "test_file.txt" in create_file.output
    assert "." in create_file.output
    assert ".." in create_file.output
