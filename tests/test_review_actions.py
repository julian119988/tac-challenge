"""Tests for review action handlers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from apps.adw_server.core.review_actions import (
    parse_review_status,
    extract_review_issues,
    merge_pull_request,
    trigger_reimplementation,
    handle_review_results,
    check_reimplement_attempts,
    increment_reimplement_attempts,
    reset_reimplement_attempts,
    _reimplement_attempts,
)
from apps.adw_server.core.adw_integration import WorkflowResult


# Sample review outputs for testing
APPROVED_REVIEW = """
# Code Review

## Summary
The changes look great and implement the requested feature correctly.

## Strengths
- Clean code
- Good test coverage

## Issues Found

### Critical
None

### Moderate
None

### Minor
None

## Recommendations
1. Consider adding more edge case tests
2. Update documentation

## Approval Status
[APPROVED]
"""

CHANGES_REQUESTED_REVIEW = """
# Code Review

## Summary
The implementation has several issues that need to be addressed.

## Strengths
- Good structure

## Issues Found

### Critical
- SQL injection vulnerability in user input handling
- Missing authentication check on admin endpoint

### Moderate
- Poor error handling in API calls
- Missing input validation

### Minor
- Code formatting inconsistencies
- Missing docstrings

## Recommendations
1. Fix SQL injection vulnerability immediately
2. Add authentication middleware
3. Improve error handling with try-catch blocks
4. Add input validation for all user inputs

## Approval Status
[CHANGES REQUESTED]
"""

NEEDS_DISCUSSION_REVIEW = """
# Code Review

## Summary
The approach needs discussion before proceeding.

## Issues Found

### Critical
None

### Moderate
- Architectural concerns about the database schema

### Minor
None

## Recommendations
1. Discuss the database schema design
2. Consider alternative approaches

## Approval Status
[NEEDS DISCUSSION]
"""


class TestParseReviewStatus:
    """Tests for parse_review_status function."""

    def test_parse_approved_status(self):
        """Test parsing APPROVED status."""
        status, summary, recs = parse_review_status(APPROVED_REVIEW)
        assert status == "APPROVED"
        assert "great" in summary.lower()
        assert len(recs) == 2
        assert "edge case" in recs[0].lower()

    def test_parse_changes_requested_status(self):
        """Test parsing CHANGES_REQUESTED status."""
        status, summary, recs = parse_review_status(CHANGES_REQUESTED_REVIEW)
        assert status == "CHANGES_REQUESTED"
        assert "issues" in summary.lower()
        assert len(recs) == 4

    def test_parse_needs_discussion_status(self):
        """Test parsing NEEDS_DISCUSSION status."""
        status, summary, recs = parse_review_status(NEEDS_DISCUSSION_REVIEW)
        assert status == "NEEDS_DISCUSSION"
        assert "discussion" in summary.lower()

    def test_parse_malformed_output(self):
        """Test fallback behavior for malformed output."""
        malformed = "This is not a proper review format"
        status, summary, recs = parse_review_status(malformed)
        assert status == "NEEDS_DISCUSSION"  # Default fallback
        assert summary == ""
        assert len(recs) == 0

    def test_parse_output_with_variations(self):
        """Test parsing with format variations."""
        # Test with spaces in status
        output_with_spaces = "## Approval Status\n[ CHANGES REQUESTED ]"
        status, _, _ = parse_review_status(output_with_spaces)
        assert status == "CHANGES_REQUESTED"

        # Test without brackets
        output_no_brackets = "## Approval Status\nAPPROVED"
        status, _, _ = parse_review_status(output_no_brackets)
        assert status == "APPROVED"


class TestExtractReviewIssues:
    """Tests for extract_review_issues function."""

    def test_extract_all_severity_levels(self):
        """Test extracting issues by all severity levels."""
        issues = extract_review_issues(CHANGES_REQUESTED_REVIEW)

        assert len(issues["Critical"]) == 2
        assert "SQL injection" in issues["Critical"][0]
        assert "authentication" in issues["Critical"][1]

        assert len(issues["Moderate"]) == 2
        assert "error handling" in issues["Moderate"][0].lower()

        assert len(issues["Minor"]) == 2
        assert "formatting" in issues["Minor"][0].lower()

    def test_extract_with_no_issues(self):
        """Test extracting when no issues present."""
        issues = extract_review_issues(APPROVED_REVIEW)

        assert len(issues["Critical"]) == 0
        assert len(issues["Moderate"]) == 0
        assert len(issues["Minor"]) == 0

    def test_extract_missing_sections(self):
        """Test extracting from output missing issues section."""
        output = "# Review\n\n## Summary\nLooks good"
        issues = extract_review_issues(output)

        assert len(issues["Critical"]) == 0
        assert len(issues["Moderate"]) == 0
        assert len(issues["Minor"]) == 0


class TestMergePullRequest:
    """Tests for merge_pull_request function."""

    @patch('subprocess.run')
    def test_successful_merge(self, mock_run):
        """Test successful PR merge."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        result = merge_pull_request(
            pr_number=42,
            repo_owner="test-owner",
            repo_name="test-repo",
            merge_method="squash"
        )

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "gh" in args
        assert "pr" in args
        assert "merge" in args
        assert "42" in args
        assert "--squash" in args

    @patch('subprocess.run')
    def test_failed_merge(self, mock_run):
        """Test failed PR merge."""
        mock_run.return_value = Mock(returncode=1, stderr="Merge conflict")

        result = merge_pull_request(
            pr_number=42,
            repo_owner="test-owner",
            repo_name="test-repo"
        )

        assert result is False

    @patch('subprocess.run')
    def test_merge_timeout(self, mock_run):
        """Test merge timeout handling."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("gh", 30)

        result = merge_pull_request(
            pr_number=42,
            repo_owner="test-owner",
            repo_name="test-repo"
        )

        assert result is False

    @patch('subprocess.run')
    def test_merge_with_different_methods(self, mock_run):
        """Test merge with different merge methods."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        # Test squash
        merge_pull_request(42, "owner", "repo", merge_method="squash")
        assert "--squash" in mock_run.call_args[0][0]

        # Test merge
        merge_pull_request(42, "owner", "repo", merge_method="merge")
        assert "--merge" in mock_run.call_args[0][0]

        # Test rebase
        merge_pull_request(42, "owner", "repo", merge_method="rebase")
        assert "--rebase" in mock_run.call_args[0][0]


