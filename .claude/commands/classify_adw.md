# Classify ADW Workflow

Extract workflow information from issue body or comment text.

## Variables
text: $1

## Instructions

- Parse the provided text from an issue body or comment
- Look for ADW workflow trigger patterns:
  - `adw_plan_iso` - Planning phase
  - `adw_build_iso` - Build phase
  - `adw_test_iso` - Test phase
  - `adw_review_iso` - Review phase
  - `adw_document_iso` - Document phase
  - `adw_patch_iso` - Patch phase
  - `adw_sdlc_iso` - Full SDLC pipeline
- Extract optional parameters:
  - `adw_id`: 8-character identifier (e.g., "adw-abc12345" or just "abc12345")
  - `model_set`: "base" or "heavy"
- Return JSON with extracted information

## Format

Return JSON in this exact format:
```json
{
  "workflow_command": "<workflow_name>",
  "adw_id": "<adw_id or null>",
  "model_set": "<base or heavy or null>"
}
```

## Examples

Text: "adw_plan_iso"
Output:
```json
{
  "workflow_command": "adw_plan_iso",
  "adw_id": null,
  "model_set": null
}
```

Text: "adw_build_iso abc12345 model_set:heavy"
Output:
```json
{
  "workflow_command": "adw_build_iso",
  "adw_id": "abc12345",
  "model_set": "heavy"
}
```

Text: "Run adw_sdlc_iso with model_set:heavy"
Output:
```json
{
  "workflow_command": "adw_sdlc_iso",
  "adw_id": null,
  "model_set": "heavy"
}
```

## Classification

Parse the text and return the JSON classification.
Return ONLY the JSON, no explanation.
