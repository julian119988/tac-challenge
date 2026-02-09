"""Core modules for the webhook server.

This package contains:
- config: Server configuration and settings
- handlers: GitHub webhook event handlers
- adw_integration: Integration with ADW (AI Developer Workflows)
"""

from .config import get_config
from .handlers import (
    validate_webhook_signature,
    handle_issue_event,
    handle_pull_request_event,
    IssueWebhookPayload,
    PullRequestWebhookPayload,
)
from .adw_integration import (
    trigger_chore_workflow,
    trigger_implement_workflow,
    trigger_chore_implement_workflow,
    generate_adw_id,
    WorkflowResult,
)

__all__ = [
    # Config
    "get_config",
    # Handlers
    "validate_webhook_signature",
    "handle_issue_event",
    "handle_pull_request_event",
    "IssueWebhookPayload",
    "PullRequestWebhookPayload",
    # ADW Integration
    "trigger_chore_workflow",
    "trigger_implement_workflow",
    "trigger_chore_implement_workflow",
    "generate_adw_id",
    "WorkflowResult",
]
