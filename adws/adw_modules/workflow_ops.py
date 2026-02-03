"""High-level workflow orchestration functions."""

import os
import json
from pathlib import Path
from typing import Optional
import logging

from .agent import execute_template, AgentTemplateRequest
from .data_types import GitHubIssue, IssueClassSlashCommand, ModelSet

# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"
AGENT_COMMITTER = "committer"
AGENT_REVIEWER = "reviewer"
AGENT_DOCUMENTER = "documenter"
AGENT_PATCHER = "patcher"
AGENT_TESTER = "tester"


def classify_issue(
    issue: GitHubIssue,
    adw_id: str,
    working_dir: str,
    model: str = "sonnet",
) -> Optional[IssueClassSlashCommand]:
    """Classify issue as /chore, /bug, or /feature.

    Args:
        issue: GitHub issue
        adw_id: ADW identifier
        working_dir: Working directory
        model: Model to use

    Returns:
        Issue class slash command or None
    """
    # Prepare issue JSON
    issue_json = json.dumps({
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
        "labels": issue.labels,
    })

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[issue_json],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if response.success and response.output:
        # Parse the output to extract issue class
        output = response.output.strip()
        if "/chore" in output:
            return "/chore"
        elif "/bug" in output:
            return "/bug"
        elif "/feature" in output:
            return "/feature"

    return None


def generate_branch_name(
    issue: GitHubIssue, adw_id: str, model: str = "sonnet"
) -> Optional[str]:
    """Generate branch name for issue.

    Args:
        issue: GitHub issue
        adw_id: ADW identifier
        model: Model to use

    Returns:
        Branch name or None
    """
    # Prepare issue JSON
    issue_json = json.dumps({
        "number": issue.number,
        "title": issue.title,
        "adw_id": adw_id,
    })

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_json],
        adw_id=adw_id,
        model=model,
    )

    response = execute_template(request)

    if response.success and response.output:
        # Extract branch name from output
        branch_name = response.output.strip()
        # Remove any markdown code blocks
        if "```" in branch_name:
            lines = branch_name.split("\n")
            for line in lines:
                if line and not line.startswith("```"):
                    branch_name = line.strip()
                    break

        return branch_name

    return None


def build_plan(
    issue_class: IssueClassSlashCommand,
    issue: GitHubIssue,
    adw_id: str,
    working_dir: str,
    model: str = "sonnet",
    logger: Optional[logging.Logger] = None,
) -> Optional[str]:
    """Build implementation plan using issue class slash command.

    Args:
        issue_class: Issue class (/chore, /bug, /feature)
        issue: GitHub issue
        adw_id: ADW identifier
        working_dir: Working directory
        model: Model to use
        logger: Optional logger

    Returns:
        Path to plan file or None
    """
    if logger:
        logger.info(f"Building plan using {issue_class} command")

    request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        slash_command=issue_class,
        args=[adw_id, issue.body],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if response.success and response.output:
        # Try to extract plan file path from output
        output = response.output
        if "specs/" in output:
            # Find the plan file path
            for line in output.split("\n"):
                if line.strip().startswith("specs/") and line.strip().endswith(".md"):
                    plan_file = line.strip()
                    if logger:
                        logger.info(f"Plan created: {plan_file}")
                    return plan_file

        if logger:
            logger.info("Plan created successfully")

        return "plan_created"

    if logger:
        logger.error("Failed to build plan")

    return None


def implement_plan(
    plan_file: str,
    adw_id: str,
    working_dir: str,
    model: str = "sonnet",
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Implement plan using /implement command.

    Args:
        plan_file: Path to plan file
        adw_id: ADW identifier
        working_dir: Working directory
        model: Model to use
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    if logger:
        logger.info(f"Implementing plan: {plan_file}")

    request = AgentTemplateRequest(
        agent_name=AGENT_IMPLEMENTOR,
        slash_command="/implement",
        args=[plan_file],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if response.success:
        if logger:
            logger.info("Implementation completed successfully")
        return True

    if logger:
        logger.error("Implementation failed")

    return False


def create_commit_message(
    adw_id: str, working_dir: str, model: str = "sonnet"
) -> Optional[str]:
    """Generate commit message using /commit command.

    Args:
        adw_id: ADW identifier
        working_dir: Working directory
        model: Model to use

    Returns:
        Commit message or None
    """
    request = AgentTemplateRequest(
        agent_name=AGENT_COMMITTER,
        slash_command="/commit",
        args=[],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if response.success and response.output:
        return response.output.strip()

    return None


def create_pull_request_description(
    issue: GitHubIssue,
    plan_file: str,
    adw_id: str,
    working_dir: str,
    model: str = "sonnet",
) -> tuple[Optional[str], Optional[str]]:
    """Generate PR title and description using /pull_request command.

    Args:
        issue: GitHub issue
        plan_file: Path to plan file
        adw_id: ADW identifier
        working_dir: Working directory
        model: Model to use

    Returns:
        Tuple of (pr_title, pr_body) or (None, None)
    """
    # Prepare context
    context = json.dumps({
        "issue_number": issue.number,
        "issue_title": issue.title,
        "plan_file": plan_file,
    })

    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/pull_request",
        args=[context],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if response.success and response.output:
        # Try to parse title and body from output
        output = response.output
        lines = output.split("\n")

        # First non-empty line is title
        title = None
        body_lines = []
        found_title = False

        for line in lines:
            if not found_title and line.strip():
                title = line.strip()
                found_title = True
            elif found_title:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()

        if title:
            return title, body if body else None

    return None, None


def find_spec_file(state, adw_id: str) -> Optional[str]:
    """Locate plan file from state or filesystem.

    Args:
        state: ADWState instance
        adw_id: ADW identifier

    Returns:
        Path to spec file or None
    """
    # Check state first
    if state.plan_file:
        return state.plan_file

    # Search specs directory
    project_root = Path(__file__).parent.parent.parent
    specs_dir = project_root / "specs"

    if not specs_dir.exists():
        return None

    # Look for files containing adw_id
    for spec_file in specs_dir.glob("*.md"):
        if adw_id in spec_file.name:
            return str(spec_file)

    return None


def create_and_implement_patch(
    review_feedback: str,
    adw_id: str,
    working_dir: str,
    model: str = "sonnet",
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Create and implement patch based on review feedback.

    Args:
        review_feedback: Feedback from code review
        adw_id: ADW identifier
        working_dir: Working directory
        model: Model to use
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    if logger:
        logger.info("Creating patch based on review feedback")

    request = AgentTemplateRequest(
        agent_name=AGENT_PATCHER,
        slash_command="/patch",
        args=[review_feedback],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if response.success:
        if logger:
            logger.info("Patch applied successfully")
        return True

    if logger:
        logger.error("Failed to apply patch")

    return False


def create_or_find_branch(state, issue: GitHubIssue, repo_owner: str, repo_name: str) -> Optional[str]:
    """Get branch name from state or generate new one.

    Args:
        state: ADWState instance
        issue: GitHub issue
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        Branch name or None
    """
    # Check state first
    if state.branch_name:
        return state.branch_name

    # Generate new branch name
    return generate_branch_name(issue, state.adw_id)
