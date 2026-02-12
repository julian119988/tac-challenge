"""Pytest configuration and shared fixtures for test suite.

This module provides shared fixtures and configuration for all tests.
Fixtures include:
- Temporary directories for testing
- Mock configuration objects
- FastAPI test clients
- Mock GitHub API responses
- Test repository setup utilities
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Pytest Configuration
# ============================================================================

pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Provide a temporary directory that's cleaned up after the test."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def temp_repo(temp_dir: str) -> Generator[str, None, None]:
    """Provide a temporary git repository for testing."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )

    # Create initial commit
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("initial content")

    subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_dir,
        capture_output=True,
        check=True
    )

    yield temp_dir


@pytest.fixture
def temp_repo_with_remote(temp_dir: str) -> Generator[tuple[str, str], None, None]:
    """Provide a temporary git repository with a remote for testing."""
    # Create bare remote repository
    remote_dir = tempfile.mkdtemp()
    subprocess.run(
        ["git", "init", "--bare"],
        cwd=remote_dir,
        capture_output=True,
        check=True
    )

    # Create local repository
    local_dir = tempfile.mkdtemp()
    subprocess.run(
        ["git", "clone", remote_dir, "."],
        cwd=local_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=local_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=local_dir,
        capture_output=True,
        check=True
    )

    # Create initial commit
    test_file = os.path.join(local_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("initial content")

    subprocess.run(["git", "add", "."], cwd=local_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=local_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=local_dir,
        capture_output=True,
        check=True
    )

    yield local_dir, remote_dir

    # Cleanup
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
    if os.path.exists(remote_dir):
        shutil.rmtree(remote_dir)


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_config(temp_dir: str):
    """Provide a mock ServerConfig for testing."""
    from apps.adw_server.core.config import ServerConfig

    # Create a mock static files directory
    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    config = ServerConfig(
        server_host="127.0.0.1",
        server_port=8000,
        github_webhook_secret="test_secret_1234567890",
        adw_working_dir=temp_dir,
        static_files_dir=static_dir,
        cors_enabled=True,
        cors_origins=["*"],
        log_level="INFO",
        environment="test"
    )
    return config


@pytest.fixture
def test_env_vars(temp_dir: str, monkeypatch):
    """Set up test environment variables."""
    static_dir = os.path.join(temp_dir, "static")
    os.makedirs(static_dir, exist_ok=True)

    env_vars = {
        "GITHUB_WEBHOOK_SECRET": "test_secret_1234567890",
        "SERVER_HOST": "127.0.0.1",
        "SERVER_PORT": "8000",
        "ADW_WORKING_DIR": temp_dir,
        "STATIC_FILES_DIR": static_dir,
        "LOG_LEVEL": "INFO",
        "ENVIRONMENT": "test",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================

@pytest.fixture
async def test_app(mock_config, monkeypatch):
    """Provide a FastAPI test application with mocked configuration."""
    # Mock the config getter
    monkeypatch.setattr(
        "apps.adw_server.core.config.get_config",
        lambda: mock_config
    )

    # Import app after mocking config
    from apps.adw_server.server import app

    return app


@pytest.fixture
async def async_client(test_app) -> AsyncClient:
    """Provide an async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# Mock GitHub API Fixtures
# ============================================================================

@pytest.fixture
def mock_github_issue_payload():
    """Provide a mock GitHub issue webhook payload."""
    return {
        "action": "opened",
        "issue": {
            "number": 123,
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "labels": [
                {"name": "adw-feature", "color": "0052cc"}
            ],
            "user": {
                "login": "testuser",
                "id": 12345,
                "type": "User"
            },
            "html_url": "https://github.com/testuser/testrepo/issues/123"
        },
        "repository": {
            "name": "testrepo",
            "full_name": "testuser/testrepo",
            "owner": {
                "login": "testuser",
                "id": 12345,
                "type": "User"
            }
        }
    }


@pytest.fixture
def mock_github_pr_payload():
    """Provide a mock GitHub pull request webhook payload."""
    return {
        "action": "opened",
        "pull_request": {
            "number": 456,
            "title": "Test PR",
            "body": "This is a test pull request",
            "state": "open",
            "labels": [
                {"name": "review", "color": "fbca04"}
            ],
            "user": {
                "login": "testuser",
                "id": 12345,
                "type": "User"
            },
            "html_url": "https://github.com/testuser/testrepo/pull/456",
            "head": {
                "ref": "feature-branch",
                "sha": "abc123def456"
            },
            "base": {
                "ref": "main",
                "sha": "def456abc123"
            }
        },
        "repository": {
            "name": "testrepo",
            "full_name": "testuser/testrepo",
            "owner": {
                "login": "testuser",
                "id": 12345,
                "type": "User"
            }
        }
    }


@pytest.fixture
def mock_subprocess_run(mocker):
    """Mock subprocess.run for testing ADW integration without actual execution."""
    mock = mocker.patch("subprocess.run")
    mock.return_value = Mock(
        returncode=0,
        stdout="",
        stderr=""
    )
    return mock


# ============================================================================
# Utility Functions
# ============================================================================

def generate_github_signature(payload: bytes, secret: str) -> str:
    """Generate a valid GitHub webhook signature for testing.

    Args:
        payload: Request body bytes
        secret: Webhook secret

    Returns:
        GitHub signature in format "sha256=<hex_digest>"
    """
    import hmac
    import hashlib

    signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


# Export utility function for use in tests
pytest.generate_github_signature = generate_github_signature
