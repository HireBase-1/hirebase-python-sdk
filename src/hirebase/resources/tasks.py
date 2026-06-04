"""The ``tasks`` resource: fetch and poll async tasks."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

from .. import _ops as ops
from ..exceptions import TaskTimeout
from ..models.tasks import TERMINAL_STATES, Task, TaskState

PollResult = Tuple[bool, Union[dict, Task, None]]


class TasksResource:
    """Synchronous tasks API."""

    def __init__(self, client) -> None:
        self._c = client

    def get(
        self, task_id: str, *, return_type: Optional[Type] = None
    ) -> Union[Task, dict]:
        req = ops.get_task_request(task_id)
        data = self._c._request(req)
        return ops.parse_task(data, self._c, return_type)

    def poll(
        self,
        task: Union[Task, dict, str],
        *,
        interval: float = 2.0,
        timeout: Optional[float] = 300.0,
        on_progress: Optional[Callable[[Task], Any]] = None,
    ) -> PollResult:
        """Poll a task until it reaches a terminal state.

        Returns ``(success, result)`` where ``result`` is the task's result
        dict on success (containing e.g. ``download_url``) or the failed
        ``Task`` on failure.
        """
        task_id = ops.task_id_of(task)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            current = self.get(task_id)
            if on_progress is not None:
                on_progress(current)
            if current.state == TaskState.FINISHED:
                return True, current.result
            if current.state in TERMINAL_STATES:
                return False, current
            if deadline is not None and time.monotonic() >= deadline:
                raise TaskTimeout(
                    f"Task {task_id} did not finish within {timeout}s "
                    f"(last state: {current.state.value}).",
                    task=current,
                )
            time.sleep(interval)


class AsyncTasksResource:
    """Asynchronous tasks API."""

    def __init__(self, client) -> None:
        self._c = client

    async def get(
        self, task_id: str, *, return_type: Optional[Type] = None
    ) -> Union[Task, dict]:
        req = ops.get_task_request(task_id)
        data = await self._c._request(req)
        return ops.parse_task(data, self._c, return_type)

    async def poll(
        self,
        task: Union[Task, dict, str],
        *,
        interval: float = 2.0,
        timeout: Optional[float] = 300.0,
        on_progress: Optional[Callable[[Task], Any]] = None,
    ) -> PollResult:
        task_id = ops.task_id_of(task)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            current = await self.get(task_id)
            if on_progress is not None:
                on_progress(current)
            if current.state == TaskState.FINISHED:
                return True, current.result
            if current.state in TERMINAL_STATES:
                return False, current
            if deadline is not None and time.monotonic() >= deadline:
                raise TaskTimeout(
                    f"Task {task_id} did not finish within {timeout}s "
                    f"(last state: {current.state.value}).",
                    task=current,
                )
            await asyncio.sleep(interval)
