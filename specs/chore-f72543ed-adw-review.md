# Chore: ADW Review

## Metadata
adw_id: `f72543ed`
prompt: `Issue #40: ADW Review

I would like to create a new adw workflow.

We should listen when a PR is uploaded to an issue and trigger this new workflow.

This workflow should review, take screenshots and execute test to make sure the PR is ready for merge.

The review should be posted in the same github issue thread.

Please take a look at the example folder to guide yourself.`

## Chore Description
Create a new ADW review workflow that automatically triggers when a pull request is created or updated that references an issue. This workflow will:

1. **Detect PR events** - Listen for PR creation/updates via GitHub webhooks
2. **Link to issues** - Identify which issue the PR is addressing
3. **Execute review workflow** - Run automated review, screenshots, and tests
4. **Post results** - Comment the review findings back to the original issue thread

The workflow should provide comprehensive PR validation including:
- Code review analysis using Claude
- Screenshot capture for UI changes (if applicable)
- Test execution to ensure all tests pass
- Summary report posted to the issue thread

## Relevant Files
Use these files to complete the chore:

- `apps/adw_server/core/handlers.py:744` - Currently has `handle_pull_request_event()` stub that logs but doesn't trigger workflows. This needs to be enhanced to trigger the review workflow.
- `apps/adw_server/core/adw_integration.py` - Contains workflow trigger functions like `trigger_chore_workflow()` and `trigger_implement_workflow()`. Need to add `trigger_review_workflow()` function here.
- `.claude/commands/review.md` - The `/review` slash command template that will be executed by the workflow. This should already exist and contain the review logic.
- `adws/adw_modules/agent.py` - Core agent execution module that provides `execute_template()` function used by all workflows.
- `apps/adw_server/core/handlers.py:84` - Contains `IssueWebhookPayload` and `PullRequestWebhookPayload` Pydantic models for webhook data.
- `adws/adw_modules/github.py` - GitHub API integration module (if exists) for operations like fetching PR details.
- `README.md:118` - Documents webhook configuration and supported events. Needs update to mention PR review workflow.
- `apps/adw_server/README.md:99` - Documents webhook endpoints and event handling. Needs update to document PR review workflow.

### New Files
- `specs/chore-f72543ed-adw-review.md` - This plan file
- `tests/test_pr_review.py` - Unit tests for PR review workflow integration

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Understand Current PR Handling
- Read `apps/adw_server/core/handlers.py:744` to see the current `handle_pull_request_event()` implementation
- Read `apps/adw_server/core/handlers.py:134` to understand the `PullRequestWebhookPayload` structure
- Read `.claude/commands/review.md` to understand what parameters the `/review` command expects
- Understand how PR events link to issues (via PR description "Closes #N" or issue references)

### 2. Create Review Workflow Trigger Function
- Add `trigger_review_workflow()` function to `apps/adw_server/core/adw_integration.py`
- Function signature: `async def trigger_review_workflow(pr_number: int, repo_full_name: str, adw_id: Optional[str] = None, model: Literal["sonnet", "opus"] = "sonnet", working_dir: Optional[str] = None) -> WorkflowResult`
- Use `execute_template()` with `/review` slash command
- Pass PR number and repo information to the review command
- Create agent output directory: `agents/{adw_id}/reviewer/`
- Return `WorkflowResult` with success status, output, and session info
- Handle errors gracefully with try/except and proper logging

### 3. Extract Issue References from PR
- Add helper function `extract_issue_references(pr_body: str) -> list[int]` to `apps/adw_server/core/handlers.py`
- Parse PR body/description for patterns like "Closes #123", "Fixes #456", "Resolves #789"
- Support common GitHub issue reference keywords: closes, fixes, resolves (case-insensitive)
- Return list of issue numbers found in the PR description
- Use regex pattern: `r'(?:closes|fixes|resolves)\s+#(\d+)'` with case-insensitive flag

### 4. Implement PR Event Handler
- Update `handle_pull_request_event()` in `apps/adw_server/core/handlers.py`
- Trigger on actions: `opened`, `synchronize` (when PR is updated with new commits)
- Extract issue references from PR body using the new helper function
- If no issue references found, log and skip workflow (return early)
- Generate unique `adw_id` for the workflow execution
- Post initial comment to the **issue thread** (not PR) indicating review has started
- Call `trigger_review_workflow()` with PR details
- Handle exceptions with try/except, log errors, post error comment to issue
- Post completion comment to the **issue thread** with review results

