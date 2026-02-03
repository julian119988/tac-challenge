# Generate Branch Name

Create a descriptive, Git-safe branch name for the issue.

## Variables
issue_json: $1

## Instructions

- Parse the `issue_json` which contains: number, title, adw_id
- Generate a branch name following this format:
  `{type}-{issue_num}-adw-{adw_id}-{short-desc}`
- Where:
  - `{type}`: One of: feature, fix, chore
  - `{issue_num}`: The issue number
  - `{adw_id}`: The ADW identifier
  - `{short-desc}`: 2-4 words from the issue title, kebab-case
- Make it Git-safe:
  - Use only lowercase letters, numbers, and hyphens
  - No spaces, underscores, or special characters
  - Max 60 characters total
- Be descriptive but concise

## Examples

Issue #42: "Add user authentication with OAuth"
Branch: feature-42-adw-abc12345-user-auth-oauth

Issue #15: "Fix broken login button"
Branch: fix-15-adw-def67890-login-button

Issue #8: "Update build configuration"
Branch: chore-8-adw-ghi11121-update-build-config

## Branch Name

Generate the branch name for the provided issue.
Return ONLY the branch name, no explanation.
