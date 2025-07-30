from __future__ import annotations

import logging
import warnings
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Type
from typing import TYPE_CHECKING

from formica.models.constant import ConnectionType
from formica.models.constant import TaskTriggerRule
from jinja2 import Template

warnings.filterwarnings("ignore", category=DeprecationWarning)


if TYPE_CHECKING:
    from formica.execution.context import Context

logger = logging.getLogger(__name__)


class NodeFactory:
    _node_classes: dict[str, Type[BaseNode]] = {}

    @classmethod
    def register_node(cls, node_type: str, node_class: Type[BaseNode]):
        """Register a new node type."""
        cls._node_classes[node_type] = node_class

    @classmethod
    def create_node(cls, node_data: dict[str, Any]) -> BaseNode:
        """
        Create a node from the given JSON data.

        Example:
        {
            "node_id": "cmd_2",
            "type": "command",
            "command": "rm error.log",
            "timeout": 10,
            "trigger_rule": "success",
        }
        :param node_data: the JSON data
        :return: The node object created from the JSON data
        """
        # Remove the "type" field from node_data because the node's constructor doesn't need it
        node_args = {
            "node_id": node_data["id"],
            "timeout": 10,
            "trigger_rule": TaskTriggerRule.SUCCESS,
        }

        node_args.update(node_data["data"]["config"])
        node_type = node_data["data"]["label"].lower()

        if node_type not in cls._node_classes:
            raise ValueError(f"Unknown node type: {node_type}")

        return cls._node_classes[node_type](**node_args)


class BaseNode(ABC):
    # TODO: Use __new__() ?
    def __init__(
        self,
        node_id: str,
        timeout: int,
        trigger_rule: TaskTriggerRule,
        flow=None,
    ):
        self.node_id = node_id
        self.flow = flow
        self.timeout = timeout
        self.trigger_rule = trigger_rule
        self.upstream_node_ids = []
        self.downstream_node_ids = []
        self.output: str = ""

    @abstractmethod
    async def execute(self, context: Context):
        pass

    def add_downstream(self, node: BaseNode):
        self.downstream_node_ids.append(node.node_id)
        node.upstream_node_ids.append(self.node_id)

    def __str__(self):
        return __name__


class StartNode(BaseNode):
    async def execute(self, context: Context):
        pass


class ConnectNode(BaseNode):
    def __init__(self, connection_type: str, **kwargs):
        self.connection_type = ConnectionType(connection_type)
        super().__init__(**kwargs)

    async def execute(self, context: Context):
        """Connect to the device using the context given"""
        try:
            await context.make_connection(self.connection_type)
        except Exception as e:
            logger.warning(
                f"Can't connect to {context.device.device_id}. Error: {str(e)}"
            )
            raise e


class CommandNode(BaseNode):
    def __init__(self, command: str = "", **kwargs):
        super().__init__(**kwargs)
        self.command = command

    async def execute(self, context: Context):
        # Compile jinja2 để lấy được command thực cần chạy
        template = Template(self.command)
        vars = context.get_variables()
        compiled_command = template.render(vars)
        logger.debug(f"Original command: {self.command}")
        logger.debug(vars)
        logger.debug(f"Compiled command: {compiled_command}")
        print(f"Compiled command: {compiled_command}")

        try:
            self.output = await context.run_command(
                compiled_command, expect_prompt=None
            )

            # Update context
            context.set_node_output(self.node_id, self.output)
            context.append_log(self.output)
        except Exception as e:
            raise e


class DecisionNode(BaseNode):
    def __init__(self, condition: str = "", true_branch="", false_branch="", **kwargs):
        super().__init__(**kwargs)
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch
        self.output: str = ""
        self.skip_task = ""

    async def execute(self, context: Context):
        template = Template(self.condition)
        vars = context.get_variables()
        compiled_condition = template.render(vars)
        logger.info(f"Compiled condition: {compiled_condition}")
        # logger.info(f"output is : {context.flow.vars['ssh_command_ls']['output']}")
        condition_is_true = eval(compiled_condition)
        if condition_is_true:
            self.output = self.true_branch
            self.skip_task = self.false_branch
        else:
            self.output = self.false_branch
            self.skip_task = self.true_branch

        logger.info(f"condition output is: {self.output}")
        logger.info(f"condition skip task is: {self.skip_task}")


class ExitNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def execute(self, context: Context):
        try:
            await context.discard_connection()
        except Exception as e:
            logger.warning(f"Error while disconnecting: {e}")
            raise e


NodeFactory.register_node("start", StartNode)
NodeFactory.register_node("connect", ConnectNode)
NodeFactory.register_node("command", CommandNode)
NodeFactory.register_node("disconnect", ExitNode)
NodeFactory.register_node("decision", DecisionNode)
