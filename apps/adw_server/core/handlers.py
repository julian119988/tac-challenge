"""GitHub webhook handlers and validation.

This module handles GitHub webhook events, validates webhook signatures,
and routes events to appropriate ADW workflows.

The module provides:
- GitHub webhook signature validation using HMAC-SHA256
- Pydantic models for GitHub webhook payloads
- Event routing logic for issues and pull requests
- Label-based workflow mapping
- Comprehensive logging for debugging

Security:
- All webhook requests must have valid GitHub signatures
- Signatures are validated using HMAC-SHA256 with the configured secret
- Invalid signatures are rejected with 401 Unauthorized

Example:
    from apps.webhook_handlers import validate_webhook_signature, handle_issue_event

    # Validate webhook signature
    is_valid = validate_webhook_signature(
        payload_body=request_body,
        signature_header=request.headers.get("X-Hub-Signature-256"),
        secret="your-webhook-secret"
    )

    # Handle issue event
    if event_type == "issues":
        result = await handle_issue_event(payload)
"""

import hmac
import hashlib
import logging
import subprocess
import os
import time
from typing import Optional, Literal
from pydantic import BaseModel, Field

from apps.adw_server.core.adw_integration import (
    trigger_chore_workflow,
    trigger_chore_implement_workflow,
    trigger_review_workflow,
    generate_adw_id,
    WorkflowResult,
)
from apps.adw_server.core.review_actions import handle_review_results

# Configure logger
logger = logging.getLogger(__name__)

# Bot identifier for GitHub comments
ADW_BOT_IDENTIFIER = "[ADW-AGENTS]"

# Deduplication cache: Track recently processed issues to prevent duplicate workflows
# Format: {(issue_number, workflow_type): timestamp}
_workflow_dedup_cache: dict[tuple[int, str], float] = {}
DEDUP_WINDOW_SECONDS = 60  # Ignore duplicate triggers within 60 seconds