class TestTriggerReimplementation:
    """Tests for trigger_reimplementation function."""

    @pytest.mark.asyncio
    @patch('apps.adw_server.core.review_actions.trigger_chore_implement_workflow')
    async def test_successful_reimplementation(self, mock_trigger):
        """Test successful re-implementation trigger."""
        mock_chore_result = WorkflowResult(
            success=True,
            output="Chore completed",
            session_id="chore-session",
            adw_id="test-adw",
            output_dir="/path/to/output",
            plan_path="/path/to/plan.md",
            error_message=None
        )
        mock_impl_result = WorkflowResult(
            success=True,
            output="Implementation completed",
            session_id="impl-session",
            adw_id="test-adw",
            output_dir="/path/to/output",
            plan_path=None,
            error_message=None
        )
        mock_trigger.return_value = (mock_chore_result, mock_impl_result)

        chore_result, impl_result = await trigger_reimplementation(
            issue_number=42,
            original_prompt="Add feature X",
            review_feedback="Fix bugs in implementation",
            adw_id="new-adw-id",
            model="sonnet",
            working_dir="/path/to/repo",
            repo_owner="owner",
            repo_name="repo",
            issue_title="Add feature X"
        )

        assert chore_result.success is True
        assert impl_result.success is True
        mock_trigger.assert_called_once()

        # Check that enhanced prompt includes original and feedback
        call_args = mock_trigger.call_args
        enhanced_prompt = call_args[1]["prompt"]
        assert "Add feature X" in enhanced_prompt
        assert "Fix bugs" in enhanced_prompt


