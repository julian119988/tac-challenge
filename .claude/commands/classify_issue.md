# Classify Issue

Analyze the GitHub issue and classify it into one of three categories.

## Variables
issue_json: $1

## Instructions

- Parse the `issue_json` which contains: number, title, body, labels
- Analyze the issue to determine its type:
  - **`/chore`**: Maintenance tasks, refactoring, documentation, tooling, build improvements, dependencies
  - **`/bug`**: Bug fixes, error corrections, broken functionality
  - **`/feature`**: New features, enhancements, new functionality
- Consider the title, body, and labels
- Return ONLY the classification as one of: `/chore`, `/bug`, or `/feature`
- Do not include any explanation, just the slash command

## Examples

Issue: "Add user authentication"
Classification: /feature

Issue: "Fix login button not working"
Classification: /bug

Issue: "Update README with setup instructions"
Classification: /chore

## Classification

Analyze the provided issue and return the classification.
