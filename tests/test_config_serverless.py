"""Tests for serverless configuration validation.

This module tests the configuration validators and serverless detection logic
to ensure proper behavior in both serverless and local environments.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

# Ensure proper imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "adw_server"))


class TestServerlessDetection:
    """Tests for serverless environment detection."""

    def test_detect_vercel_environment(self):
        """Test detection of Vercel environment via VERCEL=1 env var."""
        from core.serverless_utils import is_serverless_environment

        with patch.dict(os.environ, {"VERCEL": "1"}):
            assert is_serverless_environment() is True

    def test_detect_aws_lambda_environment(self):
        """Test detection of AWS Lambda environment."""
        from core.serverless_utils import is_serverless_environment

        with patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "my-function"}):
            assert is_serverless_environment() is True

    def test_detect_var_task_path(self):
        """Test detection of Vercel /var/task path."""
        from core.serverless_utils import is_serverless_environment

        with patch("os.getcwd", return_value="/var/task"):
            assert is_serverless_environment() is True

    def test_detect_tmp_path(self):
        """Test detection of /tmp path (common serverless pattern)."""
        from core.serverless_utils import is_serverless_environment

        with patch("os.getcwd", return_value="/tmp/my-app"):
            assert is_serverless_environment() is True

    def test_local_environment(self):
        """Test that local environment is correctly identified."""
        from core.serverless_utils import is_serverless_environment

        # Clear serverless indicators
        env = {k: v for k, v in os.environ.items() if k not in ["VERCEL", "AWS_LAMBDA_FUNCTION_NAME"]}
        with patch.dict(os.environ, env, clear=True):
            with patch("os.getcwd", return_value="/home/user/project"):
                assert is_serverless_environment() is False

    def test_multiple_indicators(self):
        """Test that any single indicator is sufficient."""
        from core.serverless_utils import is_serverless_environment

        # Both VERCEL and Lambda indicators present
        with patch.dict(os.environ, {"VERCEL": "1", "AWS_LAMBDA_FUNCTION_NAME": "fn"}):
            assert is_serverless_environment() is True


class TestWritableTempDir:
    """Tests for get_writable_temp_dir function."""

    def test_serverless_temp_dir(self):
        """Test that serverless environments use /tmp."""
        from core.serverless_utils import get_writable_temp_dir

        with patch.dict(os.environ, {"VERCEL": "1"}):
            assert get_writable_temp_dir() == "/tmp"

    def test_local_temp_dir(self):
        """Test that local environments use system temp dir."""
        from core.serverless_utils import get_writable_temp_dir
        import tempfile

        env = {k: v for k, v in os.environ.items() if k not in ["VERCEL", "AWS_LAMBDA_FUNCTION_NAME"]}
        with patch.dict(os.environ, env, clear=True):
            with patch("os.getcwd", return_value="/home/user/project"):
                result = get_writable_temp_dir()
                assert result == tempfile.gettempdir()


class TestConfigValidationServerless:
    """Tests for configuration validators in serverless environments."""

    @pytest.fixture(autouse=True)
    def reset_config(self):
        """Reset configuration singleton before each test."""
        import core.config as config_module
        config_module._config = None
        yield
        config_module._config = None

    def test_working_dir_validation_serverless(self, tmp_path):
        """Test working directory validation in serverless environment."""
        from core.config import ServerConfig

        work_dir = "/tmp/adw-work"

        with patch.dict(os.environ, {
            "VERCEL": "1",
            "GH_WB_SECRET": "test-secret-1234567890"
        }):
            with patch("os.makedirs") as mock_makedirs:
                with patch("os.path.isdir", return_value=False):
                    config = ServerConfig(adw_working_dir=work_dir)
                    assert config.adw_working_dir == work_dir
                    # Should attempt to create directory (called for both working and static dirs)
                    assert any(call[0][0] == work_dir for call in mock_makedirs.call_args_list)

    def test_working_dir_creation_fails_serverless(self):
        """Test that working directory validation doesn't fail if creation fails in serverless."""
        from core.config import ServerConfig

        work_dir = "/tmp/adw-work"

        with patch.dict(os.environ, {
            "VERCEL": "1",
            "GH_WB_SECRET": "test-secret-1234567890"
        }):
            with patch("os.makedirs", side_effect=PermissionError("Read-only filesystem")):
                with patch("os.path.isdir", return_value=False):
                    # Should not raise, just log warning
                    config = ServerConfig(adw_working_dir=work_dir)
                    assert config.adw_working_dir == work_dir

    def test_working_dir_creation_fails_local(self):
        """Test that working directory validation fails if creation fails in local environment."""
        from core.config import ServerConfig

        work_dir = "/nonexistent/path"

        env = {k: v for k, v in os.environ.items() if k not in ["VERCEL", "AWS_LAMBDA_FUNCTION_NAME"]}
        env["GH_WB_SECRET"] = "test-secret-1234567890"

        with patch.dict(os.environ, env, clear=True):
            with patch("os.getcwd", return_value="/home/user/project"):
                with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
                    with patch("os.path.isdir", return_value=False):
                        with pytest.raises(ValidationError) as exc_info:
                            ServerConfig(adw_working_dir=work_dir)
                        assert "could not be created" in str(exc_info.value)

    def test_static_dir_validation_serverless(self):
        """Test static directory validation in serverless environment."""
        from core.config import ServerConfig

        static_dir = "/tmp/static"

        with patch.dict(os.environ, {
            "VERCEL": "1",
            "GH_WB_SECRET": "test-secret-1234567890"
        }):
            with patch("os.makedirs") as mock_makedirs:
                with patch("os.path.isdir", return_value=False):
                    config = ServerConfig(static_files_dir=static_dir)
                    # Should accept the path even if creation fails
                    assert config.static_files_dir == static_dir

    def test_static_dir_creation_fails_serverless(self):
        """Test that static directory validation doesn't fail if creation fails in serverless."""
        from core.config import ServerConfig

        static_dir = "/tmp/static"

        with patch.dict(os.environ, {
            "VERCEL": "1",
            "GH_WB_SECRET": "test-secret-1234567890"
        }):
            with patch("os.makedirs", side_effect=PermissionError("Read-only filesystem")):
                with patch("os.path.isdir", return_value=False):
                    # Should not raise in serverless
                    config = ServerConfig(static_files_dir=static_dir)
                    assert config.static_files_dir == static_dir

    def test_static_dir_creation_fails_local(self):
        """Test that static directory validation fails if creation fails in local environment."""
        from core.config import ServerConfig

        static_dir = "/nonexistent/static"

        env = {k: v for k, v in os.environ.items() if k not in ["VERCEL", "AWS_LAMBDA_FUNCTION_NAME"]}
        env["GH_WB_SECRET"] = "test-secret-1234567890"

        with patch.dict(os.environ, env, clear=True):
            with patch("os.getcwd", return_value="/home/user/project"):
                with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
                    with patch("os.path.isdir", return_value=False):
                        with pytest.raises(ValidationError) as exc_info:
                            ServerConfig(static_files_dir=static_dir)
                        assert "could not be created" in str(exc_info.value)

    def test_config_loading_serverless(self):
        """Test complete configuration loading in serverless environment."""
        from core.config import ServerConfig

        with patch.dict(os.environ, {
            "VERCEL": "1",
            "GH_WB_SECRET": "test-secret-1234567890",
            "ADW_WORKING_DIR": "/tmp/adw",
            "STATIC_FILES_DIR": "/tmp/static",
            "ENVIRONMENT": "production"
        }):
            with patch("os.path.isdir", return_value=True):
                config = ServerConfig()
                assert config.adw_working_dir == "/tmp/adw"
                assert config.static_files_dir == "/tmp/static"
                assert config.environment == "production"

    def test_relative_path_resolution(self):
        """Test that relative paths are resolved correctly using PROJECT_ROOT."""
        from core.config import ServerConfig

        with patch.dict(os.environ, {
            "GH_WB_SECRET": "test-secret-1234567890"
        }):
            env = {k: v for k, v in os.environ.items() if k not in ["VERCEL", "AWS_LAMBDA_FUNCTION_NAME"]}
            env["GH_WB_SECRET"] = "test-secret-1234567890"

            with patch.dict(os.environ, env, clear=True):
                with patch("os.getcwd", return_value="/home/user/project"):
                    with patch("os.path.isdir", return_value=True):
                        config = ServerConfig(static_files_dir="apps/frontend")
                        # Should resolve relative to PROJECT_ROOT
                        assert "apps/frontend" in config.static_files_dir
                        assert os.path.isabs(config.static_files_dir)


class TestImportPathSetup:
    """Tests for import path setup utilities."""

    def test_setup_import_paths(self):
        """Test that setup_import_paths adds necessary paths to sys.path."""
        from core.serverless_utils import setup_import_paths

        original_path = sys.path.copy()

        try:
            # Remove paths that would be added
            sys.path = [p for p in sys.path if "apps/adw_server" not in p]

            setup_import_paths()

            # Check that paths were added
            assert any("apps/adw_server" in p for p in sys.path)

        finally:
            # Restore original path
            sys.path = original_path

    def test_setup_import_paths_idempotent(self):
        """Test that setup_import_paths is idempotent."""
        from core.serverless_utils import setup_import_paths

        original_path = sys.path.copy()

        try:
            setup_import_paths()
            path_after_first = sys.path.copy()

            setup_import_paths()
            path_after_second = sys.path.copy()

            # Should not add duplicate paths
            assert path_after_first == path_after_second

        finally:
            sys.path = original_path