class TestReimplementAttemptTracking:
    """Tests for re-implementation attempt tracking."""

    def setup_method(self):
        """Reset attempt counter before each test."""
        _reimplement_attempts.clear()

    def test_check_attempts_initially_allowed(self):
        """Test that re-implementation is allowed initially."""
        allowed, count = check_reimplement_attempts(42, max_attempts=3)
        assert allowed is True
        assert count == 0

    def test_increment_attempts(self):
        """Test incrementing attempt count."""
        count1 = increment_reimplement_attempts(42)
        assert count1 == 1

        count2 = increment_reimplement_attempts(42)
        assert count2 == 2

    def test_check_attempts_after_max(self):
        """Test that re-implementation is blocked after max attempts."""
        increment_reimplement_attempts(42)
        increment_reimplement_attempts(42)
        increment_reimplement_attempts(42)

        allowed, count = check_reimplement_attempts(42, max_attempts=3)
        assert allowed is False
        assert count == 3

    def test_reset_attempts(self):
        """Test resetting attempt count."""
        increment_reimplement_attempts(42)
        increment_reimplement_attempts(42)

        reset_reimplement_attempts(42)

        allowed, count = check_reimplement_attempts(42, max_attempts=3)
        assert allowed is True
        assert count == 0

    def test_multiple_issues_tracked_separately(self):
        """Test that different issues are tracked separately."""
        increment_reimplement_attempts(42)
        increment_reimplement_attempts(42)
        increment_reimplement_attempts(99)

        _, count_42 = check_reimplement_attempts(42, max_attempts=3)
        _, count_99 = check_reimplement_attempts(99, max_attempts=3)

        assert count_42 == 2
        assert count_99 == 1


