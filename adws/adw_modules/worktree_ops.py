"""Git worktree management for isolated execution."""

import os
import subprocess
import socket
from pathlib import Path
from typing import Tuple, Optional
import hashlib
import logging


def get_worktree_path(adw_id: str) -> str:
    """Get path to worktree for ADW ID.

    Args:
        adw_id: ADW identifier

    Returns:
        Path to worktree directory
    """
    # Get project root (3 levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    return str(project_root / "trees" / adw_id)


def create_worktree(
    adw_id: str,
    branch_name: str,
    base_branch: str = "main",
    logger: Optional[logging.Logger] = None,
) -> Tuple[bool, str]:
    """Create git worktree for isolated development.

    Args:
        adw_id: ADW identifier
        branch_name: Branch name for worktree
        base_branch: Base branch to branch from (default: main)
        logger: Optional logger

    Returns:
        Tuple of (success, worktree_path or error_message)
    """
    worktree_path = get_worktree_path(adw_id)
    project_root = Path(__file__).parent.parent.parent

    try:
        # Fetch latest from origin
        if logger:
            logger.info(f"Fetching latest from origin/{base_branch}")

        result = subprocess.run(
            ["git", "fetch", "origin", base_branch],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        if result.returncode != 0:
            error = f"Failed to fetch from origin: {result.stderr}"
            if logger:
                logger.error(error)
            return False, error

        # Create worktree with new branch
        if logger:
            logger.info(f"Creating worktree at {worktree_path} with branch {branch_name}")

        result = subprocess.run(
            [
                "git",
                "worktree",
                "add",
                "-b",
                branch_name,
                worktree_path,
                f"origin/{base_branch}",
            ],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            if logger:
                logger.info(f"Worktree created successfully at {worktree_path}")
            return True, worktree_path

        # If branch already exists, try without -b flag
        if "already exists" in result.stderr:
            if logger:
                logger.info(f"Branch {branch_name} exists, creating worktree without -b flag")

            result = subprocess.run(
                ["git", "worktree", "add", worktree_path, branch_name],
                capture_output=True,
                text=True,
                cwd=str(project_root),
            )

            if result.returncode == 0:
                if logger:
                    logger.info(f"Worktree created successfully at {worktree_path}")
                return True, worktree_path

        error = f"Failed to create worktree: {result.stderr}"
        if logger:
            logger.error(error)
        return False, error

    except Exception as e:
        error = f"Error creating worktree: {e}"
        if logger:
            logger.error(error)
        else:
            print(error)
        return False, error


def validate_worktree(state, logger: Optional[logging.Logger] = None) -> Tuple[bool, str]:
    """Validate worktree exists and is properly configured.

    Performs 3-way validation:
    1. State has worktree_path
    2. Directory exists on filesystem
    3. Git recognizes it as a worktree

    Args:
        state: ADWState instance
        logger: Optional logger

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check state has worktree_path
    if not state.worktree_path:
        return False, "State does not have worktree_path set"

    # Check directory exists
    if not os.path.exists(state.worktree_path):
        return False, f"Worktree directory does not exist: {state.worktree_path}"

    # Check git recognizes it as worktree
    project_root = Path(__file__).parent.parent.parent

    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        if result.returncode != 0:
            return False, "Failed to list git worktrees"

        # Check if our worktree is in the list
        if state.worktree_path not in result.stdout:
            return False, f"Worktree not recognized by git: {state.worktree_path}"

        if logger:
            logger.info(f"Worktree validated: {state.worktree_path}")

        return True, ""

    except Exception as e:
        return False, f"Error validating worktree: {e}"


def remove_worktree(adw_id: str, logger: Optional[logging.Logger] = None) -> bool:
    """Remove git worktree.

    Args:
        adw_id: ADW identifier
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    worktree_path = get_worktree_path(adw_id)
    project_root = Path(__file__).parent.parent.parent

    try:
        result = subprocess.run(
            ["git", "worktree", "remove", "-f", worktree_path],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )

        if result.returncode == 0:
            if logger:
                logger.info(f"Worktree removed: {worktree_path}")
            return True

        if logger:
            logger.error(f"Failed to remove worktree: {result.stderr}")
        return False

    except Exception as e:
        if logger:
            logger.error(f"Error removing worktree: {e}")
        else:
            print(f"Error removing worktree: {e}")
        return False


def setup_worktree_environment(
    worktree_path: str, backend_port: int, frontend_port: int
) -> bool:
    """Create .ports.env file in worktree.

    Args:
        worktree_path: Path to worktree
        backend_port: Backend port number
        frontend_port: Frontend port number

    Returns:
        True if successful, False otherwise
    """
    try:
        ports_env_path = os.path.join(worktree_path, ".ports.env")

        with open(ports_env_path, "w") as f:
            f.write(f"BACKEND_PORT={backend_port}\n")
            f.write(f"FRONTEND_PORT={frontend_port}\n")

        return True

    except Exception as e:
        print(f"Error setting up worktree environment: {e}")
        return False


def get_ports_for_adw(adw_id: str) -> Tuple[int, int]:
    """Get deterministic port assignment for ADW ID.

    Uses hash of ADW ID to deterministically assign ports in ranges:
    - Backend: 9100-9114 (15 ports)
    - Frontend: 9200-9214 (15 ports)

    Args:
        adw_id: ADW identifier

    Returns:
        Tuple of (backend_port, frontend_port)
    """
    # Hash the ADW ID to get a deterministic number
    hash_value = int(hashlib.md5(adw_id.encode()).hexdigest()[:8], 16)

    # Map to port ranges
    backend_port = 9100 + (hash_value % 15)
    frontend_port = 9200 + (hash_value % 15)

    return backend_port, frontend_port


def is_port_available(port: int) -> bool:
    """Check if a port is available for binding.

    Args:
        port: Port number

    Returns:
        True if available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))
            return True
    except:
        return False


def find_next_available_ports() -> Tuple[int, int]:
    """Find next available ports for backend and frontend.

    Fallback when deterministic ports are not available.

    Returns:
        Tuple of (backend_port, frontend_port)
    """
    # Try ports in order
    for i in range(15):
        backend_port = 9100 + i
        frontend_port = 9200 + i

        if is_port_available(backend_port) and is_port_available(frontend_port):
            return backend_port, frontend_port

    # If all ports in range are taken, try higher ports
    for port in range(9300, 9400):
        if is_port_available(port) and is_port_available(port + 100):
            return port, port + 100

    # Last resort: return default ports (might fail)
    return 9100, 9200
