#!/usr/bin/env python3
"""Unit tests for git_ops module, specifically ensure_main_branch_updated function."""

import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adws.adw_modules.git_ops import ensure_main_branch_updated, create_branch


def setup_test_repo():
    """Create a temporary git repository for testing."""
    temp_dir = tempfile.mkdtemp()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, capture_output=True)

    # Create initial commit on main branch
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("initial content")

    subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True)

    return temp_dir


def setup_test_repo_with_remote():
    """Create a temporary git repository with a remote for testing."""
    # Create bare remote repository
    remote_dir = tempfile.mkdtemp()
    subprocess.run(["git", "init", "--bare"], cwd=remote_dir, capture_output=True)

    # Create local repository
    local_dir = tempfile.mkdtemp()
    subprocess.run(["git", "clone", remote_dir, "."], cwd=local_dir, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=local_dir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=local_dir, capture_output=True)

    # Create initial commit on main branch
    test_file = os.path.join(local_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("initial content")

    subprocess.run(["git", "add", "."], cwd=local_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=local_dir, capture_output=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local_dir, capture_output=True)

    return local_dir, remote_dir


def cleanup_test_repo(repo_path):
    """Remove the temporary test repository."""
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)


def test_ensure_main_branch_updated_on_main():
    """Test ensure_main_branch_updated when already on main branch (no remote)."""
    print("\n=== Test 1: ensure_main_branch_updated when on main branch (no remote) ===")

    repo_path = setup_test_repo()

    try:
        # We're already on main, but without a remote configured
        success, error = ensure_main_branch_updated(repo_path)

        # Without a remote, the fetch will fail - this is expected
        assert not success, "Expected failure without remote configured"
        assert "Failed to fetch from origin" in error, f"Expected fetch error, got: {error}"

        # Verify we're still on main (the function should fail early during fetch)
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        current_branch = result.stdout.strip()
        assert current_branch == "main", f"Expected to be on main, got: {current_branch}"

        print("✅ Test passed: Correctly reported fetch failure (no remote configured)")

    finally:
        cleanup_test_repo(repo_path)


def test_ensure_main_branch_updated_on_feature_branch():
    """Test ensure_main_branch_updated when on a feature branch."""
    print("\n=== Test 2: ensure_main_branch_updated when on feature branch ===")

    repo_path = setup_test_repo()

    try:
        # Create and checkout a feature branch
        subprocess.run(["git", "checkout", "-b", "feature-branch"], cwd=repo_path, capture_output=True)

        # Verify we're on feature branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "feature-branch"

        # Note: This test will succeed in checking out main even without a remote
        # In a real scenario with a remote, it would fetch and update main
        success, error = ensure_main_branch_updated(repo_path)

        # The function should succeed (it will fetch, switch to main, update, and switch back)
        # However, without a remote, the fetch will fail
        # Let's update the test to expect this behavior
        print(f"Result: success={success}, error={error}")

        # In this test environment without a remote, we expect the fetch to fail
        # This is expected behavior, and the function correctly reports the error
        if not success:
            assert "Failed to fetch from origin" in error, f"Expected fetch error, got: {error}"
            print("✅ Test passed: Correctly reported fetch failure (no remote configured)")
        else:
            # If we have a remote configured (unlikely in test), verify behavior
            # Verify we're back on feature branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            current_branch = result.stdout.strip()
            assert current_branch == "feature-branch", f"Expected to be back on feature-branch, got: {current_branch}"
            print("✅ Test passed: Successfully switched to main, updated, and returned to feature branch")

    finally:
        cleanup_test_repo(repo_path)


