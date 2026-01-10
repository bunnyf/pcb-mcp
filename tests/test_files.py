"""Tests for file operation tools."""

import base64
import os
import tempfile
import pytest

from kicad_mcp_server.config import reset_config
from kicad_mcp_server.tools.files import tool_read_file


class TestToolReadFile:
    """Tests for read_file tool."""

    def setup_method(self):
        """Set up test environment."""
        reset_config()
        self.tmp_dir = tempfile.mkdtemp()
        os.environ["KICAD_MCP_PROJECTS_BASE"] = self.tmp_dir
        reset_config()

    def teardown_method(self):
        """Clean up test environment."""
        reset_config()
        if "KICAD_MCP_PROJECTS_BASE" in os.environ:
            del os.environ["KICAD_MCP_PROJECTS_BASE"]
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_read_text_file(self):
        """Test reading a text file."""
        test_file = os.path.join(self.tmp_dir, "test.txt")
        content = "Hello, World!\nLine 2"
        with open(test_file, "w") as f:
            f.write(content)

        result = tool_read_file(test_file)

        assert "error" not in result
        assert result["encoding"] == "utf-8"
        assert result["content"] == content

    def test_read_binary_file(self):
        """Test reading a binary file (base64 encoded)."""
        test_file = os.path.join(self.tmp_dir, "test.png")
        binary_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        with open(test_file, "wb") as f:
            f.write(binary_content)

        result = tool_read_file(test_file)

        assert "error" not in result
        assert result["encoding"] == "base64"

        # Decode and verify
        decoded = base64.b64decode(result["content"])
        assert decoded == binary_content

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        result = tool_read_file(os.path.join(self.tmp_dir, "nonexistent.txt"))

        assert "error" in result
        assert "not found" in result["error"].lower() or "File not found" in result["error"]

    def test_read_file_outside_projects(self):
        """Test that reading files outside projects directory is blocked."""
        result = tool_read_file("/etc/passwd")

        assert "error" in result
        assert "denied" in result["error"].lower() or "Access denied" in result["error"]

    def test_read_file_with_path_traversal(self):
        """Test that path traversal attacks are blocked."""
        # Create a file in the allowed directory
        test_file = os.path.join(self.tmp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        # Try to escape using path traversal
        traversal_path = os.path.join(self.tmp_dir, "..", "..", "etc", "passwd")
        result = tool_read_file(traversal_path)

        assert "error" in result

    def test_file_size_reported(self):
        """Test that file size is reported."""
        test_file = os.path.join(self.tmp_dir, "sized.txt")
        content = "A" * 1000
        with open(test_file, "w") as f:
            f.write(content)

        result = tool_read_file(test_file)

        assert "size" in result
        assert result["size"] == 1000

    def test_large_file_rejected(self):
        """Test that files over size limit are rejected."""
        # Create a file larger than default limit
        test_file = os.path.join(self.tmp_dir, "large.txt")

        # Default limit is 10MB, create an 11MB file
        with open(test_file, "w") as f:
            f.write("A" * (11 * 1024 * 1024))

        result = tool_read_file(test_file)

        assert "error" in result
        assert "large" in result["error"].lower() or "too large" in result["error"].lower()
