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

# Add project root to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import get_memory_root
from lib.paths import Scope, get_v2_resolver


def get_pending_file() -> Path:
    """Get path to pending capture file - must match user_prompt_submit.py."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return Path("/tmp") / f"mnemonic-pending-{session_id}.json"


def get_all_pending_files() -> list:
    """Get all pending capture files for this session (from multiple sources)."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    pending_files = []

    prompt_file = Path("/tmp") / f"mnemonic-pending-{session_id}.json"
    if prompt_file.exists():
        pending_files.append(prompt_file)

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
    """Log session end to session-scoped blackboard and write handoff."""
    resolver = get_v2_resolver()
    session_id = get_session_id()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Update session _meta.json
    session_dir = resolver.get_session_blackboard_dir(session_id, Scope.PROJECT)
    if session_dir.exists():
        meta_file = session_dir / "_meta.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                meta["ended"] = timestamp
                meta["status"] = "ended"
                meta_file.write_text(json.dumps(meta, indent=2) + "\n")
            except Exception:
                pass

        # Write session notes
        session_notes = session_dir / "session-notes.md"
        try:
            with open(session_notes, "a") as f:
                f.write(f"\n---\n**Session:** {session_id}\n**Time:** {timestamp}\n**Status:** ended\n\n")
        except Exception:
            pass

    # Write handoff files
    handoff_dir = resolver.get_handoff_dir(Scope.PROJECT)
    handoff_dir.mkdir(parents=True, exist_ok=True)

    handoff_content = (
        f"# Session Handoff\n\n"
        f"**Session:** {session_id}\n"
        f"**Ended:** {timestamp}\n"
        f"**Project:** {resolver.context.org}/{resolver.context.project}\n"
    )

    # Write latest-handoff.md (overwrite)
    try:
        (handoff_dir / "latest-handoff.md").write_text(handoff_content)
    except Exception:
        pass

    # Archive per-session handoff
    try:
        (handoff_dir / f"handoff-{session_id}.md").write_text(handoff_content)
    except Exception:
        pass


def commit_changes() -> None:
    """Commit any uncommitted memory and blackboard changes."""
    mnemonic_path = get_memory_root()

    if not (mnemonic_path / ".git").exists():
        return

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(mnemonic_path), timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return

        changes = result.stdout.strip().split("\n")
        memory_changes = sum(1 for c in changes if ".memory.md" in c)
        blackboard_changes = sum(1 for c in changes if ".blackboard" in c)

        subprocess.run(["git", "add", "-A"], cwd=str(mnemonic_path), timeout=5, capture_output=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        session_id = get_session_id()

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
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    stop_hook_active = input_data.get("stop_hook_active", False)

    if is_test_mode():
        print(json.dumps({"continue": True}))
        return

    all_pending = aggregate_all_pending()

    if not all_pending:
        single_pending = check_pending_captures()
        if single_pending:
            all_pending = [single_pending]

    if all_pending and not stop_hook_active:
        pending_list = []
        for item in all_pending:
            namespaces = ", ".join(item.get("namespaces", []))
            topic = item.get("topic", "unknown")
            pending_list.append(f"  - {topic} -> {namespaces}")

        pending_display = "\n".join(pending_list)
        first_item = all_pending[0]
        first_ns = first_item.get("namespaces", ["_semantic/knowledge"])[0]
        first_topic = first_item.get("topic", "this item")

        output = {
            "decision": "block",
            "reason": (
                f"[STOP BLOCKED] {len(all_pending)} pending capture(s):\n"
                f"{pending_display}\n"
                f'Complete now: /mnemonic:capture {first_ns} "{first_topic}"'
            ),
        }
        print(json.dumps(output))
        return

    clear_pending_captures()
    log_session_end()
    commit_changes()

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
