"""Utility functions for ADW workflows."""

import os
import sys
import uuid
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional


def setup_logger(name: str, adw_id: str, phase_name: str) -> logging.Logger:
    """Configure logger with file and console output.

    Args:
        name: Logger name
        adw_id: ADW identifier
        phase_name: Phase name for log file

    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    project_root = Path(__file__).parent.parent.parent
    log_dir = project_root / "agents" / adw_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{phase_name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


def ensure_adw_id(
    issue_number: Optional[int] = None, provided_adw_id: Optional[str] = None
) -> str:
    """Generate or validate ADW ID.

    Args:
        issue_number: Optional issue number
        provided_adw_id: Optional provided ADW ID

    Returns:
        ADW ID (8-character UUID)
    """
    if provided_adw_id:
        # Validate provided ID
        if len(provided_adw_id) >= 8:
            return provided_adw_id[:8]

    # Generate new ID
    return str(uuid.uuid4())[:8]


def get_repo_config() -> Tuple[str, str]:
    """Read repository configuration from environment.

    Returns:
        Tuple of (repo_owner, repo_name)

    Raises:
        ValueError: If environment variables not set
    """
    repo_owner = os.getenv("GITHUB_REPO_OWNER")
    repo_name = os.getenv("GITHUB_REPO_NAME")

    if not repo_owner or not repo_name:
        raise ValueError(
            "GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set in environment"
        )

    return repo_owner, repo_name


def validate_required_env_vars(vars: List[str]) -> Tuple[bool, List[str]]:
    """Check required environment variables exist.

    Args:
        vars: List of variable names to check

    Returns:
        Tuple of (all_present, missing_vars)
    """
    missing = []

    for var in vars:
        if not os.getenv(var):
            missing.append(var)

    return len(missing) == 0, missing


def truncate_output(text: str, max_length: int = 500) -> str:
    """Truncate long text for logging.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length] + "... (truncated)"


def parse_args_for_adw_context(argv: List[str]) -> Dict[str, Any]:
    """Parse command-line arguments for ADW context.

    Expected formats:
        script.py <issue_number> [adw_id] [--flags]
        script.py [adw_id] [--flags]

    Args:
        argv: Command-line arguments (sys.argv)

    Returns:
        Dictionary with parsed arguments
    """
    context = {
        "issue_number": None,
        "adw_id": None,
        "flags": {},
    }

    # Skip script name
    args = argv[1:]

    # Parse positional args
    positional = []
    for arg in args:
        if arg.startswith("--"):
            # Parse flag
            if "=" in arg:
                key, value = arg[2:].split("=", 1)
                context["flags"][key] = value
            else:
                context["flags"][arg[2:]] = True
        else:
            positional.append(arg)

    # Assign positional args
    if len(positional) >= 1:
        # First arg could be issue_number or adw_id
        first_arg = positional[0]
        if first_arg.isdigit():
            context["issue_number"] = int(first_arg)
        else:
            context["adw_id"] = first_arg

    if len(positional) >= 2:
        # Second arg is adw_id if first was issue_number
        if context["issue_number"] is not None:
            context["adw_id"] = positional[1]

    return context


def print_success(message: str):
    """Print success message with formatting.

    Args:
        message: Success message
    """
    print(f"\n✓ {message}\n")


def print_error(message: str):
    """Print error message with formatting.

    Args:
        message: Error message
    """
    print(f"\n✗ {message}\n", file=sys.stderr)


def print_info(message: str):
    """Print info message with formatting.

    Args:
        message: Info message
    """
    print(f"\nℹ {message}\n")


def print_section(title: str):
    """Print section header.

    Args:
        title: Section title
    """
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")
