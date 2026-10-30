"""
Task Orchestrator Data Models, Steps, and Execution States
"""
from enum import Enum
from typing import Any, Callable, Coroutine
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepDefinition(BaseModel):
    name: str
    description: str = ""
    is_idempotent: bool = True
    retry_count: int = 1


class TaskCheckpoint(BaseModel):
    job_id: str
    task_name: str
    current_step: int = 0
    total_steps: int = 0
    status: TaskStatus = TaskStatus.PENDING
    state_data: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
