"""Tool implementations for KiCad MCP Server."""

from .checks import tool_run_drc, tool_run_erc
from .info import tool_list_projects, tool_get_board_info, tool_get_files, tool_version
from .operations import tool_fill_zones, tool_auto_route
from .tasks import tool_get_task_status, tool_list_tasks
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
from .registry import TOOLS, get_tool_handler

__all__ = [
    "tool_run_drc",
    "tool_run_erc",
    "tool_list_projects",
    "tool_get_board_info",
    "tool_get_files",
    "tool_version",
    "tool_fill_zones",
    "tool_auto_route",
    "tool_get_task_status",
    "tool_list_tasks",
    "tool_export_gerber",
    "tool_export_bom",
    "tool_export_netlist",
    "tool_export_3d",
    "tool_export_svg",
    "tool_export_pdf",
    "tool_export_sch_pdf",
    "tool_export_sch_svg",
    "tool_export_step",
    "tool_export_jlcpcb",
    "tool_export_all",
    "tool_read_file",
    "TOOLS",
    "get_tool_handler",
]
