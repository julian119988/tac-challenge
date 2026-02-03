"""ADW core modules for workflow orchestration."""

__version__ = "0.1.0"

# Import all core modules for easy access
from . import agent
from . import agent_sdk
from . import data_types
from . import state
from . import github
from . import git_ops
from . import worktree_ops
from . import workflow_ops
from . import utils

# Export commonly used classes and functions
from .agent import (
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    RetryCode,
    execute_template,
    prompt_claude_code,
    prompt_claude_code_with_retry,
    get_model_for_slash_command,
)

from .data_types import (
    GitHubIssue,
    GitHubComment,
    ADWStateData,
    ModelSet,
    IssueClassSlashCommand,
)

from .state import ADWState

from .github import (
    fetch_issue,
    make_issue_comment,
    mark_issue_in_progress,
    fetch_issue_comments,
    find_keyword_from_comment,
    ADW_BOT_IDENTIFIER,
)

from .git_ops import (
    get_current_branch,
    create_branch,
    commit_changes,
    push_branch,
    check_pr_exists,
    create_pull_request,
    finalize_git_operations,
)

from .worktree_ops import (
    get_worktree_path,
    create_worktree,
    validate_worktree,
    remove_worktree,
    setup_worktree_environment,
    get_ports_for_adw,
)

from .workflow_ops import (
    classify_issue,
    generate_branch_name,
    build_plan,
    implement_plan,
    create_commit_message,
    create_pull_request_description,
    find_spec_file,
    create_and_implement_patch,
)

from .utils import (
    setup_logger,
    ensure_adw_id,
    get_repo_config,
    validate_required_env_vars,
    parse_args_for_adw_context,
    print_success,
    print_error,
    print_info,
    print_section,
)

__all__ = [
    # Version
    "__version__",
    # Modules
    "agent",
    "agent_sdk",
    "data_types",
    "state",
    "github",
    "git_ops",
    "worktree_ops",
    "workflow_ops",
    "utils",
    # Agent
    "AgentPromptRequest",
    "AgentPromptResponse",
    "AgentTemplateRequest",
    "RetryCode",
    "execute_template",
    "prompt_claude_code",
    "prompt_claude_code_with_retry",
    "get_model_for_slash_command",
    # Data types
    "GitHubIssue",
    "GitHubComment",
    "ADWStateData",
    "ModelSet",
    "IssueClassSlashCommand",
    # State
    "ADWState",
    # GitHub
    "fetch_issue",
    "make_issue_comment",
    "mark_issue_in_progress",
    "fetch_issue_comments",
    "find_keyword_from_comment",
    "ADW_BOT_IDENTIFIER",
    # Git operations
    "get_current_branch",
    "create_branch",
    "commit_changes",
    "push_branch",
    "check_pr_exists",
    "create_pull_request",
    "finalize_git_operations",
    # Worktree operations
    "get_worktree_path",
    "create_worktree",
    "validate_worktree",
    "remove_worktree",
    "setup_worktree_environment",
    "get_ports_for_adw",
    # Workflow operations
    "classify_issue",
    "generate_branch_name",
    "build_plan",
    "implement_plan",
    "create_commit_message",
    "create_pull_request_description",
    "find_spec_file",
    "create_and_implement_patch",
    # Utils
    "setup_logger",
    "ensure_adw_id",
    "get_repo_config",
    "validate_required_env_vars",
    "parse_args_for_adw_context",
    "print_success",
    "print_error",
    "print_info",
    "print_section",
]
