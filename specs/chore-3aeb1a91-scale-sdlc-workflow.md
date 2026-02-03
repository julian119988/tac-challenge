# Chore: Scale Up to Full SDLC Workflow with GitHub Webhooks

## Metadata
adw_id: `3aeb1a91`
prompt: `Scale up to full SDLC workflow with GitHub webhooks, worktrees, state management, and automated issue-to-PR pipeline based on example patterns`

## Chore Description
Transform the minimal agentic layer into a production-ready SDLC automation system that:
1. Receives GitHub webhook events (issue creation, comments)
2. Automatically classifies issues as features/chores/bugs
3. Creates isolated git worktrees for parallel development
4. Orchestrates multi-phase workflows (plan → build → test → review → document)
5. Manages persistent state across workflow phases
6. Creates pull requests automatically with proper issue linking
7. Provides composable workflow phases that can run independently or chained

This implementation adapts proven patterns from `example/tac8_app5__nlq_to_sql_aea/adws/` to the main codebase structure.

## Relevant Files

### Existing Files to Reference
- `adws/adw_modules/agent.py` - Core agent execution (extend with model selection)
- `adws/adw_modules/agent_sdk.py` - SDK-based execution (reference for patterns)
- `adws/adw_prompt.py` - Direct prompt execution (reference for structure)
- `adws/adw_slash_command.py` - Slash command execution (reference for structure)
- `.claude/commands/chore.md` - Existing chore planning template (keep)
- `.claude/commands/implement.md` - Existing implementation template (keep)
- `.env.sample` - Environment configuration (extend)
- `README.md` - Project documentation (update with new architecture)
- `example/tac8_app5__nlq_to_sql_aea/adws/` - Reference implementation for all patterns

### New Files to Create

#### Core Modules (`adws/adw_modules/`)
- `data_types.py` - Pydantic models for GitHubIssue, ADWState, workflow types
- `state.py` - Persistent state management with load/save/update
- `github.py` - GitHub API wrapper using `gh` CLI (issues, comments, labels)
- `git_ops.py` - Git operations (branch, commit, push, PR creation)
- `worktree_ops.py` - Git worktree management with isolation
- `workflow_ops.py` - High-level orchestration (classify, plan, implement, etc.)
- `utils.py` - Logging, helpers, environment utilities
- `__init__.py` - Package initialization

#### Webhook Triggers (`adws/adw_triggers/`)
- `trigger_webhook.py` - FastAPI webhook receiver for GitHub events
- `__init__.py` - Package initialization

#### SDLC Workflow Scripts (`adws/`)
- `adw_plan_iso.py` - Phase 1: Issue classification, worktree creation, planning
- `adw_build_iso.py` - Phase 2: Implementation execution
- `adw_test_iso.py` - Phase 3: Test execution
- `adw_review_iso.py` - Phase 4: Code review
- `adw_document_iso.py` - Phase 5: Documentation generation
- `adw_patch_iso.py` - Patch generation for review feedback
- `adw_sdlc_iso.py` - Full pipeline orchestrator (plan → build → test → review → document)

#### Slash Command Templates (`.claude/commands/`)
- `classify_issue.md` - Issue type classification (/chore, /bug, /feature)
- `generate_branch_name.md` - AI-driven branch naming
- `commit.md` - Commit message generation
- `pull_request.md` - PR description generation
- `test.md` - Test execution template
- `review.md` - Code review template
- `document.md` - Documentation generation template
- `patch.md` - Patch generation from review feedback
- `classify_adw.md` - ADW workflow classification for webhooks

#### Testing Infrastructure (`adws/adw_tests/`)
- `health_check.py` - System health validation
- `test_state.py` - State management tests
- `test_github.py` - GitHub integration tests
- `test_git_ops.py` - Git operations tests
- `test_worktree_ops.py` - Worktree management tests
- `__init__.py` - Package initialization

#### Configuration & Documentation
- `.gitignore` - Add trees/, agents/, .ports.env, *.db
- `.env.sample` - Add GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME, WEBHOOK_SECRET
- `adws/README.md` - Update with new scaled architecture documentation
- `README.md` - Update with webhook setup instructions

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Core Data Types Module
- Create `adws/adw_modules/data_types.py` with Pydantic models:
  - `GitHubIssue` model with title, body, number, labels, comments
  - `GitHubComment` model with author, body, created_at
  - `ADWStateData` model with adw_id, issue_number, branch_name, plan_file, issue_class, worktree_path, backend_port, frontend_port, model_set
  - `ModelSet` = Literal["base", "heavy"]
  - `IssueClassSlashCommand` = Literal["/chore", "/bug", "/feature"]
  - `RetryCode` enum (reuse from agent.py or extend)
