#!/usr/bin/env python3
"""Test script to verify GitHub integration by posting a comment on issue #3."""

import sys
import os

# Add adws to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "adws", "adw_modules"))

from github import make_issue_comment

# Repository details
REPO_OWNER = "julian119988"
REPO_NAME = "tac-challenge"
ISSUE_NUMBER = 3

# Test comment
comment = """Testing the ADW GitHub integration! 🤖

This comment was posted programmatically using the `make_issue_comment` function from the ADW GitHub module.

**Integration Status:** ✅ Working

The ADW workflow can now:
- Fetch issue details
- Post comments with the [ADW-AGENTS] identifier
- Mark issues as in-progress
- Interact with GitHub via the `gh` CLI
"""

# Post the comment
print(f"Posting comment to issue #{ISSUE_NUMBER}...")
success = make_issue_comment(
    issue_number=ISSUE_NUMBER,
    comment=comment,
    repo_owner=REPO_OWNER,
    repo_name=REPO_NAME,
)

if success:
    print(f"✅ Successfully posted comment to issue #{ISSUE_NUMBER}")
    print(f"View it at: https://github.com/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}")
else:
    print(f"❌ Failed to post comment to issue #{ISSUE_NUMBER}")
    sys.exit(1)
