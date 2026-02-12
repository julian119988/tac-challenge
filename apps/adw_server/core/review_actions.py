"""Review result actions and handlers.

This module provides functionality for handling PR review results, including:
- Parsing review output for approval status and issues
- Automatically merging approved PRs
- Triggering re-implementation for PRs with requested changes
- Posting status comments to GitHub issues
"""

import logging
import os
import re
import subprocess
from typing import Optional

from apps.adw_server.core.adw_integration import WorkflowResult, trigger_chore_implement_workflow
from apps.adw_server.core.config import get_config

logger = logging.getLogger(__name__)

# Re-implementation attempt tracking (in-memory)
# Maps issue_number -> attempt_count
_reimplement_attempts: dict[int, int] = {}


def check_reimplement_attempts(issue_number: int, max_attempts: int = 3) -> tuple[bool, int]:
    """Check if re-implementation is allowed for this issue.

    Args:
        issue_number: GitHub issue number
        max_attempts: Maximum allowed attempts

    Returns:
        Tuple of (allowed, current_count)
        - allowed: True if another re-implementation is allowed
        - current_count: Current attempt count for this issue

    Example:
        allowed, count = check_reimplement_attempts(42, max_attempts=3)
        if not allowed:
            logger.warning(f"Max attempts reached: {count}")
    """
    current_count = _reimplement_attempts.get(issue_number, 0)
    allowed = current_count < max_attempts
    return allowed, current_count


def increment_reimplement_attempts(issue_number: int) -> int:
    """Increment re-implementation attempt count for an issue.

    Args:
        issue_number: GitHub issue number

    Returns:
        New attempt count

    Example:
        new_count = increment_reimplement_attempts(42)
        logger.info(f"Re-implementation attempt {new_count} started")
    """
    current_count = _reimplement_attempts.get(issue_number, 0)
    new_count = current_count + 1
    _reimplement_attempts[issue_number] = new_count
    logger.info(f"Incremented re-implementation attempts for issue #{issue_number}: {new_count}")
    return new_count


def reset_reimplement_attempts(issue_number: int) -> None:
    """Reset re-implementation attempt count for an issue.

    Call this when a PR is successfully merged or manually closed.

    Args:
        issue_number: GitHub issue number

    Example:
        reset_reimplement_attempts(42)
    """
    if issue_number in _reimplement_attempts:
        del _reimplement_attempts[issue_number]
        logger.info(f"Reset re-implementation attempts for issue #{issue_number}")


def parse_review_status(review_output: str) -> tuple[str, str, list[str]]:
    """Parse review output to extract approval status, summary, and recommendations.

    Args:
        review_output: The full output from the review workflow

    Returns:
        Tuple of (approval_status, summary, recommendations)
        - approval_status: One of "APPROVED", "CHANGES_REQUESTED", "NEEDS_DISCUSSION"
        - summary: The summary section from the review
        - recommendations: List of recommendation strings

    Example:
        status, summary, recs = parse_review_status(review_output)
        if status == "APPROVED":
            merge_pull_request(pr_number, repo_owner, repo_name)
    """
    # Default values
    approval_status = "NEEDS_DISCUSSION"
    summary = ""
    recommendations = []

    # Parse approval status - looking for format: ## Approval Status\n[STATUS]
    approval_pattern = r'##\s*Approval\s*Status\s*\n\s*\[?\s*(APPROVED|CHANGES\s*REQUESTED|NEEDS\s*DISCUSSION)\s*\]?'
    approval_match = re.search(approval_pattern, review_output, re.IGNORECASE)

    if approval_match:
        status_text = approval_match.group(1).upper().replace(" ", "_")
        if "APPROVED" in status_text:
            approval_status = "APPROVED"
        elif "CHANGES" in status_text:
            approval_status = "CHANGES_REQUESTED"
        elif "NEEDS" in status_text or "DISCUSSION" in status_text:
            approval_status = "NEEDS_DISCUSSION"
    else:
        # Fallback: look for status keywords anywhere in output
        if "APPROVED" in review_output:
            approval_status = "APPROVED"
        elif "CHANGES REQUESTED" in review_output or "CHANGES_REQUESTED" in review_output:
            approval_status = "CHANGES_REQUESTED"

    # Extract summary section
    summary_pattern = r'##\s*Summary\s*\n(.*?)(?=\n##|\Z)'
    summary_match = re.search(summary_pattern, review_output, re.DOTALL | re.IGNORECASE)

    if summary_match:
        summary = summary_match.group(1).strip()

    # Extract recommendations
    recommendations_pattern = r'##\s*Recommendations\s*\n(.*?)(?=\n##|\Z)'
    recommendations_match = re.search(recommendations_pattern, review_output, re.DOTALL | re.IGNORECASE)

    if recommendations_match:
        recs_text = recommendations_match.group(1).strip()
        # Parse numbered or bulleted list
        rec_items = re.findall(r'(?:^|\n)\s*(?:\d+\.|-|\*)\s*(.+)', recs_text)
        recommendations = [rec.strip() for rec in rec_items if rec.strip()]

    return approval_status, summary, recommendations