- Import necessary types from agent.py (AgentPromptRequest, AgentPromptResponse, AgentTemplateRequest)

### 2. Create State Management Module
- Create `adws/adw_modules/state.py` with ADWState class:
  - `__init__(adw_id, **kwargs)` - Initialize with ADWStateData fields
  - `load(adw_id, logger) -> ADWState` - Load from `agents/{adw_id}/adw_state.json`
  - `save(workflow_name)` - Persist to `agents/{adw_id}/adw_state.json`
  - `update(**kwargs)` - Update fields and validate
  - `to_dict()` - Convert to dictionary
  - `from_dict(data)` - Create from dictionary
  - Support stdin/stdout piping for cross-script communication
  - Handle missing files gracefully (create new state)
  - Add validation for core fields (adw_id, issue_number)

### 3. Create GitHub Integration Module
- Create `adws/adw_modules/github.py` with functions:
  - `get_github_env() -> Dict[str, str]` - Filter env vars (GH_TOKEN, GITHUB_TOKEN, PATH only)
  - `fetch_issue(issue_number, repo_owner, repo_name) -> GitHubIssue` - Get issue via `gh api`
  - `make_issue_comment(issue_number, comment, repo_owner, repo_name)` - Post comment via `gh issue comment`
  - `mark_issue_in_progress(issue_number, repo_owner, repo_name)` - Add "in-progress" label + assign
  - `fetch_issue_comments(issue_number, repo_owner, repo_name) -> List[GitHubComment]` - Get all comments
  - `find_keyword_from_comment(comments, keyword) -> Optional[str]` - Search comments for keyword
  - Add `ADW_BOT_IDENTIFIER = "[ADW-AGENTS]"` constant
  - Prefix all comments with bot identifier to prevent webhook loops
  - Handle `gh` CLI errors gracefully

### 4. Create Git Operations Module
- Create `adws/adw_modules/git_ops.py` with functions:
  - `get_current_branch(working_dir) -> str` - Get current branch via `git branch --show-current`
  - `create_branch(branch_name, working_dir)` - Create and checkout branch with fallback
  - `commit_changes(commit_message, working_dir)` - Stage all + commit
  - `push_branch(branch_name, working_dir)` - Push with `-u origin` flag
  - `check_pr_exists(branch_name, repo_owner, repo_name) -> bool` - Check via `gh pr list`
  - `create_pull_request(title, body, branch_name, issue_number, working_dir, repo_owner, repo_name)` - Create PR via `gh pr create`
  - `approve_pr(pr_number, repo_owner, repo_name)` - Approve PR via `gh pr review`
  - `merge_pr(pr_number, repo_owner, repo_name)` - Merge PR via `gh pr merge`
  - `finalize_git_operations(state, commit_message, pr_title, pr_body, repo_owner, repo_name)` - Orchestrate push → PR creation/update
  - Handle errors gracefully (branch exists, no changes to commit, PR already exists)

### 5. Create Worktree Operations Module
- Create `adws/adw_modules/worktree_ops.py` with functions:
  - `get_worktree_path(adw_id) -> str` - Return `trees/{adw_id}` path
  - `create_worktree(adw_id, branch_name, base_branch="main")` - Create with `git worktree add`
  - `validate_worktree(state) -> Tuple[bool, str]` - 3-way validation (state, filesystem, git)
  - `remove_worktree(adw_id)` - Remove with `git worktree remove -f`
  - `setup_worktree_environment(worktree_path, backend_port, frontend_port)` - Create `.ports.env`
  - `get_ports_for_adw(adw_id) -> Tuple[int, int]` - Deterministic port assignment (hash ADW ID to 9100-9114, 9200-9214)
  - `find_next_available_ports() -> Tuple[int, int]` - Fallback port allocation
  - `is_port_available(port) -> bool` - Check port binding with socket
  - Fetch latest from origin before creating worktree
  - Handle branch already exists (fallback to checkout)

