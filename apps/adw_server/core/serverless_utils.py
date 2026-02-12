"""Serverless environment detection and utilities.

This module provides utilities for detecting and handling serverless execution
environments like Vercel and AWS Lambda. It centralizes environment detection
logic to ensure consistent behavior across the application.

Serverless Environment Detection:
    Vercel: Detected via VERCEL=1 environment variable or /var/task path prefix
    AWS Lambda: Detected via AWS_LAMBDA_FUNCTION_NAME environment variable
    General: Paths starting with /tmp are considered serverless-compatible

Usage:
    from core.serverless_utils import is_serverless_environment, get_writable_temp_dir

    if is_serverless_environment():
        temp_dir = get_writable_temp_dir()
        # Use temp_dir for ephemeral storage
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def is_serverless_environment() -> bool:
    """Detect if running in a serverless environment.

    This function checks multiple indicators to determine if the application
    is running in a serverless environment (Vercel, AWS Lambda, etc.).

    Detection criteria:
        - VERCEL environment variable equals '1' (Vercel's convention)
        - AWS_LAMBDA_FUNCTION_NAME environment variable is set (AWS Lambda)
        - Current working directory starts with /var/task (Vercel)
        - Current working directory starts with /tmp (common serverless pattern)

    Returns:
        True if running in a serverless environment, False otherwise

    Note:
        Vercel sets VERCEL='1' (string '1', not boolean True) as documented at:
        https://vercel.com/docs/concepts/projects/environment-variables#system-environment-variables
    """
    # Check Vercel environment variable (must be string '1')
    if os.environ.get('VERCEL') == '1':
        logger.debug("Serverless environment detected: VERCEL=1")
        return True

    # Check AWS Lambda environment variable
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        logger.debug("Serverless environment detected: AWS Lambda")
        return True

    # Check if running from typical serverless paths
    cwd = os.getcwd()
    if cwd.startswith('/var/task'):
        logger.debug(f"Serverless environment detected: cwd={cwd} (Vercel)")
        return True

    if cwd.startswith('/tmp'):
        logger.debug(f"Serverless environment detected: cwd={cwd} (tmp)")
        return True

    logger.debug("Local development environment detected")
    return False


def get_writable_temp_dir() -> str:
    """Get a writable temporary directory for serverless environments.

    In serverless environments, most of the filesystem is read-only.
    This function returns a writable temporary directory appropriate
    for the current environment.

    Returns:
        Path to writable temporary directory
            - /tmp in serverless environments (Vercel, Lambda)
            - System temp directory in local environments

    Example:
        temp_dir = get_writable_temp_dir()
        work_path = os.path.join(temp_dir, 'my_work')
        os.makedirs(work_path, exist_ok=True)
    """
    if is_serverless_environment():
        # In serverless, /tmp is the only writable location
        temp_dir = '/tmp'
        logger.debug(f"Using serverless temp directory: {temp_dir}")
        return temp_dir
    else:
        # In local environments, use system temp directory
        import tempfile
        temp_dir = tempfile.gettempdir()
        logger.debug(f"Using local temp directory: {temp_dir}")
        return temp_dir


def setup_import_paths() -> None:
    """Set up Python import paths for serverless environments.

    In Vercel's serverless environment, the working directory structure
    may differ from local development. This function ensures that all
    necessary directories are in sys.path for imports to work correctly.

    Paths added:
        - Project root (parent of api/ directory)
        - adw_server directory (apps/adw_server)

    Note:
        This function is idempotent - it only adds paths if they're not
        already in sys.path. It's safe to call multiple times.

    Example:
        # In api/index.py
        from apps.adw_server.core.serverless_utils import setup_import_paths
        setup_import_paths()
    """
    # Get the absolute path to the project root
    # This file is at: apps/adw_server/core/serverless_utils.py
    current_file = Path(__file__).resolve()
    core_dir = current_file.parent
    adw_server_dir = core_dir.parent
    apps_dir = adw_server_dir.parent
    project_root = apps_dir.parent

    # Add project root to sys.path (for 'apps.adw_server' imports)
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
        logger.debug(f"Added project root to sys.path: {project_root_str}")

    # Add adw_server directory to sys.path (for 'core' imports)
    adw_server_str = str(adw_server_dir)
    if adw_server_str not in sys.path:
        sys.path.insert(0, adw_server_str)
        logger.debug(f"Added adw_server to sys.path: {adw_server_str}")

    if is_serverless_environment():
        logger.info(
            f"Import paths configured for serverless environment. "
            f"Project root: {project_root_str}"
        )
