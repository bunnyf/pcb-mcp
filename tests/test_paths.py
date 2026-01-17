"""Tests for path validation utilities."""

import os
import tempfile
import pytest

from kicad_mcp_server.config import Config, set_config, reset_config
from kicad_mcp_server.utils.paths import (
    is_safe_path,
    validate_project_name,
    get_project_dir,
    validate_project_path,
    validate_file_path,
    find_pcb_file,
    find_schematic_file,
    ensure_output_dirs,
    PathValidationError,
)


class TestIsSafePath:
    """Tests for is_safe_path function."""

    def test_safe_path_within_base(self, tmp_path):
        """Test that paths within base directory are safe."""
        base = str(tmp_path)
        safe = os.path.join(base, "project", "file.txt")
        assert is_safe_path(safe, base) is True

    def test_unsafe_path_outside_base(self, tmp_path):
        """Test that paths outside base directory are unsafe."""
        base = str(tmp_path)
        unsafe = "/etc/passwd"
        assert is_safe_path(unsafe, base) is False

    def test_path_traversal_attack(self, tmp_path):
        """Test that path traversal is blocked."""
        base = str(tmp_path)
        attack = os.path.join(base, "..", "..", "etc", "passwd")
        assert is_safe_path(attack, base) is False

    def test_base_path_itself_is_safe(self, tmp_path):
        """Test that the base path itself is considered safe."""
        base = str(tmp_path)
        assert is_safe_path(base, base) is True

    def test_similar_prefix_not_confused(self, tmp_path):
        """Test that similar prefixes don't cause confusion."""
        base = str(tmp_path / "projects")
        os.makedirs(base, exist_ok=True)

        # Create a similar-named directory
        similar = str(tmp_path / "projects2")
        os.makedirs(similar, exist_ok=True)

        assert is_safe_path(similar, base) is False


class TestValidateProjectName:
    """Tests for validate_project_name function."""

    def test_valid_project_names(self):
        """Test valid project names."""
        assert validate_project_name("my_project") is True
        assert validate_project_name("Project123") is True
        assert validate_project_name("test-board") is True
        assert validate_project_name("v1.0") is True

    def test_invalid_project_names(self):
        """Test invalid project names."""
        assert validate_project_name("") is False
        assert validate_project_name(".hidden") is False
        assert validate_project_name("../escape") is False
        assert validate_project_name("path/to/project") is False
        assert validate_project_name("bad..name") is False

    def test_special_characters_rejected(self):
        """Test that special characters are rejected."""
        assert validate_project_name("project;rm -rf") is False
        assert validate_project_name("project`id`") is False
        assert validate_project_name("project$(cmd)") is False


class TestGetProjectDir:
    """Tests for get_project_dir function."""

    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_valid_project(self, tmp_path):
        """Test getting directory for valid project."""
        config = Config()
        # We can't easily override frozen dataclass, so just test the function
        result = get_project_dir("my_project")
        assert "my_project" in result

    def test_invalid_project_raises_error(self):
        """Test that invalid project names raise error."""
        with pytest.raises(PathValidationError):
            get_project_dir("../escape")

        with pytest.raises(PathValidationError):
            get_project_dir(".hidden")


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def setup_method(self):
        reset_config()
        self.tmp_dir = tempfile.mkdtemp()
        # Create a custom config pointing to our temp directory
        os.environ["KICAD_MCP_PROJECTS_BASE"] = self.tmp_dir
        reset_config()

    def teardown_method(self):
        reset_config()
        if "KICAD_MCP_PROJECTS_BASE" in os.environ:
            del os.environ["KICAD_MCP_PROJECTS_BASE"]

    def test_valid_file_within_projects(self):
        """Test validating a file within projects directory."""
        # Create a test file
        test_file = os.path.join(self.tmp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        result = validate_file_path(test_file)
        assert result == os.path.realpath(test_file)

    def test_file_outside_projects_rejected(self):
        """Test that files outside allowed directories are rejected."""
        with pytest.raises(PathValidationError):
            validate_file_path("/etc/passwd")

    def test_nonexistent_file_rejected(self):
        """Test that nonexistent files are rejected when must_exist=True."""
        fake_file = os.path.join(self.tmp_dir, "nonexistent.txt")
        with pytest.raises(PathValidationError):
            validate_file_path(fake_file, must_exist=True)


class TestFindFiles:
    """Tests for find_pcb_file and find_schematic_file."""

    def test_find_pcb_file(self, tmp_path):
        """Test finding PCB file in directory."""
        # Create a mock PCB file
        pcb_file = tmp_path / "test.kicad_pcb"
        pcb_file.write_text("")

        result = find_pcb_file(str(tmp_path))
        assert result is not None
        assert result.endswith(".kicad_pcb")

    def test_find_pcb_file_not_found(self, tmp_path):
        """Test when no PCB file exists."""
        result = find_pcb_file(str(tmp_path))
        assert result is None

    def test_find_schematic_file(self, tmp_path):
        """Test finding schematic file in directory."""
        # Create a mock schematic file
        sch_file = tmp_path / "test.kicad_sch"
        sch_file.write_text("")

        result = find_schematic_file(str(tmp_path))
        assert result is not None
        assert result.endswith(".kicad_sch")

    def test_find_schematic_file_not_found(self, tmp_path):
        """Test when no schematic file exists."""
        result = find_schematic_file(str(tmp_path))
        assert result is None


class TestEnsureOutputDirs:
    """Tests for ensure_output_dirs function."""

    def test_creates_all_subdirs(self, tmp_path):
        """Test that all output subdirectories are created."""
        ensure_output_dirs(str(tmp_path))

        assert (tmp_path / "output" / "gerber").exists()
        assert (tmp_path / "output" / "bom").exists()
        assert (tmp_path / "output" / "3d").exists()
        assert (tmp_path / "output" / "reports").exists()

    def test_idempotent(self, tmp_path):
        """Test that calling twice doesn't cause errors."""
        ensure_output_dirs(str(tmp_path))
        ensure_output_dirs(str(tmp_path))

        assert (tmp_path / "output" / "gerber").exists()
