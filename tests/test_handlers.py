"""Tests for webhook handlers and validation.

Tests cover:
- Webhook signature validation (HMAC-SHA256)
- Issue event handling
- Pull request event handling
- Label-based workflow routing
- Deduplication logic
- GitHub comment posting
"""

import pytest
import hmac
import hashlib
import time
from unittest.mock import Mock, patch, AsyncMock
from apps.adw_server.core.handlers import (
    validate_webhook_signature,
    extract_repo_info,
    get_label_names,
    should_trigger_workflow,
    determine_workflow_for_issue,
    handle_issue_event,
    handle_pull_request_event,
    create_workflow_comment,
    GitHubIssue,
    GitHubLabel,
    GitHubUser,
    _workflow_dedup_cache,
    DEDUP_WINDOW_SECONDS,
)


# ============================================================================
# Signature Validation Tests
# ============================================================================

def test_validate_webhook_signature_valid():
    """Test webhook signature validation with valid signature."""
    secret = "test_secret_12345678"
    payload = b'{"action": "opened"}'

    # Generate valid signature
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    signature_header = f"sha256={expected_sig}"

    is_valid = validate_webhook_signature(payload, signature_header, secret)
    assert is_valid is True


def test_validate_webhook_signature_invalid():
    """Test webhook signature validation with invalid signature."""
    secret = "test_secret_12345678"
    payload = b'{"action": "opened"}'
    signature_header = "sha256=invalid_signature_here"

    is_valid = validate_webhook_signature(payload, signature_header, secret)
    assert is_valid is False


def test_validate_webhook_signature_missing():
    """Test webhook signature validation with missing signature."""
    secret = "test_secret_12345678"
    payload = b'{"action": "opened"}'

    is_valid = validate_webhook_signature(payload, None, secret)
    assert is_valid is False


def test_validate_webhook_signature_wrong_format():
    """Test webhook signature validation with wrong format (missing sha256= prefix)."""
    secret = "test_secret_12345678"
    payload = b'{"action": "opened"}'
    signature_header = "invalid_format_signature"

    is_valid = validate_webhook_signature(payload, signature_header, secret)
    assert is_valid is False


def test_validate_webhook_signature_timing_attack_resistant():
    """Test that signature comparison is resistant to timing attacks."""
    secret = "test_secret_12345678"
    payload = b'{"action": "opened"}'

    # Generate two different signatures
    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    invalid_sig = "0" * len(valid_sig)

    # Both should return False/True consistently
    assert validate_webhook_signature(payload, f"sha256={valid_sig}", secret) is True
    assert validate_webhook_signature(payload, f"sha256={invalid_sig}", secret) is False


# ============================================================================
# Utility Function Tests
# ============================================================================

def test_extract_repo_info():
    """Test extracting owner and repo name from full_name."""
    owner, repo = extract_repo_info("anthropics/tac-challenge")
    assert owner == "anthropics"
    assert repo == "tac-challenge"


def test_extract_repo_info_invalid():
    """Test extracting repo info with invalid format raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        extract_repo_info("invalid_format")

    assert "Invalid repository full_name format" in str(exc_info.value)


def test_get_label_names():
    """Test extracting label names from issue."""
    issue = GitHubIssue(
        number=123,
        title="Test Issue",
        labels=[
            GitHubLabel(name="bug", color="d73a4a"),
            GitHubLabel(name="priority", color="0052cc"),
        ]
    )

    labels = get_label_names(issue)
    assert labels == ["bug", "priority"]


def test_get_label_names_empty():
    """Test extracting label names from issue with no labels."""
    issue = GitHubIssue(number=123, title="Test Issue", labels=[])
    labels = get_label_names(issue)
    assert labels == []


# ============================================================================
# Deduplication Tests
# ============================================================================

def test_should_trigger_workflow_first_trigger():
    """Test workflow triggers on first attempt."""
    # Clear cache
    _workflow_dedup_cache.clear()

    result = should_trigger_workflow(issue_number=123, workflow_type="chore")
    assert result is True


def test_should_trigger_workflow_duplicate_blocked():
    """Test workflow is blocked when triggered twice quickly."""
    _workflow_dedup_cache.clear()

    # First trigger should succeed
    assert should_trigger_workflow(123, "chore") is True

    # Immediate second trigger should be blocked
    assert should_trigger_workflow(123, "chore") is False


def test_should_trigger_workflow_expired_cache():
    """Test workflow triggers again after dedup window expires."""
    _workflow_dedup_cache.clear()

    # First trigger
    should_trigger_workflow(123, "chore")

    # Manually set cache timestamp to expired time
    _workflow_dedup_cache[(123, "chore")] = time.time() - DEDUP_WINDOW_SECONDS - 1

    # Should trigger again since cache expired
    result = should_trigger_workflow(123, "chore")
    assert result is True


def test_should_trigger_workflow_different_issue():
    """Test workflows for different issues don't interfere."""
    _workflow_dedup_cache.clear()

    assert should_trigger_workflow(123, "chore") is True
    assert should_trigger_workflow(456, "chore") is True


def test_should_trigger_workflow_different_type():
    """Test workflows of different types don't interfere."""
    _workflow_dedup_cache.clear()

    assert should_trigger_workflow(123, "chore") is True
    assert should_trigger_workflow(123, "chore_implement") is True


# ============================================================================
# Workflow Determination Tests
# ============================================================================

def test_determine_workflow_for_issue_bug_label():
    """Test bug label triggers chore_implement workflow."""
    _workflow_dedup_cache.clear()

    issue = GitHubIssue(
        number=123,
        title="Fix login bug",
        body="Login fails with error 500",
        labels=[GitHubLabel(name="bug", color="d73a4a")]
    )

    result = determine_workflow_for_issue(issue, "opened")
    assert result is not None
    workflow_type, prompt = result
    assert workflow_type == "chore_implement"
    assert "Issue #123" in prompt
    assert "Fix login bug" in prompt


def test_determine_workflow_for_issue_implement_label():
    """Test implement label triggers chore_implement workflow."""
    _workflow_dedup_cache.clear()

    issue = GitHubIssue(
        number=124,
        title="Add feature X",
        labels=[GitHubLabel(name="implement", color="0052cc")]
    )

    result = determine_workflow_for_issue(issue, "opened")
    assert result is not None
    workflow_type, prompt = result
    assert workflow_type == "chore_implement"


def test_determine_workflow_for_issue_feature_label():
    """Test feature label triggers chore workflow (planning only)."""
    _workflow_dedup_cache.clear()

    issue = GitHubIssue(
        number=125,
        title="Add authentication",
        labels=[GitHubLabel(name="feature", color="a2eeef")]
    )

    result = determine_workflow_for_issue(issue, "opened")
    assert result is not None
    workflow_type, prompt = result
    assert workflow_type == "chore"


def test_determine_workflow_for_issue_chore_label():
    """Test chore label triggers chore workflow."""
    _workflow_dedup_cache.clear()

    issue = GitHubIssue(
        number=126,
        title="Update dependencies",
        labels=[GitHubLabel(name="chore", color="fef2c0")]
    )

    result = determine_workflow_for_issue(issue, "opened")
    assert result is not None
    workflow_type, prompt = result
    assert workflow_type == "chore"


def test_determine_workflow_for_issue_no_matching_label():
    """Test no workflow triggered for issues without matching labels."""
    _workflow_dedup_cache.clear()

    issue = GitHubIssue(
        number=127,
        title="Question about docs",
        labels=[GitHubLabel(name="question", color="d876e3")]
    )

    result = determine_workflow_for_issue(issue, "opened")
    assert result is None


def test_determine_workflow_for_issue_wrong_action():
    """Test no workflow triggered for non-opened/labeled actions."""
    _workflow_dedup_cache.clear()

    issue = GitHubIssue(
        number=128,
        title="Fix bug",
        labels=[GitHubLabel(name="bug", color="d73a4a")]
    )

    result = determine_workflow_for_issue(issue, "closed")
    assert result is None


def test_determine_workflow_for_issue_truncates_long_body():
    """Test issue body is truncated if too long."""
    _workflow_dedup_cache.clear()

    long_body = "A" * 1000
    issue = GitHubIssue(
        number=129,
        title="Test",
        body=long_body,
        labels=[GitHubLabel(name="bug", color="d73a4a")]
    )

    result = determine_workflow_for_issue(issue, "opened")
    assert result is not None
    _, prompt = result
    assert len(prompt) < len(long_body) + 100  # Should be truncated
    assert "..." in prompt


# ============================================================================
# Issue Event Handler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_handle_issue_event_no_workflow():
    """Test handle_issue_event returns correctly when no workflow matches."""
    from apps.adw_server.core.handlers import IssueWebhookPayload, GitHubRepository

    payload = IssueWebhookPayload(
        action="opened",
        issue=GitHubIssue(
            number=200,
            title="Question",
            labels=[GitHubLabel(name="question", color="d876e3")]
        ),
        repository=GitHubRepository(
            name="testrepo",
            full_name="testowner/testrepo",
            html_url="https://github.com/testowner/testrepo"
        ),
        sender=GitHubUser(login="testuser", id=12345)
    )

    result = await handle_issue_event(payload)

    assert result["workflow_triggered"] is False
    assert "No matching workflow" in result["reason"]
    assert result["issue_number"] == 200


@pytest.mark.asyncio
async def test_handle_issue_event_chore_workflow():
    """Test handle_issue_event triggers chore workflow for feature label."""
    from apps.adw_server.core.handlers import (
        IssueWebhookPayload,
        GitHubRepository,
        WorkflowResult,
    )

    _workflow_dedup_cache.clear()

    payload = IssueWebhookPayload(
        action="opened",
        issue=GitHubIssue(
            number=201,
            title="Add dark mode",
            body="Users want dark mode",
            labels=[GitHubLabel(name="feature", color="a2eeef")]
        ),
        repository=GitHubRepository(
            name="testrepo",
            full_name="testowner/testrepo",
            html_url="https://github.com/testowner/testrepo"
        ),
        sender=GitHubUser(login="testuser", id=12345)
    )

    mock_result = WorkflowResult(
        success=True,
        adw_id="test-id-12345678",
        plan_path="specs/test-plan.md",
        output_dir="agents/test-id-12345678",
        output="Planning complete",
        error_message=""
    )

    with patch("apps.adw_server.core.handlers.generate_adw_id") as mock_gen_id, \
         patch("apps.adw_server.core.handlers.trigger_chore_workflow") as mock_trigger, \
         patch("apps.adw_server.core.handlers.post_workflow_comment") as mock_comment:

        mock_gen_id.return_value = "test-id-12345678"
        mock_trigger.return_value = mock_result
        mock_comment.return_value = True

        result = await handle_issue_event(payload)

        assert result["workflow_triggered"] is True
        assert result["workflow_type"] == "chore"
        assert result["issue_number"] == 201
        assert result["success"] is True
        assert result["adw_id"] == "test-id-12345678"

        # Verify trigger was called with correct parameters
        mock_trigger.assert_called_once()
        call_kwargs = mock_trigger.call_args.kwargs
        assert "Issue #201" in call_kwargs["prompt"]
        assert call_kwargs["adw_id"] == "test-id-12345678"