class TestHandleReviewResults:
    """Tests for handle_review_results function."""

    def setup_method(self):
        """Reset attempt counter before each test."""
        _reimplement_attempts.clear()

    @pytest.mark.asyncio
    @patch('apps.adw_server.core.review_actions.merge_pull_request')
    @patch('apps.adw_server.core.review_actions.post_merge_comment')
    @patch('apps.adw_server.core.review_actions.get_config')
    async def test_approved_triggers_merge(self, mock_config, mock_post_comment, mock_merge):
        """Test that APPROVED status triggers merge."""
        # Mock config
        config = Mock()
        config.auto_merge_on_approval = True
        config.auto_reimplement_on_changes = True
        config.merge_method = "squash"
        config.max_reimplement_attempts = 3
        mock_config.return_value = config

        mock_merge.return_value = True
        mock_post_comment.return_value = True

        review_result = WorkflowResult(
            success=True,
            output=APPROVED_REVIEW,
            session_id="review-session",
            adw_id="review-adw",
            output_dir="/path/to/output",
            plan_path=None,
            error_message=None
        )

        result = await handle_review_results(
            review_result=review_result,
            pr_number=42,
            issue_numbers=[1],
            repo_full_name="owner/repo",
            original_prompt="Add feature",
            issue_title="Add feature",
            model="sonnet",
            working_dir="/path/to/repo"
        )

        assert result["action"] == "approved"
        assert result["approval_status"] == "APPROVED"
        assert result["merge_attempted"] is True
        assert result["success"] is True
        mock_merge.assert_called_once()

    @pytest.mark.asyncio
    @patch('apps.adw_server.core.review_actions.trigger_reimplementation')
    @patch('apps.adw_server.core.review_actions.post_reimplementation_comment')
    @patch('apps.adw_server.core.review_actions.get_config')
    async def test_changes_requested_triggers_reimplement(
        self, mock_config, mock_post_comment, mock_reimplement
    ):
        """Test that CHANGES_REQUESTED triggers re-implementation."""
        # Mock config
        config = Mock()
        config.auto_merge_on_approval = True
        config.auto_reimplement_on_changes = True
        config.merge_method = "squash"
        config.max_reimplement_attempts = 3
        mock_config.return_value = config

        mock_chore_result = WorkflowResult(
            success=True,
            output="Chore completed",
            session_id="chore-session",
            adw_id="new-adw",
            output_dir="/path/to/output",
            plan_path="/path/to/plan.md",
            error_message=None
        )
        mock_reimplement.return_value = (mock_chore_result, None)
        mock_post_comment.return_value = True

        review_result = WorkflowResult(
            success=True,
            output=CHANGES_REQUESTED_REVIEW,
            session_id="review-session",
            adw_id="review-adw",
            output_dir="/path/to/output",
            plan_path=None,
            error_message=None
        )

        result = await handle_review_results(
            review_result=review_result,
            pr_number=42,
            issue_numbers=[1],
            repo_full_name="owner/repo",
            original_prompt="Add feature",
            issue_title="Add feature",
            model="sonnet",
            working_dir="/path/to/repo"
        )

        assert result["action"] == "changes_requested"
        assert result["approval_status"] == "CHANGES_REQUESTED"
        assert result["reimplementation_attempted"] is True
        assert result["attempt_count"] == 1
        mock_reimplement.assert_called_once()

    @pytest.mark.asyncio
    @patch('apps.adw_server.core.handlers.make_github_issue_comment')
    @patch('apps.adw_server.core.review_actions.get_config')
    async def test_max_attempts_blocks_reimplement(self, mock_config, mock_comment):
        """Test that max attempts blocks re-implementation."""
        # Mock config
        config = Mock()
        config.auto_merge_on_approval = True
        config.auto_reimplement_on_changes = True
        config.merge_method = "squash"
        config.max_reimplement_attempts = 3
        mock_config.return_value = config

        mock_comment.return_value = None

        # Simulate 3 previous attempts
        increment_reimplement_attempts(1)
        increment_reimplement_attempts(1)
        increment_reimplement_attempts(1)

        review_result = WorkflowResult(
            success=True,
            output=CHANGES_REQUESTED_REVIEW,
            session_id="review-session",
            adw_id="review-adw",
            output_dir="/path/to/output",
            plan_path=None,
            error_message=None
        )

        result = await handle_review_results(
            review_result=review_result,
            pr_number=42,
            issue_numbers=[1],
            repo_full_name="owner/repo",
            original_prompt="Add feature",
            issue_title="Add feature",
            model="sonnet",
            working_dir="/path/to/repo"
        )

        assert result["action"] == "max_attempts_reached"
        assert result["success"] is False
        assert result["attempt_count"] == 3
        mock_comment.assert_called()

    @pytest.mark.asyncio
    @patch('apps.adw_server.core.review_actions.get_config')
    async def test_needs_discussion_posts_comment_only(self, mock_config):
        """Test that NEEDS_DISCUSSION only posts comment."""
        # Mock config
        config = Mock()
        config.auto_merge_on_approval = True
        config.auto_reimplement_on_changes = True
        config.merge_method = "squash"
        config.max_reimplement_attempts = 3
        mock_config.return_value = config

        review_result = WorkflowResult(
            success=True,
            output=NEEDS_DISCUSSION_REVIEW,
            session_id="review-session",
            adw_id="review-adw",
            output_dir="/path/to/output",
            plan_path=None,
            error_message=None
        )

        result = await handle_review_results(
            review_result=review_result,
            pr_number=42,
            issue_numbers=[1],
            repo_full_name="owner/repo",
            original_prompt="Add feature",
            issue_title="Add feature",
            model="sonnet",
            working_dir="/path/to/repo"
        )

        assert result["action"] == "comment_only"
        assert result["approval_status"] == "NEEDS_DISCUSSION"
        assert result["success"] is True
        assert "merge_attempted" not in result
        assert "reimplementation_attempted" not in result

    @pytest.mark.asyncio
    @patch('apps.adw_server.core.review_actions.get_config')
    async def test_invalid_repo_name_returns_error(self, mock_config):
        """Test handling of invalid repository name format."""
        # Mock config
        config = Mock()
        config.auto_merge_on_approval = True
        config.auto_reimplement_on_changes = True
        config.merge_method = "squash"
        config.max_reimplement_attempts = 3
        mock_config.return_value = config

        review_result = WorkflowResult(
            success=True,
            output=APPROVED_REVIEW,
            session_id="review-session",
            adw_id="review-adw",
            output_dir="/path/to/output",
            plan_path=None,
            error_message=None
        )

        result = await handle_review_results(
            review_result=review_result,
            pr_number=42,
            issue_numbers=[1],
            repo_full_name="invalid-format",  # Missing slash
            original_prompt="Add feature",
            issue_title="Add feature",
            model="sonnet",
            working_dir="/path/to/repo"
        )

        assert result["action"] == "error"
        assert result["success"] is False
        assert "error" in result
