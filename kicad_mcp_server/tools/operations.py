"""
PCB operation tools for KiCad MCP Server.

Includes zone filling and auto-routing functionality.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Any

from ..config import get_config
from ..utils import (
    get_logger,
    validate_project_path,
    find_pcb_file,
    ensure_output_dirs,
    PathValidationError,
    TaskManager,
)
from ..pcbnew_api import get_pcbnew, HAS_PCBNEW


def tool_fill_zones(project: str) -> dict[str, Any]:
    """
    Fill all copper zones in a PCB.

    Args:
        project: Project name

    Returns:
        Result with zone count and status
    """
    if not HAS_PCBNEW:
        return {"error": "pcbnew module not available"}

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    try:
        pcbnew = get_pcbnew()
        board = pcbnew.LoadBoard(pcb_file)
        zones = board.Zones()
        zone_count = zones.size() if hasattr(zones, "size") else len(list(zones))

        if zone_count == 0:
            return {"success": True, "message": "No zones to fill", "zones": 0}

        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
        pcbnew.SaveBoard(pcb_file, board)

        return {
            "success": True,
            "message": f"Filled {zone_count} zone(s)",
            "zones": zone_count,
            "file": pcb_file,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_auto_route(
    project: str,
    max_passes: int = 100,
    async_mode: bool = True,
) -> dict[str, Any]:
    """
    Auto-route a PCB using FreeRouting.

    Args:
        project: Project name
        max_passes: Maximum routing passes
        async_mode: Whether to run asynchronously (recommended)

    Returns:
        Routing result or task information for async mode
    """
    logger = get_logger()
    config = get_config()

    if not HAS_PCBNEW:
        return {"error": "pcbnew module not available"}

    if not os.path.exists(config.freerouting_jar):
        return {"error": f"FreeRouting not installed: {config.freerouting_jar}"}

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    ensure_output_dirs(project_dir)

    # Create backup
    backup_dir = os.path.join(project_dir, "output/backup")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"before_autoroute_{timestamp}.kicad_pcb")
    shutil.copy(pcb_file, backup_file)

    # Temporary files for DSN/SES exchange
    dsn_file = os.path.join(project_dir, "output/temp_route.dsn")
    ses_file = os.path.join(project_dir, "output/temp_route.ses")

    # Export DSN using pcbnew API
    try:
        pcbnew = get_pcbnew()
        board = pcbnew.LoadBoard(pcb_file)
        pcbnew.ExportSpecctraDSN(board, dsn_file)
        logger.info(f"DSN export completed: {dsn_file}")
    except Exception as e:
        return {"success": False, "error": f"DSN export failed: {e}"}

    if async_mode:
        # Async mode: background execution
        task_id = f"route_{project}_{timestamp}"
        task_manager = TaskManager()

        # Create and save task info
        task_manager.save_task(task_id, {
            "id": task_id,
            "type": "auto_route",
            "project": project,
            "status": "running",
            "started_at": timestamp,
            "backup": backup_file,
            "pcb": pcb_file,
        })

        # Create background script with safe quoting
        script_file = task_manager.create_autoroute_script(
            task_id=task_id,
            project_dir=project_dir,
            pcb_file=pcb_file,
            dsn_file=dsn_file,
            ses_file=ses_file,
            max_passes=max_passes,
        )

        # Start background task
        task_manager.start_background_task(script_file)

        return {
            "success": True,
            "async": True,
            "task_id": task_id,
            "message": "Auto-routing task started, use get_task_status to check progress",
            "backup": backup_file,
        }

    else:
        # Sync mode (has timeout risk for complex boards)
        import subprocess

        try:
            cmd = [
                "xvfb-run", "-a",
                config.java_cmd, "-jar", config.freerouting_jar,
                "-de", dsn_file,
                "-do", ses_file,
                "-mp", str(max_passes),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.autoroute_sync_timeout,
            )

            if not os.path.exists(ses_file):
                return {"success": False, "error": "FreeRouting did not generate SES file"}

            pcbnew = get_pcbnew()
            board = pcbnew.LoadBoard(pcb_file)
            pcbnew.ImportSpecctraSES(board, ses_file)
            pcbnew.SaveBoard(pcb_file, board)

            # Clean up temp files
            for f in [dsn_file, ses_file]:
                if os.path.exists(f):
                    os.remove(f)

            return {
                "success": True,
                "message": "Auto-routing completed",
                "backup": backup_file,
                "pcb": pcb_file,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Auto-routing timed out (>{config.autoroute_sync_timeout}s), use async_mode=true",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
