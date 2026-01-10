"""
Async task management for KiCad MCP Server.

Provides task tracking, status monitoring, and automatic cleanup.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from ..config import get_config
from .logging import get_logger


class TaskStatus(Enum):
    """Status of an async task."""

    PENDING = "pending"
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class TaskInfo:
    """Information about an async task."""

    id: str
    type: str
    project: str
    status: TaskStatus
    started_at: str
    backup: Optional[str] = None
    pcb: Optional[str] = None
    message: Optional[str] = None
    log_tail: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "type": self.type,
            "project": self.project,
            "status": self.status.value,
            "started_at": self.started_at,
        }
        if self.backup:
            result["backup"] = self.backup
        if self.pcb:
            result["pcb"] = self.pcb
        if self.message:
            result["message"] = self.message
        if self.log_tail:
            result["log_tail"] = self.log_tail
        if self.extra:
            result.update(self.extra)
        return result


class TaskManager:
    """
    Manager for async tasks.

    Handles task creation, status tracking, and cleanup.
    """

    def __init__(self, tasks_dir: Optional[str] = None):
        """
        Initialize the task manager.

        Args:
            tasks_dir: Directory for task files (default from config)
        """
        config = get_config()
        self.tasks_dir = tasks_dir or config.tasks_dir
        self.logger = get_logger()

    def _ensure_dir(self) -> None:
        """Ensure tasks directory exists."""
        os.makedirs(self.tasks_dir, exist_ok=True)

    def _task_file(self, task_id: str) -> str:
        """Get path to task JSON file."""
        return os.path.join(self.tasks_dir, f"{task_id}.json")

    def _status_file(self, task_id: str) -> str:
        """Get path to task status file."""
        return os.path.join(self.tasks_dir, f"{task_id}.status")

    def _log_file(self, task_id: str) -> str:
        """Get path to task log file."""
        return os.path.join(self.tasks_dir, f"{task_id}.log")

    def _script_file(self, task_id: str) -> str:
        """Get path to task script file."""
        return os.path.join(self.tasks_dir, f"{task_id}.sh")

    def save_task(self, task_id: str, data: dict) -> None:
        """
        Save task information to file.

        Args:
            task_id: Task identifier
            data: Task data to save
        """
        self._ensure_dir()
        with open(self._task_file(task_id), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_task(self, task_id: str) -> Optional[dict]:
        """
        Load task information from file.

        Args:
            task_id: Task identifier

        Returns:
            Task data or None if not found
        """
        task_file = self._task_file(task_id)
        if not os.path.exists(task_file):
            return None
        try:
            with open(task_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load task {task_id}: {e}")
            return None

    def get_status(self, task_id: str) -> TaskStatus:
        """
        Get current status of a task.

        Args:
            task_id: Task identifier

        Returns:
            Current task status
        """
        status_file = self._status_file(task_id)
        if not os.path.exists(status_file):
            return TaskStatus.UNKNOWN

        try:
            with open(status_file) as f:
                status_str = f.read().strip().lower()

            status_map = {
                "pending": TaskStatus.PENDING,
                "started": TaskStatus.STARTED,
                "running": TaskStatus.RUNNING,
                "completed": TaskStatus.COMPLETED,
                "failed": TaskStatus.FAILED,
            }
            return status_map.get(status_str, TaskStatus.UNKNOWN)
        except IOError:
            return TaskStatus.UNKNOWN

    def get_log_tail(self, task_id: str, lines: int = 10) -> str:
        """
        Get the last N lines of a task's log.

        Args:
            task_id: Task identifier
            lines: Number of lines to return

        Returns:
            Log tail content
        """
        log_file = self._log_file(task_id)
        if not os.path.exists(log_file):
            return ""

        try:
            with open(log_file) as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except IOError:
            return ""

    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get full task information including current status.

        Args:
            task_id: Task identifier

        Returns:
            TaskInfo or None if task not found
        """
        data = self.load_task(task_id)
        if not data:
            return None

        status = self.get_status(task_id)
        log_tail = self.get_log_tail(task_id)

        # Determine message based on status
        messages = {
            TaskStatus.COMPLETED: "Auto-routing completed! PCB file has been updated",
            TaskStatus.FAILED: "Auto-routing failed, check log for details",
            TaskStatus.STARTED: "Routing in progress...",
            TaskStatus.RUNNING: "Routing in progress...",
        }

        return TaskInfo(
            id=data.get("id", task_id),
            type=data.get("type", "unknown"),
            project=data.get("project", "unknown"),
            status=status,
            started_at=data.get("started_at", ""),
            backup=data.get("backup"),
            pcb=data.get("pcb"),
            message=messages.get(status),
            log_tail=log_tail,
        )

    def list_tasks(self) -> list[TaskInfo]:
        """
        List all tasks.

        Returns:
            List of TaskInfo objects
        """
        if not os.path.exists(self.tasks_dir):
            return []

        tasks = []
        for filename in os.listdir(self.tasks_dir):
            if filename.endswith(".json"):
                task_id = filename[:-5]
                task_info = self.get_task_info(task_id)
                if task_info:
                    tasks.append(task_info)

        return tasks

    def create_autoroute_script(
        self,
        task_id: str,
        project_dir: str,
        pcb_file: str,
        dsn_file: str,
        ses_file: str,
        max_passes: int = 100,
    ) -> str:
        """
        Create a background script for auto-routing.

        Uses shlex.quote() to prevent shell injection.

        Args:
            task_id: Task identifier
            project_dir: Project directory path
            pcb_file: Path to PCB file
            dsn_file: Path to DSN file
            ses_file: Path to SES file
            max_passes: Maximum routing passes

        Returns:
            Path to created script file
        """
        config = get_config()
        self._ensure_dir()

        # Use shlex.quote for all user-provided paths to prevent injection
        safe_project_dir = shlex.quote(project_dir)
        safe_dsn_file = shlex.quote(dsn_file)
        safe_ses_file = shlex.quote(ses_file)
        safe_pcb_file = shlex.quote(pcb_file)
        safe_freerouting_jar = shlex.quote(config.freerouting_jar)
        safe_status_file = shlex.quote(self._status_file(task_id))
        safe_log_file = shlex.quote(self._log_file(task_id))

        script = f"""#!/bin/bash
set -e

cd {safe_project_dir}
echo "started" > {safe_status_file}

xvfb-run -a java -jar {safe_freerouting_jar} \\
    -de {safe_dsn_file} \\
    -do {safe_ses_file} \\
    -mp {int(max_passes)} > {safe_log_file} 2>&1 || true

if [ -f {safe_ses_file} ]; then
    python3 << 'PYEOF'
import pcbnew
board = pcbnew.LoadBoard({repr(pcb_file)})
pcbnew.ImportSpecctraSES(board, {repr(ses_file)})
pcbnew.SaveBoard({repr(pcb_file)}, board)
print("SES imported successfully")
PYEOF
    rm -f {safe_dsn_file} {safe_ses_file}
    echo "completed" > {safe_status_file}
else
    echo "failed" > {safe_status_file}
fi
"""

        script_file = self._script_file(task_id)
        with open(script_file, "w") as f:
            f.write(script)
        os.chmod(script_file, 0o755)

        return script_file

    def start_background_task(self, script_file: str) -> None:
        """
        Start a background task from a script file.

        Args:
            script_file: Path to script to execute
        """
        subprocess.Popen(
            ["nohup", "bash", script_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    def cleanup_old_tasks(self, max_age_days: Optional[int] = None) -> int:
        """
        Clean up old completed/failed tasks.

        Args:
            max_age_days: Maximum age in days (default from config)

        Returns:
            Number of tasks cleaned up
        """
        config = get_config()
        if max_age_days is None:
            max_age_days = config.task_max_age_days

        if not os.path.exists(self.tasks_dir):
            return 0

        cutoff = datetime.now() - timedelta(days=max_age_days)
        cleaned = 0

        for filename in os.listdir(self.tasks_dir):
            if not filename.endswith(".json"):
                continue

            task_id = filename[:-5]
            task_file = self._task_file(task_id)

            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(task_file))
                if mtime >= cutoff:
                    continue

                # Only clean up completed or failed tasks
                status = self.get_status(task_id)
                if status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    continue

                # Remove all task files
                for file_getter in [
                    self._task_file,
                    self._status_file,
                    self._log_file,
                    self._script_file,
                ]:
                    filepath = file_getter(task_id)
                    if os.path.exists(filepath):
                        os.remove(filepath)

                cleaned += 1
                self.logger.info(f"Cleaned up old task: {task_id}")

            except (OSError, IOError) as e:
                self.logger.warning(f"Failed to clean up task {task_id}: {e}")

        return cleaned
