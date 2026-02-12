"""Tests for ADW integration layer.

Tests cover:
- ADW ID generation
- Chore workflow triggering
- Implement workflow triggering
- Chore+implement workflow orchestration
- WorkflowResult parsing
- Error handling
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from apps.adw_server.core.adw_integration import (
    generate_adw_id,
    trigger_chore_workflow,
    trigger_implement_workflow,
    trigger_chore_implement_workflow,
    generate_pr_body,
    WorkflowResult,
)
from adws.adw_modules.agent import AgentPromptResponse


# ============================================================================
# ADW ID Generation Tests
# ============================================================================

def test_generate_adw_id():
    """Test ADW ID generation creates valid IDs."""
    adw_id = generate_adw_id()

    assert adw_id is not None
    assert isinstance(adw_id, str)
    assert len(adw_id) == 8
    assert adw_id.isalnum()


def test_generate_adw_id_unique():
    """Test ADW ID generation creates unique IDs."""
    id1 = generate_adw_id()
    id2 = generate_adw_id()

    assert id1 != id2


# ============================================================================
# Chore Workflow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_trigger_chore_workflow_success(temp_dir):
    """Test successful chore workflow execution."""
    mock_response = AgentPromptResponse(
        success=True,
        output="Planning complete. Plan saved to specs/chore-abc12345-test-feature.md",
        session_id="session-12345"
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = mock_response

        result = await trigger_chore_workflow(
            prompt="Add feature X",
            adw_id="abc12345",
            model="sonnet",
            working_dir=temp_dir
        )

        assert result.success is True
        assert result.adw_id == "abc12345"
        assert result.session_id == "session-12345"
        assert result.plan_path == "specs/chore-abc12345-test-feature.md"
        assert result.error_message is None

        # Verify execute_template was called correctly
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0][0]
        assert call_args.agent_name == "planner"
        assert call_args.slash_command == "/chore"
        assert call_args.adw_id == "abc12345"
        assert call_args.model == "sonnet"
        assert call_args.working_dir == temp_dir


@pytest.mark.asyncio
async def test_trigger_chore_workflow_failure(temp_dir):
    """Test chore workflow execution failure."""
    mock_response = AgentPromptResponse(
        success=False,
        output="Error: Planning failed due to timeout",
        session_id=None
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = mock_response

        result = await trigger_chore_workflow(
            prompt="Add feature X",
            working_dir=temp_dir
        )

        assert result.success is False
        assert result.error_message == "Error: Planning failed due to timeout"
        assert result.plan_path is None


@pytest.mark.asyncio
async def test_trigger_chore_workflow_generates_adw_id(temp_dir):
    """Test chore workflow generates ADW ID if not provided."""
    mock_response = AgentPromptResponse(
        success=True,
        output="Planning complete",
        session_id="session-12345"
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = mock_response

        result = await trigger_chore_workflow(
            prompt="Add feature X",
            working_dir=temp_dir
        )

        assert result.adw_id is not None
        assert len(result.adw_id) == 8


@pytest.mark.asyncio
async def test_trigger_chore_workflow_exception(temp_dir):
    """Test chore workflow handles exceptions gracefully."""
    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.side_effect = Exception("Execution error")

        result = await trigger_chore_workflow(
            prompt="Add feature X",
            working_dir=temp_dir
        )

        assert result.success is False
        assert "Execution error" in result.error_message


# ============================================================================
# Implement Workflow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_trigger_implement_workflow_success(temp_dir):
    """Test successful implement workflow execution."""
    mock_response = AgentPromptResponse(
        success=True,
        output="Implementation complete. Changes committed.",
        session_id="session-67890"
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = mock_response

        result = await trigger_implement_workflow(
            spec_path="specs/chore-abc12345-test.md",
            adw_id="abc12345",
            model="sonnet",
            working_dir=temp_dir
        )

        assert result.success is True
        assert result.adw_id == "abc12345"
        assert result.session_id == "session-67890"
        assert result.error_message is None

        # Verify execute_template was called correctly
        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0][0]
        assert call_args.agent_name == "builder"
        assert call_args.slash_command == "/implement"
        assert call_args.args == ["specs/chore-abc12345-test.md"]
        assert call_args.model == "sonnet"


@pytest.mark.asyncio
async def test_trigger_implement_workflow_failure(temp_dir):
    """Test implement workflow execution failure."""
    mock_response = AgentPromptResponse(
        success=False,
        output="Error: Implementation failed",
        session_id=None
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = mock_response

        result = await trigger_implement_workflow(
            spec_path="specs/chore-abc12345-test.md",
            working_dir=temp_dir
        )

        assert result.success is False
        assert result.error_message == "Error: Implementation failed"


# ============================================================================
# Chore+Implement Workflow Tests
# ============================================================================

@pytest.mark.asyncio
async def test_trigger_chore_implement_workflow_success(temp_dir):
    """Test successful full chore+implement workflow."""
    chore_response = AgentPromptResponse(
        success=True,
        output="Planning complete. Plan saved to specs/chore-xyz78901-feature.md",
        session_id="session-chore"
    )

    implement_response = AgentPromptResponse(
        success=True,
        output="Implementation complete",
        session_id="session-impl"
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.side_effect = [chore_response, implement_response]

        chore_result, impl_result = await trigger_chore_implement_workflow(
            prompt="Add dark mode",
            adw_id="xyz78901",
            model="sonnet",
            working_dir=temp_dir
        )

        assert chore_result.success is True
        assert chore_result.plan_path == "specs/chore-xyz78901-feature.md"
        assert impl_result is not None
        assert impl_result.success is True


@pytest.mark.asyncio
async def test_trigger_chore_implement_workflow_chore_fails(temp_dir):
    """Test chore+implement workflow when chore fails."""
    chore_response = AgentPromptResponse(
        success=False,
        output="Planning failed",
        session_id=None
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = chore_response

        chore_result, impl_result = await trigger_chore_implement_workflow(
            prompt="Add dark mode",
            working_dir=temp_dir
        )

        assert chore_result.success is False
        assert impl_result is None


@pytest.mark.asyncio
async def test_trigger_chore_implement_workflow_no_plan_path(temp_dir):
    """Test chore+implement workflow when plan path is not found."""
    chore_response = AgentPromptResponse(
        success=True,
        output="Planning complete but no spec path in output",
        session_id="session-chore"
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = chore_response

        chore_result, impl_result = await trigger_chore_implement_workflow(
            prompt="Add dark mode",
            working_dir=temp_dir
        )

        assert chore_result.success is False
        assert "Plan file path not found" in chore_result.error_message
        assert impl_result is None


@pytest.mark.asyncio
async def test_trigger_chore_implement_workflow_with_git_ops(temp_dir):
    """Test chore+implement workflow with git operations."""
    chore_response = AgentPromptResponse(
        success=True,
        output="Planning complete. Plan saved to specs/chore-git123-feature.md",
        session_id="session-chore"
    )

    implement_response = AgentPromptResponse(
        success=True,
        output="Implementation complete",
        session_id="session-impl"
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec, \
         patch("adws.adw_modules.git_ops.create_branch") as mock_create_branch, \
         patch("adws.adw_modules.git_ops.commit_changes") as mock_commit, \
         patch("adws.adw_modules.git_ops.push_branch") as mock_push, \
         patch("adws.adw_modules.git_ops.create_pull_request") as mock_pr:

        mock_exec.side_effect = [chore_response, implement_response]
        mock_create_branch.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True
        mock_pr.return_value = "https://github.com/owner/repo/pull/123"

        chore_result, impl_result = await trigger_chore_implement_workflow(
            prompt="Add dark mode",
            adw_id="git123",
            working_dir=temp_dir,
            issue_number=42,
            repo_owner="testowner",
            repo_name="testrepo",
            issue_title="Add dark mode"
        )

        assert chore_result.success is True
        assert impl_result.success is True
        assert "https://github.com/owner/repo/pull/123" in impl_result.output

        # Verify git operations were called
        mock_create_branch.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()
        mock_pr.assert_called_once()


# ============================================================================
# WorkflowResult Tests
# ============================================================================

def test_workflow_result_success():
    """Test WorkflowResult with successful workflow."""
    result = WorkflowResult(
        success=True,
        output="Workflow completed successfully",
        session_id="session-12345",
        adw_id="abc12345",
        output_dir="agents/abc12345/planner",
        plan_path="specs/chore-abc12345-feature.md",
        error_message=None
    )

    assert result.success is True
    assert result.output == "Workflow completed successfully"
    assert result.session_id == "session-12345"
    assert result.adw_id == "abc12345"
    assert result.plan_path == "specs/chore-abc12345-feature.md"
    assert result.error_message is None


def test_workflow_result_failure():
    """Test WorkflowResult with failed workflow."""
    result = WorkflowResult(
        success=False,
        output="",
        session_id=None,
        adw_id="abc12345",
        output_dir="agents/abc12345/planner",
        plan_path=None,
        error_message="Workflow failed: timeout"
    )

    assert result.success is False
    assert result.error_message == "Workflow failed: timeout"
    assert result.session_id is None
    assert result.plan_path is None


# ============================================================================
# PR Body Generation Tests
# ============================================================================

def test_generate_pr_body_basic(temp_dir):
    """Test basic PR body generation."""
    pr_body = generate_pr_body(
        issue_number=42,
        prompt="Add dark mode feature",
        adw_id="abc12345",
        plan_path="specs/chore-abc12345-dark-mode.md",
        model="sonnet",
        working_dir=temp_dir
    )

    assert f"Closes #{42}" in pr_body
    assert "Summary" in pr_body
    assert "ADW ID" in pr_body
    assert "abc12345" in pr_body
    assert "Claude Code" in pr_body


def test_generate_pr_body_with_plan_summary(temp_dir):
    """Test PR body generation extracts summary from plan file."""
    plan_path = os.path.join(temp_dir, "test-plan.md")
    with open(plan_path, "w") as f:
        f.write("""# Chore: Add Dark Mode

