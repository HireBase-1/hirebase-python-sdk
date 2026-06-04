"""Task model for async operations like job exports."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import Field

from .base import BoundModel


class TaskState(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELED = "canceled"


# States after which a task will never change again.
TERMINAL_STATES = frozenset(
    {TaskState.FINISHED, TaskState.FAILED, TaskState.CANCELED}
)


class Task(BoundModel):
    """An asynchronous server-side task (e.g. a job export)."""

    id: str
    type: Optional[str] = None
    state: TaskState = TaskState.QUEUED
    progress: float = 0.0
    input: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    user_id: Optional[str] = None
    priority: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_done(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def succeeded(self) -> bool:
        return self.state == TaskState.FINISHED

    @property
    def download_url(self) -> Optional[str]:
        """Convenience accessor for export results."""
        if self.result:
            return self.result.get("download_url")
        return None

    def poll(self, **kwargs):
        """Poll this task to completion via its bound client.

        Returns ``(success, result)``. Works on sync and async clients.
        """
        client = self._require_client()
        return client.tasks.poll(self, **kwargs)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Task(id={self.id!r}, state={self.state.value!r}, progress={self.progress})"
