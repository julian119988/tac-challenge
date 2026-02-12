"""Tests for PR review workflow integration.

This module tests the ADW review workflow that automatically triggers
when pull requests are created or updated.

Tests cover:
- Issue reference extraction from PR descriptions
- Review result formatting for GitHub comments
- PR event handler workflow trigger logic
- Error handling and comment posting
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add adw_server to path for imports
adw_server_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "apps", "adw_server")
if adw_server_dir not in sys.path:
    sys.path.insert(0, adw_server_dir)

from core.handlers import (
    extract_issue_references,
    format_review_results,
    handle_pull_request_event,
    PullRequestWebhookPayload,
    GitHubRepository,
    GitHubUser,
)
from core.adw_integration import WorkflowResult


class TestExtractIssueReferences:
    """Test issue reference extraction from PR body."""

    def test_single_issue_closes(self):
        """Test extracting single issue with 'Closes' keyword."""
        pr_body = "Closes #123"
        issues = extract_issue_references(pr_body)
        assert issues == [123]

    def test_single_issue_fixes(self):
        """Test extracting single issue with 'Fixes' keyword."""
        pr_body = "Fixes #456"
        issues = extract_issue_references(pr_body)
        assert issues == [456]

    def test_single_issue_resolves(self):
        """Test extracting single issue with 'Resolves' keyword."""
        pr_body = "Resolves #789"
        issues = extract_issue_references(pr_body)
        assert issues == [789]

    def test_multiple_issues(self):
        """Test extracting multiple issue references."""
        pr_body = "Fixes #123 and resolves #456"
        issues = extract_issue_references(pr_body)
        assert set(issues) == {123, 456}

    def test_no_references(self):
        """Test PR description without issue references."""
        pr_body = "Some PR description without issue links"
        issues = extract_issue_references(pr_body)
        assert issues == []

    def test_case_insensitive(self):
        """Test case-insensitive keyword matching."""
        test_cases = [
            "CLOSES #123",
            "closes #123",
            "Closes #123",
            "FIXES #456",
            "fixes #456",
            "Fixes #456",
        ]
        for pr_body in test_cases:
            issues = extract_issue_references(pr_body)
            assert len(issues) == 1
            assert issues[0] in [123, 456]

    def test_duplicate_references(self):
        """Test that duplicate issue references are deduplicated."""
        pr_body = "Closes #123 and fixes #123"
        issues = extract_issue_references(pr_body)
        assert issues == [123]

    def test_empty_body(self):
        """Test handling of empty PR body."""
        issues = extract_issue_references("")
        assert issues == []

    def test_none_body(self):
        """Test handling of None PR body."""
        issues = extract_issue_references(None)
        assert issues == []


class TestFormatReviewResults:
    """Test review results formatting for GitHub comments."""

    def test_basic_formatting(self):
        """Test basic review result formatting."""
        comment = format_review_results(
            review_output="Review completed successfully",
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            adw_id="abc12345",
        )

        assert "🔍 **Pull Request Review**" in comment
        assert "#42" in comment
        assert "abc12345" in comment
        assert "https://github.com/owner/repo/pull/42" in comment

    def test_approved_status(self):
        """Test formatting with APPROVED status."""
        review_output = """
        ## Summary
        Code looks good

        ## Approval Status
        APPROVED
        """
        comment = format_review_results(
            review_output=review_output,
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            adw_id="abc12345",
        )

        assert "✅ **APPROVED**" in comment

    def test_changes_requested_status(self):
        """Test formatting with CHANGES REQUESTED status."""
        review_output = """
        ## Summary
        Issues found

        ## Approval Status
        CHANGES REQUESTED
        """
        comment = format_review_results(
            review_output=review_output,
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            adw_id="abc12345",
        )

        assert "⚠️ **CHANGES REQUESTED**" in comment

    def test_test_results_parsing(self):
        """Test parsing and formatting of test results."""
        review_output = """
        Test execution completed.
        15 passed, 2 failed
        """
        comment = format_review_results(
            review_output=review_output,
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            adw_id="abc12345",
        )

        # Should extract test counts
        assert "15" in comment or "2" in comment

    def test_summary_extraction(self):
        """Test extraction of summary section from review output."""
        review_output = """
        # Code Review

        ## Summary
        This PR adds new features and fixes bugs.
        Overall quality is good.

        ## Issues Found
        None
        """
        comment = format_review_results(
            review_output=review_output,
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            adw_id="abc12345",
        )

        assert "This PR adds new features" in comment or "Summary" in comment


class TestHandlePullRequestEvent:
    """Test PR event handler workflow trigger logic."""

    @pytest.fixture
    def mock_pr_payload(self):
        """Create a mock PR webhook payload."""
        return PullRequestWebhookPayload(
            action="opened",
            number=42,
            pull_request={
                "body": "Closes #123",
                "html_url": "https://github.com/owner/repo/pull/42",
            },
            repository=GitHubRepository(
                name="repo",
                full_name="owner/repo",
                html_url="https://github.com/owner/repo",
                default_branch="main",
            ),
            sender=GitHubUser(login="testuser", id=1, type="User"),
        )

    @pytest.mark.asyncio
    async def test_opened_action_triggers_review(self, mock_pr_payload):
        """Test that 'opened' action triggers review workflow."""
        with patch("core.handlers.trigger_review_workflow", new_callable=AsyncMock) as mock_trigger:
            with patch("core.handlers.make_github_issue_comment"):
                mock_trigger.return_value = WorkflowResult(
                    success=True,
                    output="Review completed",
                    adw_id="test123",
                    output_dir="/tmp/test",
                )

                result = await handle_pull_request_event(
                    payload=mock_pr_payload,
                    working_dir="/tmp",
                    model="sonnet",
                )

                assert result["workflow_triggered"] is True
                assert result["workflow_type"] == "review"
                assert result["pr_number"] == 42
                assert mock_trigger.called

    @pytest.mark.asyncio
    async def test_synchronize_action_triggers_review(self, mock_pr_payload):
        """Test that 'synchronize' action triggers review workflow."""
        mock_pr_payload.action = "synchronize"

        with patch("core.handlers.trigger_review_workflow", new_callable=AsyncMock) as mock_trigger:
            with patch("core.handlers.make_github_issue_comment"):
                mock_trigger.return_value = WorkflowResult(
                    success=True,
                    output="Review completed",
                    adw_id="test123",
                    output_dir="/tmp/test",
                )

                result = await handle_pull_request_event(
                    payload=mock_pr_payload,
                    working_dir="/tmp",
                    model="sonnet",
                )

                assert result["workflow_triggered"] is True
                assert mock_trigger.called

    @pytest.mark.asyncio
    async def test_closed_action_does_not_trigger_review(self, mock_pr_payload):
        """Test that 'closed' action does not trigger review."""
        mock_pr_payload.action = "closed"

        result = await handle_pull_request_event(
            payload=mock_pr_payload,
            working_dir="/tmp",
            model="sonnet",
        )

        assert result["workflow_triggered"] is False
        assert "does not trigger review" in result["reason"]

    @pytest.mark.asyncio
    async def test_pr_without_issue_references_skips_workflow(self, mock_pr_payload):
        """Test that PR without issue references skips workflow."""
        mock_pr_payload.pull_request["body"] = "Just a regular PR description"

        result = await handle_pull_request_event(
            payload=mock_pr_payload,
            working_dir="/tmp",
            model="sonnet",
        )

        assert result["workflow_triggered"] is False
        assert "No issue references" in result["reason"]

    @pytest.mark.asyncio
    async def test_multiple_issue_references(self, mock_pr_payload):
        """Test handling of multiple issue references."""
        mock_pr_payload.pull_request["body"] = "Fixes #123 and resolves #456"

        with patch("core.handlers.trigger_review_workflow", new_callable=AsyncMock) as mock_trigger:
            with patch("core.handlers.make_github_issue_comment") as mock_comment:
                mock_trigger.return_value = WorkflowResult(
                    success=True,
                    output="Review completed",
                    adw_id="test123",
                    output_dir="/tmp/test",
                )

                result = await handle_pull_request_event(
                    payload=mock_pr_payload,
                    working_dir="/tmp",
                    model="sonnet",
                )

                assert result["workflow_triggered"] is True
                assert set(result["issue_numbers"]) == {123, 456}
                # Should post comments to both issues (2 initial + 2 final = 4 total)
                assert mock_comment.call_count == 4

    @pytest.mark.asyncio
    async def test_error_handling_posts_error_comment(self, mock_pr_payload):
        """Test that errors during review workflow post error comments."""
        with patch("core.handlers.trigger_review_workflow", new_callable=AsyncMock) as mock_trigger:
            with patch("core.handlers.make_github_issue_comment") as mock_comment:
                mock_trigger.side_effect = Exception("Test error")

                result = await handle_pull_request_event(
                    payload=mock_pr_payload,
                    working_dir="/tmp",
                    model="sonnet",
                )

                assert result["success"] is False
                assert "Test error" in result["error_message"]
                # Should post initial comment + error comment
                assert mock_comment.call_count >= 2

                # Check that error comment was posted
                error_comment_posted = False
                for call in mock_comment.call_args_list:
                    if "Failed" in str(call) or "error" in str(call):
                        error_comment_posted = True
                        break
                assert error_comment_posted


class TestTriggerReviewWorkflow:
    """Test review workflow trigger function."""

    @pytest.mark.asyncio
    async def test_trigger_review_workflow_success(self):
        """Test successful review workflow execution."""
        from core.adw_integration import trigger_review_workflow

        with patch("core.adw_integration.execute_template") as mock_execute:
            mock_response = Mock()
            mock_response.success = True
            mock_response.output = "Review completed successfully"
            mock_response.session_id = "session123"
            mock_execute.return_value = mock_response

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_response)

                with patch("subprocess.run") as mock_subprocess:
                    # Mock git commands for branch checkout flow
                    def subprocess_side_effect(*args, **kwargs):
                        mock_result = Mock()
                        mock_result.returncode = 0
                        mock_result.stdout = "main\n"
                        mock_result.stderr = ""

                        # Handle different git commands
                        if args[0][1] == "log":
                            mock_result.stdout = "abc123 Test commit\n"
                        elif args[0][1] == "rev-parse":
                            mock_result.stdout = "main\n"

                        return mock_result

                    mock_subprocess.side_effect = subprocess_side_effect

                    result = await trigger_review_workflow(
                        pr_number=42,
                        repo_full_name="owner/repo",
                        adw_id="test123",
                        model="sonnet",
                        working_dir="/tmp",
                    )

                    assert result.success is True
                    assert result.output == "Review completed successfully"
                    assert result.adw_id == "test123"
                    assert "reviewer" in result.output_dir

                    # Verify git operations were called
                    assert mock_subprocess.call_count >= 4  # rev-parse, fetch, checkout, log (at minimum)

    @pytest.mark.asyncio
    async def test_trigger_review_workflow_failure(self):
        """Test review workflow execution failure."""
        from core.adw_integration import trigger_review_workflow

        with patch("core.adw_integration.execute_template") as mock_execute:
            mock_execute.side_effect = Exception("Execution failed")

            with patch("asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = AsyncMock(side_effect=Exception("Execution failed"))

                with patch("subprocess.run") as mock_subprocess:
                    # Mock git commands to succeed initially
                    def subprocess_side_effect(*args, **kwargs):
                        mock_result = Mock()
                        mock_result.returncode = 0
                        mock_result.stdout = "main\n"
                        mock_result.stderr = ""

                        # Handle different git commands
                        if args[0][1] == "log":
                            mock_result.stdout = "abc123 Test commit\n"
                        elif args[0][1] == "rev-parse":
                            mock_result.stdout = "main\n"

                        return mock_result

                    mock_subprocess.side_effect = subprocess_side_effect

                    result = await trigger_review_workflow(
                        pr_number=42,
                        repo_full_name="owner/repo",
                        adw_id="test123",
                        model="sonnet",
                        working_dir="/tmp",
                    )

                    assert result.success is False
                    assert "Execution failed" in result.error_message
