"""Tests for FastAPI webhook server endpoints.

Tests cover:
- Health check endpoints
- Webhook signature validation
- Event routing (issues, pull_request)
- CORS middleware
- Error handling
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock

from httpx import AsyncClient
from conftest import generate_github_signature


# ============================================================================
# Health Check Tests
# ============================================================================

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test basic health check endpoint."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "adw-webhook-server"
    assert "environment" in data


@pytest.mark.asyncio
async def test_readiness_check(async_client: AsyncClient, mock_config):
    """Test readiness check endpoint."""
    with patch("apps.adw_server.core.adw_integration.generate_adw_id") as mock_gen:
        mock_gen.return_value = "test-id-12345678"

        response = await async_client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "working_dir" in data
        assert "static_dir" in data
        assert data["working_dir"] == mock_config.adw_working_dir


@pytest.mark.asyncio
async def test_readiness_check_failure(async_client: AsyncClient, monkeypatch):
    """Test readiness check fails when ADW modules are not accessible."""
    with patch("apps.adw_server.core.adw_integration.generate_adw_id") as mock_gen:
        mock_gen.side_effect = Exception("ADW modules not found")

        response = await async_client.get("/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert "Server not ready" in data["detail"]


# ============================================================================
# Root Endpoint Tests
# ============================================================================

@pytest.mark.asyncio
async def test_root_redirect(async_client: AsyncClient):
    """Test root endpoint redirects to camera app."""
    response = await async_client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/app"


# ============================================================================
# Webhook Signature Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_valid_signature(
    async_client: AsyncClient,
    mock_github_issue_payload,
    mock_config
):
    """Test webhook with valid signature is accepted."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    with patch("apps.adw_server.core.handlers.handle_issue_event") as mock_handler:
        mock_handler.return_value = {
            "status": "success",
            "workflow_triggered": True,
            "adw_id": "test-id-12345678"
        }

        response = await async_client.post(
            "/",
            content=payload,
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 200
        mock_handler.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_invalid_signature(
    async_client: AsyncClient,
    mock_github_issue_payload
):
    """Test webhook with invalid signature is rejected."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")
    invalid_signature = "sha256=invalid_signature_here"

    response = await async_client.post(
        "/",
        content=payload,
        headers={
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": invalid_signature,
            "Content-Type": "application/json"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert "Invalid webhook signature" in data["detail"]


@pytest.mark.asyncio
async def test_webhook_missing_signature(
    async_client: AsyncClient,
    mock_github_issue_payload
):
    """Test webhook with missing signature is rejected."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")

    response = await async_client.post(
        "/",
        content=payload,
        headers={
            "X-GitHub-Event": "issues",
            "Content-Type": "application/json"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert "Invalid webhook signature" in data["detail"]


@pytest.mark.asyncio
async def test_webhook_missing_event_header(
    async_client: AsyncClient,
    mock_github_issue_payload,
    mock_config
):
    """Test webhook with missing X-GitHub-Event header is rejected."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    response = await async_client.post(
        "/",
        content=payload,
        headers={
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert "Missing X-GitHub-Event header" in data["detail"]


# ============================================================================
# Issue Event Routing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_issue_event(
    async_client: AsyncClient,
    mock_github_issue_payload,
    mock_config
):
    """Test webhook routes issue events to handle_issue_event."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    with patch("apps.adw_server.core.handlers.handle_issue_event") as mock_handler:
        mock_handler.return_value = {
            "status": "success",
            "workflow_triggered": True,
            "adw_id": "test-id-12345678",
            "issue_number": 123
        }

        response = await async_client.post(
            "/",
            content=payload,
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["workflow_triggered"] is True
        assert data["adw_id"] == "test-id-12345678"

        # Verify handler was called with correct parameters
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args.kwargs["payload"].issue.number == 123
        assert call_args.kwargs["working_dir"] == mock_config.adw_working_dir


# ============================================================================
# Pull Request Event Routing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_pull_request_event(
    async_client: AsyncClient,
    mock_github_pr_payload,
    mock_config
):
    """Test webhook routes pull request events to handle_pull_request_event."""
    payload = json.dumps(mock_github_pr_payload).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    with patch("apps.adw_server.core.handlers.handle_pull_request_event") as mock_handler:
        mock_handler.return_value = {
            "status": "success",
            "workflow_triggered": False,
            "pr_number": 456,
            "reason": "No review label found"
        }

        response = await async_client.post(
            "/",
            content=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["pr_number"] == 456

        # Verify handler was called
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args.kwargs["payload"].pull_request.number == 456


# ============================================================================
# Unsupported Event Tests
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_unsupported_event(
    async_client: AsyncClient,
    mock_config
):
    """Test webhook ignores unsupported event types."""
    payload = json.dumps({"action": "created", "comment": {"body": "test"}}).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    response = await async_client.post(
        "/",
        content=payload,
        headers={
            "X-GitHub-Event": "issue_comment",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert "not supported" in data["reason"]
    assert data["event_type"] == "issue_comment"


# ============================================================================
# Alternative Endpoint Tests
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_alternative_endpoint(
    async_client: AsyncClient,
    mock_github_issue_payload,
    mock_config
):
    """Test alternative webhook endpoint /webhooks/github works the same."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    with patch("apps.adw_server.core.handlers.handle_issue_event") as mock_handler:
        mock_handler.return_value = {
            "status": "success",
            "workflow_triggered": True
        }

        response = await async_client.post(
            "/webhooks/github",
            content=payload,
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 200
        mock_handler.assert_called_once()


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_invalid_json(
    async_client: AsyncClient,
    mock_config
):
    """Test webhook with invalid JSON payload is rejected."""
    payload = b"invalid json here"
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    response = await async_client.post(
        "/",
        content=payload,
        headers={
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert "Invalid JSON payload" in data["detail"]


@pytest.mark.asyncio
async def test_webhook_handler_error(
    async_client: AsyncClient,
    mock_github_issue_payload,
    mock_config
):
    """Test webhook handles errors from event handlers gracefully."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.gh_wb_secret)

    with patch("apps.adw_server.core.handlers.handle_issue_event") as mock_handler:
        mock_handler.side_effect = Exception("Handler error")

        response = await async_client.post(
            "/",
            content=payload,
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert "Error processing webhook" in data["detail"]


# ============================================================================
# CORS Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cors_headers(async_client: AsyncClient, mock_config):
    """Test CORS headers are present when CORS is enabled."""
    if not mock_config.cors_enabled:
        pytest.skip("CORS not enabled in test config")

    response = await async_client.options(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )

    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers
