#!/usr/bin/env python3
"""
Mnemonic Stop Hook

Finalizes the session by:
1. Summarizing session activity
2. Suggesting any final captures
3. Committing memory changes to git
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_session_stats() -> dict:
    """Get statistics about memories created/modified this session."""
    home = Path.home()
    mnemonic_path = home / ".claude" / "mnemonic"

    stats = {
        "new_memories": 0,
        "modified_memories": 0,
        "uncommitted_changes": 0
    }

    if not mnemonic_path.exists():
        return stats

    # Check git status for uncommitted changes
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(mnemonic_path),
            timeout=5
        )
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split("\n") if l]
            stats["uncommitted_changes"] = len(lines)

            for line in lines:
                if line.startswith("A ") or line.startswith("??"):
                    stats["new_memories"] += 1
                elif line.startswith("M "):
                    stats["modified_memories"] += 1
    except Exception:
        pass

    return stats


def commit_changes() -> bool:
    """Commit any uncommitted memory changes."""
    home = Path.home()
    mnemonic_path = home / ".claude" / "mnemonic"

    if not (mnemonic_path / ".git").exists():
        return False

    try:
        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(mnemonic_path),
            timeout=5,
            capture_output=True
        )

        # Commit
        session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        result = subprocess.run(
            ["git", "commit", "-m", f"Session {session_id}: Memory updates ({timestamp})"],
            cwd=str(mnemonic_path),
            timeout=5,
            capture_output=True
        )

        return result.returncode == 0
    except Exception:
        return False


def write_session_note(stats: dict) -> None:
    """Write a session summary to the blackboard."""
    home = Path.home()
    blackboard_path = home / ".claude" / "mnemonic" / ".blackboard"
    blackboard_path.mkdir(parents=True, exist_ok=True)

    session_notes = blackboard_path / "session-notes.md"

    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    note = f"""
---
**Session:** {session_id}
**Time:** {timestamp}
**Status:** ended

### Summary
- New memories: {stats['new_memories']}
- Modified memories: {stats['modified_memories']}

---
"""

    with open(session_notes, "a") as f:
        f.write(note)


def main():
    # Get session statistics
    stats = get_session_stats()

    messages = []

    # Report activity
    if stats["new_memories"] > 0 or stats["modified_memories"] > 0:
        messages.append(
            f"Session captured {stats['new_memories']} new, "
            f"{stats['modified_memories']} modified memories"
        )

    # Commit changes
    if stats["uncommitted_changes"] > 0:
        if commit_changes():
            messages.append("Memory changes committed to git")
        else:
            messages.append("Note: Uncommitted memory changes exist")

    # Write session note
    write_session_note(stats)

    # Output result
    if messages:
        result = {
            "continue": True,
            "systemMessage": "**Mnemonic Session End:** " + "; ".join(messages)
        }
    else:
        result = {"continue": True}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
