"""
MCP Protocol handler for KiCad MCP Server.

Implements JSON-RPC 2.0 based Model Context Protocol.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from . import __version__
from .tools.registry import TOOLS, get_tool_handler
from .utils import get_logger


# MCP Protocol version
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "kicad-mcp"
SERVER_VERSION = __version__


def handle_request(request: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Handle an MCP protocol request.

    Args:
        request: JSON-RPC request object

    Returns:
        JSON-RPC response or None for notifications
    """
    logger = get_logger()

    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")

    # Handle initialize request
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }

    # Handle initialized notification (no response needed)
    if method == "notifications/initialized":
        return None

    # Handle tools/list request
    if method == "tools/list":
        tools = [
            {
                "name": name,
                "description": tool["desc"],
                "inputSchema": tool["schema"],
            }
            for name, tool in TOOLS.items()
        ]
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools},
        }

    # Handle tools/call request
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        logger.info(f"Tool call: {tool_name}, args: {arguments}")

        try:
            handler = get_tool_handler(tool_name)
            if handler is None:
                result = {"error": f"Unknown tool: {tool_name}"}
            else:
                result = handler(**arguments)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2),
                        }
                    ]
                },
            }
        except Exception as e:
            logger.error(f"Tool error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(e)},
            }

    # Unknown method
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }
