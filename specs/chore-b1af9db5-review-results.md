# Chore: Review Results

## Metadata
adw_id: `b1af9db5`
prompt: `After a successful or failed review we need to take action.

If successful, we should merge the PR,

If failed we should trigger a new implement with the results of the review or we should create a new ADW, either way we should be listenning for the review on the github issue and a new agent should resolve this in a new thread`

## Chore Description
Implement automated post-review action handling that monitors PR review results and takes appropriate actions based on review outcomes. When a PR review completes (successful or failed), the system should:

1. **Parse review results** - Analyze the review output to determine approval status (APPROVED, CHANGES REQUESTED, NEEDS DISCUSSION)
2. **Handle success case** - If review is APPROVED:
   - Automatically merge the PR
   - Post confirmation to the issue thread
3. **Handle failure case** - If review has CHANGES REQUESTED:
   - Parse the review feedback and recommendations
   - Trigger a new implementation workflow with the review results as context
   - Create a new agent thread to address the review feedback
4. **Handle discussion case** - If review NEEDS DISCUSSION:
   - Post the results to the issue thread
   - Wait for manual intervention/decision

This creates a feedback loop where failed reviews automatically trigger new implementation attempts with the review findings as additional context.

## Relevant Files
Use these files to complete the chore:

- `apps/adw_server/core/handlers.py:960` - Contains `format_review_results()` which parses review output for approval status (lines 1004-1011). This logic needs to be extracted and enhanced.
- `apps/adw_server/core/handlers.py:778` - `handle_pull_request_event()` triggers review workflow and posts results. Needs to be enhanced to take action based on review status.
- `apps/adw_server/core/adw_integration.py:574` - `trigger_review_workflow()` returns WorkflowResult with review output. This is where we get review results from.
- `apps/adw_server/core/adw_integration.py:401` - `trigger_chore_implement_workflow()` can be called to re-implement with review feedback as additional context.
- `.claude/commands/review.md:46` - Documents the review approval status format: `[APPROVED / CHANGES REQUESTED / NEEDS DISCUSSION]`
- `adws/adw_modules/github.py` - May contain GitHub API integration for PR merging (needs investigation)
- `apps/adw_server/core/handlers.py:260` - `make_github_issue_comment()` function for posting comments to issues
- `README.md:129` - Documents PR review workflow behavior, needs update for automatic merge/re-implement logic

### New Files
- `apps/adw_server/core/review_actions.py` - New module containing review result parsing and action handling logic
- `tests/test_review_actions.py` - Unit tests for review action handling

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Understand Current Review Workflow
- Read `apps/adw_server/core/handlers.py:778-958` to understand how PR reviews are currently triggered and results posted
- Read `.claude/commands/review.md` to understand the review output format and approval statuses
- Read `apps/adw_server/core/adw_integration.py:574-788` to understand WorkflowResult structure returned by reviews
- Identify where approval status is extracted from review output (currently in `format_review_results()`)

### 2. Create Review Result Parser
- Create new file `apps/adw_server/core/review_actions.py`
- Add function `parse_review_status(review_output: str) -> tuple[str, str, list[str]]`
  - Return tuple of: (approval_status, summary, recommendations)
  - Parse approval status: APPROVED, CHANGES_REQUESTED, NEEDS_DISCUSSION
  - Extract summary section from review output
  - Extract recommendations list from review output
  - Handle cases where review output format is unexpected (fallback to NEEDS_DISCUSSION)
- Add function `extract_review_issues(review_output: str) -> dict[str, list[str]]`
  - Parse issues by severity: Critical, Moderate, Minor
  - Return dict with severity levels as keys and issue lists as values
  - Use regex to extract sections: `## Issues Found` followed by severity subsections

### 3. Implement PR Merge Functionality
- Add function `merge_pull_request(pr_number: int, repo_owner: str, repo_name: str, logger: Optional[logging.Logger] = None) -> bool` to `review_actions.py`
- Use GitHub CLI (`gh pr merge`) to merge the PR
- Parameters:
  - Use `--squash` merge method (configurable later)
  - Use `--auto` to merge when all checks pass
  - Pass proper repo context: `--repo owner/repo`
- Handle GitHub PAT token from environment (`GITHUB_PAT`, `GH_TOKEN`, or `GITHUB_TOKEN`)
- Return True if merge successful, False otherwise
- Add proper error handling and logging