### 6. Create Workflow Operations Module
- Create `adws/adw_modules/workflow_ops.py` with functions:
  - Define agent name constants (AGENT_PLANNER, AGENT_IMPLEMENTOR, AGENT_CLASSIFIER, etc.)
  - `classify_issue(issue, adw_id, working_dir, model) -> IssueClassSlashCommand` - Call `/classify_issue` agent
  - `build_plan(issue_class, issue, adw_id, working_dir, model) -> str` - Call issue_class agent (/chore, /bug, /feature)
  - `implement_plan(plan_file, adw_id, working_dir, model) -> bool` - Call `/implement` agent
  - `generate_branch_name(issue, adw_id, model) -> str` - Call `/generate_branch_name` agent
  - `create_commit_message(adw_id, working_dir, model) -> str` - Call `/commit` agent
  - `create_pull_request_description(issue, plan_file, adw_id, working_dir, model) -> str` - Call `/pull_request` agent
  - `create_or_find_branch(state, issue, repo_owner, repo_name) -> str` - Branch resolution logic
  - `find_spec_file(state, adw_id) -> str` - Locate plan file from state or filesystem
  - `create_and_implement_patch(review_feedback, adw_id, working_dir, model) -> bool` - Call `/patch` agent
  - Use `execute_template()` from agent.py for all agent calls
  - Parse agent responses and extract meaningful results

### 7. Create Utilities Module
- Create `adws/adw_modules/utils.py` with helpers:
  - `setup_logger(name, adw_id, phase_name) -> logging.Logger` - Configure logger with file + console output to `agents/{adw_id}/logs/{phase_name}.log`
  - `ensure_adw_id(issue_number=None, provided_adw_id=None) -> str` - Generate or validate ADW ID
  - `get_repo_config() -> Tuple[str, str]` - Read GITHUB_REPO_OWNER, GITHUB_REPO_NAME from env
  - `validate_required_env_vars(vars: List[str])` - Check required env vars exist
  - `truncate_output(text, max_length=500)` - Truncate long text for logging
  - `parse_args_for_adw_context(argv) -> Dict[str, Any]` - Parse command-line args for issue_number, adw_id, flags
  - Add rich console formatting helpers for success/failure messages

### 8. Update Agent Module with Model Selection
- Extend `adws/adw_modules/agent.py`:
  - Add `SLASH_COMMAND_MODEL_MAP` dictionary mapping slash commands to models
  - Add `ModelSet` support with "base" and "heavy" sets
  - Add `get_model_for_slash_command(slash_command, model_set) -> str` function
  - Update `execute_template()` to accept optional `model_set` parameter
  - Update `execute_template()` to read model_set from ADWState if working_dir provided
  - Add logic to auto-select model based on slash command and model_set
  - Keep backward compatibility with explicit model parameter

### 9. Create Package Initialization Files
- Create `adws/adw_modules/__init__.py`:
  - Import and expose all core modules (state, github, git_ops, worktree_ops, workflow_ops, utils, data_types)
  - Add version string
- Create `adws/adw_triggers/__init__.py`:
  - Import trigger_webhook
  - Add version string
- Create `adws/adw_tests/__init__.py`:
  - Import test modules
  - Add version string

### 10. Create Webhook Trigger System
- Create `adws/adw_triggers/trigger_webhook.py` with FastAPI app:
  - POST `/gh-webhook` endpoint:
    - Verify webhook signature with WEBHOOK_SECRET
    - Parse GitHub event (issues.opened, issue_comment.created)
    - Check for ADW_BOT_IDENTIFIER in issue body/comment (skip if found)
    - Look for "adw_" keyword in issue body/comment
    - Call `/classify_adw` agent to extract workflow_command, adw_id, model_set
    - Validate dependent workflows have existing ADW ID (build, test, review, document, ship require adw_id)
    - Create or update state file with extracted data
    - Launch workflow in background via subprocess.Popen with:
      - `start_new_session=True` (detached process)
      - `get_safe_subprocess_env()` filtered environment
      - Redirect stdout/stderr to `agents/{adw_id}/logs/{workflow_name}.log`
    - Return 200 immediately (meets GitHub 10-second timeout)
  - GET `/health` endpoint:
    - Return system status (Claude Code installed, env vars present, etc.)
  - Add error handling for malformed payloads
  - Add logging for all webhook events
  - Add CORS middleware if needed

