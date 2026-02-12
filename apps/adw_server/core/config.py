"""Server configuration management using Pydantic settings.

This module provides configuration management for the FastAPI webhook server,
including settings for server operation, GitHub webhook validation, ADW execution,
and static file serving.

Environment variables can be provided via .env file or system environment.
See .env.example for required configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .serverless_utils import is_serverless_environment

# Configure logger for this module
logger = logging.getLogger(__name__)

# Project root path - computed once at module load time
# This file is at: apps/adw_server/core/config.py
# Project root is 4 levels up: core -> adw_server -> apps -> project_root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class ServerConfig(BaseSettings):
    """Server configuration with environment variable support.

    Attributes:
        server_host: Host address to bind the server (default: 0.0.0.0)
        server_port: Port to run the server on (default: 8000)
        gh_wb_secret: Secret for validating GitHub webhook signatures (required)
        adw_working_dir: Working directory for ADW workflow execution (default: current dir)
        static_files_dir: Directory for serving static frontend files (default: apps/static)
        cors_enabled: Enable CORS for frontend requests (default: True)
        cors_origins: Allowed CORS origins (default: ["*"])
        log_level: Logging level (default: INFO)
        environment: Deployment environment (default: development)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Server settings
    server_host: str = Field(default="0.0.0.0", description="Server host address")
    server_port: int = Field(default=8000, description="Server port", ge=1, le=65535)

    # GitHub webhook settings
    gh_wb_secret: str = Field(
        ...,  # Required field
        description="GitHub webhook secret for signature validation"
    )

    # ADW settings
    adw_working_dir: str = Field(
        default_factory=os.getcwd,
        description="Working directory for ADW workflow execution"
    )
    adw_default_model: str = Field(
        default="sonnet",
        description="Default model for ADW workflows (sonnet or opus)"
    )

    # Static files
    static_files_dir: str = Field(
        default="apps/frontend",
        description="Directory for static frontend files"
    )

    # CORS settings
    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS middleware"
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Deployment environment (development, staging, production)"
    )

    # Review action settings
    auto_merge_on_approval: bool = Field(
        default=True,
        description="Automatically merge PRs when review is approved"
    )
    auto_reimplement_on_changes: bool = Field(
        default=True,
        description="Automatically trigger re-implementation when review requests changes"
    )
    merge_method: str = Field(
        default="squash",
        description="PR merge method (squash, merge, rebase)"
    )
    max_reimplement_attempts: int = Field(
        default=3,
        description="Maximum re-implementation attempts per issue to prevent loops",
        ge=1,
        le=10
    )

    @field_validator("gh_wb_secret")
    @classmethod
    def validate_webhook_secret(cls, v: str) -> str:
        """Validate that webhook secret is provided and not empty."""
        if not v or v.strip() == "":
            raise ValueError(
                "GH_WB_SECRET must be set. "
                "Generate a strong secret and configure it in GitHub webhook settings."
            )
        if len(v) < 16:
            raise ValueError(
                "GH_WB_SECRET should be at least 16 characters for security. "
                "Generate a strong random secret."
            )
        return v

    @field_validator("adw_working_dir")
    @classmethod
    def validate_working_dir(cls, v: str) -> str:
        """Validate that working directory exists or can be created.

        In serverless environments (like Vercel), we may need to create
        the directory at runtime since it doesn't exist at config load time.
        Only /tmp is writable in serverless environments.
        """
        abs_path = os.path.abspath(v)
        serverless = is_serverless_environment()

        logger.debug(f"Validating working directory: {abs_path} (serverless={serverless})")

        # Check if directory already exists
        if os.path.isdir(abs_path):
            logger.info(f"Working directory exists: {abs_path}")
            return abs_path

        # Directory doesn't exist - try to create it
        if serverless:
            # In serverless environments, only /tmp is writable
            logger.info(
                f"Serverless environment detected. Attempting to create working directory: {abs_path}"
            )
            try:
                os.makedirs(abs_path, exist_ok=True)
                logger.info(f"Successfully created working directory: {abs_path}")
                return abs_path
            except Exception as e:
                # Log the error but don't fail - directory might be created later by the application
                logger.warning(
                    f"Failed to create working directory in serverless environment: {abs_path}. "
                    f"Error: {e}. Directory will be created on first use if needed."
                )
                return abs_path
        else:
            # In non-serverless environments, require the directory to exist or be creatable
            try:
                os.makedirs(abs_path, exist_ok=True)
                logger.info(f"Created working directory: {abs_path}")
                return abs_path
            except Exception as e:
                logger.error(f"Failed to create working directory: {abs_path}. Error: {e}")
                raise ValueError(
                    f"ADW working directory does not exist and could not be created: {abs_path}. "
                    f"Error: {e}"
                )

        return abs_path

    @field_validator("static_files_dir")
    @classmethod
    def validate_static_dir(cls, v: str) -> str:
        """Validate that static files directory exists or skip in serverless.

        In serverless environments, static files may not be available or needed,
        so we make this validation more lenient. Vercel typically handles static
        files separately from the application runtime.
        """
        # Convert relative paths to absolute paths using PROJECT_ROOT
        if not os.path.isabs(v):
            v = str(PROJECT_ROOT / v)

        abs_path = os.path.abspath(v)
        serverless = is_serverless_environment()

        logger.debug(f"Validating static directory: {abs_path} (serverless={serverless})")

        # Check if directory already exists
        if os.path.isdir(abs_path):
            logger.info(f"Static files directory exists: {abs_path}")
            return abs_path

        # Directory doesn't exist - handle based on environment
        if serverless:
            # In serverless, static files are typically not served from the application
            # Vercel handles static files separately via their CDN
            logger.info(
                f"Serverless environment detected. Static files directory does not exist: {abs_path}. "
                "This is expected in serverless environments where static files are served separately."
            )
            try:
                os.makedirs(abs_path, exist_ok=True)
                logger.info(f"Created static files directory: {abs_path}")
            except Exception as e:
                # In serverless, it's acceptable if we can't create the directory
                # Static files may not be needed or may be read-only filesystem
                logger.warning(
                    f"Could not create static files directory in serverless environment: {abs_path}. "
                    f"Error: {e}. This is acceptable if static files are served separately."
                )
            return abs_path
        else:
            # In non-serverless environments, try to create the directory
            try:
                os.makedirs(abs_path, exist_ok=True)
                logger.info(f"Created static files directory: {abs_path}")
                return abs_path
            except Exception as e:
                logger.error(f"Failed to create static files directory: {abs_path}. Error: {e}")
                raise ValueError(
                    f"Static files directory does not exist and could not be created: {abs_path}. "
                    f"Error: {e}"
                )

        return abs_path

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v_upper

    @field_validator("merge_method")
    @classmethod
    def validate_merge_method(cls, v: str) -> str:
        """Validate merge method is one of the supported methods."""
        valid_methods = ["squash", "merge", "rebase"]
        v_lower = v.lower()
        if v_lower not in valid_methods:
            raise ValueError(
                f"Invalid merge method: {v}. Must be one of {valid_methods}"
            )
        return v_lower

    def get_absolute_static_path(self) -> str:
        """Get absolute path to static files directory.

        Returns:
            Absolute path to static files directory
        """
        return os.path.abspath(self.static_files_dir)

    def is_production(self) -> bool:
        """Check if running in production environment.

        Returns:
            True if environment is production
        """
        return self.environment.lower() == "production"


# Global config instance (lazy loaded)
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """Get or create the global configuration instance.

    This function provides a singleton pattern for configuration access.
    The configuration is loaded once and reused across the application.

    Returns:
        ServerConfig instance with loaded settings

    Raises:
        ValidationError: If required configuration is missing or invalid
    """
    global _config
    if _config is None:
        serverless = is_serverless_environment()
        logger.info(
            f"Loading configuration (serverless={serverless}, environment={os.environ.get('ENVIRONMENT', 'development')})"
        )
        _config = ServerConfig()
        logger.info(
            f"Configuration loaded successfully. "
            f"Working dir: {_config.adw_working_dir}, "
            f"Static dir: {_config.static_files_dir}, "
            f"Environment: {_config.environment}"
        )
    return _config


def reload_config() -> ServerConfig:
    """Reload configuration from environment.

    Useful for testing or when environment variables change.

    Returns:
        New ServerConfig instance with reloaded settings
    """
    global _config
    _config = ServerConfig()
    return _config
