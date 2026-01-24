#!/usr/bin/env python3
"""
Mnemonic Stop Hook

Finalizes the session by:
1. Committing any memory changes to git
2. Reminding about any uncaptured opportunities
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def is_test_mode() -> bool:
    """Check if we're in test mode (running automated tests)."""
    try:
        state_file = Path.cwd() / ".claude" / "test-state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                return state.get("mode") == "running"
    except Exception:
        pass
    return False


def commit_changes() -> tuple[bool, int]:
    """Commit any uncommitted memory changes. Returns (success, count)."""
    home = Path.home()
    mnemonic_path = home / ".claude" / "mnemonic"

    if not (mnemonic_path / ".git").exists():
        return False, 0

    try:
        # Check for changes
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(mnemonic_path), timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return True, 0

        changes = len([line for line in result.stdout.strip().split("\n") if line])

        # Stage all changes
        subprocess.run(["git", "add", "-A"], cwd=str(mnemonic_path), timeout=5, capture_output=True)

        # Commit
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        result = subprocess.run(
            ["git", "commit", "-m", f"Memory updates ({timestamp})"],
            cwd=str(mnemonic_path),
            timeout=5,
            capture_output=True,
        )

        return result.returncode == 0, changes
    except Exception:
        return False, 0


def main():
    # Skip verbose output during test mode to avoid interrupting test flow
    if is_test_mode():
        print(json.dumps({"continue": True}))
        return

    success, count = commit_changes()

    if count > 0:
        if success:
            message = f"Committed {count} memory changes to git."
        else:
            message = f"Warning: {count} uncommitted memory changes."
        print(json.dumps({"continue": True, "systemMessage": message}))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