## Chore Description
This feature adds dark mode support to the application.
Users can toggle between light and dark themes.

## Relevant Files
- `app.js`
- `styles.css`
""")

    pr_body = generate_pr_body(
        issue_number=42,
        prompt="Add dark mode",
        adw_id="abc12345",
        plan_path=plan_path,
        model="sonnet",
        working_dir=temp_dir
    )

    assert "dark mode support" in pr_body.lower()


def test_generate_pr_body_with_git_diff(temp_dir):
    """Test PR body generation includes git diff output."""
    # This test would require a real git repo, so we'll mock subprocess
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="app.js | 10 ++++++++++\nstyles.css | 5 +++++\n2 files changed, 15 insertions(+)"
        )

        pr_body = generate_pr_body(
            issue_number=42,
            prompt="Add dark mode",
            adw_id="abc12345",
            plan_path="specs/test.md",
            model="sonnet",
            working_dir=temp_dir
        )

        assert "app.js" in pr_body
        assert "styles.css" in pr_body


def test_generate_pr_body_handles_missing_plan(temp_dir):
    """Test PR body generation handles missing plan file gracefully."""
    pr_body = generate_pr_body(
        issue_number=42,
        prompt="Add feature X",
        adw_id="abc12345",
        plan_path="/nonexistent/plan.md",
        model="sonnet",
        working_dir=temp_dir
    )

    # Should still generate a valid PR body with the prompt
    assert "Closes #42" in pr_body
    assert "Add feature X" in pr_body
    assert "ADW ID" in pr_body
