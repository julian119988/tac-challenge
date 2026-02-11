# Chore: ADW PR Summary Improved

## Metadata
adw_id: `Issue #17`
prompt: `With the bug label I didn't get a summary with the PR, we should add one.

Also the summary we leave with the PR doesn't have a good summary, it doesn't say what the PR changes in the code. We should add more info about the changes in the code, not only the planId and AWD id.`

## Chore Description
Improve the PR body/summary generation for ADW workflows to include:

1. **For bug label**: Ensure a comprehensive summary is included in the PR (currently missing)
2. **For all labels**: Enhance the summary section to include actual code changes, not just metadata (planId, ADW ID)

The current PR summaries only contain the issue title and description but lack information about what was actually changed in the codebase. The PR body should provide a clear summary of the code modifications made during implementation.

## Relevant Files
Use these files to complete the chore:

- `apps/adw_server/core/adw_integration.py:384-393` - Contains the PR body generation logic in the `trigger_chore_implement_workflow` function. This is where we construct the PR title and body before calling `create_pull_request`.

- `apps/adw_server/core/handlers.py:654-698` - Contains the success comment generation logic after PR creation. Shows the flow of how PR results are communicated back to GitHub issues.

- `adws/adw_modules/git_ops.py:365-434` - Contains the `create_pull_request` function that executes the `gh pr create` command with the title and body.

- `.claude/commands/pull_request.md` - Template for the `/pull_request` slash command that shows the desired PR format with Summary, Changes, Testing, and Related Issue sections.

### New Files
None required - we'll modify existing PR generation logic.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Analyze Current PR Generation Flow
- Read the current PR body generation in `apps/adw_server/core/adw_integration.py:384-393`
- Understand how the workflow results are passed to PR creation
- Identify what information is available at PR creation time (plan_path, adw_id, prompt, model)

### 2. Design Enhanced PR Summary Structure
- Review the template in `.claude/commands/pull_request.md` for the ideal format
- Design a new PR body structure that includes:
  - Concise summary of what was changed (not just the issue description)
  - Key code changes made during implementation
  - Testing instructions (if applicable)
  - ADW metadata (planId, ADW ID, model)
- Determine how to extract code change information from the implementation results

### 3. Enhance PR Body Generation in adw_integration.py
- Modify the `trigger_chore_implement_workflow` function's PR body generation (lines 384-393)
- Update the PR body template to include:
  - A "Summary" section with actual code changes
  - A "Changes" section listing key modifications
  - ADW metadata in a dedicated section
- Extract relevant information from `chore_result` and `impl_result` to populate these sections
- Ensure the PR body works for both bug and implement labels

### 4. Add Code Changes Extraction Logic
- Determine the best way to infer or extract code changes information
- Consider reading the plan file (`chore_result.plan_path`) to extract planned changes
- Consider parsing git diff output to summarize what files were modified
- Implement logic to generate a concise summary of code changes

### 5. Update Success Comment in handlers.py
- Review the success comment generation in `apps/adw_server/core/handlers.py:654-698`
- Ensure the GitHub issue comment also reflects the improved summary
- Update comment text to mention the enhanced PR summary

### 6. Test PR Generation
- Review example PRs (like #16) to understand current output
- Verify the new PR body format matches the template in `.claude/commands/pull_request.md`
- Ensure both bug and implement label workflows generate good summaries

### 7. Validate the Changes
- Check that PR bodies now include code change summaries
- Verify that all existing functionality (Closes #N, ADW metadata) is preserved
- Ensure the PR body is readable and informative

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -n "pr_body = " apps/adw_server/core/adw_integration.py` - Verify PR body generation logic has been updated
- `git diff apps/adw_server/core/adw_integration.py` - Review changes to PR generation
- `git diff apps/adw_server/core/handlers.py` - Review changes to success comments (if applicable)
- `python -m py_compile apps/adw_server/core/adw_integration.py` - Ensure Python syntax is valid
- `python -m py_compile apps/adw_server/core/handlers.py` - Ensure Python syntax is valid

## Notes
- The main challenge is extracting meaningful code change information at PR creation time
- We have access to the plan file path which contains detailed implementation steps
- We could also use git diff to see what files were changed
- The PR summary should be concise but informative - focus on what changed, not just why
- Ensure backward compatibility - don't break existing PR creation flow