def extract_review_issues(review_output: str) -> dict[str, list[str]]:
    """Extract issues by severity from review output.

    Args:
        review_output: The full output from the review workflow

    Returns:
        Dictionary with severity levels as keys ("Critical", "Moderate", "Minor")
        and lists of issue strings as values

    Example:
        issues = extract_review_issues(review_output)
        if issues["Critical"]:
            logger.error(f"Found {len(issues['Critical'])} critical issues")
    """
    issues = {
        "Critical": [],
        "Moderate": [],
        "Minor": []
    }

    # Look for ## Issues Found section
    # Use negative lookahead to avoid matching ### sections as ## sections
    issues_section_pattern = r'##\s*Issues\s*Found\s*\n(.*?)(?=\n##(?!#)|\Z)'
    issues_match = re.search(issues_section_pattern, review_output, re.DOTALL | re.IGNORECASE)

    if not issues_match:
        return issues

    issues_text = issues_match.group(1)

    # Extract each severity section
    for severity in ["Critical", "Moderate", "Minor"]:
        severity_pattern = rf'###\s*{severity}\s*\n(.*?)(?=###|\n##|\Z)'
        severity_match = re.search(severity_pattern, issues_text, re.DOTALL | re.IGNORECASE)

        if severity_match:
            severity_text = severity_match.group(1).strip()
            # Skip if it's just "None"
            if severity_text.lower() == "none":
                continue
            # Parse bulleted or numbered items
            issue_items = re.findall(r'(?:^|\n)\s*(?:-|\*|\d+\.)\s*(.+)', severity_text)
            issues[severity] = [item.strip() for item in issue_items if item.strip()]

    return issues


