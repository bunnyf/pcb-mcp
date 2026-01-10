"""
Task management tools for KiCad MCP Server.
"""

from __future__ import annotations

from typing import Any

from ..utils import TaskManager


def tool_get_task_status(task_id: str) -> dict[str, Any]:
    """
    Get the status of an async task.

    Args:
        task_id: Task identifier

    Returns:
        Task information including status and log tail
    """
    task_manager = TaskManager()
    task_info = task_manager.get_task_info(task_id)

    if not task_info:
        return {"error": f"Task not found: {task_id}"}

    return task_info.to_dict()


def tool_list_tasks() -> dict[str, Any]:
    """
    List all async tasks.

    Returns:
        List of all tasks with their status
    """
    task_manager = TaskManager()
    tasks = task_manager.list_tasks()

    return {
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
    }


def tool_cleanup_tasks(max_age_days: int = 7) -> dict[str, Any]:
    """
    Clean up old completed/failed tasks.

    Args:
        max_age_days: Maximum age in days for tasks to keep

    Returns:
        Number of tasks cleaned up
    """
    task_manager = TaskManager()
    cleaned = task_manager.cleanup_old_tasks(max_age_days)

    return {
        "success": True,
        "cleaned": cleaned,
        "message": f"Cleaned up {cleaned} old task(s)",
    }
