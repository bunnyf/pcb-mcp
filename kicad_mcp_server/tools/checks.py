"""
DRC and ERC check tools for KiCad MCP Server.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ..config import get_config
from ..utils import (
    get_logger,
    run_cmd,
    validate_project_path,
    find_pcb_file,
    find_schematic_file,
    ensure_output_dirs,
    PathValidationError,
)


def tool_run_drc(project: str) -> dict[str, Any]:
    """
    Run Design Rule Check (DRC) on a PCB.

    Args:
        project: Project name

    Returns:
        DRC results including violations count and summary
    """
    logger = get_logger()
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_file = os.path.join(project_dir, "output/reports/drc_report.json")

    result = run_cmd([
        config.kicad_cli, "pcb", "drc", pcb_file,
        "--severity-all",
        "--format", "json",
        "--output", output_file,
    ])

    if result.success and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                data = json.load(f)
            violations = data.get("violations", [])
            return {
                "success": True,
                "violations": len(violations),
                "file": output_file,
                "summary": [
                    {"type": v.get("type"), "desc": v.get("description")}
                    for v in violations[:10]
                ],
            }
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse DRC report: {e}")
            return {"success": False, "error": f"Failed to parse DRC report: {e}"}

    return {"success": False, "error": result.stderr or result.error}


def tool_run_erc(project: str) -> dict[str, Any]:
    """
    Run Electrical Rule Check (ERC) on a schematic.

    Args:
        project: Project name

    Returns:
        ERC results including violations count and summary
    """
    logger = get_logger()
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    sch_file = find_schematic_file(project_dir)
    if not sch_file:
        return {"error": f"Schematic file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_file = os.path.join(project_dir, "output/reports/erc_report.json")

    result = run_cmd([
        config.kicad_cli, "sch", "erc", sch_file,
        "--severity-all",
        "--format", "json",
        "--output", output_file,
    ])

    if result.success and os.path.exists(output_file):
        try:
            with open(output_file) as f:
                data = json.load(f)
            violations = data.get("violations", data.get("errors", []))
            if not isinstance(violations, list):
                violations = []
            return {
                "success": True,
                "violations": len(violations),
                "file": output_file,
                "summary": [
                    {"type": v.get("type"), "desc": v.get("description")}
                    for v in violations[:10]
                ],
            }
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse ERC report: {e}")
            return {"success": False, "error": f"Failed to parse ERC report: {e}"}

    return {"success": False, "error": result.stderr or result.error}
