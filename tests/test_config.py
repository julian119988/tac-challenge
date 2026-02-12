"""Tests for server configuration management.

Tests cover:
- Configuration loading from environment variables
- Default values
- Configuration validation
- Path resolution for static files and working directory
"""

import pytest
import os
from pydantic import ValidationError


# ============================================================================
# Configuration Loading Tests
# ============================================================================

def test_config_loads_from_env(test_env_vars, temp_dir):
    """Test configuration loads successfully from environment variables."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    assert config.gh_wb_secret == "test_secret_1234567890"
    assert config.adw_working_dir == temp_dir
    assert config.static_files_dir == static_dir


def test_config_default_values(temp_dir):
    """Test configuration uses correct default values."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    assert config.server_host == "0.0.0.0"
    assert config.server_port == 8000
    assert config.cors_enabled is True
    assert config.cors_origins == ["*"]
    assert config.log_level == "INFO"
    assert config.environment == "development"
    assert config.adw_default_model == "sonnet"


def test_config_custom_values(temp_dir):
    """Test configuration accepts custom values."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        server_host="127.0.0.1",
        server_port=9000,
        gh_wb_secret="custom_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir,
        cors_enabled=False,
        log_level="DEBUG",
        environment="production"
    )

    assert config.server_host == "127.0.0.1"
    assert config.server_port == 9000
    assert config.gh_wb_secret == "custom_secret_1234567890"
    assert config.cors_enabled is False
    assert config.log_level == "DEBUG"
    assert config.environment == "production"


# ============================================================================
# Configuration Validation Tests
# ============================================================================

def test_config_requires_webhook_secret():
    """Test configuration requires gh_wb_secret."""
    from apps.adw_server.core.config import ServerConfig

    with pytest.raises(ValidationError) as exc_info:
        ServerConfig()

    assert "gh_wb_secret" in str(exc_info.value)


def test_config_rejects_empty_webhook_secret(temp_dir):
    """Test configuration rejects empty webhook secret."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            gh_wb_secret="",
            adw_working_dir=temp_dir,
            static_files_dir=static_dir
        )

    assert "must be set" in str(exc_info.value).lower()


def test_config_rejects_short_webhook_secret(temp_dir):
    """Test configuration rejects webhook secret shorter than 16 characters."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            gh_wb_secret="short",
            adw_working_dir=temp_dir,
            static_files_dir=static_dir
        )

    assert "at least 16 characters" in str(exc_info.value).lower()


def test_config_validates_port_range(temp_dir):
    """Test configuration validates port is in valid range."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    # Port too low
    with pytest.raises(ValidationError):
        ServerConfig(
            server_port=0,
            gh_wb_secret="test_secret_1234567890",
            adw_working_dir=temp_dir,
            static_files_dir=static_dir
        )

    # Port too high
    with pytest.raises(ValidationError):
        ServerConfig(
            server_port=70000,
            gh_wb_secret="test_secret_1234567890",
            adw_working_dir=temp_dir,
            static_files_dir=static_dir
        )


def test_config_validates_log_level(temp_dir):
    """Test configuration validates log level."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            log_level="INVALID_LEVEL",
            gh_wb_secret="test_secret_1234567890",
            adw_working_dir=temp_dir,
            static_files_dir=static_dir
        )

    assert "Invalid log level" in str(exc_info.value)


def test_config_validates_working_dir_exists(temp_dir):
    """Test configuration validates working directory exists."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    nonexistent_dir = "/nonexistent/directory/path"

    with pytest.raises(ValidationError) as exc_info:
        ServerConfig(
            adw_working_dir=nonexistent_dir,
            gh_wb_secret="test_secret_1234567890",
            static_files_dir=static_dir
        )

    assert "does not exist" in str(exc_info.value)


def test_config_creates_static_dir_if_missing(temp_dir):
    """Test configuration creates static directory if it doesn't exist."""
    from apps.adw_server.core.config import ServerConfig

    # Use a subdirectory that doesn't exist yet
    static_dir = os.path.join(temp_dir, "new_static")

    config = ServerConfig(
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    # Should be created
    assert os.path.isdir(config.static_files_dir)


# ============================================================================
# Path Resolution Tests
# ============================================================================

def test_config_converts_working_dir_to_absolute(temp_dir):
    """Test configuration converts working directory to absolute path."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    assert os.path.isabs(config.adw_working_dir)
    assert config.adw_working_dir == os.path.abspath(temp_dir)


def test_config_converts_static_dir_to_absolute(temp_dir):
    """Test configuration converts static directory to absolute path."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    assert os.path.isabs(config.static_files_dir)


def test_config_get_absolute_static_path(temp_dir):
    """Test get_absolute_static_path returns absolute path."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    abs_path = config.get_absolute_static_path()
    assert os.path.isabs(abs_path)
    assert abs_path == config.static_files_dir


# ============================================================================
# Environment Detection Tests
# ============================================================================

def test_config_is_production_true(temp_dir):
    """Test is_production returns True for production environment."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        environment="production",
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    assert config.is_production() is True


def test_config_is_production_false(temp_dir):
    """Test is_production returns False for non-production environments."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        environment="development",
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    assert config.is_production() is False


def test_config_is_production_case_insensitive(temp_dir):
    """Test is_production is case insensitive."""
    from apps.adw_server.core.config import ServerConfig

    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        environment="PRODUCTION",
        gh_wb_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir
    )

    assert config.is_production() is True


# ============================================================================
# Singleton Pattern Tests
# ============================================================================

def test_get_config_singleton(test_env_vars, monkeypatch):
    """Test get_config returns the same instance."""
    from apps.adw_server.core.config import get_config, _config

    # Clear singleton
    monkeypatch.setattr("apps.adw_server.core.config._config", None)

    config1 = get_config()
    config2 = get_config()

    assert config1 is config2


def test_reload_config_creates_new_instance(test_env_vars, monkeypatch):
    """Test reload_config creates a new configuration instance."""
    from apps.adw_server.core.config import get_config, reload_config

    # Clear singleton
    monkeypatch.setattr("apps.adw_server.core.config._config", None)

    config1 = get_config()
    config2 = reload_config()

    # They should have the same values but be different objects
    assert config1 is not config2
    assert config1.gh_wb_secret == config2.gh_wb_secret
