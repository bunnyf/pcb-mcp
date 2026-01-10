"""Tests for MCP protocol handler."""

import json
import pytest

from kicad_mcp_server.protocol import handle_request, PROTOCOL_VERSION, SERVER_VERSION


class TestProtocolHandler:
    """Tests for MCP protocol handling."""

    def test_initialize_request(self):
        """Test handling initialize request."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        }

        response = handle_request(request)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert response["result"]["serverInfo"]["version"] == SERVER_VERSION

    def test_initialized_notification(self):
        """Test handling initialized notification."""
        request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        response = handle_request(request)

        # Notifications don't get a response
        assert response is None

    def test_tools_list(self):
        """Test listing available tools."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        response = handle_request(request)

        assert response is not None
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]

        tools = response["result"]["tools"]
        assert len(tools) > 0

        # Check some expected tools exist
        tool_names = [t["name"] for t in tools]
        assert "list_projects" in tool_names
        assert "run_drc" in tool_names
        assert "export_gerber" in tool_names
        assert "read_file" in tool_names

    def test_tools_list_has_schemas(self):
        """Test that tools have input schemas."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {},
        }

        response = handle_request(request)
        tools = response["result"]["tools"]

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    def test_tools_call_list_projects(self):
        """Test calling list_projects tool."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "list_projects",
                "arguments": {},
            },
        }

        response = handle_request(request)

        assert response is not None
        assert response["id"] == 4
        assert "result" in response
        assert "content" in response["result"]

        content = response["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"

        # Parse the JSON result
        result = json.loads(content[0]["text"])
        assert "projects" in result
        assert "count" in result

    def test_tools_call_get_version(self):
        """Test calling get_version tool."""
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_version",
                "arguments": {},
            },
        }

        response = handle_request(request)

        assert response is not None
        content = response["result"]["content"]
        result = json.loads(content[0]["text"])

        assert "mcp_server" in result
        assert "features" in result
        assert isinstance(result["features"], list)

    def test_tools_call_unknown_tool(self):
        """Test calling an unknown tool."""
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {},
            },
        }

        response = handle_request(request)

        assert response is not None
        content = response["result"]["content"]
        result = json.loads(content[0]["text"])

        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_unknown_method(self):
        """Test handling unknown method."""
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "unknown/method",
            "params": {},
        }

        response = handle_request(request)

        assert response is not None
        assert "error" in response
        assert response["error"]["code"] == -32601

    def test_request_id_preserved(self):
        """Test that request ID is preserved in response."""
        request = {
            "jsonrpc": "2.0",
            "id": "custom-id-123",
            "method": "tools/list",
            "params": {},
        }

        response = handle_request(request)

        assert response["id"] == "custom-id-123"

    def test_tools_call_with_invalid_project(self):
        """Test calling tool with invalid project name."""
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "run_drc",
                "arguments": {"project": "../escape"},
            },
        }

        response = handle_request(request)

        content = response["result"]["content"]
        result = json.loads(content[0]["text"])

        assert "error" in result
