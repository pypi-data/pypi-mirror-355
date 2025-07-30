from __future__ import annotations

import copy

from formica.models.models import FlowVersionModel
from formica.node.nodes import NodeFactory
from formica.utils.validate import convert_keys_to_snake_case


class Flow:
    def __init__(self, flow_version: FlowVersionModel, arguments=None):
        """
        Khởi tạo Flow từ cấu trúc Flow dạng JSON, khởi tạo các Node thêm vào node_dict
        Set các đối số được truyền vào từ `arguments`
        :param flow_id: flow id
        :param structure: cấu trúc đồ thị của Flow
        :param arguments: các đối số truyền vào

        :raises ValueError: Tên đối số không tồn tại trong danh sách tham số của Flow
        """
        if arguments is None:
            arguments = {}
        self.flow_id = flow_version.flow_id
        self.node_dict = {}
        self.params: list[str] = flow_version.parameters
        self.vars: dict[str, str] = {}
        structure_ = copy.deepcopy(flow_version.structure)

        self._deserialize(structure_)
        try:
            self._pass_arguments(arguments)
        except ValueError as e:
            raise e

    def _pass_arguments(self, arguments: dict[str, str]):
        """
        Gọi hàm này để truyền các đối số (arguments) vào flow
        Các giá trị này sau đó sẽ được set vào self.vars (global giữa các toán tử)
        :param arguments: các đối số
        :return:

        :raises ValueError: Tên đối số không tồn tại trong danh sách tham số của Flow
        """
        for arg_name in arguments:
            if arg_name not in self.params:
                raise ValueError(
                    f"Tên đối số không tồn tại trong danh sách tham số của Flow: {arg_name}"
                )

        # Tới đây được nghĩa là tất cả đối số đã hợp lệ
        self.vars.update(arguments)

    def _deserialize(self, structure: dict) -> None:
        """
        Parse dạng json của flow ra thành các toán tử liên kết với nhau trong node_dict

        Đồng thời cũng parse các tham số truyền vào và biến global
        :param structure: Dạng json của flow
        :return: None
        """
        flow_json = structure
        # version = flow_json["version"]
        # if version == "0.1":
        self._parse_flow_v0_1(flow_json)
        # else:
        #     raise ValueError(f"Unknown flow version {version}")

    def _parse_flow_v0_1(self, flow_json: dict):
        # Parse các tham số (biến global)
        # self.vars = flow_json["globals"]
        # Parse các Node và đẩy vào `node_dict`
        flow_json = self._preprocess_flow(flow_json)
        # print(flow_json)
        for node_json in flow_json["nodes"]:
            new_node = NodeFactory.create_node(node_json)
            new_node.flow = self
            self.node_dict[new_node.node_id] = new_node

        # Update the edges
        for edge_json in flow_json["edges"]:
            print(edge_json)
            print("+=============================================================")
            self.node_dict[edge_json["source"]].add_downstream(
                self.node_dict[edge_json["target"]]
            )

    def _preprocess_flow(self, flow_json: dict) -> dict:
        flow_json = convert_keys_to_snake_case(flow_json)
        for node in flow_json["nodes"]:
            if node["data"]["label"] == "Decision":
                for edge in flow_json["edges"]:
                    if (
                        edge["source"] == node["id"]
                        and edge["source_handle"] == "out-1"
                    ):
                        node["data"]["config"]["true_branch"] = edge["target"]
                    elif (
                        edge["source"] == node["id"]
                        and edge["source_handle"] == "out-2"
                    ):
                        node["data"]["config"]["false_branch"] = edge["target"]

        return flow_json

    def print_flow(self):
        """Hàm này để debug"""
        for node in self.node_dict.values():
            print(f"{node.node_id} => {node.downstream_node_ids}")
