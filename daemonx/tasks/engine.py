"""
Persistent Task Execution Engine with SQLite Checkpointing and Resumability
"""
import time
import uuid
from typing import Any, Callable
from daemonx.core.exceptions import TaskExecutionError
from daemonx.storage.database import Database
from daemonx.tasks.model import TaskStatus, TaskCheckpoint


class TaskEngine:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self._active_jobs: dict[str, TaskCheckpoint] = {}
        self._step_handlers: dict[str, list[tuple[str, Callable[[dict[str, Any]], dict[str, Any]]]]] = {}

    def register_workflow(self, workflow_name: str, steps: list[tuple[str, Callable[[dict[str, Any]], dict[str, Any]]]]):
        """Registers a named workflow with ordered step functions: [(step_name, handler_func), ...]"""
        self._step_handlers[workflow_name] = steps

    def create_job(self, workflow_name: str, initial_state: dict[str, Any] | None = None) -> TaskCheckpoint:
        """Initializes a new persistent task job in SQLite."""
        if workflow_name not in self._step_handlers:
            raise TaskExecutionError(f"Workflow '{workflow_name}' is not registered.")

        steps = self._step_handlers[workflow_name]
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        checkpoint = TaskCheckpoint(
            job_id=job_id,
            task_name=workflow_name,
            current_step=0,
            total_steps=len(steps),
            status=TaskStatus.PENDING,
            state_data=initial_state or {}
        )
        self._save_checkpoint(checkpoint)
        self._active_jobs[job_id] = checkpoint
        return checkpoint

    def run_step(self, job_id: str) -> TaskCheckpoint:
        """Executes the next atomic step in the task sequence and updates SQLite checkpoint."""
        checkpoint = self.get_checkpoint(job_id)
        if checkpoint.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
            return checkpoint

        steps = self._step_handlers.get(checkpoint.task_name, [])
        idx = checkpoint.current_step

        if idx >= len(steps):
            checkpoint.status = TaskStatus.COMPLETED
            self._save_checkpoint(checkpoint)
            return checkpoint

        step_name, handler = steps[idx]
        checkpoint.status = TaskStatus.RUNNING
        checkpoint.logs.append(f"Starting step {idx+1}/{len(steps)}: {step_name}")
        self._save_checkpoint(checkpoint)

        try:
            # Execute step handler
            updated_state = handler(checkpoint.state_data)
            checkpoint.state_data = updated_state or checkpoint.state_data
            checkpoint.current_step = idx + 1
            checkpoint.logs.append(f"Completed step {idx+1}: {step_name}")

            if checkpoint.current_step >= len(steps):
                checkpoint.status = TaskStatus.COMPLETED
            else:
                checkpoint.status = TaskStatus.PAUSED if checkpoint.status == TaskStatus.PAUSED else TaskStatus.RUNNING

            self._save_checkpoint(checkpoint)
            return checkpoint

        except Exception as e:
            checkpoint.status = TaskStatus.FAILED
            checkpoint.logs.append(f"Error in step '{step_name}': {str(e)}")
            self._save_checkpoint(checkpoint)
            raise TaskExecutionError(f"Task {job_id} failed at step '{step_name}': {e}")

    def run_all(self, job_id: str) -> TaskCheckpoint:
        """Runs all remaining steps until completion, failure, or pause."""
        checkpoint = self.get_checkpoint(job_id)
        while checkpoint.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            checkpoint = self.run_step(job_id)
        return checkpoint

    def pause_job(self, job_id: str) -> TaskCheckpoint:
        """Pauses a running job after the current atomic step."""
        checkpoint = self.get_checkpoint(job_id)
        if checkpoint.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            checkpoint.status = TaskStatus.PAUSED
            checkpoint.logs.append("Task paused by operator")
            self._save_checkpoint(checkpoint)
        return checkpoint

    def resume_job(self, job_id: str) -> TaskCheckpoint:
        """Resumes a paused or interrupted job from its last recorded checkpoint."""
        checkpoint = self.get_checkpoint(job_id)
        if checkpoint.status in (TaskStatus.PAUSED, TaskStatus.PENDING):
            checkpoint.status = TaskStatus.RUNNING
            checkpoint.logs.append("Task resumed from checkpoint")
            self._save_checkpoint(checkpoint)
            return self.run_all(job_id)
        return checkpoint

    def cancel_job(self, job_id: str) -> TaskCheckpoint:
        """Cancels a job."""
        checkpoint = self.get_checkpoint(job_id)
        checkpoint.status = TaskStatus.CANCELLED
        checkpoint.logs.append("Task cancelled by operator")
        self._save_checkpoint(checkpoint)
        return checkpoint

    def get_checkpoint(self, job_id: str) -> TaskCheckpoint:
        """Loads task checkpoint from active memory or SQLite."""
        if job_id in self._active_jobs:
            return self._active_jobs[job_id]

        row = self.db.get_job(job_id)
        if not row:
            raise TaskExecutionError(f"Job '{job_id}' not found in database.")

        raw_state = row.get("state", {})
        state_data = raw_state.get("data", raw_state) if isinstance(raw_state, dict) else {}
        logs = raw_state.get("logs", []) if isinstance(raw_state, dict) else []

        checkpoint = TaskCheckpoint(
            job_id=row["id"],
            task_name=row["task_name"],
            current_step=row["current_step"],
            total_steps=row["total_steps"],
            status=TaskStatus(row["status"]),
            state_data=state_data,
            logs=logs
        )
        self._active_jobs[job_id] = checkpoint
        return checkpoint

    def _save_checkpoint(self, cp: TaskCheckpoint):
        self._active_jobs[cp.job_id] = cp
        self.db.save_job(
            job_id=cp.job_id,
            task_name=cp.task_name,
            status=cp.status.value,
            current_step=cp.current_step,
            total_steps=cp.total_steps,
            state={"data": cp.state_data, "logs": cp.logs}
        )