def test_create_branch_with_main_update():
    """Test create_branch function with main branch update enabled."""
    print("\n=== Test 3: create_branch with main branch update ===")

    repo_path = setup_test_repo()

    try:
        # Test creating a branch with update_main=True (but no remote, so it should fail)
        success = create_branch("new-feature", repo_path, update_main=True)

        # Without a remote, this should fail during the fetch
        assert not success, "Expected create_branch to fail without remote"
        print("✅ Test passed: create_branch correctly requires remote for main update")

        # Test creating a branch with update_main=False (should succeed)
        success = create_branch("new-feature-no-update", repo_path, update_main=False)

        assert success, "Expected create_branch to succeed with update_main=False"

        # Verify branch was created
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        current_branch = result.stdout.strip()
        assert current_branch == "new-feature-no-update", f"Expected to be on new-feature-no-update, got: {current_branch}"

        print("✅ Test passed: create_branch works correctly with update_main=False")

    finally:
        cleanup_test_repo(repo_path)


def test_create_branch_already_exists():
    """Test create_branch when branch already exists."""
    print("\n=== Test 4: create_branch when branch already exists ===")

    repo_path = setup_test_repo()

    try:
        # Create a branch first (without main update to avoid fetch error)
        subprocess.run(["git", "checkout", "-b", "existing-branch"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=repo_path, capture_output=True)

        # Try to create the same branch again (should checkout existing branch)
        success = create_branch("existing-branch", repo_path, update_main=False)

        assert success, "Expected create_branch to succeed by checking out existing branch"

        # Verify we're on the existing branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        current_branch = result.stdout.strip()
        assert current_branch == "existing-branch", f"Expected to be on existing-branch, got: {current_branch}"

        print("✅ Test passed: create_branch correctly handles existing branches")

    finally:
        cleanup_test_repo(repo_path)


def test_ensure_main_branch_updated_with_remote():
    """Test ensure_main_branch_updated with a proper remote repository."""
    print("\n=== Test 5: ensure_main_branch_updated with remote repository ===")

    local_dir, remote_dir = setup_test_repo_with_remote()

    try:
        # Create a feature branch
        subprocess.run(["git", "checkout", "-b", "feature-branch"], cwd=local_dir, capture_output=True)

        # Now test ensure_main_branch_updated - should work with remote configured
        success, error = ensure_main_branch_updated(local_dir)

        assert success, f"Expected success with remote configured, got error: {error}"
        assert error == "", f"Expected empty error message, got: {error}"

        # Verify we're back on feature branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=local_dir,
            capture_output=True,
            text=True
        )
        current_branch = result.stdout.strip()
        assert current_branch == "feature-branch", f"Expected to be on feature-branch, got: {current_branch}"

        print("✅ Test passed: Successfully updated main and returned to feature branch")

    finally:
        cleanup_test_repo(local_dir)
        cleanup_test_repo(remote_dir)


def test_create_branch_with_remote():
    """Test create_branch with main update and remote repository."""
    print("\n=== Test 6: create_branch with main update and remote ===")

    local_dir, remote_dir = setup_test_repo_with_remote()

    try:
        # Test creating a branch with update_main=True (with remote configured)
        success = create_branch("new-feature", local_dir, update_main=True)

        assert success, "Expected create_branch to succeed with remote configured"

        # Verify branch was created
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=local_dir,
            capture_output=True,
            text=True
        )
        current_branch = result.stdout.strip()
        assert current_branch == "new-feature", f"Expected to be on new-feature, got: {current_branch}"

        print("✅ Test passed: create_branch with main update works correctly with remote")

    finally:
        cleanup_test_repo(local_dir)
        cleanup_test_repo(remote_dir)


if __name__ == "__main__":
    print("Running git_ops unit tests...")
    print("=" * 80)

    try:
        test_ensure_main_branch_updated_on_main()
        test_ensure_main_branch_updated_on_feature_branch()
        test_create_branch_with_main_update()
        test_create_branch_already_exists()
        test_ensure_main_branch_updated_with_remote()
        test_create_branch_with_remote()

        print("\n" + "=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
        sys.exit(0)

    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"❌ Test failed: {e}")
        print("=" * 80)
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ Unexpected error: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)