### 4. Implement Re-Implementation Trigger
- Add function `trigger_reimplementation(issue_number: int, original_prompt: str, review_feedback: str, adw_id: str, model: str, working_dir: str, repo_owner: str, repo_name: str, issue_title: str, logger: Optional[logging.Logger] = None) -> tuple[WorkflowResult, Optional[WorkflowResult]]` to `review_actions.py`
- Build enhanced prompt that includes:
  - Original issue description
  - Review feedback section with:
    - Approval status
    - Issues found (by severity)
    - Recommendations
  - Clear instruction to address review feedback
- Call `trigger_chore_implement_workflow()` from adw_integration module with enhanced prompt
- Use a new ADW ID for the re-implementation (not the review ADW ID)
- Return the workflow results (chore_result, impl_result)

### 5. Create Action Handler Function
- Add async function `handle_review_results(review_result: WorkflowResult, pr_number: int, issue_numbers: list[int], repo_full_name: str, original_prompt: str, issue_title: str, model: str, working_dir: str, logger: Optional[logging.Logger] = None) -> dict` to `review_actions.py`
- Parse review status using `parse_review_status()`
- Based on status, take action:
  - **APPROVED**: Call `merge_pull_request()` and post success comment to issues
  - **CHANGES_REQUESTED**: Call `trigger_reimplementation()` and post re-implementation started comment to issues
  - **NEEDS_DISCUSSION**: Post review results to issues and request manual intervention
- Return dict with action taken, success status, and any additional context
- Handle errors gracefully, log failures, return error details in result dict

### 6. Integrate Action Handler into PR Event Handler
- Update `handle_pull_request_event()` in `apps/adw_server/core/handlers.py`
- After review workflow completes (line 890), call `handle_review_results()`
- Pass all necessary context: review_result, pr_number, issue_numbers, repo info, etc.
- Store original issue prompt/description for re-implementation context
  - Fetch issue details using `gh issue view {issue_number} --json title,body`
  - Extract title and body for re-implementation prompt
- Update comment posting logic to reflect action taken (merged, re-implementing, or needs discussion)
- Add logging to track action execution flow

### 7. Handle Merge Success/Failure Comments
- Add function `post_merge_comment(issue_number: int, repo_full_name: str, pr_number: int, pr_url: str, adw_id: str, merge_success: bool) -> bool` to `review_actions.py`
- If merge successful:
  - Post success comment: "✅ **PR Merged Successfully**"
  - Include PR link, ADW ID, review summary
  - Thank contributors and close loop
- If merge failed:
  - Post failure comment: "⚠️ **Automatic Merge Failed**"
  - Include error details and manual merge instructions
  - Suggest manual review or re-running workflow

### 8. Handle Re-Implementation Comments
- Add function `post_reimplementation_comment(issue_number: int, repo_full_name: str, review_adw_id: str, new_adw_id: str, review_feedback: str) -> bool` to `review_actions.py`
- Post comment indicating new implementation cycle started:
  - "🔄 **Re-Implementation Started**"
  - Include original review ADW ID and new implementation ADW ID
  - Summarize review feedback that needs to be addressed
  - Link to new workflow logs location
- Handle cases where re-implementation itself fails

### 9. Add Configuration for Action Behavior
- Add configuration settings to `apps/adw_server/core/config.py`:
  - `AUTO_MERGE_ON_APPROVAL: bool = True` - Enable/disable automatic merging
  - `AUTO_REIMPLEMENT_ON_CHANGES: bool = True` - Enable/disable automatic re-implementation
  - `MERGE_METHOD: str = "squash"` - PR merge method (squash, merge, rebase)
  - `MAX_REIMPLEMENT_ATTEMPTS: int = 3` - Prevent infinite re-implementation loops
- Update settings class to include these new configuration options
- Document in `.env.example` with sensible defaults

### 10. Implement Re-Implementation Loop Protection
- Add tracking mechanism to prevent infinite re-implementation loops
- Store re-implementation attempts in a simple dict/cache: `{issue_number: attempt_count}`
- Check attempt count before triggering re-implementation
- If max attempts reached:
  - Post comment: "⚠️ **Maximum Re-Implementation Attempts Reached**"
  - Suggest manual intervention
  - Log warning and skip automatic re-implementation
- Reset counter when PR is merged or closed

### 11. Add Comprehensive Tests
- Create `tests/test_review_actions.py` with pytest tests
- Test `parse_review_status()`:
  - Test parsing APPROVED status
  - Test parsing CHANGES_REQUESTED status
  - Test parsing NEEDS_DISCUSSION status
  - Test malformed review output (fallback behavior)