def merge_pull_request(
    pr_number: int,
    repo_owner: str,
    repo_name: str,
    merge_method: str = "squash",
    logger: Optional[logging.Logger] = None
) -> bool:
    """Merge a pull request using GitHub CLI.

    Args:
        pr_number: Pull request number to merge
        repo_owner: Repository owner
        repo_name: Repository name
        merge_method: Merge method (squash, merge, rebase)
        logger: Optional logger instance

    Returns:
        True if merge successful, False otherwise

    Example:
        success = merge_pull_request(42, "myorg", "myrepo")
        if success:
            print("PR merged successfully")
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    repo_full_name = f"{repo_owner}/{repo_name}"

    logger.info(f"Attempting to merge PR #{pr_number} in {repo_full_name} using {merge_method} method")

    try:
        # Build gh pr merge command
        cmd = [
            "gh", "pr", "merge", str(pr_number),
            "--repo", repo_full_name,
            f"--{merge_method}",
            "--auto",  # Merge when all checks pass
        ]

        # Execute merge command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            logger.info(f"✓ Successfully merged PR #{pr_number}")
            return True
        else:
            logger.error(f"Failed to merge PR #{pr_number}: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while merging PR #{pr_number}")
        return False
    except Exception as e:
        logger.error(f"Error merging PR #{pr_number}: {e}", exc_info=True)
        return False


async def trigger_reimplementation(
    issue_number: int,
    original_prompt: str,
    review_feedback: str,
    adw_id: str,
    model: str,
    working_dir: str,
    repo_owner: str,
    repo_name: str,
    issue_title: str,
    logger: Optional[logging.Logger] = None
) -> tuple[WorkflowResult, Optional[WorkflowResult]]:
    """Trigger a re-implementation workflow based on review feedback.

    Args:
        issue_number: GitHub issue number
        original_prompt: Original issue description
        review_feedback: Review feedback to address
        adw_id: ADW ID for tracking
        model: Model to use (sonnet/opus)
        working_dir: Working directory path
        repo_owner: Repository owner
        repo_name: Repository name
        issue_title: Issue title for branch naming
        logger: Optional logger instance

    Returns:
        Tuple of (chore_result, implement_result)

    Example:
        chore_result, impl_result = await trigger_reimplementation(
            issue_number=42,
            original_prompt="Add rate limiting",
            review_feedback="Fix validation issues",
            adw_id="new-adw-id",
            model="sonnet",
            working_dir="/path/to/repo",
            repo_owner="myorg",
            repo_name="myrepo",
            issue_title="Add rate limiting"
        )
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Build enhanced prompt with review feedback
    enhanced_prompt = f"""# Original Task
{original_prompt}

# Review Feedback
The previous implementation was reviewed and requires changes. Please address the following feedback:

{review_feedback}

# Instructions
Re-implement the task above, making sure to address all review feedback. Pay special attention to the issues identified in the review.
"""

    logger.info(f"Triggering re-implementation for issue #{issue_number} with ADW ID {adw_id}")

    # Trigger the chore + implement workflow
    chore_result, impl_result = await trigger_chore_implement_workflow(
        prompt=enhanced_prompt,
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
        issue_number=issue_number,
        repo_owner=repo_owner,
        repo_name=repo_name,
        issue_title=issue_title,
    )

    return chore_result, impl_result