### 11. Create Plan Workflow (Phase 1)
- Create `adws/adw_plan_iso.py`:
  - Accept args: `issue_number` (required), `adw_id` (optional)
  - Setup logger via utils.setup_logger()
  - Call ensure_adw_id() to get/create ADW ID
  - Load or create ADWState
  - Fetch GitHub issue via github.fetch_issue()
  - Validate worktree doesn't already exist
  - Allocate ports via worktree_ops.get_ports_for_adw()
  - Classify issue via workflow_ops.classify_issue()
  - Generate branch name via workflow_ops.generate_branch_name()
  - Create worktree via worktree_ops.create_worktree()
  - Setup worktree environment via worktree_ops.setup_worktree_environment()
  - Build plan via workflow_ops.build_plan() with worktree as working_dir
  - Generate commit message via workflow_ops.create_commit_message()
  - Commit changes via git_ops.commit_changes()
  - Generate PR description via workflow_ops.create_pull_request_description()
  - Finalize git operations via git_ops.finalize_git_operations()
  - Comment on issue at key steps via github.make_issue_comment()
  - Save final state via state.save()
  - Print summary with rich console formatting

### 12. Create Build Workflow (Phase 2)
- Create `adws/adw_build_iso.py`:
  - Accept args: `issue_number` (optional), `adw_id` (REQUIRED)
  - Fail fast if adw_id not provided
  - Setup logger via utils.setup_logger()
  - Load ADWState (must exist from plan phase)
  - Validate worktree exists via worktree_ops.validate_worktree()
  - Fetch issue from state or GitHub
  - Find plan file via workflow_ops.find_spec_file()
  - Implement plan via workflow_ops.implement_plan() with worktree as working_dir
  - Generate commit message via workflow_ops.create_commit_message()
  - Commit changes via git_ops.commit_changes()
  - Finalize git operations via git_ops.finalize_git_operations()
  - Comment on issue via github.make_issue_comment()
  - Save final state via state.save()
  - Print summary with rich console formatting