# Check if GitHub CLI and token are available
def check_github_available() -> bool:
    """Check if GitHub CLI and credentials are available."""
    try:
        # Check if gh is installed
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            return False

        # Check if we have a GitHub token
        return bool(os.getenv("GITHUB_PAT") or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

GITHUB_COMMENTS_ENABLED = check_github_available()
if GITHUB_COMMENTS_ENABLED:
    logger.info("GitHub comment integration enabled")
else:
    logger.info("GitHub comments disabled - gh CLI or token not available")


# Pydantic models for GitHub webhook payloads


class GitHubUser(BaseModel):
    """GitHub user information."""
    login: str
    id: int
    type: str = "User"


class GitHubLabel(BaseModel):
    """GitHub label information."""
    name: str
    color: str = ""


class GitHubIssue(BaseModel):
    """GitHub issue information from webhook payload."""
    number: int
    title: str
    body: Optional[str] = None
    state: str = "open"
    labels: list[GitHubLabel] = Field(default_factory=list)
    user: Optional[GitHubUser] = None
    html_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GitHubRepository(BaseModel):
    """GitHub repository information."""
    name: str
    full_name: str
    html_url: str
    default_branch: str = "main"


class IssueWebhookPayload(BaseModel):
    """GitHub issue webhook payload.

    Payload structure for 'issues' events.
    See: https://docs.github.com/en/webhooks/webhook-events-and-payloads#issues
    """
    action: str  # opened, edited, closed, reopened, labeled, unlabeled, etc.
    issue: GitHubIssue
    repository: GitHubRepository
    sender: GitHubUser


class PullRequestWebhookPayload(BaseModel):
    """GitHub pull request webhook payload.

    Payload structure for 'pull_request' events.
    See: https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
    """
    action: str  # opened, edited, closed, reopened, synchronize, etc.
    number: int
    pull_request: dict  # Simplified - can be expanded as needed
    repository: GitHubRepository
    sender: GitHubUser


# Webhook signature validation


def validate_webhook_signature(
    payload_body: bytes,
    signature_header: Optional[str],
    secret: str,
) -> bool:
    """Validate GitHub webhook signature using HMAC-SHA256.

    GitHub signs webhook payloads with the configured secret using HMAC-SHA256.
    The signature is sent in the X-Hub-Signature-256 header as 'sha256=<signature>'.

    Args:
        payload_body: Raw request body as bytes
        signature_header: Value of X-Hub-Signature-256 header
        secret: Configured webhook secret

    Returns:
        True if signature is valid, False otherwise

    Example:
        is_valid = validate_webhook_signature(
            payload_body=await request.body(),
            signature_header=request.headers.get("X-Hub-Signature-256"),
            secret=config.gh_wb_secret
        )
    """
    if not signature_header:
        logger.warning("No signature header provided in webhook request")
        return False

    # Extract signature from header (format: sha256=<hex_signature>)
    if not signature_header.startswith("sha256="):
        logger.warning(f"Invalid signature header format: {signature_header}")
        return False

    received_signature = signature_header[7:]  # Remove 'sha256=' prefix

    # Compute expected signature
    expected_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Compare signatures using constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(received_signature, expected_signature)

    if not is_valid:
        logger.warning("Webhook signature validation failed")
    else:
        logger.debug("Webhook signature validated successfully")

    return is_valid


# Event handling


def extract_repo_info(full_name: str) -> tuple[str, str]:
    """Extract owner and repo name from full_name.

    Args:
        full_name: Repository full name in format "owner/repo"

    Returns:
        Tuple of (owner, repo_name)

    Example:
        owner, repo = extract_repo_info("anthropics/tac-challenge")
        # Returns: ("anthropics", "tac-challenge")
    """
    parts = full_name.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid repository full_name format: {full_name}")
    return parts[0], parts[1]


def extract_issue_references(pr_body: str) -> list[int]:
    """Extract issue references from PR body/description.

    Parses PR body for patterns like "Closes #123", "Fixes #456", "Resolves #789".
    Supports common GitHub issue reference keywords (case-insensitive).

    Args:
        pr_body: Pull request body/description text

    Returns:
        List of issue numbers found in the PR description

    Example:
        issues = extract_issue_references("Closes #123 and fixes #456")
        # Returns: [123, 456]
    """
    import re

    if not pr_body:
        return []

    # Pattern to match: closes/fixes/resolves #123
    # Case-insensitive, supports multiple references
    pattern = r'(?:closes|fixes|resolves)\s+#(\d+)'
    matches = re.findall(pattern, pr_body, re.IGNORECASE)

    # Convert to integers and remove duplicates
    issue_numbers = list(set(int(match) for match in matches))

    logger.debug(f"Extracted issue references from PR body: {issue_numbers}")
    return issue_numbers


def make_github_issue_comment(
    issue_number: int,
    comment: str,
    repo_owner: str,
    repo_name: str,
) -> bool:
    """Post a comment to a GitHub issue using gh CLI.

    Args:
        issue_number: GitHub issue number
        comment: Comment text to post
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        True if comment was posted successfully, False otherwise
    """
    try:
        # Prefix comment with bot identifier
        full_comment = f"{ADW_BOT_IDENTIFIER}\n\n{comment}"

        # Build GitHub env with token
        env = os.environ.copy()
        if os.getenv("GITHUB_PAT"):
            env["GH_TOKEN"] = os.getenv("GITHUB_PAT")

        cmd = [
            "gh",
            "issue",
            "comment",
            str(issue_number),
            "--body",
            full_comment,
            "--repo",
            f"{repo_owner}/{repo_name}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        return result.returncode == 0

    except Exception as e:
        logger.error(f"Error posting GitHub comment: {e}")
        return False


def post_workflow_comment(
    issue_number: int,
    repo_full_name: str,
    comment: str,
) -> bool:
    """Post a comment to a GitHub issue.

    Args:
        issue_number: GitHub issue number
        repo_full_name: Repository full name in format "owner/repo"
        comment: Comment text to post

    Returns:
        True if comment was posted successfully, False otherwise
    """
    logger.info(f"→ post_workflow_comment called: issue=#{issue_number}, repo={repo_full_name}, comment_preview={comment[:100]}...")

    if not GITHUB_COMMENTS_ENABLED:
        logger.warning(f"⚠️ GitHub comments disabled - skipping comment on issue #{issue_number}")
        logger.warning(f"   GITHUB_COMMENTS_ENABLED={GITHUB_COMMENTS_ENABLED}")
        logger.warning(f"   GITHUB_PAT env var present: {bool(os.getenv('GITHUB_PAT'))}")
        logger.warning(f"   GH_TOKEN env var present: {bool(os.getenv('GH_TOKEN'))}")
        logger.warning(f"   GITHUB_TOKEN env var present: {bool(os.getenv('GITHUB_TOKEN'))}")
        return False

    try:
        owner, repo = extract_repo_info(repo_full_name)
        logger.info(f"   Extracted: owner={owner}, repo={repo}")
        logger.info(f"   Calling make_github_issue_comment...")
        success = make_github_issue_comment(issue_number, comment, owner, repo)
        if success:
            logger.info(f"✓ Posted comment to issue #{issue_number}")
        else:
            logger.warning(f"✗ Failed to post comment to issue #{issue_number}")
        return success
    except Exception as e:
        logger.error(f"✗ Error posting comment to issue #{issue_number}: {e}", exc_info=True)
        return False


def get_label_names(issue: GitHubIssue) -> list[str]:
    """Extract label names from issue.

    Args:
        issue: GitHub issue object

    Returns:
        List of label names
    """
    return [label.name for label in issue.labels]


def should_trigger_workflow(
    issue_number: int,
    workflow_type: str,
) -> bool:
    """Check if workflow should be triggered based on deduplication cache.

    Prevents duplicate workflows from firing when GitHub sends multiple
    webhook events for the same issue (e.g., 'opened' + 'labeled').

    Args:
        issue_number: GitHub issue number
        workflow_type: Type of workflow (chore, chore_implement)

    Returns:
        True if workflow should be triggered, False if recently triggered
    """
    cache_key = (issue_number, workflow_type)
    current_time = time.time()

    # Clean old entries from cache (older than dedup window)
    expired_keys = [
        key for key, timestamp in _workflow_dedup_cache.items()
        if current_time - timestamp > DEDUP_WINDOW_SECONDS
    ]
    for key in expired_keys:
        del _workflow_dedup_cache[key]

    # Check if this workflow was recently triggered
    if cache_key in _workflow_dedup_cache:
        last_trigger = _workflow_dedup_cache[cache_key]
        time_since = current_time - last_trigger
        if time_since < DEDUP_WINDOW_SECONDS:
            logger.warning(
                f"⚠️ Skipping duplicate workflow trigger for issue #{issue_number} "
                f"(workflow_type={workflow_type}, last_trigger={time_since:.1f}s ago)"
            )
            return False

    # Mark as triggered
    _workflow_dedup_cache[cache_key] = current_time
    return True


def determine_workflow_for_issue(
    issue: GitHubIssue,
    action: str,
) -> Optional[tuple[Literal["chore", "chore_implement"], str]]:
    """Determine which ADW workflow to trigger for an issue event.

    Maps issue labels and actions to appropriate ADW workflows:
    - 'bug' label → chore_implement (plan and implement immediately)
    - 'implement' label → chore_implement (plan and implement immediately)
    - 'feature' label → chore (plan only, await manual approval)
    - 'chore' label → chore (plan only)
    - 'plan' label → chore (plan only)
    - Other labels → No workflow

    Note: Includes deduplication to prevent duplicate workflows when GitHub
    sends both 'opened' and 'labeled' events for the same issue.

    Args:
        issue: GitHub issue object
        action: Issue action (opened, labeled, etc.)

    Returns:
        Tuple of (workflow_type, prompt) if workflow should be triggered,
        None if no workflow should be triggered

    Example:
        workflow = determine_workflow_for_issue(issue, "opened")
        if workflow:
            workflow_type, prompt = workflow
    """
    # Only trigger on opened or labeled actions
    if action not in ["opened", "labeled"]:
        logger.debug(f"Skipping issue #{issue.number} action: {action}")
        return None

    labels = get_label_names(issue)
    logger.info(f"Issue #{issue.number} labels: {labels}")

    # Build prompt from issue
    prompt = f"Issue #{issue.number}: {issue.title}"
    if issue.body:
        # Truncate body if too long
        body_preview = issue.body[:500] + "..." if len(issue.body) > 500 else issue.body
        prompt += f"\n\n{body_preview}"

    # Determine workflow based on labels
    workflow_type = None

    if "bug" in labels:
        # Bug issues get immediate implementation
        workflow_type = "chore_implement"
        logger.info(f"Issue #{issue.number} is a bug - workflow: {workflow_type}")

    elif "implement" in labels:
        # Implement label triggers full workflow (plan + implement)
        workflow_type = "chore_implement"
        logger.info(f"Issue #{issue.number} has implement label - workflow: {workflow_type}")

    elif "feature" in labels:
        # Feature issues get planning only (manual approval for implementation)
        workflow_type = "chore"
        logger.info(f"Issue #{issue.number} is a feature - workflow: {workflow_type}")

    elif "chore" in labels or "plan" in labels:
        # Chore/plan issues get planning only
        workflow_type = "chore"
        logger.info(f"Issue #{issue.number} is a chore/plan - workflow: {workflow_type}")

    else:
        # No matching labels
        logger.info(f"Issue #{issue.number} has no matching labels - skipping workflow")
        return None

    # Check deduplication cache before triggering
    if not should_trigger_workflow(issue.number, workflow_type):
        return None

    return (workflow_type, prompt)


async def handle_issue_event(
    payload: IssueWebhookPayload,
    working_dir: Optional[str] = None,
    model: Literal["sonnet", "opus"] = "sonnet",
) -> dict:
    """Handle GitHub issue webhook event.

    Routes issue events to appropriate ADW workflows based on labels.

    Args:
        payload: Parsed issue webhook payload
        working_dir: Working directory for ADW execution
        model: Model to use for ADW workflows

    Returns:
        Dictionary with handling status and results

    Example:
        result = await handle_issue_event(payload)
        if result["workflow_triggered"]:
            print(f"Workflow started: {result['adw_id']}")
    """
    issue = payload.issue
    action = payload.action

    logger.info(
        f"Handling issue event: #{issue.number} '{issue.title}' "
        f"action={action} labels={get_label_names(issue)}"
    )

    # Determine workflow
    workflow_info = determine_workflow_for_issue(issue, action)

    if not workflow_info:
        return {
            "workflow_triggered": False,
            "reason": "No matching workflow for this issue event",
            "issue_number": issue.number,
        }

    workflow_type, prompt = workflow_info

    # Generate unique ADW ID for this webhook trigger
    adw_id = generate_adw_id()

    # Get label that triggered the workflow
    labels = get_label_names(issue)
    trigger_label = None
    for label in ["bug", "implement", "feature", "chore", "plan"]:
        if label in labels:
            trigger_label = label
            break

    logger.info(
        f"Triggering {workflow_type} workflow for issue #{issue.number}, "
        f"adw_id={adw_id}"
    )

    # Post initial comment about workflow detection
    repo_full_name = payload.repository.full_name
    logger.info(f"📝 Posting initial workflow comment to issue #{issue.number}")
    comment_posted = post_workflow_comment(
        issue.number,
        repo_full_name,
        f"🤖 **Workflow Detected: `{trigger_label}` label**\n\n"
        f"**ADW ID:** `{adw_id}`\n"
        f"**Workflow:** `{workflow_type}`\n"
        f"**Model:** `{model}`\n\n"
        f"⏳ Initializing workflow execution...\n\n"
        f"Logs will be available at: `agents/{adw_id}/planner/`"
    )
    logger.info(f"   Initial comment posted: {comment_posted}")

    # Trigger appropriate workflow
    if workflow_type == "chore":
        logger.info(f"🚀 Starting chore workflow for issue #{issue.number}")

        try:
            result = await trigger_chore_workflow(
                prompt=prompt,
                adw_id=adw_id,
                model=model,
                working_dir=working_dir,
            )
            logger.info(f"✓ Chore workflow completed: success={result.success}, plan_path={result.plan_path}")
        except Exception as e:
            logger.error(f"💥 Exception during chore workflow: {e}", exc_info=True)

            # Post error comment to issue
            import traceback
            error_details = str(e)
            error_type = type(e).__name__

            comment_posted = post_workflow_comment(
                issue.number,
                repo_full_name,
                f"💥 **Workflow Error**\n\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Error Type:** `{error_type}`\n\n"
                f"```\n{error_details}\n```\n\n"
                f"The workflow encountered an unexpected error. Check server logs for details.\n\n"
                f"**Logs location:** `agents/{adw_id}/planner/`"
            )
            logger.info(f"   Error comment posted: {comment_posted}")

            return {
                "workflow_triggered": True,
                "workflow_type": "chore",
                "issue_number": issue.number,
                "adw_id": adw_id,
                "success": False,
                "error": error_details,
                "error_type": error_type,
            }

        # Post completion comment
        logger.info(f"📝 Posting chore completion comment to issue #{issue.number}")
        if result.success:
            comment_posted = post_workflow_comment(
                issue.number,
                repo_full_name,
                f"✅ **Planning Complete**\n\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Plan Created:** `{result.plan_path}`\n\n"
                f"The implementation plan has been created. Review the plan and run `/implement {result.plan_path}` when ready."
            )
            logger.info(f"   Completion comment posted: {comment_posted}")
        else:
            comment_posted = post_workflow_comment(
                issue.number,
                repo_full_name,
                f"❌ **Planning Failed**\n\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Error:** {result.error_message}\n\n"
                f"Check logs at: `agents/{adw_id}/planner/`"
            )
            logger.info(f"   Error comment posted: {comment_posted}")

        return {
            "workflow_triggered": True,
            "workflow_type": "chore",
            "issue_number": issue.number,
            "adw_id": adw_id,
            "success": result.success,
            "plan_path": result.plan_path,
            "output_dir": result.output_dir,
            "error_message": result.error_message,
        }

    elif workflow_type == "chore_implement":
        logger.info(f"🚀 Starting chore_implement workflow for issue #{issue.number}")

        # Extract repo owner and name from full_name (e.g., "owner/repo")
        repo_parts = repo_full_name.split("/")
        repo_owner = repo_parts[0] if len(repo_parts) > 0 else None
        repo_name = repo_parts[1] if len(repo_parts) > 1 else None

        try:
            chore_result, impl_result = await trigger_chore_implement_workflow(
                prompt=prompt,
                adw_id=adw_id,
                model=model,
                working_dir=working_dir,
                issue_number=issue.number,
                repo_owner=repo_owner,
                repo_name=repo_name,
                issue_title=issue.title,
            )
            logger.info(f"✓ Chore_implement workflow completed: chore_success={chore_result.success}, impl_success={impl_result.success if impl_result else None}")
        except Exception as e:
            logger.error(f"💥 Exception during chore_implement workflow: {e}", exc_info=True)

            # Post error comment to issue
            import traceback
            error_details = str(e)
            error_type = type(e).__name__

            comment_posted = post_workflow_comment(
                issue.number,
                repo_full_name,
                f"💥 **Workflow Error**\n\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Error Type:** `{error_type}`\n\n"
                f"```\n{error_details}\n```\n\n"
                f"The workflow encountered an unexpected error. Check server logs for details.\n\n"
                f"**Logs location:** `agents/{adw_id}/`"
            )
            logger.info(f"   Error comment posted: {comment_posted}")

            return {
                "workflow_triggered": True,
                "workflow_type": "chore_implement",
                "issue_number": issue.number,
                "adw_id": adw_id,
                "success": False,
                "error": error_details,
                "error_type": error_type,
            }

        # Post completion comment based on results
        logger.info(f"📝 Posting chore_implement completion comment to issue #{issue.number}")
        if chore_result.success and impl_result and impl_result.success:
            # Check if PR URL is in output
            pr_url = None
            if impl_result.output and "Pull Request:" in impl_result.output:
                import re
                match = re.search(r"Pull Request: (https://[^\s]+)", impl_result.output)
                if match:
                    pr_url = match.group(1)

            if pr_url:
                comment_text = (
                    f"✅ **Full Workflow Complete**\n\n"
                    f"Successfully implemented: **{issue.title}**\n\n"
                    f"## Pull Request Created\n"
                    f"🔗 {pr_url}\n\n"
                    f"The PR includes a detailed summary of code changes and files modified.\n\n"
                    f"## Summary\n"
                    f"✓ Planning completed\n"
                    f"✓ Implementation completed\n"
                    f"✓ Pull request created\n\n"
                    f"## Details\n"
                    f"- **ADW ID:** `{adw_id}`\n"
                    f"- **Plan:** `{chore_result.plan_path}`\n"
                    f"- **Model:** `{model}`\n\n"
                    f"**Next Steps:** Please review the pull request and merge when ready."
                )
            else:
                comment_text = (
                    f"✅ **Full Workflow Complete**\n\n"
                    f"Successfully implemented: **{issue.title}**\n\n"
                    f"## Summary\n"
                    f"✓ Planning completed\n"
                    f"✓ Implementation completed\n\n"
                    f"## Details\n"
                    f"- **ADW ID:** `{adw_id}`\n"
                    f"- **Plan:** `{chore_result.plan_path}`\n"
                    f"- **Model:** `{model}`\n\n"
                    f"⚠️ **Note:** PR creation was not attempted or failed. Please review the changes manually."
                )

            comment_posted = post_workflow_comment(
                issue.number,
                repo_full_name,
                comment_text
            )
            logger.info(f"   Success comment posted: {comment_posted}")
        elif chore_result.success and (not impl_result or not impl_result.success):
            comment_posted = post_workflow_comment(
                issue.number,
                repo_full_name,
                f"⚠️ **Partial Success**\n\n"
                f"**ADW ID:** `{adw_id}`\n\n"
                f"✓ Planning completed: `{chore_result.plan_path}`\n"
                f"✗ Implementation failed\n\n"
                f"**Error:** {impl_result.error_message if impl_result else 'Implementation did not run'}\n\n"
                f"Check logs at: `agents/{adw_id}/`"
            )
            logger.info(f"   Partial success comment posted: {comment_posted}")
        else:
            comment_posted = post_workflow_comment(
                issue.number,
                repo_full_name,
                f"❌ **Workflow Failed**\n\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Error:** {chore_result.error_message}\n\n"
                f"Check logs at: `agents/{adw_id}/planner/`"
            )
            logger.info(f"   Failure comment posted: {comment_posted}")

        return {
            "workflow_triggered": True,
            "workflow_type": "chore_implement",
            "issue_number": issue.number,
            "adw_id": adw_id,
            "chore_success": chore_result.success,
            "implement_success": impl_result.success if impl_result else False,
            "plan_path": chore_result.plan_path,
            "output_dir": chore_result.output_dir,
            "error_message": chore_result.error_message or (
                impl_result.error_message if impl_result else None
            ),
        }

    return {
        "workflow_triggered": False,
        "reason": "Unknown workflow type",
        "issue_number": issue.number,
    }


async def handle_pull_request_event(
    payload: PullRequestWebhookPayload,
    working_dir: Optional[str] = None,
    model: Literal["sonnet", "opus"] = "sonnet",
) -> dict:
    """Handle GitHub pull request webhook event.

    Triggers automated PR review workflow when a PR is opened or updated.
    The review workflow analyzes code, runs tests, and posts results to
    the linked issue thread.

    Args:
        payload: Parsed pull request webhook payload
        working_dir: Working directory for ADW execution
        model: Model to use for ADW workflows

    Returns:
        Dictionary with handling status and workflow results

    Example:
        result = await handle_pull_request_event(payload)
    """
    pr_number = payload.number
    action = payload.action
    repo_full_name = payload.repository.full_name

    logger.info(
        f"Handling pull request event: #{pr_number} action={action} repo={repo_full_name}"
    )

    # Only trigger review for opened and synchronize (new commits) actions
    if action not in ["opened", "synchronize"]:
        logger.info(f"Skipping PR review for action: {action}")
        return {
            "workflow_triggered": False,
            "reason": f"PR action '{action}' does not trigger review workflow",
            "pr_number": pr_number,
            "action": action,
        }

    # Extract PR body to find issue references
    pr_body = payload.pull_request.get("body", "")
    pr_html_url = payload.pull_request.get("html_url", f"https://github.com/{repo_full_name}/pull/{pr_number}")

    # Extract issue references from PR body
    issue_numbers = extract_issue_references(pr_body)

    if not issue_numbers:
        logger.info(f"No issue references found in PR #{pr_number} body, skipping review workflow")
        return {
            "workflow_triggered": False,
            "reason": "No issue references found in PR body",
            "pr_number": pr_number,
            "action": action,
        }

    logger.info(f"Found issue references in PR #{pr_number}: {issue_numbers}")

    # Generate unique ADW ID for this review workflow
    adw_id = generate_adw_id()

    # Extract repo owner and name
    try:
        repo_owner, repo_name = extract_repo_info(repo_full_name)
    except ValueError as e:
        logger.error(f"Invalid repository full_name: {e}")
        return {
            "workflow_triggered": False,
            "reason": f"Invalid repository name: {str(e)}",
            "pr_number": pr_number,
            "action": action,
        }

    # Post initial comment to issue thread(s) indicating review has started
    for issue_number in issue_numbers:
        initial_comment = (
            f"🔍 **Pull Request Review Started**\n\n"
            f"**PR:** [#{pr_number}]({pr_html_url})\n"
            f"**ADW ID:** `{adw_id}`\n\n"
            f"Automated review is in progress. Results will be posted shortly..."
        )
        try:
            make_github_issue_comment(
                issue_number=issue_number,
                comment=initial_comment,
                repo_owner=repo_owner,
                repo_name=repo_name,
            )
            logger.info(f"Posted review start comment to issue #{issue_number}")
        except Exception as e:
            logger.warning(f"Failed to post initial comment to issue #{issue_number}: {e}")

    # Extract PR branch information
    pr_head_ref = payload.pull_request.get("head", {}).get("ref", "")
    pr_head_sha = payload.pull_request.get("head", {}).get("sha", "")
    pr_base_ref = payload.pull_request.get("base", {}).get("ref", "main")

    logger.info(f"PR branch info: head={pr_head_ref}, sha={pr_head_sha}, base={pr_base_ref}")

    # Trigger the review workflow
    try:
        logger.info(f"Triggering review workflow for PR #{pr_number}, adw_id={adw_id}")
        review_result = await trigger_review_workflow(
            pr_number=pr_number,
            repo_full_name=repo_full_name,
            adw_id=adw_id,
            model=model,
            working_dir=working_dir,
            pr_head_ref=pr_head_ref,
            pr_head_sha=pr_head_sha,
            pr_base_ref=pr_base_ref,
        )

        # Format review results for comment
        review_comment = format_review_results(
            review_output=review_result.output,
            pr_number=pr_number,
            pr_url=pr_html_url,
            adw_id=adw_id,
        )

        # Post review results to all linked issues
        for issue_number in issue_numbers:
            try:
                make_github_issue_comment(
                    issue_number=issue_number,
                    comment=review_comment,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                )
                logger.info(f"Posted review results to issue #{issue_number}")
            except Exception as e:
                logger.error(f"Failed to post review results to issue #{issue_number}: {e}")

        # Fetch issue details for re-implementation context
        original_prompt = ""
        issue_title_text = ""
        if issue_numbers:
            primary_issue = issue_numbers[0]
            try:
                logger.info(f"Fetching issue #{primary_issue} details for context")
                result = subprocess.run(
                    ["gh", "issue", "view", str(primary_issue), "--json", "title,body", "--repo", repo_full_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    import json
                    issue_data = json.loads(result.stdout)
                    issue_title_text = issue_data.get("title", "")
                    issue_body = issue_data.get("body", "")
                    original_prompt = f"# {issue_title_text}\n\n{issue_body}"
                    logger.info(f"Fetched issue #{primary_issue} context successfully")
                else:
                    logger.warning(f"Failed to fetch issue #{primary_issue}: {result.stderr}")
            except Exception as e:
                logger.warning(f"Error fetching issue details: {e}")

        # Handle review results (merge, re-implement, or comment)
        try:
            logger.info(f"Handling review results for PR #{pr_number}")
            action_result = await handle_review_results(
                review_result=review_result,
                pr_number=pr_number,
                issue_numbers=issue_numbers,
                repo_full_name=repo_full_name,
                original_prompt=original_prompt or f"Implement changes for PR #{pr_number}",
                issue_title=issue_title_text or f"PR #{pr_number}",
                model=model,
                working_dir=working_dir,
                logger=logger,
            )
            logger.info(f"Review action completed: {action_result.get('action')}, success={action_result.get('success')}")

            return {
                "workflow_triggered": True,
                "workflow_type": "review",
                "pr_number": pr_number,
                "action": action,
                "adw_id": adw_id,
                "success": review_result.success,
                "issue_numbers": issue_numbers,
                "error_message": review_result.error_message,
                "review_action": action_result,
            }
        except Exception as e:
            logger.error(f"Error handling review results: {e}", exc_info=True)
            # Don't fail the whole workflow if action handling fails
            return {
                "workflow_triggered": True,
                "workflow_type": "review",
                "pr_number": pr_number,
                "action": action,
                "adw_id": adw_id,
                "success": review_result.success,
                "issue_numbers": issue_numbers,
                "error_message": review_result.error_message,
                "review_action_error": str(e),
            }

    except Exception as e:
        logger.error(f"Error executing review workflow for PR #{pr_number}: {e}", exc_info=True)

        # Post error comment to issue threads
        error_comment = (
            f"🔍 **Pull Request Review Failed**\n\n"
            f"**PR:** [#{pr_number}]({pr_html_url})\n"
            f"**ADW ID:** `{adw_id}`\n\n"
            f"❌ Review workflow encountered an error:\n"
            f"```\n{str(e)}\n```\n\n"
            f"Please check the logs for details: `agents/{adw_id}/reviewer/`"
        )

        for issue_number in issue_numbers:
            try:
                make_github_issue_comment(
                    issue_number=issue_number,
                    comment=error_comment,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                )
                logger.info(f"Posted error comment to issue #{issue_number}")
            except Exception as post_error:
                logger.error(f"Failed to post error comment to issue #{issue_number}: {post_error}")

        return {
            "workflow_triggered": True,
            "workflow_type": "review",
            "pr_number": pr_number,
            "action": action,
            "adw_id": adw_id,
            "success": False,
            "issue_numbers": issue_numbers,
            "error_message": str(e),
        }


def format_review_results(
    review_output: str,
    pr_number: int,
    pr_url: str,
    adw_id: str,
) -> str:
    """Format review workflow results for posting as an issue comment.

    Parses review workflow output for key information and creates a
    formatted markdown comment with review summary, test results, and metadata.

    Args:
        review_output: Output from the review workflow
        pr_number: Pull request number
        pr_url: Pull request URL
        adw_id: ADW workflow ID

    Returns:
        Formatted markdown string ready for GitHub comment posting

    Example:
        comment = format_review_results(
            review_output="Review completed...",
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            adw_id="abc12345"
        )
    """
    # Parse review output for key information
    # Look for test results, review status, etc.
    import re

    # Try to extract test results from output
    test_summary = ""
    if "test" in review_output.lower():
        # Look for common test result patterns
        test_match = re.search(r'(\d+)\s+passed', review_output, re.IGNORECASE)
        fail_match = re.search(r'(\d+)\s+failed', review_output, re.IGNORECASE)

        if test_match or fail_match:
            passed = test_match.group(1) if test_match else "0"
            failed = fail_match.group(1) if fail_match else "0"
            test_summary = f"\n### Test Results\n✅ {passed} passed | ❌ {failed} failed\n"

    # Try to extract approval status
    approval_status = ""
    if "APPROVED" in review_output:
        approval_status = "✅ **APPROVED**"
    elif "CHANGES REQUESTED" in review_output or "CHANGES_REQUESTED" in review_output:
        approval_status = "⚠️ **CHANGES REQUESTED**"
    elif "NEEDS DISCUSSION" in review_output or "NEEDS_DISCUSSION" in review_output:
        approval_status = "💬 **NEEDS DISCUSSION**"

    # Build formatted comment
    comment_parts = [
        "🔍 **Pull Request Review**\n",
        f"**PR:** [#{pr_number}]({pr_url})\n",
        f"**ADW ID:** `{adw_id}`\n\n",
    ]

    if approval_status:
        comment_parts.append(f"**Status:** {approval_status}\n\n")

    if test_summary:
        comment_parts.append(test_summary)

    # Add review summary (truncate if too long)
    comment_parts.append("\n### Review Summary\n")

    # Try to extract summary section from review output
    summary_match = re.search(r'## Summary\s*\n(.*?)(?=\n##|\Z)', review_output, re.DOTALL | re.IGNORECASE)
    if summary_match:
        summary_text = summary_match.group(1).strip()
        # Truncate if too long
        if len(summary_text) > 500:
            summary_text = summary_text[:500] + "...\n\n_See full review output for details._"
        comment_parts.append(f"{summary_text}\n")
    else:
        # No summary section found, provide generic message
        comment_parts.append("Code review completed. Check the review output for details.\n")

    # Add metadata section
    comment_parts.append(f"\n---\n")
    comment_parts.append(f"🤖 Automated review by ADW • Logs: `agents/{adw_id}/reviewer/`\n")

    return ''.join(comment_parts)


def create_workflow_comment(
    workflow_result: dict,
    issue_number: int,
) -> str:
    """Create a comment message for posting back to GitHub issue.

    This can be used to notify users about workflow execution status
    on the issue that triggered the workflow.

    Args:
        workflow_result: Result dictionary from handle_issue_event
        issue_number: GitHub issue number

    Returns:
        Formatted comment message

    Example:
        comment = create_workflow_comment(result, issue.number)
        # Post comment back to GitHub using GitHub API
    """
    if not workflow_result.get("workflow_triggered"):
        return ""

    adw_id = workflow_result.get("adw_id")
    workflow_type = workflow_result.get("workflow_type")

    if workflow_type == "chore":
        if workflow_result.get("success"):
            plan_path = workflow_result.get("plan_path")
            return (
                f"🤖 ADW Workflow Triggered\n\n"
                f"**Workflow:** Planning (`/chore`)\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Status:** ✅ Success\n"
                f"**Plan:** `{plan_path}`\n\n"
                f"The implementation plan has been created. "
                f"Review the plan and manually trigger `/implement` when ready."
            )
        else:
            return (
                f"🤖 ADW Workflow Triggered\n\n"
                f"**Workflow:** Planning (`/chore`)\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Status:** ❌ Failed\n\n"
                f"Error: {workflow_result.get('error_message', 'Unknown error')}"
            )

    elif workflow_type == "chore_implement":
        chore_success = workflow_result.get("chore_success")
        impl_success = workflow_result.get("implement_success")

        if chore_success and impl_success:
            return (
                f"🤖 ADW Workflow Triggered\n\n"
                f"**Workflow:** Full Implementation (`/chore` + `/implement`)\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Status:** ✅ Success\n\n"
                f"The issue has been planned and implemented automatically. "
                f"Please review the changes."
            )
        elif chore_success and not impl_success:
            return (
                f"🤖 ADW Workflow Triggered\n\n"
                f"**Workflow:** Full Implementation (`/chore` + `/implement`)\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Status:** ⚠️ Partial Success\n\n"
                f"Planning succeeded but implementation failed.\n"
                f"Error: {workflow_result.get('error_message', 'Unknown error')}"
            )
        else:
            return (
                f"🤖 ADW Workflow Triggered\n\n"
                f"**Workflow:** Full Implementation (`/chore` + `/implement`)\n"
                f"**ADW ID:** `{adw_id}`\n"
                f"**Status:** ❌ Failed\n\n"
                f"Error: {workflow_result.get('error_message', 'Unknown error')}"
            )

    return ""
