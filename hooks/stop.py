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


def commit_changes() -> tuple[bool, int]:
    """Commit any uncommitted memory changes. Returns (success, count)."""
    home = Path.home()
    mnemonic_path = home / ".claude" / "mnemonic"

    if not (mnemonic_path / ".git").exists():
        return False, 0

    try:
        # Check for changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(mnemonic_path),
            timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return True, 0

        changes = len([l for l in result.stdout.strip().split("\n") if l])

        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(mnemonic_path),
            timeout=5,
            capture_output=True
        )

        # Commit
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        result = subprocess.run(
            ["git", "commit", "-m", f"Memory updates ({timestamp})"],
            cwd=str(mnemonic_path),
            timeout=5,
            capture_output=True
        )

        return result.returncode == 0, changes
    except Exception:
        return False, 0


def main():
    success, count = commit_changes()

    if count > 0:
        if success:
            message = f"<mnemonic-session-end>Committed {count} memory changes to git.</mnemonic-session-end>"
        else:
            message = f"<mnemonic-session-end>Warning: {count} uncommitted memory changes.</mnemonic-session-end>"
        print(json.dumps({
            "continue": True,
            "systemMessage": message
        }))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
