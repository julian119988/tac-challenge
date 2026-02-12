"""Tests for agent module.

Tests cover:
- ADW ID generation (generate_short_id)
- JSONL parsing and result extraction
- AgentPromptRequest/Response models
- Error handling and retry logic
"""

import pytest
import json
from unittest.mock import Mock, patch
from adws.adw_modules.agent import (
    generate_short_id,
    parse_jsonl_output,
    extract_session_id_from_jsonl,
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    ClaudeCodeResultMessage,
    RetryCode,
    get_safe_subprocess_env,
)


# ============================================================================
# ID Generation Tests
# ============================================================================

def test_generate_short_id():
    """Test short ID generation."""
    id1 = generate_short_id()
    id2 = generate_short_id()

    # IDs should be 8 characters
    assert len(id1) == 8
    assert len(id2) == 8

    # IDs should be hexadecimal
    assert all(c in "0123456789abcdef" for c in id1)
    assert all(c in "0123456789abcdef" for c in id2)

    # IDs should be unique
    assert id1 != id2


# ============================================================================
# JSONL Parsing Tests
# ============================================================================

def test_parse_jsonl_output_valid():
    """Test parsing valid JSONL output."""
    jsonl_output = '''{"type": "log", "message": "Starting"}
{"type": "log", "message": "Processing"}
{"type": "result", "subtype": "success", "is_error": false, "duration_ms": 1000, "duration_api_ms": 500, "num_turns": 3, "result": "Task completed", "session_id": "session-123", "total_cost_usd": 0.05}'''

    messages = parse_jsonl_output(jsonl_output)

    assert len(messages) == 3
    assert messages[0]["type"] == "log"
    assert messages[1]["message"] == "Processing"
    assert messages[2]["type"] == "result"


def test_parse_jsonl_output_empty():
    """Test parsing empty JSONL output."""
    messages = parse_jsonl_output("")
    assert messages == []


def test_parse_jsonl_output_invalid_line():
    """Test parsing JSONL with invalid JSON line."""
    jsonl_output = '''{"type": "log", "message": "Valid"}
invalid json line
{"type": "log", "message": "Also valid"}'''

    messages = parse_jsonl_output(jsonl_output)

    # Should parse valid lines and skip invalid ones
    assert len(messages) == 2
    assert messages[0]["message"] == "Valid"
    assert messages[1]["message"] == "Also valid"


def test_extract_session_id_from_jsonl():
    """Test extracting session ID from JSONL output."""
    jsonl_output = '''{"type": "log", "message": "Starting"}
{"type": "result", "subtype": "success", "is_error": false, "duration_ms": 1000, "duration_api_ms": 500, "num_turns": 3, "result": "Done", "session_id": "session-abc123", "total_cost_usd": 0.05}'''

    session_id = extract_session_id_from_jsonl(jsonl_output)
    assert session_id == "session-abc123"


def test_extract_session_id_from_jsonl_no_result():
    """Test extracting session ID when no result message exists."""
    jsonl_output = '''{"type": "log", "message": "Starting"}
{"type": "log", "message": "Processing"}'''

    session_id = extract_session_id_from_jsonl(jsonl_output)
    assert session_id is None


def test_extract_session_id_from_jsonl_empty():
    """Test extracting session ID from empty output."""
    session_id = extract_session_id_from_jsonl("")
    assert session_id is None


# ============================================================================
# Pydantic Model Tests
# ============================================================================

def test_agent_prompt_request_model():
    """Test AgentPromptRequest model."""
    request = AgentPromptRequest(
        prompt="Test prompt",
        adw_id="abc12345",
        agent_name="ops",
        model="sonnet",
        output_file="/tmp/output.jsonl",
        working_dir="/tmp/work"
    )

    assert request.prompt == "Test prompt"
    assert request.adw_id == "abc12345"
    assert request.model == "sonnet"
    assert request.agent_name == "ops"
    assert request.dangerously_skip_permissions is False


def test_agent_prompt_response_model():
    """Test AgentPromptResponse model."""
    response = AgentPromptResponse(
        output="Task completed successfully",
        success=True,
        session_id="session-123",
        retry_code=RetryCode.NONE
    )

    assert response.success is True
    assert response.output == "Task completed successfully"
    assert response.session_id == "session-123"
    assert response.retry_code == RetryCode.NONE


def test_agent_template_request_model():
    """Test AgentTemplateRequest model."""
    request = AgentTemplateRequest(
        agent_name="planner",
        slash_command="/chore",
        args=["abc12345", "Test prompt"],
        adw_id="abc12345",
        model="opus",
        working_dir="/tmp/work"
    )

    assert request.agent_name == "planner"
    assert request.slash_command == "/chore"
    assert request.args == ["abc12345", "Test prompt"]
    assert request.model == "opus"


def test_claude_code_result_message_model():
    """Test ClaudeCodeResultMessage model parsing."""
    result_data = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "duration_ms": 5000,
        "duration_api_ms": 3000,
        "num_turns": 5,
        "result": "Task completed",
        "session_id": "session-xyz",
        "total_cost_usd": 0.10
    }

    result = ClaudeCodeResultMessage(**result_data)

    assert result.type == "result"
    assert result.is_error is False
    assert result.num_turns == 5
    assert result.session_id == "session-xyz"
    assert result.total_cost_usd == 0.10


# ============================================================================
# RetryCode Tests
# ============================================================================

def test_retry_code_enum():
    """Test RetryCode enum values."""
    assert RetryCode.NONE == "none"
    assert RetryCode.CLAUDE_CODE_ERROR == "claude_code_error"
    assert RetryCode.TIMEOUT_ERROR == "timeout_error"
    assert RetryCode.EXECUTION_ERROR == "execution_error"
    assert RetryCode.ERROR_DURING_EXECUTION == "error_during_execution"


# ============================================================================
# Environment Variables Tests
# ============================================================================

def test_get_safe_subprocess_env():
    """Test safe subprocess environment extraction."""
    with patch.dict("os.environ", {
        "ANTHROPIC_API_KEY": "test-key",
        "HOME": "/home/test",
        "PATH": "/usr/bin",
        "SENSITIVE_VAR": "should-not-be-included"
    }):
        env = get_safe_subprocess_env()

        # Should include safe variables
        assert "ANTHROPIC_API_KEY" in env
        assert env["ANTHROPIC_API_KEY"] == "test-key"
        assert "HOME" in env
        assert "PATH" in env

        # Should not include sensitive variables not in the safe list
        assert "SENSITIVE_VAR" not in env


def test_get_safe_subprocess_env_missing_optional():
    """Test safe subprocess environment with missing optional variables."""
    with patch.dict("os.environ", {
        "ANTHROPIC_API_KEY": "test-key",
        "HOME": "/home/test"
    }, clear=True):
        env = get_safe_subprocess_env()

        # Required variables should be present
        assert "ANTHROPIC_API_KEY" in env

        # Optional variables might be None, which is ok
        # The function should handle missing optional vars gracefully


# ============================================================================
# Response Model Validation Tests
# ============================================================================

def test_agent_prompt_response_defaults():
    """Test AgentPromptResponse default values."""
    response = AgentPromptResponse(
        output="Test output",
        success=True
    )

    assert response.session_id is None
    assert response.retry_code == RetryCode.NONE


def test_agent_prompt_request_defaults():
    """Test AgentPromptRequest default values."""
    request = AgentPromptRequest(
        prompt="Test",
        adw_id="abc12345",
        output_file="/tmp/out.jsonl"
    )

    assert request.agent_name == "ops"
    assert request.model == "sonnet"
    assert request.dangerously_skip_permissions is False
    assert request.working_dir is None
