# Chore: Fix ADW Review - Checkout PR Branch Before Review

## Metadata
adw_id: `c29ba9c9`
prompt: `Issue #44: ADW review not working

The ADW is not making a review after a PR is posted on an issue`

## Chore Description
Fix the ADW review workflow to properly checkout the PR branch before running the review. Currently, when a PR webhook is received, the review workflow executes `/review` which runs `git diff`, but the working directory is still on the main branch (or whatever branch the server is on), not the PR branch. This results in an empty diff and no actual code review.

The fix involves:
1. Fetching the PR branch from the remote repository
2. Checking out the PR branch in a safe manner (using worktrees or stashing changes)
3. Running the review workflow on the checked-out PR branch
4. Returning to the original branch after the review completes

## Relevant Files
Use these files to complete the chore:

- `apps/adw_server/core/adw_integration.py:573-675` - The `trigger_review_workflow()` function that needs to checkout the PR branch before executing the review
- `adws/adw_modules/git_ops.py` - Git operations module that may already have helper functions for branch operations
- `adws/adw_modules/worktree_ops.py` - Worktree operations that provide a safer way to checkout branches without affecting the main working directory
- `apps/adw_server/core/handlers.py:778-947` - The `handle_pull_request_event()` function that calls `trigger_review_workflow()` - may need to pass PR branch information
- `.claude/commands/review.md` - The review command template to understand what it expects
- `tests/test_pr_review.py` - Tests for PR review workflow that may need updates

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Understand Current Git Operations
- Read `adws/adw_modules/git_ops.py` to see available git helper functions
- Read `adws/adw_modules/worktree_ops.py` to understand worktree operations
- Determine the best approach: worktree (isolated) vs direct checkout (affects main dir)
- Check if there are existing functions for fetching and checking out PR branches

### 2. Analyze PR Webhook Data
- Review `apps/adw_server/core/handlers.py:778-947` to see what PR data is available
- Check `PullRequestWebhookPayload` model to see if it includes branch information
- Identify the PR head ref (branch name) and base ref (target branch) from the webhook payload
- Understand the repository structure (owner/repo) available in the payload

### 3. Design the Solution
- Choose between two approaches:
  - **Option A (Worktree)**: Create an isolated worktree for the PR branch, review there, then cleanup
    - Pros: Doesn't affect main working directory, safer for concurrent reviews
    - Cons: More complex, requires disk space
  - **Option B (Direct Checkout)**: Fetch and checkout PR branch, review, then return to original branch
    - Pros: Simpler implementation
    - Cons: Affects main working directory, potential conflicts with concurrent operations
- Document the chosen approach and rationale

### 4. Extract PR Branch Information from Webhook
- Update `handle_pull_request_event()` in `apps/adw_server/core/handlers.py`
- Extract the following from `pr_payload.pull_request`:
  - `head.ref` - The PR branch name (e.g., "feature-branch")
  - `head.sha` - The commit SHA being reviewed
  - `base.ref` - The target branch (e.g., "main")
- Pass this information to `trigger_review_workflow()`

### 5. Update trigger_review_workflow Signature
- Modify `trigger_review_workflow()` in `apps/adw_server/core/adw_integration.py:573`
- Add parameters for PR branch information:
  - `pr_branch: str` - The branch name to checkout
  - `pr_sha: str` - The specific commit SHA to review
  - `base_branch: str` - The target branch for comparison
- Update function docstring with new parameters

### 6. Implement Branch Checkout Logic
- In `trigger_review_workflow()`, before calling `execute_template()`:
  - Save the current branch name (`git rev-parse --abbrev-ref HEAD`)
  - Fetch the PR branch: `git fetch origin {pr_branch}`
  - Checkout the PR branch: `git checkout {pr_branch}` or use worktree
  - Optionally: Reset to specific SHA: `git reset --hard {pr_sha}`
- Add proper error handling for git operations
- Log each git operation for debugging

### 7. Ensure Review Runs on PR Branch
- Verify that when `execute_template()` is called with `/review`, it will run on the checked-out PR branch
- The `/review` command should execute `git diff {base_branch}...{pr_branch}` to see changes
- May need to pass base branch information to the review command as an argument