async def handle_review_results(
    review_result: WorkflowResult,
    pr_number: int,
    issue_numbers: list[int],
    repo_full_name: str,
    original_prompt: str,
    issue_title: str,
    model: str,
    working_dir: str,
    logger: Optional[logging.Logger] = None
) -> dict:
    """Handle review results and take appropriate action.

    Args:
        review_result: The workflow result from the review
        pr_number: Pull request number
        issue_numbers: List of linked issue numbers
        repo_full_name: Full repository name (owner/repo)
        original_prompt: Original issue prompt
        issue_title: Issue title
        model: Model to use (sonnet/opus)
        working_dir: Working directory path
        logger: Optional logger instance

    Returns:
        Dictionary with action taken and status

    Example:
        result = await handle_review_results(
            review_result=review_result,
            pr_number=42,
            issue_numbers=[1, 2],
            repo_full_name="myorg/myrepo",
            original_prompt="Add feature",
            issue_title="Add feature",
            model="sonnet",
            working_dir="/path/to/repo"
        )
        print(f"Action: {result['action']}, Success: {result['success']}")
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Parse repository info
    try:
        repo_owner, repo_name = repo_full_name.split("/")
    except ValueError:
        logger.error(f"Invalid repo_full_name format: {repo_full_name}")
        return {
            "action": "error",
            "success": False,
            "error": "Invalid repository name format"
        }

    # Parse review status
    approval_status, summary, recommendations = parse_review_status(review_result.output)
    issues = extract_review_issues(review_result.output)

    logger.info(f"Review status: {approval_status}")

    result = {
        "action": approval_status.lower(),
        "success": False,
        "approval_status": approval_status,
        "summary": summary,
        "recommendations": recommendations,
        "issues": issues,
    }

    # Get configuration settings
    config = get_config()
    auto_merge_enabled = config.auto_merge_on_approval
    auto_reimplement_enabled = config.auto_reimplement_on_changes
    merge_method = config.merge_method

    if approval_status == "APPROVED" and auto_merge_enabled:
        # Merge the PR
        logger.info(f"Review approved, attempting to merge PR #{pr_number}")
        merge_success = merge_pull_request(pr_number, repo_owner, repo_name, merge_method=merge_method, logger=logger)
        result["success"] = merge_success
        result["merge_attempted"] = True

        # Reset re-implementation attempts on successful merge
        if merge_success and issue_numbers:
            for issue_num in issue_numbers:
                reset_reimplement_attempts(issue_num)

        # Post comment about merge status
        for issue_num in issue_numbers:
            try:
                post_merge_comment(
                    issue_number=issue_num,
                    repo_full_name=repo_full_name,
                    pr_number=pr_number,
                    pr_url=f"https://github.com/{repo_full_name}/pull/{pr_number}",
                    adw_id=review_result.adw_id,
                    merge_success=merge_success,
                    error_message=None if merge_success else "Merge failed",
                )
            except Exception as e:
                logger.error(f"Failed to post merge comment to issue #{issue_num}: {e}")

    elif approval_status == "CHANGES_REQUESTED" and auto_reimplement_enabled:
        # Check loop protection
        primary_issue = issue_numbers[0] if issue_numbers else 0
        allowed, current_count = check_reimplement_attempts(
            primary_issue,
            max_attempts=config.max_reimplement_attempts
        )

        if not allowed:
            logger.warning(
                f"Maximum re-implementation attempts ({config.max_reimplement_attempts}) "
                f"reached for issue #{primary_issue}, skipping auto-reimplement"
            )
            result["action"] = "max_attempts_reached"
            result["success"] = False
            result["attempt_count"] = current_count

            # Post comment about max attempts
            from apps.adw_server.core.handlers import make_github_issue_comment

            max_attempts_comment = (
                f"⚠️ **Maximum Re-Implementation Attempts Reached**\n\n"
                f"**Attempts:** {current_count}/{config.max_reimplement_attempts}\n\n"
                f"The automatic re-implementation workflow has been attempted {current_count} times "
                f"for this issue. To prevent infinite loops, manual intervention is now required.\n\n"
                f"**Next Steps:**\n"
                f"- Review the previous implementation attempts\n"
                f"- Address the issues manually\n"
                f"- Consider if the requirements need clarification\n"
                f"- Close and re-open the issue to reset the counter if needed"
            )

            for issue_num in issue_numbers:
                try:
                    make_github_issue_comment(
                        issue_number=issue_num,
                        comment=max_attempts_comment,
                        repo_owner=repo_owner,
                        repo_name=repo_name,
                    )
                except Exception as e:
                    logger.error(f"Failed to post max attempts comment to issue #{issue_num}: {e}")

            return result

        # Trigger re-implementation
        logger.info(f"Changes requested, triggering re-implementation for PR #{pr_number}")

        # Increment attempt counter
        new_count = increment_reimplement_attempts(primary_issue)
        result["attempt_count"] = new_count

        # Format review feedback
        feedback_parts = []
        if summary:
            feedback_parts.append(f"## Summary\n{summary}\n")

        if any(issues.values()):
            feedback_parts.append("## Issues Found\n")
            for severity in ["Critical", "Moderate", "Minor"]:
                if issues[severity]:
                    feedback_parts.append(f"### {severity}\n")
                    for issue in issues[severity]:
                        feedback_parts.append(f"- {issue}\n")

        if recommendations:
            feedback_parts.append("## Recommendations\n")
            for i, rec in enumerate(recommendations, 1):
                feedback_parts.append(f"{i}. {rec}\n")

        review_feedback = "\n".join(feedback_parts)

        # Generate new ADW ID for re-implementation
        from apps.adw_server.core.adw_integration import generate_short_id
        new_adw_id = generate_short_id()

        try:
            chore_result, impl_result = await trigger_reimplementation(
                issue_number=primary_issue,
                original_prompt=original_prompt,
                review_feedback=review_feedback,
                adw_id=new_adw_id,
                model=model,
                working_dir=working_dir,
                repo_owner=repo_owner,
                repo_name=repo_name,
                issue_title=issue_title,
                logger=logger,
            )

            result["success"] = chore_result.success
            result["reimplementation_attempted"] = True
            result["new_adw_id"] = new_adw_id
            result["chore_result"] = chore_result
            result["impl_result"] = impl_result

            # Post re-implementation comment
            for issue_num in issue_numbers:
                try:
                    post_reimplementation_comment(
                        issue_number=issue_num,
                        repo_full_name=repo_full_name,
                        review_adw_id=review_result.adw_id,
                        new_adw_id=new_adw_id,
                        review_feedback=review_feedback[:500],  # Truncate if too long
                    )
                except Exception as e:
                    logger.error(f"Failed to post reimplementation comment to issue #{issue_num}: {e}")

        except Exception as e:
            logger.error(f"Error triggering re-implementation: {e}", exc_info=True)
            result["success"] = False
            result["error"] = str(e)

    else:
        # NEEDS_DISCUSSION or auto-actions disabled
        logger.info(f"Review needs discussion or auto-actions disabled, posting results only")
        result["action"] = "comment_only"
        result["success"] = True

        # The review results are already posted by handle_pull_request_event
        # No additional action needed here

    return result


def post_merge_comment(
    issue_number: int,
    repo_full_name: str,
    pr_number: int,
    pr_url: str,
    adw_id: str,
    merge_success: bool,
    error_message: Optional[str] = None
) -> bool:
    """Post a comment about merge success or failure.

    Args:
        issue_number: GitHub issue number
        repo_full_name: Full repository name (owner/repo)
        pr_number: Pull request number
        pr_url: Pull request URL
        adw_id: ADW workflow ID
        merge_success: Whether merge succeeded
        error_message: Optional error message if merge failed

    Returns:
        True if comment posted successfully, False otherwise
    """
    from apps.adw_server.core.handlers import make_github_issue_comment

    try:
        repo_owner, repo_name = repo_full_name.split("/")
    except ValueError:
        logger.error(f"Invalid repo_full_name format: {repo_full_name}")
        return False

    if merge_success:
        comment = (
            f"✅ **PR Merged Successfully**\n\n"
            f"**PR:** [#{pr_number}]({pr_url})\n"
            f"**ADW ID:** `{adw_id}`\n\n"
            f"The pull request has been automatically merged after passing review. "
            f"Great work! 🎉"
        )
    else:
        comment = (
            f"⚠️ **Automatic Merge Failed**\n\n"
            f"**PR:** [#{pr_number}]({pr_url})\n"
            f"**ADW ID:** `{adw_id}`\n\n"
            f"The pull request was approved but automatic merge failed.\n\n"
        )
        if error_message:
            comment += f"**Error:**\n```\n{error_message}\n```\n\n"

        comment += (
            f"**Next Steps:**\n"
            f"- Check for merge conflicts\n"
            f"- Ensure all required checks have passed\n"
            f"- Try merging manually or re-running the workflow"
        )

    try:
        make_github_issue_comment(
            issue_number=issue_number,
            comment=comment,
            repo_owner=repo_owner,
            repo_name=repo_name,
        )
        logger.info(f"Posted merge status comment to issue #{issue_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to post merge comment to issue #{issue_number}: {e}")
        return False


def post_reimplementation_comment(
    issue_number: int,
    repo_full_name: str,
    review_adw_id: str,
    new_adw_id: str,
    review_feedback: str
) -> bool:
    """Post a comment about re-implementation being started.

    Args:
        issue_number: GitHub issue number
        repo_full_name: Full repository name (owner/repo)
        review_adw_id: Original review ADW ID
        new_adw_id: New re-implementation ADW ID
        review_feedback: Summary of review feedback

    Returns:
        True if comment posted successfully, False otherwise
    """
    from apps.adw_server.core.handlers import make_github_issue_comment

    try:
        repo_owner, repo_name = repo_full_name.split("/")
    except ValueError:
        logger.error(f"Invalid repo_full_name format: {repo_full_name}")
        return False

    comment = (
        f"🔄 **Re-Implementation Started**\n\n"
        f"**Review ADW ID:** `{review_adw_id}`\n"
        f"**New ADW ID:** `{new_adw_id}`\n\n"
        f"The previous implementation received change requests. "
        f"A new implementation cycle has been started to address the review feedback.\n\n"
        f"**Review Feedback:**\n{review_feedback}\n\n"
        f"Results will be posted when the re-implementation completes."
    )

    try:
        make_github_issue_comment(
            issue_number=issue_number,
            comment=comment,
            repo_owner=repo_owner,
            repo_name=repo_name,
        )
        logger.info(f"Posted re-implementation start comment to issue #{issue_number}")
        return True
    except Exception as e:
        logger.error(f"Failed to post re-implementation comment to issue #{issue_number}: {e}")
        return False
