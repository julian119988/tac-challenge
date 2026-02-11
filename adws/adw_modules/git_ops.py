"""Git operations and PR management."""

import subprocess
from typing import Optional
import logging

from .github import get_github_env


def get_current_branch(working_dir: str) -> Optional[str]:
    """Get current git branch.

    Args:
        working_dir: Working directory

    Returns:
        Branch name or None if error
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return None

    except Exception as e:
        print(f"Error getting current branch: {e}")
        return None


def create_branch(branch_name: str, working_dir: str) -> bool:
    """Create and checkout a new branch.

    Args:
        branch_name: Branch name
        working_dir: Working directory

    Returns:
        True if successful, False otherwise
    """
    try:
        # Try to create and checkout
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        if result.returncode == 0:
            return True

        # If branch exists, just checkout
        if "already exists" in result.stderr:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=working_dir,
            )
            return result.returncode == 0

        return False

    except Exception as e:
        print(f"Error creating branch: {e}")
        return False


def commit_changes(commit_message: str, working_dir: str, logger: Optional[logging.Logger] = None) -> bool:
    """Stage all changes and commit.

    Args:
        commit_message: Commit message
        working_dir: Working directory
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    try:
        # Stage all changes
        result = subprocess.run(
            ["git", "add", "."],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        if result.returncode != 0:
            if logger:
                logger.error(f"Failed to stage changes: {result.stderr}")
            return False

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        # If returncode is 0, there are no changes
        if result.returncode == 0:
            if logger:
                logger.info("No changes to commit")
            return True

        # Commit changes
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        if result.returncode == 0:
            if logger:
                logger.info("Changes committed successfully")
            return True

        if logger:
            logger.error(f"Failed to commit changes: {result.stderr}")
        return False

    except Exception as e:
        if logger:
            logger.error(f"Error committing changes: {e}")
        else:
            print(f"Error committing changes: {e}")
        return False


def push_branch(branch_name: str, working_dir: str, logger: Optional[logging.Logger] = None) -> bool:
    """Push branch to origin with upstream tracking.

    Args:
        branch_name: Branch name
        working_dir: Working directory
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            capture_output=True,
            text=True,
            cwd=working_dir,
        )

        if result.returncode == 0:
            if logger:
                logger.info(f"Branch {branch_name} pushed successfully")
            return True

        # Check if push failed because remote already exists
        if "already exists" in result.stderr or "up-to-date" in result.stderr:
            if logger:
                logger.info(f"Branch {branch_name} already pushed")
            return True

        if logger:
            logger.error(f"Failed to push branch: {result.stderr}")
        return False

    except Exception as e:
        if logger:
            logger.error(f"Error pushing branch: {e}")
        else:
            print(f"Error pushing branch: {e}")
        return False


def check_pr_exists(branch_name: str, repo_owner: str, repo_name: str) -> bool:
    """Check if PR exists for branch.

    Args:
        branch_name: Branch name
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        True if PR exists, False otherwise
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch_name,
                "--repo",
                f"{repo_owner}/{repo_name}",
                "--json",
                "number",
            ],
            capture_output=True,
            text=True,
            env=get_github_env(),
        )

        if result.returncode == 0:
            import json
            prs = json.loads(result.stdout)
            return len(prs) > 0

        return False

    except Exception as e:
        print(f"Error checking PR existence: {e}")
        return False


def create_pull_request(
    title: str,
    body: str,
    branch_name: str,
    issue_number: Optional[int],
    working_dir: str,
    repo_owner: str,
    repo_name: str,
    logger: Optional[logging.Logger] = None,
) -> Optional[str]:
    """Create a pull request.

    Args:
        title: PR title
        body: PR body
        branch_name: Branch name
        issue_number: Optional issue number to link
        working_dir: Working directory
        repo_owner: Repository owner
        repo_name: Repository name
        logger: Optional logger

    Returns:
        PR URL or None if error
    """
    try:
        cmd = [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--head",
            branch_name,
            "--repo",
            f"{repo_owner}/{repo_name}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=working_dir,
            env=get_github_env(),
        )

        if result.returncode == 0:
            pr_url = result.stdout.strip()
            if logger:
                logger.info(f"Pull request created: {pr_url}")
            return pr_url

        # PR might already exist
        if "already exists" in result.stderr:
            if logger:
                logger.info("Pull request already exists")
            return "already_exists"

        if logger:
            logger.error(f"Failed to create PR: {result.stderr}")
        return None

    except Exception as e:
        if logger:
            logger.error(f"Error creating PR: {e}")
        else:
            print(f"Error creating PR: {e}")
        return None


def approve_pr(pr_number: int, repo_owner: str, repo_name: str) -> bool:
    """Approve a pull request.

    Args:
        pr_number: PR number
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "review",
                str(pr_number),
                "--approve",
                "--repo",
                f"{repo_owner}/{repo_name}",
            ],
            capture_output=True,
            text=True,
            env=get_github_env(),
        )

        return result.returncode == 0

    except Exception as e:
        print(f"Error approving PR: {e}")
        return False


def merge_pr(pr_number: int, repo_owner: str, repo_name: str) -> bool:
    """Merge a pull request.

    Args:
        pr_number: PR number
        repo_owner: Repository owner
        repo_name: Repository name

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "merge",
                str(pr_number),
                "--squash",
                "--repo",
                f"{repo_owner}/{repo_name}",
            ],
            capture_output=True,
            text=True,
            env=get_github_env(),
        )

        return result.returncode == 0

    except Exception as e:
        print(f"Error merging PR: {e}")
        return False


def finalize_git_operations(
    state,
    commit_message: str,
    pr_title: str,
    pr_body: str,
    repo_owner: str,
    repo_name: str,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Orchestrate push and PR creation/update.

    Args:
        state: ADWState instance
        commit_message: Commit message
        pr_title: PR title
        pr_body: PR body
        repo_owner: Repository owner
        repo_name: Repository name
        logger: Optional logger

    Returns:
        True if successful, False otherwise
    """
    # Push branch
    if not push_branch(state.branch_name, state.worktree_path, logger):
        return False

    # Check if PR exists
    if check_pr_exists(state.branch_name, repo_owner, repo_name):
        if logger:
            logger.info("PR already exists, skipping creation")
        return True

    # Create PR
    pr_url = create_pull_request(
        title=pr_title,
        body=pr_body,
        branch_name=state.branch_name,
        issue_number=state.issue_number,
        working_dir=state.worktree_path,
        repo_owner=repo_owner,
        repo_name=repo_name,
        logger=logger,
    )

    return pr_url is not None