### 13. Create Test Workflow (Phase 3)
- Create `adws/adw_test_iso.py`:
  - Accept args: `issue_number` (optional), `adw_id` (REQUIRED), `--skip-e2e` (flag)
  - Fail fast if adw_id not provided
  - Setup logger via utils.setup_logger()
  - Load ADWState (must exist)
  - Validate worktree exists
  - Execute `/test` agent in worktree
  - If tests fail, continue with warning (don't block pipeline)
  - If `--skip-e2e` not set, execute `/test_e2e` agent
  - Comment test results on issue
  - Save state
  - Print summary

### 14. Create Review Workflow (Phase 4)
- Create `adws/adw_review_iso.py`:
  - Accept args: `issue_number` (optional), `adw_id` (REQUIRED), `--skip-resolution` (flag)
  - Fail fast if adw_id not provided
  - Setup logger
  - Load ADWState
  - Validate worktree exists
  - Execute `/review` agent in worktree
  - If `--skip-resolution` not set and review suggests changes:
    - Call workflow_ops.create_and_implement_patch()
    - Commit patch
    - Push changes
  - Comment review results on issue
  - Save state
  - Print summary

### 15. Create Document Workflow (Phase 5)
- Create `adws/adw_document_iso.py`:
  - Accept args: `issue_number` (optional), `adw_id` (REQUIRED)
  - Fail fast if adw_id not provided
  - Setup logger
  - Load ADWState
  - Validate worktree exists
  - Execute `/document` agent in worktree
  - Commit documentation changes
  - Push changes
  - Comment on issue
  - Save state
  - Print summary

### 16. Create Patch Workflow
- Create `adws/adw_patch_iso.py`:
  - Accept args: `issue_number` (optional), `adw_id` (REQUIRED), `feedback` (optional, from stdin)
  - Fail fast if adw_id not provided
  - Setup logger
  - Load ADWState
  - Validate worktree exists
  - Get review feedback from args or prompt user
  - Execute `/patch` agent with feedback in worktree
  - Commit patch changes
  - Push changes
  - Comment on issue
  - Save state
  - Print summary

### 17. Create Full SDLC Orchestrator
- Create `adws/adw_sdlc_iso.py`:
  - Accept args: `issue_number` (required), `adw_id` (optional), `--skip-e2e`, `--skip-resolution` (flags)
  - Setup logger
  - Execute phases in sequence:
    1. Call `adw_plan_iso.py` (creates worktree, generates plan)
    2. Call `adw_build_iso.py` (implements plan)
    3. Call `adw_test_iso.py` (runs tests, continues on failure with warning)
    4. Call `adw_review_iso.py` (reviews code)
    5. Call `adw_document_iso.py` (generates docs)
  - Pass flags through to child scripts
  - Handle failures: stop on phase failure (except test phase)
  - Print overall summary
  - Exit with appropriate code

### 18. Create New Slash Command Templates
- Create `.claude/commands/classify_issue.md`:
  - Input: GitHub issue JSON
  - Output: One of "/chore", "/bug", "/feature"
  - Instructions for classification based on keywords, labels, description
- Create `.claude/commands/generate_branch_name.md`:
  - Input: GitHub issue + adw_id
  - Output: Branch name format: `{type}-{issue_num}-adw-{adw_id}-{short-desc}`
  - Instructions for generating meaningful, Git-safe branch names
- Create `.claude/commands/commit.md`:
  - Input: Git diff context
  - Output: Commit message following conventional commits
  - Instructions for generating concise, descriptive commit messages
- Create `.claude/commands/pull_request.md`:
  - Input: Issue + plan file + changes
  - Output: PR title and body with issue linking
  - Instructions for creating comprehensive PR descriptions
- Create `.claude/commands/test.md`:
  - Instructions for running project tests and interpreting results
- Create `.claude/commands/review.md`:
  - Instructions for code review focusing on best practices, bugs, improvements
- Create `.claude/commands/document.md`:
  - Instructions for generating/updating documentation based on code changes
- Create `.claude/commands/patch.md`:
  - Input: Review feedback
  - Instructions for implementing fixes based on review comments
- Create `.claude/commands/classify_adw.md`:
  - Input: Issue body or comment text
  - Output: JSON with workflow_command, adw_id (optional), model_set (optional)
  - Instructions for extracting ADW workflow information from text

### 19. Update Configuration Files
- Update `.env.sample`:
  - Add `GITHUB_TOKEN=` (GitHub personal access token)
  - Add `GITHUB_REPO_OWNER=` (GitHub username or org)
  - Add `GITHUB_REPO_NAME=` (Repository name)
  - Add `WEBHOOK_SECRET=` (Secret for webhook signature verification)
  - Add `ADW_WEBHOOK_PORT=8000` (Port for webhook server)
  - Add comments explaining each variable
- Update `.gitignore`:
  - Add `trees/` (git worktrees)
  - Add `agents/` (agent outputs and state)
  - Add `.ports.env` (port configuration)
  - Add `*.db` (database files)
  - Add `adws/adw_data/` (ADW data directory)
  - Add `__pycache__/` if not already present
  - Add `*.pyc` if not already present

### 20. Create Testing Infrastructure
- Create `adws/adw_tests/health_check.py`:
  - Check Claude Code CLI is installed
  - Check all required env vars are set (ANTHROPIC_API_KEY, GITHUB_TOKEN, etc.)
  - Check `gh` CLI is installed and authenticated
  - Check git is configured (user.name, user.email)
  - Check write permissions to trees/, agents/ directories
  - Return detailed health report
- Create `adws/adw_tests/test_state.py`:
  - Test ADWState creation, load, save, update
  - Test missing file handling
  - Test validation
  - Test to_dict/from_dict
- Create `adws/adw_tests/test_github.py`:
  - Mock tests for GitHub operations (don't hit real API)
  - Test issue fetching, commenting, labeling
  - Test error handling
- Create `adws/adw_tests/test_git_ops.py`:
  - Test git operations in temporary test repo
  - Test branch creation, commits, pushing (with mocks)
- Create `adws/adw_tests/test_worktree_ops.py`:
  - Test worktree creation, validation, removal in temp directory
  - Test port allocation logic
  - Test environment setup

### 21. Update Documentation
- Update `adws/README.md`:
  - Add "Scaled ADW Structure" section with full architecture
  - Document all new modules and their purposes
  - Add workflow execution examples for each phase
  - Add webhook setup instructions
  - Add troubleshooting section
  - Update data flow diagram
- Update root `README.md`:
  - Add "Getting Started with Automated SDLC" section
  - Add webhook configuration steps for GitHub
  - Add environment setup instructions
  - Add example issue format for triggering workflows
  - Link to adws/README.md for detailed documentation

### 22. Create Example Issue Templates
- Create `.github/ISSUE_TEMPLATE/feature.md`:
  - Template for feature requests
  - Include "adw_plan_iso" or "adw_sdlc_iso" trigger keywords
  - Include model_set selection (optional)
- Create `.github/ISSUE_TEMPLATE/bug.md`:
  - Template for bug reports
  - Include trigger keywords
- Create `.github/ISSUE_TEMPLATE/chore.md`:
  - Template for chores/maintenance
  - Include trigger keywords

### 23. Add Workflow Execution Scripts
- Create `scripts/start_webhook_server.sh`:
  - Bash script to start webhook server with proper environment
  - Use uvicorn with reload for development
  - Log to agents/webhook/server.log
- Create `scripts/setup_github_webhook.sh`:
  - Helper script to configure GitHub webhook via `gh api`
  - Set webhook URL, secret, events (issues, issue_comment, pull_request)
- Create `scripts/test_health.sh`:
  - Run health_check.py and display results
  - Check all dependencies and configuration

### 24. Validate and Test
- Run `python -m py_compile adws/adw_modules/*.py` to check syntax
- Run `python -m py_compile adws/*.py` to check workflow scripts
- Run `python -m py_compile adws/adw_triggers/*.py` to check triggers
- Run `uv run adws/adw_tests/health_check.py` to validate system health
- Test ADWState creation: Create a test state, save, load, verify
- Test worktree operations: Create a test worktree, validate, remove
- Manually test adw_plan_iso.py with a test issue number
- Verify all files created match the spec

## Validation Commands
Execute these commands to validate the chore is complete:

- `python -m py_compile adws/adw_modules/*.py` - Validate all core modules compile
- `python -m py_compile adws/*.py` - Validate all workflow scripts compile
- `python -m py_compile adws/adw_triggers/*.py` - Validate trigger system compiles
- `python -m py_compile adws/adw_tests/*.py` - Validate test infrastructure compiles
- `uv run adws/adw_tests/health_check.py` - Run system health check
- `git ls-files | grep -E "^adws/adw_modules/(state|github|git_ops|worktree_ops|workflow_ops|data_types|utils).py$"` - Verify core modules exist
- `git ls-files | grep -E "^adws/adw_(plan|build|test|review|document|patch|sdlc)_iso.py$"` - Verify workflow scripts exist
- `git ls-files | grep -E "^.claude/commands/(classify_issue|generate_branch_name|commit|pull_request|test|review|document|patch|classify_adw).md$"` - Verify new slash commands exist
- `ls -la trees/ agents/` - Verify output directories exist (should be in .gitignore)
- `grep -E "(GITHUB_TOKEN|GITHUB_REPO_OWNER|WEBHOOK_SECRET)" .env.sample` - Verify env vars documented

## Notes

### Architecture Decisions
- **Modular Design**: Each workflow phase is independent, allowing manual intervention or automated chaining
- **State Persistence**: Single JSON file per ADW ID enables cross-phase communication and resumability
- **Worktree Isolation**: Git worktrees prevent conflicts and enable parallel development on multiple issues
- **Webhook Detachment**: Background process launching meets GitHub's 10-second timeout requirement
- **Agent Model Selection**: Dynamic model selection balances cost (sonnet) vs. capability (opus) based on task complexity
- **Bot Identifier**: Prevents infinite webhook loops when agent comments on issues

### Security Considerations
- **Environment Filtering**: Only pass required env vars to subprocesses (prevent leakage)
- **Webhook Signature Verification**: Validate GitHub webhook signatures with WEBHOOK_SECRET
- **Token Permissions**: GitHub token needs: repo (full), workflow, read:org
- **Subprocess Isolation**: Use filtered environment and validate inputs

### Scalability Notes
- **Port Allocation**: Deterministic hashing allows 15 concurrent worktrees (9100-9114, 9200-9214)
- **State Management**: File-based state is simple but limits concurrency; consider DB for high scale
- **Webhook Queue**: FastAPI handles concurrent requests, but consider task queue (Celery) for high volume
- **Worktree Cleanup**: Consider cron job to remove stale worktrees (>7 days old)

### Future Enhancements
- Add `adw_ship_iso.py` for automatic PR merging and deployment
- Add `adw_triggers/trigger_cron.py` for scheduled workflows
- Add database backend for state (SQLite → PostgreSQL)
- Add metrics tracking and observability dashboards
- Add retry logic for transient GitHub API failures
- Add support for multiple repositories
- Add CI/CD integration for running tests before PR creation