- Test `extract_review_issues()`:
  - Test parsing issues by severity
  - Test missing sections
  - Test empty issues
- Test `merge_pull_request()` with mocked gh CLI calls
- Test `trigger_reimplementation()` with mocked workflow calls
- Test `handle_review_results()`:
  - Test APPROVED flow (calls merge)
  - Test CHANGES_REQUESTED flow (calls re-implement)
  - Test NEEDS_DISCUSSION flow (posts comment only)
  - Test error handling in each case
- Test loop protection mechanism

### 12. Update Documentation
- Update `README.md:129` to document automatic post-review actions
- Add section explaining:
  - Automatic merge on APPROVED reviews
  - Automatic re-implementation on CHANGES_REQUESTED
  - Manual intervention on NEEDS_DISCUSSION
  - Configuration options for enabling/disabling these behaviors
  - Loop protection mechanism
- Update `apps/adw_server/README.md` with same information
- Add troubleshooting section for common issues:
  - Merge failures due to conflicts
  - Re-implementation loop scenarios
  - GitHub permissions needed for merging

### 13. Validate Implementation
- Test with real PR review workflow:
  - Create test PR that passes review
  - Verify automatic merge occurs
  - Verify success comment posted to issue
- Test with failing review:
  - Create test PR with intentional issues
  - Verify re-implementation workflow triggered
  - Verify new ADW ID generated
  - Verify review feedback included in re-implementation prompt
- Test loop protection:
  - Trigger multiple review failures on same issue
  - Verify loop protection activates after max attempts
- Verify all tests pass: `uv run pytest tests/test_review_actions.py -v`

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile apps/adw_server/core/review_actions.py` - Verify review_actions.py compiles without syntax errors
- `uv run python -m py_compile apps/adw_server/core/handlers.py` - Verify handlers.py compiles after updates
- `uv run python -m py_compile apps/adw_server/core/config.py` - Verify config.py compiles with new settings
- `uv run pytest tests/test_review_actions.py -v` - Run review action tests and verify all pass
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `grep -r "handle_review_results" apps/adw_server/` - Verify action handler is implemented and integrated
- `grep -r "merge_pull_request" apps/adw_server/` - Verify merge functionality is implemented
- `grep -r "trigger_reimplementation" apps/adw_server/` - Verify re-implementation trigger is implemented
- `grep -r "AUTO_MERGE_ON_APPROVAL" apps/adw_server/` - Verify configuration options are defined

## Notes

### Review Status Detection
The `/review` command outputs an approval status in the format:
```
## Approval Status
[APPROVED / CHANGES REQUESTED / NEEDS DISCUSSION]
```

We need to parse this reliably, with fallback handling for cases where the format is unexpected.

### PR Merge Permissions
Automatic merging requires:
- GitHub PAT token with `repo` scope (read/write access)
- Branch protection rules allow merging (no required reviews/checks that would block)
- PR is in mergeable state (no conflicts, checks passing)

If merge fails, the system should gracefully handle it and suggest manual merge.

### Re-Implementation Context
When triggering re-implementation, the prompt should include:
1. Original issue description
2. Review feedback section with:
   - Approval status and reason
   - Critical/Moderate/Minor issues found
   - Specific recommendations
3. Clear instruction: "Address the review feedback above while implementing this issue"

This gives the agent full context to fix the issues identified in the review.

### Loop Protection Strategy
To prevent infinite re-implementation loops:
- Track attempts per issue number (not per ADW ID)
- Reset counter when PR is merged or manually closed
- Use configurable max attempts (default: 3)
- After max attempts, require manual intervention

This prevents scenarios where the agent repeatedly generates code that fails review.

### Future Enhancements
- Support for draft PRs (skip auto-merge, only review)
- Integration with GitHub Checks API to block merge if tests fail
- Custom merge strategies per repository
- Webhook event for PR merge to trigger deployment workflows
- Support for incremental fixes (apply review suggestions without full re-implementation)
- AI-powered review feedback summarization for complex reviews
- Support for multi-PR workflows (e.g., stacked PRs)

### Error Handling Considerations
Each action (merge, re-implement) can fail for various reasons:
- **Merge failures**: Conflicts, permissions, branch protection
- **Re-implementation failures**: Agent errors, timeout, Claude API issues
- **GitHub API failures**: Rate limits, authentication, network issues

Each failure should be logged, communicated to the user via issue comment, and not block the overall workflow.
