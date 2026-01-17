"""
Subprocess utilities for KiCad MCP Server.

Provides safe command execution with proper timeout handling.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional, Sequence

from ..config import get_config
from .logging import get_logger


@dataclass
class CommandResult:
    """Result of a command execution."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    return_code: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }
        if self.error:
            result["error"] = self.error
        if self.return_code is not None:
            result["return_code"] = self.return_code
        return result


def run_cmd(
    cmd: Sequence[str],
    cwd: Optional[str] = None,
    use_xvfb: bool = False,
    timeout: Optional[int] = None,
) -> CommandResult:
    """
    Execute a command with proper error handling.

    Args:
        cmd: Command and arguments as a sequence
        cwd: Working directory for the command
        use_xvfb: Whether to wrap command with xvfb-run for headless rendering
        timeout: Command timeout in seconds (default from config)

    Returns:
        CommandResult with execution details
    """
    logger = get_logger()
    config = get_config()

    if timeout is None:
        timeout = config.default_timeout

    # Wrap with xvfb-run if needed for headless rendering
    cmd_list = list(cmd)
    if use_xvfb:
        cmd_list = ["xvfb-run", "-a"] + cmd_list

    logger.info(f"Executing: {' '.join(cmd_list)}")

    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return CommandResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {' '.join(cmd_list)}")
        return CommandResult(
            success=False,
            stdout=e.stdout or "" if hasattr(e, "stdout") else "",
            stderr=e.stderr or "" if hasattr(e, "stderr") else "",
            error=f"Command timed out after {timeout} seconds",
        )
    except FileNotFoundError as e:
        logger.error(f"Command not found: {cmd_list[0]}")
        return CommandResult(
            success=False,
            error=f"Command not found: {cmd_list[0]}",
        )
    except PermissionError as e:
        logger.error(f"Permission denied: {cmd_list[0]}")
        return CommandResult(
            success=False,
            error=f"Permission denied executing: {cmd_list[0]}",
        )
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return CommandResult(
            success=False,
            error=str(e),
        )
