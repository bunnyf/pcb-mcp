"""
Logging utilities for KiCad MCP Server.

Provides structured logging to stderr (keeping stdout clean for MCP protocol).
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


# Custom formatter for MCP server logs
class MCPFormatter(logging.Formatter):
    """Custom formatter that adds [MCP] prefix and formats for terminal output."""

    def format(self, record: logging.LogRecord) -> str:
        # Add level-specific prefixes
        level_prefixes = {
            logging.DEBUG: "[MCP:DEBUG]",
            logging.INFO: "[MCP]",
            logging.WARNING: "[MCP:WARN]",
            logging.ERROR: "[MCP:ERROR]",
            logging.CRITICAL: "[MCP:CRITICAL]",
        }
        prefix = level_prefixes.get(record.levelno, "[MCP]")
        return f"{prefix} {record.getMessage()}"


# Module-level logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    name: str = "kicad_mcp",
) -> logging.Logger:
    """
    Set up logging for the MCP server.

    Args:
        level: Logging level (default: INFO)
        name: Logger name

    Returns:
        Configured logger instance
    """
    global _logger

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create stderr handler (stdout is reserved for MCP protocol)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(MCPFormatter())

    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """
    Get the MCP server logger instance.

    If logging hasn't been set up yet, initializes with default settings.

    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger
