"""Tests for GitHub API integration.

Tests cover:
- GitHub comment posting (mocked)
- Issue/PR retrieval (mocked)
- API error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# GitHub Comment Tests
# ============================================================================

def test_make_github_comment_success():
    """Test successful GitHub comment posting."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        from apps.adw_server.core.handlers import make_github_issue_comment

        result = make_github_issue_comment(
            issue_number=123,
            comment="Test comment",
            repo_owner="testowner",
            repo_name="testrepo"
        )

        assert result is True
        mock_run.assert_called_once()

        # Verify gh CLI was called with correct arguments
        call_args = mock_run.call_args[0][0]
        assert "gh" in call_args
        assert "issue" in call_args
        assert "comment" in call_args
        assert "123" in call_args


def test_make_github_comment_failure():
    """Test failed GitHub comment posting."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error")

        from apps.adw_server.core.handlers import make_github_issue_comment

        result = make_github_issue_comment(
            issue_number=123,
            comment="Test comment",
            repo_owner="testowner",
            repo_name="testrepo"
        )

        assert result is False


def test_make_github_comment_exception():
    """Test GitHub comment posting handles exceptions."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Command failed")

        from apps.adw_server.core.handlers import make_github_issue_comment

        result = make_github_issue_comment(
            issue_number=123,
            comment="Test comment",
            repo_owner="testowner",
            repo_name="testrepo"
        )

        assert result is False


def test_make_github_comment_timeout():
    """Test GitHub comment posting handles timeout."""
    with patch("subprocess.run") as mock_run:
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("gh", 30)

        from apps.adw_server.core.handlers import make_github_issue_comment

        result = make_github_issue_comment(
            issue_number=123,
            comment="Test comment",
            repo_owner="testowner",
            repo_name="testrepo"
        )

        assert result is False


# ============================================================================
# GitHub CLI Availability Tests
# ============================================================================

def test_check_github_available_with_gh_and_token():
    """Test GitHub availability check when gh CLI and token are present."""
    with patch("subprocess.run") as mock_run, \
         patch.dict("os.environ", {"GITHUB_PAT": "test-token"}):

        mock_run.return_value = Mock(returncode=0)

        from apps.adw_server.core.handlers import check_github_available

        result = check_github_available()
        assert result is True


def test_check_github_available_without_gh():
    """Test GitHub availability check when gh CLI is not installed."""
    with patch("subprocess.run") as mock_run:
        import subprocess
        mock_run.side_effect = FileNotFoundError()

        from apps.adw_server.core.handlers import check_github_available

        result = check_github_available()
        assert result is False


def test_check_github_available_without_token():
    """Test GitHub availability check when token is missing."""
    with patch("subprocess.run") as mock_run, \
         patch.dict("os.environ", {}, clear=True):

        mock_run.return_value = Mock(returncode=0)

        from apps.adw_server.core.handlers import check_github_available

        result = check_github_available()
        assert result is False


# ============================================================================
# Post Workflow Comment Tests
# ============================================================================

def test_post_workflow_comment_success():
    """Test successful workflow comment posting."""
    with patch("apps.adw_server.core.handlers.GITHUB_COMMENTS_ENABLED", True), \
         patch("apps.adw_server.core.handlers.make_github_issue_comment") as mock_post:

        mock_post.return_value = True

        from apps.adw_server.core.handlers import post_workflow_comment

        result = post_workflow_comment(
            issue_number=123,
            repo_full_name="testowner/testrepo",
            comment="Test workflow comment"
        )

        assert result is True
        mock_post.assert_called_once()


def test_post_workflow_comment_disabled():
    """Test workflow comment posting when GitHub comments are disabled."""
    with patch("apps.adw_server.core.handlers.GITHUB_COMMENTS_ENABLED", False):

        from apps.adw_server.core.handlers import post_workflow_comment

        result = post_workflow_comment(
            issue_number=123,
            repo_full_name="testowner/testrepo",
            comment="Test comment"
        )

        assert result is False


def test_post_workflow_comment_invalid_repo_name():
    """Test workflow comment posting with invalid repo name."""
    with patch("apps.adw_server.core.handlers.GITHUB_COMMENTS_ENABLED", True):

        from apps.adw_server.core.handlers import post_workflow_comment

        result = post_workflow_comment(
            issue_number=123,
            repo_full_name="invalid_format",
            comment="Test comment"
        )

        assert result is False


# ============================================================================
# Comment Formatting Tests
# ============================================================================

def test_comment_includes_bot_identifier():
    """Test that comments include the ADW bot identifier."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)

        from apps.adw_server.core.handlers import make_github_issue_comment, ADW_BOT_IDENTIFIER

        make_github_issue_comment(
            issue_number=123,
            comment="Test comment",
            repo_owner="owner",
            repo_name="repo"
        )

        # Verify the comment includes the bot identifier
        call_args = mock_run.call_args[0][0]
        body_index = call_args.index("--body") + 1
        full_comment = call_args[body_index]

        assert ADW_BOT_IDENTIFIER in full_comment
        assert "Test comment" in full_comment
