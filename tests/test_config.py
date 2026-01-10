"""Tests for configuration module."""

import os
import pytest

from kicad_mcp_server.config import Config, get_config, set_config, reset_config


class TestConfig:
    """Tests for Config dataclass."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config()

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        assert config.projects_base == "/root/pcb/projects"
        assert config.tasks_dir == "/root/pcb/tasks"
        assert config.kicad_cli == "kicad-cli"
        assert config.default_timeout == 300
        assert config.max_file_size_bytes == 10 * 1024 * 1024

    def test_environment_override(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("KICAD_MCP_PROJECTS_BASE", "/custom/projects")
        monkeypatch.setenv("KICAD_MCP_DEFAULT_TIMEOUT", "600")

        reset_config()
        config = get_config()

        assert config.projects_base == "/custom/projects"
        assert config.default_timeout == 600

    def test_binary_extensions(self):
        """Test binary extensions set."""
        config = Config()
        assert ".png" in config.binary_extensions
        assert ".pdf" in config.binary_extensions
        assert ".txt" not in config.binary_extensions

    def test_output_subdirs(self):
        """Test output subdirectories tuple."""
        config = Config()
        assert "output/gerber" in config.output_subdirs
        assert "output/bom" in config.output_subdirs
        assert "output/3d" in config.output_subdirs


class TestConfigSingleton:
    """Tests for config singleton behavior."""

    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_get_config_returns_same_instance(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_set_config_replaces_instance(self):
        """Test that set_config replaces the global instance."""
        original = get_config()
        custom = Config()
        set_config(custom)

        assert get_config() is custom
        assert get_config() is not original

    def test_reset_config_creates_new_instance(self):
        """Test that reset_config creates a new instance."""
        config1 = get_config()
        reset_config()
        config2 = get_config()

        assert config1 is not config2
