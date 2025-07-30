from formica.node.flow import Flow


def test_parse_flow_v0_1(sample_flow_structures):
    ssh_2_commands_flow = Flow(
        flow_id="mock_flow",
        structure=sample_flow_structures["test_ssh_2_commands"],
    )

    # Phải có 4 toán tử trong Flow này
    assert len(ssh_2_commands_flow.node_dict) == 4
    # Phải có toán tử có id là "ssh_command_history"
    assert "ssh_ls" in ssh_2_commands_flow.node_dict
    # Toán tử id "ssh_command_history" chỉ có 1 toán tử downstream là exit_ssh
    assert len(ssh_2_commands_flow.node_dict["ssh_ls"].downstream_node_ids) == 1
    assert ssh_2_commands_flow.node_dict["ssh_ls"].downstream_node_ids[0] == "ssh_exit"

    # Test Flow có toán tử rẽ nhánh
    decision_flow = Flow(
        flow_id="mock_flow",
        structure=sample_flow_structures["test_decision_node"],
    )
    # Phải có 6 toán tử trong Flow này
    assert len(decision_flow.node_dict) == len(
        sample_flow_structures["test_decision_node"]["nodes"]
    )
    # Phải có toán tử có id là "dummy_decision"
    assert "dummy_decision" in decision_flow.node_dict
    # Toán tử id "dummy_decision" có 2 toán tử downstream là remove_dummy và create_dummy
    assert len(decision_flow.node_dict["dummy_decision"].downstream_node_ids) == 2
    assert (
        "remove_dummy" in decision_flow.node_dict["dummy_decision"].downstream_node_ids
    )
    assert (
        "create_dummy" in decision_flow.node_dict["dummy_decision"].downstream_node_ids
    )
