import logging
import traceback

from formica.execution.context import Context
from formica.models.constant import TaskState
from formica.models.constant import TaskTriggerRule
from formica.node.nodes import BaseNode

logger = logging.getLogger(__name__)


class Task:
    def __init__(self, node: BaseNode, trigger_rule: TaskTriggerRule):
        self.node: BaseNode = node
        self.state = TaskState.WAIT_FOR_EXECUTING
        self.trigger_rule = trigger_rule

    async def run(self, context: Context) -> None:
        self.state = TaskState.RUNNING
        try:
            await self.node.execute(context)
            self.state = TaskState.SUCCESS
        except Exception as e:
            logger.warning(
                f"Error while executing task {self.node.node_id} (type {self.node.__class__}): {e}"
            )
            traceback.print_exc()

            self.state = TaskState.FAILED
