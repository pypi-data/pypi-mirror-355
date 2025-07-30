import logging
from typing import Optional

from formica.execution.context import Context
from formica.execution.task import Task
from formica.models.constant import DeviceRunState
from formica.models.constant import TaskState
from formica.models.models import DeviceRunModel
from formica.models.models import TaskModel
from formica.node.nodes import DecisionNode

logger = logging.getLogger(__name__)


class DeviceRun:
    def __init__(self, device_run_model: DeviceRunModel, context: Context) -> None:
        self._context = context
        # TODO: Có nên hợp DB model với các class xử lý logic không? Tại vì nếu làm vậy code gọn
        #  Task và DeviceRun khi chạy có thể cập nhật trạng thái của chính mình vào DB dễ hơn
        self._device_run_model = device_run_model
        self._task_dict: dict[str, Task] = {}
        self._target_task: Optional[Task] = None
        for task_model in device_run_model.tasks:
            task = Task(
                node=context.get_node_by_id(task_model.node_id),
                trigger_rule=task_model.trigger_rule,
            )
            self._task_dict[task_model.node_id] = task

    async def run(self):
        self._context.session.add(self._device_run_model)
        self._device_run_model.set_state(DeviceRunState.RUNNING)

        while (
            next_task := await self._update_state_and_get_next_task_to_run()
        ) is not None:
            self._log_task_states()
            self._target_task = next_task
            logger.debug(f"next task is: {next_task.node.node_id}")
            target_task_model = self._find_task_model_by_node_id(next_task.node.node_id)
            target_task_model.set_state(TaskState.RUNNING)
            await self._context.session.commit()

            await next_task.run(self._context)

            # Update the state of the target task in the model
            target_task_model.set_state(next_task.state)

    def _find_entry_task(self):
        """Find task without upstream tasks, which is the entry point of the flow."""
        # TODO: Should we keep this information in Flow?
        for task in self._task_dict.values():
            upstream_tasks = [
                self._task_dict[node_id] for node_id in task.node.upstream_node_ids
            ]
            if not upstream_tasks:
                return task
        return None

    def _update_task_state(self, task: Task, state: TaskState):
        """Update the state of a task and its corresponding TaskModel."""
        task.state = state
        task_model = self._find_task_model_by_node_id(task.node.node_id)
        task_model.set_state(state)

    def _find_task_model_by_node_id(self, node_id: str) -> Optional[TaskModel]:
        for task_model in self._device_run_model.tasks:
            if task_model.node_id == node_id:
                return task_model
        return None

    def _skip_branch(self, task: Task) -> None:
        """Recursively skip the entire branch rooted at this task by setting the state of all tasks in that branch to 'SKIPPED'."""
        if not task.node.downstream_node_ids:
            self._update_task_state(task, TaskState.SKIPPED)
            return

        for downstream_task in [
            self._task_dict[node_id] for node_id in task.node.downstream_node_ids
        ]:
            self._skip_branch(downstream_task)

    async def _update_state_and_get_next_task_to_run(self) -> Optional[Task]:
        """Cập nhật trạng thái của RetryRun (đã chạy xong chưa) và tìm task tiếp theo để chạy"""
        # Nếu là toán tử vừa chạy xong là decision thì phải skip các
        # toán tử trong nhánh không thực thi và trả về toán tử sẽ được thực thi
        if self._target_task is None:
            return self._find_entry_task()

        if self._target_task.state == TaskState.FAILED:
            # Nếu Task vừa chạy mà thất bại thì không
            return None

        if isinstance(self._target_task.node, DecisionNode):
            # Tìm ra toán tử ở nhánh không được chọn
            skip_task = self._task_dict[self._target_task.node.skip_task]
            self._skip_branch(skip_task)
            await self._context.session.commit()

            return self._task_dict[self._target_task.node.output]
        else:
            if self._target_task.node.downstream_node_ids:
                return self._task_dict[self._target_task.node.downstream_node_ids[0]]

        # If control reaches here, it means all tasks are either running or finished
        # Calculate the status of this DeviceRun (success or failed)

        logging.info("Checking device run state...")
        # If only one task failed, then the whole device run is considered failed
        if any(task.state == TaskState.FAILED for task in self._task_dict.values()):
            logging.info("Set device run state to FAILED")
            self._device_run_model.set_state(DeviceRunState.FAILED)
        else:
            logging.info("Set device run state to SUCCESS")
            self._device_run_model.set_state(DeviceRunState.SUCCESS)

        await self._context.session.commit()
        return None

    def _log_task_states(self):
        """Log ra trạng thái hiện tại các task, dùng để debug"""
        logger.debug("============ TASK STATES ==============")
        for task in self._task_dict.values():
            logger.debug(f"{task.node.node_id}: {task.state}")
