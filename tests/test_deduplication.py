#!/usr/bin/env python3
"""Test deduplication logic for webhook handlers."""

import time
import sys
sys.path.insert(0, "apps")

from webhook_handlers import should_trigger_workflow, DEDUP_WINDOW_SECONDS

def test_deduplication():
    """Test that duplicate workflows are blocked within the dedup window."""

    issue_number = 999
    workflow_type = "chore_implement"

    print("Testing workflow deduplication...")
    print("=" * 60)

    # First trigger - should succeed
    result1 = should_trigger_workflow(issue_number, workflow_type)
    print(f"✓ First trigger: {result1} (expected: True)")
    assert result1 == True, "First trigger should succeed"

    # Immediate duplicate - should be blocked
    result2 = should_trigger_workflow(issue_number, workflow_type)
    print(f"✓ Immediate duplicate: {result2} (expected: False)")
    assert result2 == False, "Duplicate should be blocked"

    # Another immediate duplicate - should be blocked
    result3 = should_trigger_workflow(issue_number, workflow_type)
    print(f"✓ Second duplicate: {result3} (expected: False)")
    assert result3 == False, "Second duplicate should be blocked"

    # Different workflow type - should succeed
    result4 = should_trigger_workflow(issue_number, "chore")
    print(f"✓ Different workflow type: {result4} (expected: True)")
    assert result4 == True, "Different workflow type should succeed"

    # Different issue number - should succeed
    result5 = should_trigger_workflow(998, workflow_type)
    print(f"✓ Different issue: {result5} (expected: True)")
    assert result5 == True, "Different issue should succeed"

    print("=" * 60)
    print("✅ All deduplication tests passed!")
    print(f"\nDeduplication window: {DEDUP_WINDOW_SECONDS} seconds")
    print("Duplicate workflows will be blocked within this time window.")

if __name__ == "__main__":
    test_deduplication()
