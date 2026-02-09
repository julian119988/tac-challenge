"""ADW integration layer for webhook server.

This module provides the interface between the FastAPI webhook server
and the ADW (AI Developer Workflows) system. It enables programmatic
execution of ADW workflows in response to webhook events.

The integration supports:
- Executing chore planning workflows (/chore)
- Executing implementation workflows (/implement)
- Executing full chore+implement workflows
- Async execution compatible with FastAPI
- Proper output file management

Example:
    from apps.adw_integration import trigger_chore_workflow

    # Trigger a chore planning workflow
    result = await trigger_chore_workflow(
        prompt="Add error handling to webhook endpoint",
        adw_id="abc12345"
    )

    if result.success:
        print(f"Plan created at: {result.plan_path}")
"""

import os
import sys
import asyncio
import logging
from typing import Optional, Literal
from pathlib import Path
from pydantic import BaseModel

# Add adw_modules to path for imports
# apps/server/core/adw_integration.py -> project_root/adws/adw_modules
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
adws_path = os.path.join(project_root, "adws")
adw_modules_path = os.path.join(adws_path, "adw_modules")
if adw_modules_path not in sys.path:
    sys.path.insert(0, adw_modules_path)

from agent import (
    AgentTemplateRequest,
    AgentPromptResponse,
    execute_template,
    generate_short_id,
)

# Configure logger
logger = logging.getLogger(__name__)


class WorkflowResult(BaseModel):
    """Result from an ADW workflow execution.

    Attributes:
        success: Whether the workflow executed successfully
        output: Output text from the workflow
        session_id: Claude Code session ID (if available)
        adw_id: Unique identifier for this workflow execution
        output_dir: Directory containing workflow artifacts
        plan_path: Path to generated plan file (for chore workflows)
        error_message: Error message if workflow failed
    """
    success: bool
    output: str
    session_id: Optional[str] = None
    adw_id: str
    output_dir: str
    plan_path: Optional[str] = None
    error_message: Optional[str] = None


async def trigger_chore_workflow(
    prompt: str,
    adw_id: Optional[str] = None,
    model: Literal["sonnet", "opus"] = "sonnet",
    working_dir: Optional[str] = None,
) -> WorkflowResult:
    """Trigger a chore planning workflow.

    The /chore command creates a detailed implementation plan based on the prompt.
    The plan is saved to specs/chore-{adw_id}-{slug}.md and can be used as input
    for the /implement command.

    Args:
        prompt: Description of the work to be planned
        adw_id: Unique identifier for this workflow (generated if not provided)
        model: Claude model to use (sonnet or opus)
        working_dir: Working directory for workflow execution (default: current dir)

    Returns:
        WorkflowResult with success status, output, and plan path

    Example:
        result = await trigger_chore_workflow(
            prompt="Add logging to all webhook handlers",
            model="sonnet"
        )
        if result.success:
            print(f"Plan: {result.plan_path}")
    """
    # Generate ADW ID if not provided
    if adw_id is None:
        adw_id = generate_short_id()

    # Use current directory if no working directory specified
    if working_dir is None:
        working_dir = os.getcwd()

    logger.info(
        f"→ trigger_chore_workflow called: adw_id={adw_id}, "
        f"model={model}, working_dir={working_dir}"
    )
    logger.info(f"   Prompt preview: {prompt[:200]}...")

    # Create the template request
    request = AgentTemplateRequest(
        agent_name="planner",
        slash_command="/chore",
        args=[adw_id, prompt],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )
    logger.info(f"   Created AgentTemplateRequest: agent=planner, slash_command=/chore")

    try:
        # Execute in thread pool to avoid blocking async event loop
        logger.info(f"   Executing template in thread pool...")
        loop = asyncio.get_event_loop()
        response: AgentPromptResponse = await loop.run_in_executor(
            None,
            execute_template,
            request
        )
        logger.info(f"   ✓ Template execution completed: success={response.success}, session_id={response.session_id}")

        # Determine output directory
        output_dir = os.path.join(working_dir, "agents", adw_id, "planner")

        # Try to extract plan path from output
        plan_path = None
        if response.success:
            # Look for specs/chore-*.md pattern in output
            import re
            match = re.search(r"specs/chore-[a-zA-Z0-9\-]+\.md", response.output)
            if match:
                plan_path = match.group(0)
                logger.info(f"Plan created at: {plan_path}")

        return WorkflowResult(
            success=response.success,
            output=response.output,
            session_id=response.session_id,
            adw_id=adw_id,
            output_dir=output_dir,
            plan_path=plan_path,
            error_message=None if response.success else response.output,
        )

    except Exception as e:
        logger.error(f"Error executing /chore workflow: {e}", exc_info=True)
        return WorkflowResult(
            success=False,
            output="",
            session_id=None,
            adw_id=adw_id,
            output_dir=os.path.join(working_dir, "agents", adw_id, "planner"),
            plan_path=None,
            error_message=f"Workflow execution error: {str(e)}",
        )


