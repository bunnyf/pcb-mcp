"""
Configuration module for KiCad MCP Server.

All configuration values can be overridden via environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True)
class Config:
    """Immutable configuration for KiCad MCP Server."""

    # Base directories
    projects_base: str = field(
        default_factory=lambda: os.environ.get("KICAD_MCP_PROJECTS_BASE", "/root/pcb/projects")
    )
    tasks_dir: str = field(
        default_factory=lambda: os.environ.get("KICAD_MCP_TASKS_DIR", "/root/pcb/tasks")
    )

    # External tools
    kicad_cli: str = field(
        default_factory=lambda: os.environ.get("KICAD_MCP_KICAD_CLI", "kicad-cli")
    )
    freerouting_jar: str = field(
        default_factory=lambda: os.environ.get("KICAD_MCP_FREEROUTING_JAR", "/opt/freerouting.jar")
    )
    java_cmd: str = field(
        default_factory=lambda: os.environ.get("KICAD_MCP_JAVA_CMD", "java")
    )

    # Timeouts (in seconds)
    default_timeout: int = field(
        default_factory=lambda: int(os.environ.get("KICAD_MCP_DEFAULT_TIMEOUT", "300"))
    )
    autoroute_sync_timeout: int = field(
        default_factory=lambda: int(os.environ.get("KICAD_MCP_AUTOROUTE_TIMEOUT", "600"))
    )

    # File limits
    max_file_size_bytes: int = field(
        default_factory=lambda: int(os.environ.get("KICAD_MCP_MAX_FILE_SIZE", str(10 * 1024 * 1024)))
    )

    # Render settings
    render_width: int = field(
        default_factory=lambda: int(os.environ.get("KICAD_MCP_RENDER_WIDTH", "1920"))
    )
    render_height: int = field(
        default_factory=lambda: int(os.environ.get("KICAD_MCP_RENDER_HEIGHT", "1080"))
    )

    # Task cleanup settings
    task_max_age_days: int = field(
        default_factory=lambda: int(os.environ.get("KICAD_MCP_TASK_MAX_AGE_DAYS", "7"))
    )

    # Binary file extensions (for base64 encoding)
    binary_extensions: FrozenSet[str] = field(
        default_factory=lambda: frozenset({
            '.png', '.jpg', '.jpeg', '.gif', '.zip', '.pdf', '.step', '.glb', '.bmp', '.ico'
        })
    )

    # Output subdirectories
    output_subdirs: tuple[str, ...] = (
        "output/gerber",
        "output/bom",
        "output/3d",
        "output/reports",
        "output/jlcpcb",
        "output/docs",
        "output/images",
        "output/netlist",
        "output/backup",
    )


# Global configuration instance - can be replaced for testing
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """Set a custom configuration (useful for testing)."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset configuration to default (re-reads environment variables)."""
    global _config
    _config = None
