"""Data types and models for ADW workflows."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Re-export types from agent.py for convenience
from .agent import (
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    RetryCode,
)

# Type aliases
ModelSet = Literal["base", "heavy"]
IssueClassSlashCommand = Literal["/chore", "/bug", "/feature"]


class GitHubComment(BaseModel):
    """GitHub issue comment data."""
    author: str
    body: str
    created_at: str
    id: Optional[int] = None


class GitHubIssue(BaseModel):
    """GitHub issue data."""
    number: int
    title: str
    body: str
    state: str = "open"
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    comments: List[GitHubComment] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    url: Optional[str] = None


class ADWStateData(BaseModel):
    """ADW state data model for validation."""
    adw_id: str
    issue_number: Optional[int] = None
    branch_name: Optional[str] = None
    plan_file: Optional[str] = None
    issue_class: Optional[IssueClassSlashCommand] = None
    worktree_path: Optional[str] = None
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    model_set: ModelSet = "base"
    all_adws: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Export all types
__all__ = [
    "AgentPromptRequest",
    "AgentPromptResponse",
    "AgentTemplateRequest",
    "RetryCode",
    "ModelSet",
    "IssueClassSlashCommand",
    "GitHubComment",
    "GitHubIssue",
    "ADWStateData",
]
