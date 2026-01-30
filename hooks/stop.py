#!/usr/bin/env python3
"""
Mnemonic Stop Hook

Blocks Claude from stopping if there are pending captures.
Also commits memory and blackboard changes at session end.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_pending_file() -> Path:
    """Get path to pending capture file - must match user_prompt_submit.py."""
    # Use session ID if available, otherwise use a fixed name
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return Path("/tmp") / f"mnemonic-pending-{session_id}.json"


def get_all_pending_files() -> list:
    """Get all pending capture files for this session (from multiple sources)."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    pending_files = []

    # Check for prompt-submit pending file
    prompt_file = Path("/tmp") / f"mnemonic-pending-{session_id}.json"
    if prompt_file.exists():
        pending_files.append(prompt_file)

    # Check for post-tool-use pending files (could be multiple)
    for f in Path("/tmp").glob(f"mnemonic-pending-{session_id}-*.json"):
        pending_files.append(f)

    return pending_files


def check_pending_captures() -> dict | None:
    """Check if there are pending captures that weren't completed."""
    pending_file = get_pending_file()
    if pending_file.exists():
        try:
            return json.loads(pending_file.read_text())
        except Exception:
            pass
    return None


def aggregate_all_pending() -> list:
    """Aggregate all pending captures from all sources."""
    pending_items = []
    seen_topics = set()

    for pending_file in get_all_pending_files():
        try:
            data = json.loads(pending_file.read_text())
            topic = data.get("topic", "unknown")
            # Deduplicate by topic
            if topic not in seen_topics:
                seen_topics.add(topic)
                pending_items.append(data)
        except Exception:
            continue

    return pending_items


def clear_pending_captures():
    """Clear pending capture file after capture is done."""
    pending_file = get_pending_file()
    if pending_file.exists():
        try:
            pending_file.unlink()
        except Exception:
            pass


def is_test_mode() -> bool:
    """Check if we're in test mode."""
    try:
        state_file = Path.cwd() / ".claude" / "test-state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                return state.get("mode") == "running"
    except Exception:
        pass
    return False


def get_session_id() -> str:
    """Get session ID from environment or generate one."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if not session_id:
        session_id = f"{int(datetime.now().timestamp())}-{os.getpid()}"
    return session_id


def log_session_end() -> None:
    """Log session end to blackboard for handoff tracking."""
    home = Path.home()
    bb_dir = home / ".claude" / "mnemonic" / ".blackboard"

    if not bb_dir.exists():
        return

    session_notes = bb_dir / "session-notes.md"
    session_id = get_session_id()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        with open(session_notes, "a") as f:
            f.write(f"\n---\n**Session:** {session_id}\n**Time:** {timestamp}\n**Status:** ended\n\n")
    except Exception:
        pass


def commit_changes() -> None:
    """Commit any uncommitted memory and blackboard changes."""
    home = Path.home()
    mnemonic_path = home / ".claude" / "mnemonic"

    if not (mnemonic_path / ".git").exists():
        return

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(mnemonic_path), timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return

        # Count what's being committed
        changes = result.stdout.strip().split("\n")
        memory_changes = sum(1 for c in changes if ".memory.md" in c)
        blackboard_changes = sum(1 for c in changes if ".blackboard" in c)

        subprocess.run(["git", "add", "-A"], cwd=str(mnemonic_path), timeout=5, capture_output=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        session_id = get_session_id()

        # Build commit message
        parts = []
        if memory_changes:
            parts.append(f"{memory_changes} memories")
        if blackboard_changes:
            parts.append(f"{blackboard_changes} blackboard entries")

        if parts:
            detail = ", ".join(parts)
            message = f"Session {session_id}: {detail} ({timestamp})"
        else:
            message = f"Session {session_id}: updates ({timestamp})"

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(mnemonic_path),
            timeout=5,
            capture_output=True,
        )
    except Exception:
        pass


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    # Check if stop hook is already active (prevent infinite loop)
    stop_hook_active = input_data.get("stop_hook_active", False)

    if is_test_mode():
        print(json.dumps({"continue": True}))
        return

    # Check for pending captures from all sources
    all_pending = aggregate_all_pending()

    # Also check single pending file for backwards compatibility
    if not all_pending:
        single_pending = check_pending_captures()
        if single_pending:
            all_pending = [single_pending]

    if all_pending and not stop_hook_active:
        # Block stopping - Claude needs to capture first
        # Build list of all pending items
        pending_list = []
        for item in all_pending:
            namespaces = ", ".join(item.get("namespaces", []))
            topic = item.get("topic", "unknown")
            pending_list.append(f"  • {topic} → {namespaces}")

        pending_display = "\n".join(pending_list)
        first_item = all_pending[0]
        first_ns = first_item.get("namespaces", ["_semantic/knowledge"])[0]
        first_topic = first_item.get("topic", "this item")

        output = {
            "decision": "block",
            "reason": (
                "═══════════════════════════════════════════════════════\n"
                ">>> YOUR WORK IS NOT YET COMPLETE <<<\n"
                "═══════════════════════════════════════════════════════\n\n"
                f"As Claude with persistent memory, you committed to\n"
                f"preserving knowledge. {len(all_pending)} capture(s) pending:\n\n"
                f"{pending_display}\n\n"
                f"Complete your work now:\n"
                f'  /mnemonic:capture {first_ns} "{first_topic}"\n\n'
                "The user trusts you to preserve valuable knowledge.\n"
                "Future sessions depend on what you capture today.\n\n"
                "This session cannot end until captures are complete."
            ),
        }
        print(json.dumps(output))
        return

    # Clear pending captures since we're allowing the stop
    clear_pending_captures()

    # Log session end to blackboard
    log_session_end()

    # Commit all changes (memories + blackboard)
    commit_changes()

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
