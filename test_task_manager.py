import pytest
from task_manager import TaskManager


def test_task_crud():
    TaskManager.save_tasks([])
    assert len(TaskManager.get_all_tasks()) == 0

    t1 = TaskManager.add_task("Review PR", description="Check code quality", priority="High")
    t2 = TaskManager.add_task("Buy groceries", priority="Low", delay_seconds=60)

    tasks = TaskManager.get_all_tasks()
    assert len(tasks) == 2
    assert t1["priority"] == "High"
    assert t2["due_at"] != ""

    pending = TaskManager.get_all_tasks(filter_status="pending")
    assert len(pending) == 2

    ok = TaskManager.mark_task_completed(t1["id"])
    assert ok is True

    completed = TaskManager.get_all_tasks(filter_status="completed")
    assert len(completed) == 1
    assert completed[0]["id"] == t1["id"]

    deleted = TaskManager.delete_task(t2["id"])
    assert deleted is True
    assert len(TaskManager.get_all_tasks()) == 1

    TaskManager.clear_completed_tasks()
    assert len(TaskManager.get_all_tasks()) == 0
