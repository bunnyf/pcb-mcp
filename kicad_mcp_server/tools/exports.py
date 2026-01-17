"""
Export tools for KiCad MCP Server.

Provides various export formats for PCB and schematic files.
"""

from __future__ import annotations

import glob
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


def tool_export_gerber(project: str) -> dict[str, Any]:
    """
    Export Gerber and drill files.

    Args:
        project: Project name

    Returns:
        Export result with file list
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_dir = os.path.join(project_dir, "output/gerber")

    # Export Gerber files
    r1 = run_cmd([
        config.kicad_cli, "pcb", "export", "gerbers",
        "--output", output_dir + "/",
        pcb_file,
    ])

    # Export drill files
    r2 = run_cmd([
        config.kicad_cli, "pcb", "export", "drill",
        "--output", output_dir + "/",
        pcb_file,
    ])

    if r1.success and r2.success:
        files = os.listdir(output_dir)
        return {"success": True, "dir": output_dir, "files": files, "count": len(files)}

    error = " ".join(filter(None, [r1.stderr, r2.stderr])).strip()
    return {"success": False, "error": error or "Export failed"}


def tool_export_bom(project: str) -> dict[str, Any]:
    """
    Export Bill of Materials (BOM) as CSV.

    Args:
        project: Project name

    Returns:
        Export result with file preview
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    sch_file = find_schematic_file(project_dir)
    if not sch_file:
        return {"error": f"Schematic file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_file = os.path.join(project_dir, "output/bom/bom.csv")

    result = run_cmd([
        config.kicad_cli, "sch", "export", "bom",
        "--output", output_file,
        sch_file,
    ])

    if result.success and os.path.exists(output_file):
        with open(output_file) as f:
            lines = f.readlines()
        return {
            "success": True,
            "file": output_file,
            "lines": len(lines),
            "preview": lines[:5],
        }

    return {"success": False, "error": result.stderr or result.error}


def tool_export_netlist(project: str, format: str = "kicadxml") -> dict[str, Any]:
    """
    Export netlist in various formats.

    Args:
        project: Project name
        format: Output format (kicadxml, spice, cadstar, orcadpcb2)

    Returns:
        Export result
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    sch_file = find_schematic_file(project_dir)
    if not sch_file:
        return {"error": f"Schematic file not found: {project}"}

    ensure_output_dirs(project_dir)

    ext_map = {"kicadxml": "xml", "cadstar": "cir", "orcadpcb2": "net", "spice": "cir"}
    ext = ext_map.get(format, "net")
    output_file = os.path.join(project_dir, f"output/netlist/netlist.{ext}")

    result = run_cmd([
        config.kicad_cli, "sch", "export", "netlist",
        "--format", format,
        "--output", output_file,
        sch_file,
    ])

    if result.success and os.path.exists(output_file):
        return {"success": True, "file": output_file, "format": format}

    return {"success": False, "error": result.stderr or result.error}


def tool_export_3d(project: str, view: str = "top") -> dict[str, Any]:
    """
    Export 3D rendered images of the PCB.

    Args:
        project: Project name
        view: View angle (top, bottom, front, back, iso, iso_back, all)

    Returns:
        Export result with rendered files
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_dir = os.path.join(project_dir, "output/3d")

    views_config = {
        "top": {"side": "top", "rotate": None},
        "bottom": {"side": "bottom", "rotate": None},
        "front": {"side": "front", "rotate": None},
        "back": {"side": "back", "rotate": None},
        "iso": {"side": "top", "rotate": "30,0,-45"},
        "iso_back": {"side": "bottom", "rotate": "30,0,135"},
    }

    if view == "all":
        views_to_render = ["top", "bottom", "iso"]
    elif view in views_config:
        views_to_render = [view]
    else:
        valid_views = ", ".join(list(views_config.keys()) + ["all"])
        return {"error": f"Unknown view: {view}, valid options: {valid_views}"}

    results = {}
    for v in views_to_render:
        cfg = views_config[v]
        output_file = os.path.join(output_dir, f"pcb_{v}.png")

        cmd = [
            config.kicad_cli, "pcb", "render",
            "--output", output_file,
            "--width", str(config.render_width),
            "--height", str(config.render_height),
            "--side", cfg["side"],
            "--quality", "high",
            "--background", "opaque",
            "--perspective",
        ]

        if cfg.get("rotate"):
            cmd.extend(["--rotate", cfg["rotate"]])

        cmd.append(pcb_file)

        r = run_cmd(cmd, cwd=project_dir, use_xvfb=True)
        success = r.success and os.path.exists(output_file)

        results[v] = {
            "success": success,
            "file": output_file if success else None,
            "size": f"{os.path.getsize(output_file) / 1024:.1f}KB" if success else None,
            "error": r.stderr if not success else None,
        }

    success_count = sum(1 for r in results.values() if r["success"])
    files = [r["file"] for r in results.values() if r["file"]]

    return {
        "success": success_count > 0,
        "results": results,
        "files": files,
        "message": f"Generated {success_count}/{len(views_to_render)} 3D render(s)",
    }


def tool_export_svg(project: str, view: str = "all") -> dict[str, Any]:
    """
    Export PCB as SVG images.

    Args:
        project: Project name
        view: View (top, bottom, all)

    Returns:
        Export result with SVG files
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_dir = os.path.join(project_dir, "output/images")

    views_config = {
        "top": {"layers": "F.Cu,F.SilkS,F.Mask,Edge.Cuts", "mirror": False},
        "bottom": {"layers": "B.Cu,B.SilkS,B.Mask,Edge.Cuts", "mirror": True},
    }

    if view == "all":
        views_to_render = list(views_config.keys())
    elif view in views_config:
        views_to_render = [view]
    else:
        return {"error": f"Unknown view: {view}, valid options: top, bottom, all"}

    results = {}
    for v in views_to_render:
        cfg = views_config[v]
        output_file = os.path.join(output_dir, f"pcb_{v}.svg")

        cmd = [
            config.kicad_cli, "pcb", "export", "svg",
            "--output", output_file,
            "--layers", cfg["layers"],
            "--page-size-mode", "2",
            "--exclude-drawing-sheet",
        ]

        if cfg["mirror"]:
            cmd.append("--mirror")

        cmd.append(pcb_file)

        r = run_cmd(cmd, cwd=project_dir)
        success = r.success and os.path.exists(output_file)
        results[v] = {"success": success, "file": output_file if success else None}

    files = [r["file"] for r in results.values() if r["file"]]
    return {"success": len(files) > 0, "files": files, "results": results}


def tool_export_pdf(project: str, layers: str = "all") -> dict[str, Any]:
    """
    Export PCB as PDF.

    Args:
        project: Project name
        layers: Layer set (top, bottom, all) or custom layer string

    Returns:
        Export result
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    ensure_output_dirs(project_dir)

    layer_sets = {
        "top": "F.Cu,F.SilkS,F.Mask,Edge.Cuts",
        "bottom": "B.Cu,B.SilkS,B.Mask,Edge.Cuts",
        "all": "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
    }

    layer_str = layer_sets.get(layers, layers)
    output_file = os.path.join(project_dir, f"output/docs/pcb_{layers}.pdf")

    result = run_cmd([
        config.kicad_cli, "pcb", "export", "pdf",
        "--output", output_file,
        "--layers", layer_str,
        pcb_file,
    ])

    if result.success and os.path.exists(output_file):
        return {"success": True, "file": output_file}

    return {"success": False, "error": result.stderr or result.error}


def tool_export_sch_pdf(project: str) -> dict[str, Any]:
    """
    Export schematic as PDF.

    Args:
        project: Project name

    Returns:
        Export result
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    sch_file = find_schematic_file(project_dir)
    if not sch_file:
        return {"error": f"Schematic file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_file = os.path.join(project_dir, "output/docs/schematic.pdf")

    result = run_cmd([
        config.kicad_cli, "sch", "export", "pdf",
        "--output", output_file,
        sch_file,
    ])

    if result.success and os.path.exists(output_file):
        return {"success": True, "file": output_file}

    return {"success": False, "error": result.stderr or result.error}


def tool_export_sch_svg(project: str) -> dict[str, Any]:
    """
    Export schematic as SVG.

    Args:
        project: Project name

    Returns:
        Export result with SVG files
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    sch_file = find_schematic_file(project_dir)
    if not sch_file:
        return {"error": f"Schematic file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_dir = os.path.join(project_dir, "output/images")

    result = run_cmd([
        config.kicad_cli, "sch", "export", "svg",
        "--output", output_dir + "/",
        sch_file,
    ])

    if result.success:
        svg_files = glob.glob(os.path.join(output_dir, "*.svg"))
        return {"success": True, "files": svg_files}

    return {"success": False, "error": result.stderr or result.error}


def tool_export_step(project: str) -> dict[str, Any]:
    """
    Export PCB as STEP 3D model.

    Args:
        project: Project name

    Returns:
        Export result
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    ensure_output_dirs(project_dir)
    output_file = os.path.join(project_dir, "output/3d/pcb.step")

    result = run_cmd([
        config.kicad_cli, "pcb", "export", "step",
        "--output", output_file,
        "--subst-models",
        pcb_file,
    ])

    if result.success and os.path.exists(output_file):
        size = os.path.getsize(output_file)
        return {
            "success": True,
            "file": output_file,
            "size": f"{size / 1024 / 1024:.1f}MB",
        }

    return {"success": False, "error": result.stderr or result.error}


def tool_export_jlcpcb(project: str) -> dict[str, Any]:
    """
    Export complete JLCPCB/PCBWay manufacturing package.

    Includes Gerber, drill, BOM, and position files.

    Args:
        project: Project name

    Returns:
        Export result with all manufacturing files
    """
    config = get_config()

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    pcb_file = find_pcb_file(project_dir)
    sch_file = find_schematic_file(project_dir)

    if not pcb_file:
        return {"error": f"PCB file not found: {project}"}

    jlcpcb_dir = os.path.join(project_dir, "output/jlcpcb")
    os.makedirs(jlcpcb_dir, exist_ok=True)

    results = {}

    # Export Gerber and drill files
    r1 = run_cmd([
        config.kicad_cli, "pcb", "export", "gerbers",
        "--output", jlcpcb_dir + "/",
        pcb_file,
    ])
    r2 = run_cmd([
        config.kicad_cli, "pcb", "export", "drill",
        "--output", jlcpcb_dir + "/",
        pcb_file,
    ])
    results["gerber"] = r1.success and r2.success

    # Export BOM if schematic exists
    if sch_file:
        bom_file = os.path.join(jlcpcb_dir, "bom.csv")
        r3 = run_cmd([
            config.kicad_cli, "sch", "export", "bom",
            "--output", bom_file,
            sch_file,
        ])
        results["bom"] = r3.success
    else:
        results["bom"] = False

    # Export position file
    pos_file = os.path.join(jlcpcb_dir, "position.csv")
    r4 = run_cmd([
        config.kicad_cli, "pcb", "export", "pos",
        "--output", pos_file,
        "--format", "csv",
        "--units", "mm",
        "--side", "both",
        "--smd-only",
        pcb_file,
    ])
    results["position"] = r4.success and os.path.exists(pos_file)

    files = os.listdir(jlcpcb_dir) if os.path.exists(jlcpcb_dir) else []

    return {
        "success": results["gerber"],
        "results": results,
        "dir": jlcpcb_dir,
        "files": files,
        "count": len(files),
        "message": "JLCPCB manufacturing package generated",
    }


def tool_export_all(project: str) -> dict[str, Any]:
    """
    Export all available file types.

    Args:
        project: Project name

    Returns:
        Results for all export operations
    """
    from .checks import tool_run_drc, tool_run_erc

    try:
        project_dir = validate_project_path(project)
    except PathValidationError as e:
        return {"error": str(e)}

    results = {}

    results["drc"] = tool_run_drc(project)
    results["erc"] = tool_run_erc(project)
    results["gerber"] = tool_export_gerber(project)
    results["bom"] = tool_export_bom(project)
    results["3d"] = tool_export_3d(project, "all")
    results["svg"] = tool_export_svg(project, "all")
    results["sch_pdf"] = tool_export_sch_pdf(project)

    output_dir = os.path.join(project_dir, "output")
    total_files = sum(
        len(files) for _, _, files in os.walk(output_dir)
    ) if os.path.exists(output_dir) else 0

    return {
        "success": True,
        "results": results,
        "total_files": total_files,
        "output_dir": output_dir,
    }
