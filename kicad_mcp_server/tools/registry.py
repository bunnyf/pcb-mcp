"""
Tool registry for KiCad MCP Server.

Defines all available tools and their JSON schemas.
"""

from __future__ import annotations

from typing import Any, Callable

from .checks import tool_run_drc, tool_run_erc
from .info import tool_list_projects, tool_get_board_info, tool_get_files, tool_version
from .operations import tool_fill_zones, tool_auto_route
from .tasks import tool_get_task_status, tool_list_tasks, tool_cleanup_tasks
from .exports import (
    tool_export_gerber,
    tool_export_bom,
    tool_export_netlist,
    tool_export_3d,
    tool_export_svg,
    tool_export_pdf,
    tool_export_sch_pdf,
    tool_export_sch_svg,
    tool_export_step,
    tool_export_jlcpcb,
    tool_export_all,
)
from .files import tool_read_file


# Tool definitions with JSON Schema
TOOLS: dict[str, dict[str, Any]] = {
    "list_projects": {
        "desc": "List all projects",
        "schema": {"type": "object", "properties": {}, "required": []},
    },
    "run_drc": {
        "desc": "Run Design Rule Check (DRC) on PCB",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "run_erc": {
        "desc": "Run Electrical Rule Check (ERC) on schematic",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "fill_zones": {
        "desc": "Fill all copper zones in PCB",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "auto_route": {
        "desc": "Auto-route PCB using FreeRouting (async by default, creates backup)",
        "schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
                "max_passes": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum routing passes",
                },
                "async_mode": {
                    "type": "boolean",
                    "default": True,
                    "description": "Run asynchronously (recommended)",
                },
            },
            "required": ["project"],
        },
    },
    "get_task_status": {
        "desc": "Get status of an async task",
        "schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string", "description": "Task ID"}},
            "required": ["task_id"],
        },
    },
    "list_tasks": {
        "desc": "List all async tasks",
        "schema": {"type": "object", "properties": {}, "required": []},
    },
    "cleanup_tasks": {
        "desc": "Clean up old completed/failed tasks",
        "schema": {
            "type": "object",
            "properties": {
                "max_age_days": {
                    "type": "integer",
                    "default": 7,
                    "description": "Maximum age in days for tasks to keep",
                },
            },
            "required": [],
        },
    },
    "get_board_info": {
        "desc": "Get PCB board information (dimensions, layers, components)",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "export_gerber": {
        "desc": "Export Gerber and drill files",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "export_bom": {
        "desc": "Export Bill of Materials (CSV)",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "export_netlist": {
        "desc": "Export netlist (kicadxml, spice, cadstar, orcadpcb2)",
        "schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
                "format": {
                    "type": "string",
                    "enum": ["kicadxml", "spice", "cadstar", "orcadpcb2"],
                    "default": "kicadxml",
                    "description": "Output format",
                },
            },
            "required": ["project"],
        },
    },
    "export_3d": {
        "desc": "Export 3D rendered images (top, bottom, iso, all)",
        "schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
                "view": {
                    "type": "string",
                    "enum": ["top", "bottom", "front", "back", "iso", "iso_back", "all"],
                    "default": "top",
                    "description": "View angle",
                },
            },
            "required": ["project"],
        },
    },
    "export_svg": {
        "desc": "Export PCB as SVG images",
        "schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
                "view": {
                    "type": "string",
                    "enum": ["top", "bottom", "all"],
                    "default": "all",
                    "description": "View (top/bottom/all)",
                },
            },
            "required": ["project"],
        },
    },
    "export_pdf": {
        "desc": "Export PCB as PDF",
        "schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
                "layers": {
                    "type": "string",
                    "default": "all",
                    "description": "Layer set (top, bottom, all) or custom layers",
                },
            },
            "required": ["project"],
        },
    },
    "export_sch_pdf": {
        "desc": "Export schematic as PDF",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "export_sch_svg": {
        "desc": "Export schematic as SVG",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "export_step": {
        "desc": "Export PCB as STEP 3D model",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "export_jlcpcb": {
        "desc": "Export complete JLCPCB/PCBWay manufacturing package",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "export_all": {
        "desc": "Export all available file types",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "get_output_files": {
        "desc": "List project output files",
        "schema": {
            "type": "object",
            "properties": {"project": {"type": "string", "description": "Project name"}},
            "required": ["project"],
        },
    },
    "read_file": {
        "desc": "Read file content (restricted to project/task directories)",
        "schema": {
            "type": "object",
            "properties": {"filepath": {"type": "string", "description": "File path"}},
            "required": ["filepath"],
        },
    },
    "get_version": {
        "desc": "Get version information",
        "schema": {"type": "object", "properties": {}, "required": []},
    },
}


# Tool handler mapping
_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_projects": lambda **_: tool_list_projects(),
    "run_drc": lambda project, **_: tool_run_drc(project),
    "run_erc": lambda project, **_: tool_run_erc(project),
    "fill_zones": lambda project, **_: tool_fill_zones(project),
    "auto_route": lambda project, max_passes=100, async_mode=True, **_: tool_auto_route(
        project, max_passes, async_mode
    ),
    "get_task_status": lambda task_id, **_: tool_get_task_status(task_id),
    "list_tasks": lambda **_: tool_list_tasks(),
    "cleanup_tasks": lambda max_age_days=7, **_: tool_cleanup_tasks(max_age_days),
    "get_board_info": lambda project, **_: tool_get_board_info(project),
    "export_gerber": lambda project, **_: tool_export_gerber(project),
    "export_bom": lambda project, **_: tool_export_bom(project),
    "export_netlist": lambda project, format="kicadxml", **_: tool_export_netlist(
        project, format
    ),
    "export_3d": lambda project, view="top", **_: tool_export_3d(project, view),
    "export_svg": lambda project, view="all", **_: tool_export_svg(project, view),
    "export_pdf": lambda project, layers="all", **_: tool_export_pdf(project, layers),
    "export_sch_pdf": lambda project, **_: tool_export_sch_pdf(project),
    "export_sch_svg": lambda project, **_: tool_export_sch_svg(project),
    "export_step": lambda project, **_: tool_export_step(project),
    "export_jlcpcb": lambda project, **_: tool_export_jlcpcb(project),
    "export_all": lambda project, **_: tool_export_all(project),
    "get_output_files": lambda project, **_: tool_get_files(project),
    "read_file": lambda filepath, **_: tool_read_file(filepath),
    "get_version": lambda **_: tool_version(),
}


def get_tool_handler(tool_name: str) -> Callable[..., dict[str, Any]] | None:
    """
    Get the handler function for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Handler function or None if not found
    """
    return _HANDLERS.get(tool_name)