### 5. Format Review Results for Issue Comment
- Add helper function `format_review_results(review_output: str, pr_number: int, pr_url: str, adw_id: str) -> str` to `apps/adw_server/core/handlers.py`
- Parse review workflow output for key information:
  - Test results (pass/fail counts)
  - Code review findings (if available in output)
  - Screenshot references (if applicable)
- Create formatted markdown comment with sections:
  - Header: "🔍 **Pull Request Review**"
  - PR link and number
  - Review summary
  - Test results (with pass/fail emoji indicators)
  - Screenshots section (if applicable)
  - ADW metadata (adw_id, logs location)
- Return formatted string ready for GitHub comment posting

### 6. Handle Screenshots (Future Enhancement)
- Document in code comments how screenshots could be integrated
- Review workflow should capture screenshots if UI changes detected
- Screenshots should be saved to `agents/{adw_id}/reviewer/screenshots/`
- For now, just log if screenshots are found in output directory
- Future: Could upload screenshots to GitHub as PR comments or store in issue

### 7. Update Webhook Event Routing
- Ensure `apps/adw_server/server.py` routes PR webhook events to `handle_pull_request_event()`
- Verify PR events are enabled in webhook configuration
- Add logging to track PR event processing

### 8. Add Tests for PR Review Workflow
- Create `tests/test_pr_review.py` with pytest tests
- Test `extract_issue_references()` with various PR body formats:
  - Single issue: "Closes #123"
  - Multiple issues: "Fixes #123 and resolves #456"
  - No references: "Some PR description"
  - Mixed case: "CLOSES #123", "fixes #456"
- Test `format_review_results()` output formatting
- Test `trigger_review_workflow()` with mocked `execute_template()`
- Test `handle_pull_request_event()` with mocked ADW integration:
  - Test 'opened' action triggers review
  - Test 'synchronize' action triggers review
  - Test 'closed' action does not trigger review
  - Test PR without issue references skips workflow
  - Test error handling and comment posting

### 9. Update Documentation
- Update `README.md:118` to document PR review workflow
- Add section explaining that PRs linked to issues will be automatically reviewed
- Update webhook configuration docs to mention enabling "Pull requests" events
- Update `apps/adw_server/README.md:99` to document `handle_pull_request_event()` behavior
- Add example of PR review workflow trigger and output

### 10. Validate the Implementation
- Test with real webhook payload (can use GitHub webhook delivery replay)
- Verify review workflow executes successfully
- Verify issue comments are posted correctly (not PR comments)
- Verify ADW output is stored in correct directory structure
- Check logs for proper error handling and informative messages

## Validation Commands
Execute these commands to validate the chore is complete:

- `uv run python -m py_compile apps/adw_server/core/handlers.py` - Verify handlers.py compiles without syntax errors
- `uv run python -m py_compile apps/adw_server/core/adw_integration.py` - Verify adw_integration.py compiles without syntax errors
- `uv run pytest tests/test_pr_review.py -v` - Run PR review tests and verify all pass
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `grep -r "trigger_review_workflow" apps/adw_server/` - Verify review workflow trigger function is implemented
- `grep -r "extract_issue_references" apps/adw_server/` - Verify issue reference extraction function is implemented
- `grep -r "format_review_results" apps/adw_server/` - Verify review results formatting function is implemented

## Notes

### PR to Issue Linking
GitHub PRs can reference issues in several ways:
- PR description: "Closes #123" - This is the primary method we'll support
- Commit messages: Also can contain "Closes #123" but harder to parse from webhook
- Manual linking: Users can link PRs to issues via UI, but webhook doesn't include this

For simplicity, we'll focus on parsing the PR description for issue references.

### Review Workflow Scope
The `/review` slash command should handle:
- Code quality review using Claude analysis
- Running test suite (`./scripts/run_tests.sh` or equivalent)
- Capturing screenshots if applicable (for frontend changes)
- Generating summary report

The review workflow should be idempotent - running it multiple times on the same PR should be safe.

### Comment Posting Strategy
We post to the **issue thread**, not the PR thread, because:
- The issue is the source of truth for the feature/bug
- Multiple PRs might address the same issue
- Issue comments provide historical context of all attempts
- Easier to track workflow executions per issue

### Error Handling
If the review workflow fails (tests fail, review errors, etc.):
- Still post a comment to the issue with error details
- Mark the review as failed with ❌ emoji
- Include logs location for debugging
- Don't block the PR - review is advisory only

### Future Enhancements
- Support reviewing PRs not linked to issues (review only, no comment posting)
- Upload screenshots to GitHub as PR comments
- Integration with GitHub Checks API to show review status
- Support for custom review templates per repo
- Caching review results to avoid re-running on unchanged commits
