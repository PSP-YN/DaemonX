"""
Tests for Phase 4: Task Engine, Checkpoints, and Recovery
"""
import pytest
from pathlib import Path
from nexora.storage.database import Database
from nexora.tasks.engine import TaskEngine
from nexora.tasks.model import TaskStatus


@pytest.fixture
def task_engine(tmp_path: Path):
    db_file = tmp_path / "test_tasks.db"
    db = Database(db_path=db_file)
    engine = TaskEngine(db=db)
    return engine


def test_task_lifecycle_and_execution(task_engine: TaskEngine):
    execution_trail = []

    def step_1(state):
        execution_trail.append("step_1")
        state["step1_done"] = True
        return state

    def step_2(state):
        execution_trail.append("step_2")
        state["step2_done"] = True
        return state

    task_engine.register_workflow("sample_pipeline", [
        ("Step 1 - Init", step_1),
        ("Step 2 - Process", step_2),
    ])

    job = task_engine.create_job("sample_pipeline", initial_state={"init": 1})
    assert job.status == TaskStatus.PENDING
    assert job.total_steps == 2
    assert job.current_step == 0

    completed_job = task_engine.run_all(job.job_id)
    assert completed_job.status == TaskStatus.COMPLETED
    assert completed_job.current_step == 2
    assert completed_job.state_data["step1_done"] is True
    assert completed_job.state_data["step2_done"] is True
    assert execution_trail == ["step_1", "step_2"]


def test_task_checkpoint_resume(task_engine: TaskEngine):
    """TEST 12: Resume an interrupted processing job."""
    step_calls = {"step1": 0, "step2": 0, "step3": 0}

    def s1(state):
        step_calls["step1"] += 1
        state["val1"] = 100
        return state

    def s2(state):
        step_calls["step2"] += 1
        state["val2"] = 200
        return state

    def s3(state):
        step_calls["step3"] += 1
        state["val3"] = 300
        return state

    task_engine.register_workflow("resumable_flow", [
        ("Step 1", s1),
        ("Step 2", s2),
        ("Step 3", s3),
    ])

    job = task_engine.create_job("resumable_flow")

    # Run step 1 only
    cp1 = task_engine.run_step(job.job_id)
    assert cp1.current_step == 1
    assert step_calls["step1"] == 1

    # Simulate pause / process interruption
    task_engine.pause_job(job.job_id)
    cp_paused = task_engine.get_checkpoint(job.job_id)
    assert cp_paused.status == TaskStatus.PAUSED

    # Create a fresh TaskEngine instance pointing to the same DB to simulate restart
    fresh_engine = TaskEngine(db=task_engine.db)
    fresh_engine.register_workflow("resumable_flow", [
        ("Step 1", s1),
        ("Step 2", s2),
        ("Step 3", s3),
    ])

    # Resume job from fresh engine
    resumed = fresh_engine.resume_job(job.job_id)
    assert resumed.status == TaskStatus.COMPLETED
    assert resumed.current_step == 3

    # CRITICAL: Step 1 must NOT have run again! (step_calls['step1'] is still 1)
    assert step_calls["step1"] == 1
    assert step_calls["step2"] == 1
    assert step_calls["step3"] == 1
    assert resumed.state_data["val1"] == 100
    assert resumed.state_data["val2"] == 200
    assert resumed.state_data["val3"] == 300