### 8. Cleanup After Review
- After `execute_template()` completes (in try/finally block):
  - If using worktree: Remove the worktree
  - If using direct checkout: Return to the original branch
  - Clean up any temporary files or stashed changes
- Ensure cleanup happens even if review fails or throws an exception

### 9. Update Review Command
- Review `.claude/commands/review.md` to see if it needs updates
- If needed, modify the review command to accept a base branch parameter
- Ensure it compares the current branch against the base branch: `git diff {base_branch}...HEAD`

### 10. Handle Edge Cases
- What if the PR branch has already been deleted (merged/closed PR)?
  - Skip review or use the commit SHA directly
- What if there are uncommitted changes in the working directory?
  - Stash before checkout, pop after returning
- What if multiple reviews are running concurrently?
  - Use worktrees with unique directory names per adw_id
- What if git operations fail (network issues, permission problems)?
  - Log errors, post error comment to issue, return gracefully

### 11. Update Tests
- Modify `tests/test_pr_review.py` to test the new branch checkout logic
- Add test for successful PR branch checkout and review
- Add test for handling git operation failures
- Add test for cleanup after review (returns to original branch)
- Mock git operations to avoid actual git commands in tests

### 12. Test the Implementation
- Manually test with a real PR:
  - Create a test issue
  - Create a test PR that references the issue (e.g., "Closes #N")
  - Verify webhook triggers review workflow
  - Check that PR branch is checked out
  - Verify review runs successfully with actual diff
  - Confirm review results are posted to issue
  - Verify original branch is restored after review
- Check server logs for git operation output
- Verify no side effects in working directory

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile apps/adw_server/core/adw_integration.py` - Verify adw_integration.py compiles
- `uv run python -m py_compile apps/adw_server/core/handlers.py` - Verify handlers.py compiles
- `uv run pytest tests/test_pr_review.py -v` - Run PR review tests
- `uv run pytest tests/ -k review -v` - Run all review-related tests
- `git status` - Verify working directory is clean after tests
- `git branch` - Verify no temporary branches were left behind

## Notes

### Why This Bug Occurred
The original implementation of the review workflow assumed that the code to review would already be in the working directory. This works for local development where you manually checkout branches, but for automated PR reviews triggered by webhooks, the server's working directory is typically on the main/default branch.

### Worktree vs Direct Checkout
**Recommendation: Use worktrees for production, direct checkout for simplicity**

Worktrees provide better isolation but are more complex. For an initial fix, direct checkout may be sufficient if:
- Reviews are serialized (one at a time)
- The working directory is dedicated to this server (no human developers using it)

For production with concurrent reviews, worktrees are safer:
```bash
# Create isolated worktree for PR review
git worktree add agents/{adw_id}/reviewer-worktree {pr_branch}
cd agents/{adw_id}/reviewer-worktree
# Run review here
cd ../../../..
git worktree remove agents/{adw_id}/reviewer-worktree
```

### Base Branch Comparison
The review should show what changed in the PR, which is the diff between the PR branch and the base branch (usually main). This is done with:
```bash
git diff {base_branch}...{pr_branch}
```

The `...` (three dots) syntax shows changes in `pr_branch` since it diverged from `base_branch`, which is exactly what we want for PR review.

### Alternative: Fetch PR Directly
GitHub allows fetching PRs directly without knowing the branch name:
```bash
git fetch origin pull/{pr_number}/head:pr-{pr_number}
git checkout pr-{pr_number}
```

This is more reliable since branch names might conflict or be deleted, but we have the PR number and the commit SHA is immutable.

### Security Considerations
- **Code execution risk**: Checking out untrusted PR code and running tests could be dangerous if the PR contains malicious code
- **Mitigation**: Run in isolated environment (container/VM) or at minimum use worktrees
- **Trust level**: Since this is for internal team repos, risk is lower, but still good to be aware

### Future Enhancements
- Support reviewing specific commit ranges within a PR
- Cache PR branches locally to speed up subsequent reviews
- Parallel review execution using multiple worktrees
- Integration with GitHub Checks API to show review progress
