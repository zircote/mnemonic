#!/usr/bin/env python3
"""
Mnemonic SessionStart Hook

Initializes the session by:
1. Detecting org/project context
2. Ensuring mnemonic directories exist
3. Loading relevant recent memories
4. Returning context to inject into the session
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def get_org() -> str:
    """Get organization from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Handle git@github.com:org/repo.git or https://github.com/org/repo.git
            if ":" in url and "@" in url:
                # SSH format
                org = url.split(":")[-1].split("/")[0]
            else:
                # HTTPS format
                parts = url.rstrip(".git").split("/")
                org = parts[-2] if len(parts) >= 2 else "default"
            return org.replace(".git", "")
    except Exception:
        pass
    return "default"


def get_project() -> str:
    """Get project name from git root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return os.path.basename(result.stdout.strip())
    except Exception:
        pass
    return os.path.basename(os.getcwd())


def ensure_directories(org: str) -> None:
    """Ensure mnemonic directories exist."""
    home = Path.home()
    namespaces = ["apis", "blockers", "context", "decisions", "learnings",
                  "patterns", "security", "testing", "episodic"]

    # User-level directories
    for ns in namespaces:
        (home / ".claude" / "mnemonic" / org / ns / "user").mkdir(parents=True, exist_ok=True)
        (home / ".claude" / "mnemonic" / org / ns / "project").mkdir(parents=True, exist_ok=True)

    (home / ".claude" / "mnemonic" / ".blackboard").mkdir(parents=True, exist_ok=True)

    # Project-level directories
    cwd = Path.cwd()
    for ns in namespaces:
        (cwd / ".claude" / "mnemonic" / ns / "project").mkdir(parents=True, exist_ok=True)

    (cwd / ".claude" / "mnemonic" / ".blackboard").mkdir(parents=True, exist_ok=True)


def get_recent_memories(org: str, days: int = 7, limit: int = 10) -> list:
    """Get recent memories for context injection."""
    memories = []
    home = Path.home()
    cwd = Path.cwd()

    search_paths = [
        home / ".claude" / "mnemonic" / org,
        cwd / ".claude" / "mnemonic"
    ]

    cutoff = datetime.now() - timedelta(days=days)

    for search_path in search_paths:
        if not search_path.exists():
            continue

        for memory_file in search_path.rglob("*.memory.md"):
            try:
                mtime = datetime.fromtimestamp(memory_file.stat().st_mtime)
                if mtime >= cutoff:
                    # Read frontmatter for summary
                    content = memory_file.read_text()
                    lines = content.split("\n")

                    # Extract title
                    title = ""
                    namespace = ""
                    mem_type = ""

                    in_frontmatter = False
                    for line in lines:
                        if line.strip() == "---":
                            in_frontmatter = not in_frontmatter
                            continue
                        if in_frontmatter:
                            if line.startswith("title:"):
                                title = line.replace("title:", "").strip().strip('"')
                            elif line.startswith("namespace:"):
                                namespace = line.replace("namespace:", "").strip()
                            elif line.startswith("type:"):
                                mem_type = line.replace("type:", "").strip()

                    if title:
                        memories.append({
                            "title": title,
                            "namespace": namespace,
                            "type": mem_type,
                            "file": str(memory_file),
                            "mtime": mtime.isoformat()
                        })
            except Exception:
                continue

    # Sort by modification time, most recent first
    memories.sort(key=lambda x: x["mtime"], reverse=True)
    return memories[:limit]


def get_blackboard_summary() -> str:
    """Get recent blackboard activity."""
    home = Path.home()
    cwd = Path.cwd()

    summaries = []

    for bb_path in [home / ".claude" / "mnemonic" / ".blackboard",
                    cwd / ".claude" / "mnemonic" / ".blackboard"]:
        if not bb_path.exists():
            continue

        for topic_file in bb_path.glob("*.md"):
            try:
                content = topic_file.read_text()
                lines = content.strip().split("\n")
                # Get last few lines
                recent = lines[-10:] if len(lines) > 10 else lines
                if recent:
                    summaries.append(f"**{topic_file.stem}**: {len(lines)} entries")
            except Exception:
                continue

    return "\n".join(summaries) if summaries else "No blackboard activity"


def main():
    org = get_org()
    project = get_project()

    # Ensure directories exist
    ensure_directories(org)

    # Get recent memories
    memories = get_recent_memories(org)

    # Build context message
    context_parts = [
        f"**Mnemonic Initialized**",
        f"- Organization: {org}",
        f"- Project: {project}",
        ""
    ]

    if memories:
        context_parts.append(f"**Recent Memories ({len(memories)}):**")
        for mem in memories[:5]:
            context_parts.append(f"- [{mem['type']}] {mem['title']} ({mem['namespace']})")
        context_parts.append("")

    # Add blackboard summary
    bb_summary = get_blackboard_summary()
    if bb_summary != "No blackboard activity":
        context_parts.append("**Blackboard:**")
        context_parts.append(bb_summary)

    # Output result
    result = {
        "continue": True,
        "systemMessage": "\n".join(context_parts)
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
