"""
File operation tools for KiCad MCP Server.
"""

from __future__ import annotations

import base64
import os
from typing import Any

from ..config import get_config
from ..utils import (
    get_logger,
    validate_file_path,
    PathValidationError,
)


def tool_read_file(filepath: str) -> dict[str, Any]:
    """
    Read file content with path validation.

    Only allows reading files within the projects or tasks directory.
    Binary files are returned as base64-encoded content.

    Args:
        filepath: Path to file to read

    Returns:
        File content (text or base64-encoded)
    """
    logger = get_logger()
    config = get_config()

    # Validate path is within allowed directories
    try:
        safe_path = validate_file_path(filepath, must_exist=True)
    except PathValidationError as e:
        logger.warning(f"File access denied: {filepath}")
        return {"error": str(e)}

    # Check file size
    size = os.path.getsize(safe_path)
    if size > config.max_file_size_bytes:
        max_mb = config.max_file_size_bytes / (1024 * 1024)
        return {"error": f"File too large (>{max_mb:.0f}MB)"}

    # Determine if file is binary
    ext = os.path.splitext(safe_path)[1].lower()
    is_binary = ext in config.binary_extensions

    try:
        if is_binary:
            with open(safe_path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            return {"encoding": "base64", "content": content, "size": size}
        else:
            with open(safe_path, "r", errors="replace") as f:
                content = f.read()
            return {"encoding": "utf-8", "content": content, "size": size}
    except IOError as e:
        logger.error(f"Failed to read file {safe_path}: {e}")
        return {"error": f"Failed to read file: {e}"}
