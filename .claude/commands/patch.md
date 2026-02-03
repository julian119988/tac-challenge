# Create Patch

Implement fixes based on review feedback.

## Variables
review_feedback: $1

## Instructions

- Read and understand the review feedback
- Identify all issues that need to be addressed
- Implement fixes for each issue:
  - Fix bugs and logic errors
  - Address security vulnerabilities
  - Improve code quality and style
  - Enhance performance where needed
  - Add missing tests or documentation
- Make targeted changes without modifying unrelated code
- Test that fixes don't introduce new issues

## Approach

1. **Parse Feedback**: Break down feedback into actionable items
2. **Prioritize**: Address critical issues first
3. **Implement**: Make precise, focused changes
4. **Verify**: Ensure fixes work as intended
5. **Document**: Add comments if complexity increased

## Example

Review Feedback:
"The authentication function doesn't handle null tokens properly and could throw an unhandled exception."

Patch:
- Add null check for token before processing
- Return appropriate error response for null tokens
- Add test case for null token scenario

## Patch

Implement the necessary fixes based on the review feedback.
