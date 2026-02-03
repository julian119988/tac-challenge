# Run Tests

Execute the project's test suite and analyze results.

## Instructions

- Identify the testing framework used in the project (pytest, jest, etc.)
- Run the appropriate test command
- Analyze test results:
  - Count passed/failed tests
  - Identify failing test cases
  - Extract error messages and stack traces
- Report results in a structured format

## Common Test Commands

- Python: `pytest`, `python -m pytest`, `uv run pytest`
- JavaScript: `npm test`, `yarn test`, `bun test`
- TypeScript: `npm test`, `yarn test`
- Go: `go test ./...`
- Rust: `cargo test`

## Report Format

```
Test Summary:
- Framework: <framework name>
- Total: <number> tests
- Passed: <number>
- Failed: <number>
- Skipped: <number>

Failed Tests:
1. <test name>: <error message>
2. <test name>: <error message>
...
```

## Testing

Identify the test framework and run the tests. Report the results.