async def trigger_implement_workflow(
    spec_path: str,
    adw_id: Optional[str] = None,
    model: Literal["sonnet", "opus"] = "sonnet",
    working_dir: Optional[str] = None,
) -> WorkflowResult:
    """Trigger an implementation workflow.

    The /implement command executes the implementation plan specified in the spec file.
    The spec file is typically generated by the /chore command.

    Args:
        spec_path: Path to the specification/plan file (e.g., specs/chore-abc-task.md)
        adw_id: Unique identifier for this workflow (generated if not provided)
        model: Claude model to use (sonnet or opus)
        working_dir: Working directory for workflow execution (default: current dir)

    Returns:
        WorkflowResult with success status and output

    Example:
        result = await trigger_implement_workflow(
            spec_path="specs/chore-abc12345-add-logging.md",
            model="sonnet"
        )
    """
    # Generate ADW ID if not provided
    if adw_id is None:
        adw_id = generate_short_id()

    # Use current directory if no working directory specified
    if working_dir is None:
        working_dir = os.getcwd()

    logger.info(
        f"→ trigger_implement_workflow called: adw_id={adw_id}, "
        f"spec={spec_path}, model={model}, working_dir={working_dir}"
    )

    # Create the template request
    request = AgentTemplateRequest(
        agent_name="builder",
        slash_command="/implement",
        args=[spec_path],
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )
    logger.info(f"   Created AgentTemplateRequest: agent=builder, slash_command=/implement")

    try:
        # Execute in thread pool to avoid blocking async event loop
        logger.info(f"   Executing template in thread pool...")
        loop = asyncio.get_event_loop()
        response: AgentPromptResponse = await loop.run_in_executor(
            None,
            execute_template,
            request
        )
        logger.info(f"   ✓ Template execution completed: success={response.success}, session_id={response.session_id}")

        # Determine output directory
        output_dir = os.path.join(working_dir, "agents", adw_id, "builder")

        return WorkflowResult(
            success=response.success,
            output=response.output,
            session_id=response.session_id,
            adw_id=adw_id,
            output_dir=output_dir,
            plan_path=None,
            error_message=None if response.success else response.output,
        )

    except Exception as e:
        logger.error(f"Error executing /implement workflow: {e}", exc_info=True)
        return WorkflowResult(
            success=False,
            output="",
            session_id=None,
            adw_id=adw_id,
            output_dir=os.path.join(working_dir, "agents", adw_id, "builder"),
            plan_path=None,
            error_message=f"Workflow execution error: {str(e)}",
        )


