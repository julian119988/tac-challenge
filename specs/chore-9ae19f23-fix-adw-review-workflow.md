# Chore: Fix ADW Review Workflow

## Metadata
adw_id: `9ae19f23`
prompt: `Issue #44: ADW review not working

The ADW is not making a review after a PR is posted on an issue`

## Chore Description
The ADW review workflow that was implemented in issue #40 is not working correctly. When a pull request is created that references an issue (e.g., "Closes #42"), the webhook server should trigger an automated code review and post the results to the issue thread. However, the review workflow is not executing properly.

After analyzing the codebase, the root cause is that the `trigger_review_workflow()` function doesn't check out the PR branch before running the review. The `/review` command executes `git diff` on the current branch, which means it's reviewing the wrong code (likely the main branch instead of the PR branch).

## Relevant Files
Use these files to complete the chore:

- `apps/adw_server/core/adw_integration.py:573` - The `trigger_review_workflow()` function that needs to be fixed. Currently it doesn't fetch or checkout the PR branch before reviewing.
- `apps/adw_server/core/handlers.py:778` - The `handle_pull_request_event()` function that calls the review workflow. It extracts PR details but doesn't pass branch information.
- `adws/adw_modules/git_ops.py` - Contains git helper functions like `checkout_branch()`, `fetch_remote()` that should be used.
- `.claude/commands/review.md` - The review command template that analyzes `git diff` changes.
- `tests/test_pr_review.py` - Existing tests for PR review workflow that may need updates.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Understand Current Git Flow
- Read `adws/adw_modules/git_ops.py` to understand available git operations
- Verify functions exist for: fetching remote branches, checking out branches
- Read `.claude/commands/review.md` to understand what the review command expects (it uses `git diff`)
- Understand that the review runs in the working directory context

### 2. Add PR Branch Checkout to Review Workflow
- Update `trigger_review_workflow()` in `apps/adw_server/core/adw_integration.py`
- Before calling `execute_template()`, add git operations to:
  - Fetch the PR branch from remote: `git fetch origin pull/{pr_number}/head:pr-{pr_number}`
  - Checkout the PR branch: `git checkout pr-{pr_number}`
  - Log the current branch and commit to verify correct checkout
- Use helper functions from `git_ops.py` if available, otherwise use subprocess
- Add error handling for git operations (branch already exists, fetch failures, etc.)
- After review completes, checkout back to the original branch to clean up

### 3. Pass PR Context to Review Command
- The `/review` command should have context about what it's reviewing
- Consider passing PR number and repo info as context in the working directory
- Ensure the review analyzes the diff between the PR branch and the base branch (main)

### 4. Handle Git State Management
- Store the current branch before checkout: `current_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])`
- After review workflow completes (success or failure), restore original branch
- Use try/finally block to ensure cleanup happens even if review fails
- Delete the temporary PR branch after review: `git branch -D pr-{pr_number}`

### 5. Update Error Handling
- If git operations fail (fetch, checkout), return a WorkflowResult with success=False
- Include detailed error messages about which git operation failed
- Don't attempt to run review if checkout fails
- Log all git commands for debugging

### 6. Test the Fix
- Run existing tests: `uv run pytest tests/test_pr_review.py -v`
- Manually test by:
  - Creating a test branch with changes
  - Simulating a PR webhook event
  - Verifying the review runs on the correct branch
  - Verifying the original branch is restored after review

### 7. Validate Review Workflow End-to-End
- Trigger a real PR review workflow
- Check that the review comments are posted to the issue thread
- Verify the git repository is left in a clean state (on original branch)
- Check logs to ensure PR branch was checked out correctly
- Verify review output contains actual PR changes, not main branch changes

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile apps/adw_server/core/adw_integration.py` - Verify code compiles
- `uv run pytest tests/test_pr_review.py -v` - Run PR review tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `git status` - Verify repository is in clean state after test
- `git branch` - Verify no temporary PR branches remain

## Notes

### Git Operations for PR Review

The correct git flow for reviewing a PR is:

```bash
# Save current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Fetch the PR branch from GitHub
git fetch origin pull/{pr_number}/head:pr-{pr_number}

# Checkout the PR branch
git checkout pr-{pr_number}

# Run review (git diff will now show PR changes)
# ... review workflow executes here ...

# Cleanup: go back to original branch
git checkout $current_branch

# Delete temporary PR branch
git branch -D pr-{pr_number}
```

### Alternative: Use Git Diff with Refs

Instead of checking out the branch, we could pass the PR ref to git diff:
```bash
git fetch origin pull/{pr_number}/head
git diff main...FETCH_HEAD
```

However, checking out the branch is cleaner because:
- The `/review` command already uses `git diff` without arguments
- It allows running tests in the PR context
- It's easier to debug (can see exactly what state the code is in)

### Error Recovery

If the workflow crashes mid-execution, the repository might be left on the PR branch. To prevent this:
- Always use try/finally to ensure cleanup
- Log the current branch at start and end
- Consider adding a cleanup check at workflow startup to delete any stale pr-* branches

### Test Execution Context

When running tests as part of the review, they should run against the PR code, not main. This means:
- Checkout must happen before test execution
- Tests should be isolated (not affect main branch)
- Test failures should be reported but not block PR review posting
