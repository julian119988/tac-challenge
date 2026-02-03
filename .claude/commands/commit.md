# Generate Commit Message

Create a concise, descriptive commit message following conventional commits format.

## Instructions

- Review the staged changes using git diff
- Generate a commit message following this format:
  ```
  <type>: <subject>

  <body>

  Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
  ```
- Where:
  - `<type>`: One of: feat, fix, chore, docs, refactor, test, style
  - `<subject>`: Concise description (50 chars or less)
  - `<body>`: Optional detailed explanation focusing on "why" not "what"
- Keep the subject line imperative mood: "add" not "added"
- Focus on the purpose and impact, not implementation details

## Examples

```
feat: add user authentication with OAuth 2.0

Implements secure authentication flow using OAuth 2.0 providers.
Users can now sign in with Google, GitHub, or email.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
fix: resolve login button click handler

Fixes issue where login button was not triggering authentication.
The event handler was not properly bound to the button element.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Commit Message

Review the changes and generate an appropriate commit message.