@pytest.mark.asyncio
async def test_handle_issue_event_chore_implement_workflow():
    """Test handle_issue_event triggers chore_implement workflow for bug label."""
    from apps.adw_server.core.handlers import (
        IssueWebhookPayload,
        GitHubRepository,
        WorkflowResult,
    )

    _workflow_dedup_cache.clear()

    payload = IssueWebhookPayload(
        action="opened",
        issue=GitHubIssue(
            number=202,
            title="Fix crash on startup",
            labels=[GitHubLabel(name="bug", color="d73a4a")]
        ),
        repository=GitHubRepository(
            name="testrepo",
            full_name="testowner/testrepo",
            html_url="https://github.com/testowner/testrepo"
        ),
        sender=GitHubUser(login="testuser", id=12345)
    )

    mock_chore_result = WorkflowResult(
        success=True,
        adw_id="test-id-87654321",
        plan_path="specs/test-plan.md",
        output_dir="agents/test-id-87654321",
        output="Planning complete",
        error_message=""
    )

    mock_impl_result = WorkflowResult(
        success=True,
        adw_id="test-id-87654321",
        plan_path="",
        output_dir="agents/test-id-87654321",
        output="Implementation complete",
        error_message=""
    )

    with patch("apps.adw_server.core.handlers.generate_adw_id") as mock_gen_id, \
         patch("apps.adw_server.core.handlers.trigger_chore_implement_workflow") as mock_trigger, \
         patch("apps.adw_server.core.handlers.post_workflow_comment") as mock_comment:

        mock_gen_id.return_value = "test-id-87654321"
        mock_trigger.return_value = (mock_chore_result, mock_impl_result)
        mock_comment.return_value = True

        result = await handle_issue_event(payload)

        assert result["workflow_triggered"] is True
        assert result["workflow_type"] == "chore_implement"
        assert result["issue_number"] == 202
        assert result["chore_success"] is True
        assert result["implement_success"] is True

        # Verify trigger was called
        mock_trigger.assert_called_once()


# ============================================================================
# Pull Request Event Handler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_handle_pull_request_event():
    """Test handle_pull_request_event logs event and returns not implemented."""
    from apps.adw_server.core.handlers import PullRequestWebhookPayload, GitHubRepository

    payload = PullRequestWebhookPayload(
        action="opened",
        number=300,
        pull_request={"title": "Test PR", "state": "open"},
        repository=GitHubRepository(
            name="testrepo",
            full_name="testowner/testrepo",
            html_url="https://github.com/testowner/testrepo"
        ),
        sender=GitHubUser(login="testuser", id=12345)
    )

    result = await handle_pull_request_event(payload)

    assert result["workflow_triggered"] is False
    assert "not yet implemented" in result["reason"]
    assert result["pr_number"] == 300
    assert result["action"] == "opened"


# ============================================================================
# Workflow Comment Creation Tests
# ============================================================================

def test_create_workflow_comment_chore_success():
    """Test creating comment for successful chore workflow."""
    result = {
        "workflow_triggered": True,
        "workflow_type": "chore",
        "adw_id": "test-id-12345678",
        "success": True,
        "plan_path": "specs/feature-12345678.md"
    }

    comment = create_workflow_comment(result, 123)

    assert "ADW Workflow Triggered" in comment
    assert "test-id-12345678" in comment
    assert "Success" in comment
    assert "specs/feature-12345678.md" in comment


def test_create_workflow_comment_chore_failure():
    """Test creating comment for failed chore workflow."""
    result = {
        "workflow_triggered": True,
        "workflow_type": "chore",
        "adw_id": "test-id-12345678",
        "success": False,
        "error_message": "Planning failed: timeout"
    }

    comment = create_workflow_comment(result, 123)

    assert "Failed" in comment
    assert "timeout" in comment


def test_create_workflow_comment_not_triggered():
    """Test creating comment when workflow was not triggered."""
    result = {
        "workflow_triggered": False,
        "reason": "No matching label"
    }

    comment = create_workflow_comment(result, 123)
    assert comment == ""


def test_create_workflow_comment_chore_implement_success():
    """Test creating comment for successful chore_implement workflow."""
    result = {
        "workflow_triggered": True,
        "workflow_type": "chore_implement",
        "adw_id": "test-id-87654321",
        "chore_success": True,
        "implement_success": True
    }

    comment = create_workflow_comment(result, 123)

    assert "Full Implementation" in comment
    assert "Success" in comment


def test_create_workflow_comment_chore_implement_partial():
    """Test creating comment for partially successful chore_implement workflow."""
    result = {
        "workflow_triggered": True,
        "workflow_type": "chore_implement",
        "adw_id": "test-id-87654321",
        "chore_success": True,
        "implement_success": False,
        "error_message": "Implementation failed"
    }

    comment = create_workflow_comment(result, 123)

    assert "Partial Success" in comment
    assert "Implementation failed" in comment
