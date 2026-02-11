# Chore: Check Branches Before ADW Creation

## Metadata
adw_id: `649f7e32`
prompt: `Issue #9: Check branches

We should always make sure that we are on an updated main branch before creating any adw.`

## Chore Description
Ensure that all ADW workflows verify and update the main branch before creating new branches for work. This prevents creating branches from stale code and ensures all new work is based on the latest changes from the remote repository. The check should:

1. Verify we're starting from the main branch (or switch to it)
2. Fetch the latest changes from the remote repository
3. Update the local main branch to match the remote
4. Only then create the new working branch

This is critical for maintaining a clean git history and preventing merge conflicts or working from outdated code.

## Relevant Files
Use these files to complete the chore:

- `adws/adw_modules/git_ops.py` - Contains git operation functions including `create_branch()` that needs to be enhanced to check for updated main branch first
- `adws/adw_modules/worktree_ops.py` - Contains `create_worktree()` function at line 26 that already fetches from origin but should ensure main is updated
- `apps/adw_server/core/adw_integration.py` - Integration layer that calls `create_branch()` at line 330, needs to ensure main is updated before branch creation
- `adws/adw_modules/workflow_ops.py` - Contains `create_or_find_branch()` function at line 387 that generates branch names

### New Files
- None required - we'll enhance existing functions

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Main Branch Verification Function
- Create a new function `ensure_main_branch_updated()` in `adws/adw_modules/git_ops.py`
- Function should:
  - Accept `working_dir` and optional `logger` parameters
  - Check current branch and switch to main if needed
  - Fetch latest changes from origin
  - Reset local main to match origin/main (or pull with fast-forward)
  - Return tuple of (success: bool, error_message: str)
- Add proper error handling and logging

### 2. Update create_branch Function
- Modify `create_branch()` function in `adws/adw_modules/git_ops.py` (line 37)
- Add call to `ensure_main_branch_updated()` before creating new branch
- Pass logger parameter through for proper logging
- Return False if main branch update fails
- Ensure new branch is created from updated main

### 3. Update create_worktree Function
- Review `create_worktree()` in `adws/adw_modules/worktree_ops.py` (line 26)
- Currently fetches from origin (line 52) but doesn't verify local main is updated
- Ensure worktrees are created from `origin/base_branch` which already happens (line 76)
- Add logging to confirm worktree is being created from latest remote branch
- No changes needed if already using `origin/{base_branch}` as the starting point

### 4. Update ADW Integration Layer
- Review `trigger_chore_implement_workflow()` in `apps/adw_server/core/adw_integration.py` (line 256)
- The branch creation logic (lines 311-334) should use the updated `create_branch()` function
- Ensure proper error handling if branch creation fails due to main update failure
- Add logging to track main branch update status

### 5. Add Unit Tests
- Create test cases for `ensure_main_branch_updated()` function
- Test scenarios:
  - Successfully updating main branch
  - Handling case when already on main branch
  - Handling case when on different branch
  - Error handling for fetch failures
  - Error handling for merge/reset failures

### 6. Validate Implementation
- Run manual tests to verify branch creation workflow
- Ensure main branch is updated before each new ADW branch
- Verify proper error messages when main update fails
- Test with both direct `create_branch()` calls and full workflow execution

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile adws/adw_modules/git_ops.py` - Verify git_ops.py compiles without errors
- `uv run python -m py_compile adws/adw_modules/worktree_ops.py` - Verify worktree_ops.py compiles without errors
- `uv run python -m py_compile apps/adw_server/core/adw_integration.py` - Verify adw_integration.py compiles without errors
- `git checkout -b test-branch-check main` - Create test branch
- Manual test: Trigger a chore workflow and verify main is fetched/updated in logs
- `git branch -D test-branch-check` - Clean up test branch

## Notes
- The `create_worktree()` function already uses `origin/{base_branch}` as the base (line 76 in worktree_ops.py), which is good practice as it creates from the remote branch directly
- The main concern is `create_branch()` in regular workflows which may create branches from a stale local main
- We should maintain backward compatibility - if main update fails, we should log a warning but consider whether to fail hard or continue
- Consider making the main branch name configurable (currently hardcoded as "main" in some places, but some repos use "master")
