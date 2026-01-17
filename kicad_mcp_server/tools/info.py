"""
Information and query tools for KiCad MCP Server.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from .. import __version__
from ..config import get_config
from ..utils import (
    get_logger,
    run_cmd,
    validate_project_path,
    find_pcb_file,
    find_schematic_file,
    PathValidationError,
)
from ..pcbnew_api import get_pcbnew, HAS_PCBNEW


def tool_list_projects() -> dict[str, Any]:
    """
    List all projects in the projects directory.

    Returns:
        List of projects with their file information
    """
    config = get_config()
    projects = []

    if os.path.exists(config.projects_base):
        for name in os.listdir(config.projects_base):
            project_path = os.path.join(config.projects_base, name)
            if os.path.isdir(project_path) and not name.startswith("."):
                pcb = find_pcb_file(project_path)
                sch = find_schematic_file(project_path)
                projects.append({
                    "name": name,
                    "has_pcb": pcb is not None,
                    "has_sch": sch is not None,
                    "pcb_file": os.path.basename(pcb) if pcb else None,
                })

    return {"projects": projects, "count": len(projects)}


def tool_get_board_info(project: str) -> dict[str, Any]:
    """
    Get detailed information about a PCB board.

    Args:
        project: Project name

    Returns:
        Board information including dimensions, layers, components, etc.
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

        # Board dimensions
        bbox = board.GetBoardEdgesBoundingBox()
        width_mm = bbox.GetWidth() / 1_000_000.0
        height_mm = bbox.GetHeight() / 1_000_000.0

        # Layer count
        layer_count = board.GetCopperLayerCount()

        # Component statistics
        footprints = board.GetFootprints()
        fp_count = len(footprints)

        smd_count = 0
        tht_count = 0
        for fp in footprints:
            attrs = fp.GetAttributes()
            if attrs & pcbnew.FP_SMD:
                smd_count += 1
            elif attrs & pcbnew.FP_THROUGH_HOLE:
                tht_count += 1

        # Net count
        netinfo = board.GetNetInfo()
        net_count = netinfo.GetNetCount()

        # Zone count
        zones = board.Zones()
        zone_count = zones.size() if hasattr(zones, "size") else len(list(zones))

        # Via count
        tracks = board.GetTracks()
        via_count = sum(1 for t in tracks if t.GetClass() == "PCB_VIA")

        return {
            "success": True,
            "board": {
                "width_mm": round(width_mm, 2),
                "height_mm": round(height_mm, 2),
                "area_mm2": round(width_mm * height_mm, 2),
                "layers": layer_count,
            },
            "components": {
                "total": fp_count,
                "smd": smd_count,
                "tht": tht_count,
            },
            "nets": net_count,
            "zones": zone_count,
            "vias": via_count,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_get_files(project: str) -> dict[str, Any]:
    """
    Get list of output files for a project.

    Args:
        project: Project name

    Returns:
        List of output files with their paths and sizes
    """
    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    output_dir = os.path.join(project_dir, "output")
    if not os.path.exists(output_dir):
        return {"files": [], "error": "Output directory does not exist"}

    files = []
    for root, _, filenames in os.walk(output_dir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, output_dir)
            size = os.path.getsize(filepath)
            files.append({
                "name": filename,
                "path": rel_path,
                "full_path": filepath,
                "size": f"{size / 1024:.1f}KB" if size > 1024 else f"{size}B",
            })

    return {"files": files, "count": len(files)}


def tool_version() -> dict[str, Any]:
    """
    Get version information about KiCad and MCP server.

    Returns:
        Version information for all components
    """
    config = get_config()

    result = run_cmd([config.kicad_cli, "--version"])
    freerouting_ok = os.path.exists(config.freerouting_jar)

    return {
        "kicad": result.stdout.strip() if result.success else "Not installed",
        "pcbnew_api": HAS_PCBNEW,
        "freerouting": freerouting_ok,
        "mcp_server": __version__,
        "features": [
            "drc", "erc", "fill_zones", "board_info",
            "auto_route_async", "task_status", "task_cleanup",
            "gerber", "drill", "bom", "netlist", "pos",
            "3d_render", "svg", "pdf", "step",
            "sch_pdf", "sch_svg",
        ],
    }
