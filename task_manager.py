from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Any

from config import _get_config_dir

logger = logging.getLogger(__name__)

TASKS_FILE = "jarvis_tasks.json"


class TaskManager:
    """
    Manages JARVIS AI's tasks, goals, reminders, and scheduled workflows.
    """

    @classmethod
    def _get_tasks_filepath(cls) -> str:
        return os.path.join(_get_config_dir(), TASKS_FILE)

    @classmethod
    def get_all_tasks(cls, filter_status: str = "all") -> list[dict[str, Any]]:
        """Loads and returns tasks, optionally filtered by status ('all', 'pending', 'completed')."""
        path = cls._get_tasks_filepath()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                tasks = data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error loading tasks from {path}: {e}")
            return []

        if filter_status == "pending":
            return [t for t in tasks if t.get("status") == "pending"]
        elif filter_status == "completed":
            return [t for t in tasks if t.get("status") == "completed"]

        return tasks

    @classmethod
    def save_tasks(cls, tasks: list[dict[str, Any]]) -> bool:
        """Saves task list to JSON file."""
        path = cls._get_tasks_filepath()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving tasks to {path}: {e}")
            return False

    @classmethod
    def add_task(
        cls,
        title: str,
        description: str = "",
        priority: str = "Medium",
        delay_seconds: float = 0
    ) -> dict[str, Any]:
        """Creates a new task or reminder."""
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty.")

        tasks = cls.get_all_tasks()
        now = time.time()
        due_at_str = ""
        if delay_seconds > 0:
            due_at_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now + delay_seconds))

        entry = {
            "id": str(uuid.uuid4())[:8],
            "title": clean_title,
            "description": description.strip(),
            "priority": priority.strip().capitalize() if priority in ("Low", "Medium", "High") else "Medium",
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
            "due_at": due_at_str
        }
        tasks.append(entry)
        cls.save_tasks(tasks)
        logger.info(f"Added task [{entry['id']}]: '{clean_title}'")
        return entry

    @classmethod
    def mark_task_completed(cls, task_id: str) -> bool:
        """Marks a task as completed."""
        tasks = cls.get_all_tasks()
        updated = False
        for t in tasks:
            if t.get("id") == task_id:
                t["status"] = "completed"
                t["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                updated = True
                break

        if updated:
            cls.save_tasks(tasks)
            logger.info(f"Task [{task_id}] marked completed.")
        return updated

    @classmethod
    def delete_task(cls, task_id: str) -> bool:
        """Deletes a task by ID."""
        tasks = cls.get_all_tasks()
        filtered = [t for t in tasks if t.get("id") != task_id]
        if len(filtered) < len(tasks):
            cls.save_tasks(filtered)
            logger.info(f"Deleted task [{task_id}]")
            return True
        return False

    @classmethod
    def clear_completed_tasks(cls) -> bool:
        """Removes all completed tasks."""
        tasks = cls.get_all_tasks()
        pending = [t for t in tasks if t.get("status") == "pending"]
        return cls.save_tasks(pending)
