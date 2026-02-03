"""GitHub integration using gh CLI."""

import json
import os
import subprocess
from typing import Dict, List, Optional

from .data_types import GitHubIssue, GitHubComment

# Bot identifier to prevent webhook loops
ADW_BOT_IDENTIFIER = "[ADW-AGENTS]"


def get_github_env() -> Dict[str, str]:
    """Get filtered environment variables for GitHub CLI.

    Returns only GH_TOKEN, GITHUB_TOKEN, and PATH to prevent leakage.

    Returns:
        Dictionary with filtered environment variables
    """
    safe_env = {}

    # GitHub tokens
    if os.getenv("GH_TOKEN"):
        safe_env["GH_TOKEN"] = os.getenv("GH_TOKEN")
    if os.getenv("GITHUB_TOKEN"):
        safe_env["GITHUB_TOKEN"] = os.getenv("GITHUB_TOKEN")

    # PATH for finding gh executable
    if os.getenv("PATH"):
        safe_env["PATH"] = os.getenv("PATH")

    # HOME might be needed for gh config
    if os.getenv("HOME"):
        safe_env["HOME"] = os.getenv("HOME")

    return safe_env


def fetch_issue(
    issue_number: int, repo_owner: str, repo_name: str
) -> Optional[GitHubIssue]:
    """Fetch issue from GitHub via gh CLI.

    Args:
        issue_number: Issue number
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        GitHubIssue instance or None if error
    """
    try:
        # Fetch issue data
        cmd = [
            "gh",
            "api",
            f"repos/{repo_owner}/{repo_name}/issues/{issue_number}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=get_github_env(),
        )

        if result.returncode != 0:
            return None

        issue_data = json.loads(result.stdout)

        # Fetch comments
        comments = fetch_issue_comments(issue_number, repo_owner, repo_name)

        # Parse labels
        labels = [label["name"] for label in issue_data.get("labels", [])]

        # Parse assignees
        assignees = [assignee["login"] for assignee in issue_data.get("assignees", [])]

        return GitHubIssue(
            number=issue_data["number"],
            title=issue_data["title"],
            body=issue_data.get("body", ""),
            state=issue_data["state"],
            labels=labels,
            assignees=assignees,
            comments=comments,
            created_at=issue_data.get("created_at"),
            updated_at=issue_data.get("updated_at"),
            url=issue_data.get("html_url"),
        )

    except Exception as e:
        print(f"Error fetching issue: {e}")
        return None


def fetch_issue_comments(
    issue_number: int, repo_owner: str, repo_name: str
) -> List[GitHubComment]:
    """Fetch all comments for an issue.

    Args:
        issue_number: Issue number
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        List of GitHubComment instances
    """
    try:
        cmd = [
            "gh",
            "api",
            f"repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=get_github_env(),
        )

        if result.returncode != 0:
            return []

        comments_data = json.loads(result.stdout)

        return [
            GitHubComment(
                id=comment.get("id"),
                author=comment["user"]["login"],
                body=comment["body"],
                created_at=comment["created_at"],
            )
            for comment in comments_data
        ]

    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []


def make_issue_comment(
    issue_number: int, comment: str, repo_owner: str, repo_name: str
) -> bool:
    """Post a comment on an issue with bot identifier.

    Args:
        issue_number: Issue number
        comment: Comment text
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        True if successful, False otherwise
    """
    try:
        # Prefix comment with bot identifier
        full_comment = f"{ADW_BOT_IDENTIFIER}\n\n{comment}"

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
            env=get_github_env(),
        )

        return result.returncode == 0

    except Exception as e:
        print(f"Error posting comment: {e}")
        return False


def mark_issue_in_progress(
    issue_number: int, repo_owner: str, repo_name: str
) -> bool:
    """Mark issue as in progress by adding label.

    Args:
        issue_number: Issue number
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        True if successful, False otherwise
    """
    try:
        # Add in-progress label
        cmd = [
            "gh",
            "issue",
            "edit",
            str(issue_number),
            "--add-label",
            "in-progress",
            "--repo",
            f"{repo_owner}/{repo_name}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=get_github_env(),
        )

        return result.returncode == 0

    except Exception as e:
        print(f"Error marking issue in progress: {e}")
        return False


def find_keyword_from_comment(comments: List[GitHubComment], keyword: str) -> Optional[str]:
    """Search comments for a keyword.

    Args:
        comments: List of GitHubComment instances
        keyword: Keyword to search for

    Returns:
        Comment body containing keyword or None
    """
    for comment in comments:
        if keyword.lower() in comment.body.lower():
            return comment.body

    return None
