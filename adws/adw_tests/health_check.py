#!/usr/bin/env python3
"""Health check for ADW system."""

import os
import subprocess
import sys
from pathlib import Path


def check_claude_code_cli():
    """Check if Claude Code CLI is installed."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✓ Claude Code CLI is installed")
            return True
        else:
            print("✗ Claude Code CLI is not working")
            return False
    except FileNotFoundError:
        print("✗ Claude Code CLI is not installed")
        return False


def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("✗ GitHub CLI (gh) is not installed")
            return False

        # Check authentication
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✓ GitHub CLI is installed and authenticated")
            return True
        else:
            print("⚠ GitHub CLI is installed but not authenticated")
            print("  Run: gh auth login")
            return False
    except FileNotFoundError:
        print("✗ GitHub CLI (gh) is not installed")
        return False


def check_git_config():
    """Check if git is configured."""
    try:
        name_result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
        )
        email_result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
        )

        if name_result.returncode == 0 and email_result.returncode == 0:
            print(f"✓ Git is configured ({name_result.stdout.strip()})")
            return True
        else:
            print("✗ Git user.name or user.email not configured")
            return False
    except:
        print("✗ Git is not installed")
        return False


def check_env_vars():
    """Check required environment variables."""
    required = {
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude Code",
    }

    optional = {
        "GITHUB_TOKEN": "GitHub personal access token",
        "GITHUB_REPO_OWNER": "GitHub repository owner",
        "GITHUB_REPO_NAME": "GitHub repository name",
        "WEBHOOK_SECRET": "Webhook secret for verification",
    }

    all_good = True

    print("\nRequired environment variables:")
    for var, desc in required.items():
        if os.getenv(var):
            print(f"  ✓ {var}")
        else:
            print(f"  ✗ {var} ({desc})")
            all_good = False

    print("\nOptional environment variables (for SDLC workflows):")
    for var, desc in optional.items():
        if os.getenv(var):
            print(f"  ✓ {var}")
        else:
            print(f"  ⚠ {var} ({desc})")

    return all_good


def check_directories():
    """Check if required directories exist or can be created."""
    project_root = Path(__file__).parent.parent.parent
    dirs = [
        project_root / "trees",
        project_root / "agents",
        project_root / "specs",
    ]

    all_good = True
    for dir_path in dirs:
        if dir_path.exists():
            if os.access(dir_path, os.W_OK):
                print(f"✓ {dir_path.name}/ exists and is writable")
            else:
                print(f"✗ {dir_path.name}/ exists but is not writable")
                all_good = False
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✓ {dir_path.name}/ created")
            except:
                print(f"✗ Cannot create {dir_path.name}/ directory")
                all_good = False

    return all_good


def main():
    """Run all health checks."""
    print("=" * 60)
    print("  ADW System Health Check")
    print("=" * 60)
    print()

    checks = [
        ("Claude Code CLI", check_claude_code_cli),
        ("GitHub CLI", check_gh_cli),
        ("Git Configuration", check_git_config),
        ("Directories", check_directories),
    ]

    results = []
    for name, check_func in checks:
        result = check_func()
        results.append(result)
        print()

    # Check env vars separately (has its own output)
    env_result = check_env_vars()
    results.append(env_result)

    print()
    print("=" * 60)

    if all(results):
        print("  ✓ All checks passed! System is ready.")
        print("=" * 60)
        return 0
    else:
        print("  ⚠ Some checks failed. See details above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
