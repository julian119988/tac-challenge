#!/usr/bin/env python3
"""Test script to manually trigger ADW workflow for issue #3."""

import asyncio
import sys
import os

# Set up Python path
sys.path.insert(0, os.path.dirname(__file__))

async def main():
    """Test the ADW workflow integration."""
    from apps.adw_integration import trigger_chore_implement_workflow

    print("Testing ADW chore_implement workflow for issue #3...")
    print("-" * 60)

    # Issue #3 details
    prompt = """Issue #3: Implement simple frontend.

Implement the chore chore-e934b0d2-react-frontend-app.md"""

    chore_result, impl_result = await trigger_chore_implement_workflow(
        prompt=prompt,
        adw_id="issue-3-test",
        model="sonnet",
        working_dir="."
    )

    print("\n" + "=" * 60)
    print("WORKFLOW RESULTS")
    print("=" * 60)

    print(f"\n📋 PLANNING PHASE:")
    print(f"  Success: {chore_result.success}")
    print(f"  ADW ID: {chore_result.adw_id}")
    print(f"  Plan Path: {chore_result.plan_path}")
    print(f"  Output Dir: {chore_result.output_dir}")
    if chore_result.error_message:
        print(f"  Error: {chore_result.error_message}")

    if impl_result:
        print(f"\n🔨 IMPLEMENTATION PHASE:")
        print(f"  Success: {impl_result.success}")
        print(f"  Output Dir: {impl_result.output_dir}")
        if impl_result.error_message:
            print(f"  Error: {impl_result.error_message}")
    else:
        print(f"\n🔨 IMPLEMENTATION PHASE:")
        print(f"  Not executed (planning failed)")

    print("\n" + "=" * 60)

    if chore_result.success and impl_result and impl_result.success:
        print("✅ FULL WORKFLOW COMPLETED SUCCESSFULLY")
        return 0
    else:
        print("❌ WORKFLOW FAILED OR INCOMPLETE")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
