"""Tests for task management utilities."""

import json
import os
import tempfile
import pytest

from kicad_mcp_server.utils.tasks import (
    TaskManager,
    TaskStatus,
    TaskInfo,
)


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.STARTED.value == "started"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.UNKNOWN.value == "unknown"


class TestTaskInfo:
    """Tests for TaskInfo dataclass."""

    def test_to_dict(self):
        """Test converting TaskInfo to dictionary."""
        info = TaskInfo(
            id="test_task",
            type="auto_route",
            project="my_project",
            status=TaskStatus.RUNNING,
            started_at="20240101_120000",
            backup="/path/to/backup.kicad_pcb",
            message="In progress",
        )

        result = info.to_dict()

        assert result["id"] == "test_task"
        assert result["type"] == "auto_route"
        assert result["project"] == "my_project"
        assert result["status"] == "running"
        assert result["backup"] == "/path/to/backup.kicad_pcb"
        assert result["message"] == "In progress"

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields."""
        info = TaskInfo(
            id="test",
            type="route",
            project="proj",
            status=TaskStatus.PENDING,
            started_at="now",
        )

        result = info.to_dict()

        assert "backup" not in result
        assert "message" not in result
        assert "log_tail" not in result


class TestTaskManager:
    """Tests for TaskManager class."""

    def setup_method(self):
        """Create a temporary directory for tasks."""
        self.tmp_dir = tempfile.mkdtemp()
        self.manager = TaskManager(tasks_dir=self.tmp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_save_and_load_task(self):
        """Test saving and loading task data."""
        task_id = "test_task_123"
        data = {
            "id": task_id,
            "type": "auto_route",
            "project": "my_project",
            "status": "running",
        }

        self.manager.save_task(task_id, data)
        loaded = self.manager.load_task(task_id)

        assert loaded is not None
        assert loaded["id"] == task_id
        assert loaded["type"] == "auto_route"

    def test_load_nonexistent_task(self):
        """Test loading a task that doesn't exist."""
        result = self.manager.load_task("nonexistent")
        assert result is None

    def test_get_status(self):
        """Test getting task status."""
        task_id = "status_test"

        # Create status file
        status_file = os.path.join(self.tmp_dir, f"{task_id}.status")
        with open(status_file, "w") as f:
            f.write("completed")

        status = self.manager.get_status(task_id)
        assert status == TaskStatus.COMPLETED

    def test_get_status_unknown(self):
        """Test getting status for task without status file."""
        status = self.manager.get_status("no_status")
        assert status == TaskStatus.UNKNOWN

    def test_get_log_tail(self):
        """Test getting log tail."""
        task_id = "log_test"

        # Create log file
        log_file = os.path.join(self.tmp_dir, f"{task_id}.log")
        lines = [f"Line {i}\n" for i in range(20)]
        with open(log_file, "w") as f:
            f.writelines(lines)

        tail = self.manager.get_log_tail(task_id, lines=5)

        assert "Line 15" in tail
        assert "Line 19" in tail
        assert "Line 0" not in tail

    def test_get_log_tail_empty(self):
        """Test getting log tail for nonexistent log."""
        tail = self.manager.get_log_tail("no_log")
        assert tail == ""

    def test_list_tasks(self):
        """Test listing all tasks."""
        # Create some tasks
        for i in range(3):
            task_id = f"task_{i}"
            self.manager.save_task(task_id, {
                "id": task_id,
                "type": "test",
                "project": f"project_{i}",
                "started_at": "now",
            })

        tasks = self.manager.list_tasks()
        assert len(tasks) == 3

    def test_create_autoroute_script(self):
        """Test creating auto-route script."""
        script_file = self.manager.create_autoroute_script(
            task_id="route_test",
            project_dir="/path/to/project",
            pcb_file="/path/to/project/board.kicad_pcb",
            dsn_file="/path/to/project/output/temp.dsn",
            ses_file="/path/to/project/output/temp.ses",
            max_passes=50,
        )

        assert os.path.exists(script_file)

        with open(script_file) as f:
            content = f.read()

        # Check script contains necessary parts
        assert "#!/bin/bash" in content
        assert "xvfb-run" in content
        assert "freerouting" in content.lower() or "FREEROUTING" in content
        assert "50" in content  # max_passes

    def test_cleanup_old_tasks(self):
        """Test cleaning up old tasks."""
        import time

        # Create an old task
        old_task_id = "old_task"
        self.manager.save_task(old_task_id, {
            "id": old_task_id,
            "type": "test",
            "project": "old",
            "started_at": "old",
        })

        # Create status file marking it as completed
        status_file = os.path.join(self.tmp_dir, f"{old_task_id}.status")
        with open(status_file, "w") as f:
            f.write("completed")

        # Set file modification time to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        task_file = os.path.join(self.tmp_dir, f"{old_task_id}.json")
        os.utime(task_file, (old_time, old_time))

        # Create a new task
        new_task_id = "new_task"
        self.manager.save_task(new_task_id, {
            "id": new_task_id,
            "type": "test",
            "project": "new",
            "started_at": "new",
        })

        # Clean up tasks older than 7 days
        cleaned = self.manager.cleanup_old_tasks(max_age_days=7)

        assert cleaned == 1
        assert not os.path.exists(task_file)
        assert os.path.exists(os.path.join(self.tmp_dir, f"{new_task_id}.json"))