async def trigger_chore_implement_workflow(
    prompt: str,
    adw_id: Optional[str] = None,
    model: Literal["sonnet", "opus"] = "sonnet",
    working_dir: Optional[str] = None,
    issue_number: Optional[int] = None,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
    issue_title: Optional[str] = None,
) -> tuple[WorkflowResult, Optional[WorkflowResult]]:
    """Trigger a full chore + implement workflow.

    This executes both planning and implementation in sequence:
    1. Runs /chore to create a plan
    2. If planning succeeds, runs /implement to execute the plan
    3. If git info provided, creates branch, commits, pushes, and creates PR

    Args:
        prompt: Description of the work to be planned and implemented
        adw_id: Unique identifier for this workflow (generated if not provided)
        model: Claude model to use (sonnet or opus)
        working_dir: Working directory for workflow execution (default: current dir)
        issue_number: GitHub issue number (for PR linking)
        repo_owner: Repository owner (for git operations)
        repo_name: Repository name (for git operations)
        issue_title: Issue title (for branch naming)

    Returns:
        Tuple of (chore_result, implement_result)
        The implement_result will be None if chore planning failed

    Example:
        chore_result, impl_result = await trigger_chore_implement_workflow(
            prompt="Add rate limiting to webhook endpoint",
            issue_number=42,
            repo_owner="myorg",
            repo_name="myrepo",
            issue_title="Add rate limiting"
        )
        if chore_result.success and impl_result and impl_result.success:
            print("Full workflow completed successfully")
    """
    # Generate ADW ID if not provided
    if adw_id is None:
        adw_id = generate_short_id()

    # Use current directory if no working directory specified
    if working_dir is None:
        working_dir = os.getcwd()

    logger.info(
        f"Triggering /chore + /implement workflow: adw_id={adw_id}, "
        f"model={model}, working_dir={working_dir}, issue_number={issue_number}"
    )

    # Create branch if git info provided
    branch_name = None
    if issue_number and repo_owner and repo_name:
        from git_ops import create_branch

        # Generate branch name from issue number and title
        if issue_title:
            # Sanitize title for branch name
            sanitized_title = issue_title.lower()
            sanitized_title = sanitized_title.replace(" ", "-")
            # Remove special characters except hyphens
            sanitized_title = "".join(c for c in sanitized_title if c.isalnum() or c == "-")
            # Limit length
            sanitized_title = sanitized_title[:50]
            branch_name = f"issue-{issue_number}-{sanitized_title}"
        else:
            branch_name = f"issue-{issue_number}"

        logger.info(f"Creating branch: {branch_name}")
        if create_branch(branch_name, working_dir):
            logger.info(f"✓ Branch created: {branch_name}")
        else:
            logger.warning(f"⚠️ Failed to create branch {branch_name}, continuing anyway")
            branch_name = None

    # Phase 1: Run chore workflow
    chore_result = await trigger_chore_workflow(
        prompt=prompt,
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    # Check if chore succeeded
    if not chore_result.success:
        logger.error(f"Chore workflow failed for adw_id={adw_id}")
        return chore_result, None

    # Check if we got a plan path
    if not chore_result.plan_path:
        logger.error(f"Chore workflow succeeded but no plan path found for adw_id={adw_id}")
        chore_result.success = False
        chore_result.error_message = "Plan file path not found in chore output"
        return chore_result, None

    # Phase 2: Run implement workflow
    implement_result = await trigger_implement_workflow(
        spec_path=chore_result.plan_path,
        adw_id=adw_id,
        model=model,
        working_dir=working_dir,
    )

    # Phase 3: Commit, push, and create PR if git info provided
    pr_url = None
    if implement_result.success and branch_name and repo_owner and repo_name:
        from git_ops import commit_changes, push_branch, create_pull_request

        logger.info("Starting git operations...")

        # Commit changes
        commit_message = f"Implement issue #{issue_number}: {issue_title}\n\nADW ID: {adw_id}"
        logger.info(f"Committing changes: {commit_message[:100]}...")
        if commit_changes(commit_message, working_dir, logger):
            logger.info("✓ Changes committed")

            # Push branch
            logger.info(f"Pushing branch {branch_name}...")
            if push_branch(branch_name, working_dir, logger):
                logger.info("✓ Branch pushed")

                # Create PR
                pr_title = f"{issue_title} (#{issue_number})"
                pr_body = (
                    f"Closes #{issue_number}\n\n"
                    f"## Summary\n\n"
                    f"{prompt}\n\n"
                    f"## ADW Info\n\n"
                    f"- **ADW ID:** `{adw_id}`\n"
                    f"- **Plan:** `{chore_result.plan_path}`\n"
                    f"- **Model:** `{model}`\n\n"
                    f"🤖 Generated with [Claude Code](https://claude.com/claude-code)"
                )

                logger.info(f"Creating pull request...")
                pr_url = create_pull_request(
                    title=pr_title,
                    body=pr_body,
                    branch_name=branch_name,
                    issue_number=issue_number,
                    working_dir=working_dir,
                    repo_owner=repo_owner,
                    repo_name=repo_name,
                    logger=logger,
                )

                if pr_url:
                    logger.info(f"✓ Pull request created: {pr_url}")
                else:
                    logger.warning("⚠️ Failed to create pull request")
            else:
                logger.warning("⚠️ Failed to push branch")
        else:
            logger.warning("⚠️ Failed to commit changes (may be no changes to commit)")

    logger.info(
        f"Full workflow completed: adw_id={adw_id}, "
        f"chore_success={chore_result.success}, "
        f"implement_success={implement_result.success}, "
        f"pr_created={pr_url is not None}"
    )

    # Store PR URL in implement_result if available
    if pr_url and implement_result:
        implement_result.output = f"{implement_result.output}\n\n🔗 Pull Request: {pr_url}"

    return chore_result, implement_result


def generate_adw_id() -> str:
    """Generate a unique ADW identifier.

    This is a convenience wrapper around the agent module's generate_short_id.

    Returns:
        8-character unique identifier
    """
    return generate_short_id()
