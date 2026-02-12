"""Server configuration management using Pydantic settings.

This module provides configuration management for the FastAPI webhook server,
including settings for server operation, GitHub webhook validation, ADW execution,
and static file serving.

Environment variables can be provided via .env file or system environment.
See .env.example for required configuration.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        """
        abs_path = os.path.abspath(v)

        # In production/serverless, try to create the directory if it doesn't exist
        if not os.path.isdir(abs_path):
            # Check if we're in a serverless environment (Vercel uses /tmp)
            is_serverless = abs_path.startswith('/tmp') or os.environ.get('VERCEL') == '1'

            if is_serverless:
                # In serverless, just return the path - it will be created when needed
                try:
                    os.makedirs(abs_path, exist_ok=True)
                except Exception:
                    # If creation fails, just log and continue - directory might be created later
                    pass
                return abs_path
            else:
                # In non-serverless, require the directory to exist
                raise ValueError(
                    f"ADW working directory does not exist: {abs_path}. "
                    "Please provide a valid directory path."
                )

        return abs_path

    @field_validator("static_files_dir")
    @classmethod
    def validate_static_dir(cls, v: str) -> str:
        """Validate that static files directory exists or skip in serverless.

        In serverless environments, static files may not be available or needed,
        so we make this validation more lenient.
        """
        # Convert to absolute path relative to working directory
        if not os.path.isabs(v):
            # Get the project root (parent of apps directory)
            current_file = os.path.abspath(__file__)
            # Navigate up from config.py -> core -> adw_server -> apps -> project_root
            core_dir = os.path.dirname(current_file)
            adw_server_dir = os.path.dirname(core_dir)
            apps_dir = os.path.dirname(adw_server_dir)
            project_root = os.path.dirname(apps_dir)
            v = os.path.join(project_root, v)

        abs_path = os.path.abspath(v)

        # Check if we're in a serverless environment
        is_serverless = abs_path.startswith('/tmp') or os.environ.get('VERCEL') == '1'

        if not os.path.isdir(abs_path):
            if is_serverless:
                # In serverless, static files might not be available - that's OK
                # Just create the directory if possible, but don't fail if we can't
                try:
                    os.makedirs(abs_path, exist_ok=True)
                except Exception:
                    # Ignore errors in serverless - static files may not be needed
                    pass
                return abs_path
            else:
                # In non-serverless, try to create it
                try:
                    os.makedirs(abs_path, exist_ok=True)
                except Exception as e:
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
        _config = ServerConfig()
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
