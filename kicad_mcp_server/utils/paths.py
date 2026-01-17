"""
Path utilities for KiCad MCP Server.

Provides safe path handling with validation to prevent directory traversal attacks.
"""

from __future__ import annotations

import glob
import os
import re
from typing import Optional

from ..config import get_config
from .logging import get_logger


class PathValidationError(Exception):
    """Raised when path validation fails."""

    pass


def is_safe_path(path: str, base_dir: str) -> bool:
    """
    Check if a path is safe (within the base directory).

    Prevents directory traversal attacks by ensuring the resolved path
    stays within the allowed base directory.

    Args:
        path: Path to validate
        base_dir: Allowed base directory

    Returns:
        True if path is safe, False otherwise
    """
    # Resolve both paths to absolute, normalized paths
    try:
        resolved_path = os.path.realpath(os.path.abspath(path))
        resolved_base = os.path.realpath(os.path.abspath(base_dir))
    except (OSError, ValueError):
        return False

    # Check if the resolved path starts with the base directory
    # Add trailing separator to prevent partial matches (e.g., /root/pcb2 matching /root/pcb)
    if not resolved_base.endswith(os.sep):
        resolved_base += os.sep

    return resolved_path.startswith(resolved_base) or resolved_path == resolved_base.rstrip(os.sep)


def validate_project_name(project: str) -> bool:
    """
    Validate that a project name is safe.

    Args:
        project: Project name to validate

    Returns:
        True if valid, False otherwise
    """
    # Only allow alphanumeric, underscore, hyphen, and dot
    # Must not start with dot or contain path separators
    if not project:
        return False
    if project.startswith("."):
        return False
    if os.sep in project or "/" in project or "\\" in project:
        return False
    if ".." in project:
        return False
    # Allow reasonable project name characters
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*$", project))


def get_project_dir(project: str) -> str:
    """
    Get the full path to a project directory.

    Args:
        project: Project name

    Returns:
        Full path to project directory

    Raises:
        PathValidationError: If project name is invalid
    """
    config = get_config()

    if not validate_project_name(project):
        raise PathValidationError(f"Invalid project name: {project}")

    project_path = os.path.join(config.projects_base, project)

    # Double-check the path is safe
    if not is_safe_path(project_path, config.projects_base):
        raise PathValidationError(f"Invalid project path: {project}")

    return project_path


def validate_project_path(project: str) -> str:
    """
    Validate and return the project directory path.

    Args:
        project: Project name

    Returns:
        Full path to project directory

    Raises:
        PathValidationError: If project is invalid or doesn't exist
    """
    project_path = get_project_dir(project)

    if not os.path.isdir(project_path):
        raise PathValidationError(f"Project not found: {project}")

    return project_path


def validate_file_path(filepath: str, must_exist: bool = True) -> str:
    """
    Validate that a file path is safe to access.

    Only allows access to files within the projects directory or tasks directory.

    Args:
        filepath: File path to validate
        must_exist: Whether the file must exist

    Returns:
        Validated absolute file path

    Raises:
        PathValidationError: If path is invalid or outside allowed directories
    """
    config = get_config()
    logger = get_logger()

    # Resolve to absolute path
    try:
        abs_path = os.path.realpath(os.path.abspath(filepath))
    except (OSError, ValueError) as e:
        raise PathValidationError(f"Invalid file path: {filepath}") from e

    # Check if path is within allowed directories
    allowed_dirs = [config.projects_base, config.tasks_dir]
    is_allowed = any(is_safe_path(abs_path, allowed_dir) for allowed_dir in allowed_dirs)

    if not is_allowed:
        logger.warning(f"Blocked access to file outside allowed directories: {filepath}")
        raise PathValidationError(
            f"Access denied: file must be within projects or tasks directory"
        )

    # Check existence if required
    if must_exist and not os.path.exists(abs_path):
        raise PathValidationError(f"File not found: {filepath}")

    return abs_path


def find_pcb_file(project_dir: str) -> Optional[str]:
    """
    Find the KiCad PCB file in a project directory.

    Args:
        project_dir: Project directory path

    Returns:
        Path to PCB file, or None if not found
    """
    files = glob.glob(os.path.join(project_dir, "*.kicad_pcb"))
    return files[0] if files else None


def find_schematic_file(project_dir: str) -> Optional[str]:
    """
    Find the KiCad schematic file in a project directory.

    Args:
        project_dir: Project directory path

    Returns:
        Path to schematic file, or None if not found
    """
    files = glob.glob(os.path.join(project_dir, "*.kicad_sch"))
    return files[0] if files else None


def ensure_output_dirs(project_dir: str) -> None:
    """
    Ensure all output directories exist for a project.

    Args:
        project_dir: Project directory path
    """
    config = get_config()

    for subdir in config.output_subdirs:
        dir_path = os.path.join(project_dir, subdir)
        os.makedirs(dir_path, exist_ok=True)
