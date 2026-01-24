#!/usr/bin/env python3
"""
Mnemonic SessionStart Hook

Reinforces CLAUDE.md by reminding Claude to:
1. Check existing memories before acting
2. Capture decisions/learnings/patterns as they occur
"""

import json
import subprocess
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
            if ":" in url and "@" in url:
                org = url.split(":")[-1].split("/")[0]
            else:
                parts = url.rstrip(".git").split("/")
                org = parts[-2] if len(parts) >= 2 else "default"
            return org.replace(".git", "")
    except Exception:
        pass
    return "default"


def count_memories() -> dict:
    """Count memories by namespace."""
    counts = {}
    home = Path.home()
    org = get_org()

    paths = [
        home / ".claude" / "mnemonic" / org,
        home / ".claude" / "mnemonic" / "default",
        Path.cwd() / ".claude" / "mnemonic"
    ]

    for base_path in paths:
        if not base_path.exists():
            continue
        for memory_file in base_path.rglob("*.memory.md"):
            parts = memory_file.parts
            for part in parts:
                if part in ["decisions", "learnings", "patterns", "blockers", "context", "apis", "security", "testing", "episodic"]:
                    counts[part] = counts.get(part, 0) + 1
                    break

    return counts


def main():
    counts = count_memories()
    total = sum(counts.values())

    if total > 0:
        summary = ", ".join(f"{ns}:{c}" for ns, c in sorted(counts.items()) if c > 0)
        reminder = f"""<mnemonic status="active" memories="{total}">
{summary}

REMINDER: Per CLAUDE.md, you MUST:
1. Search relevant memories BEFORE implementing anything
2. Capture decisions, learnings, and patterns as they occur
3. Write memories directly to ~/.claude/mnemonic/default/{{namespace}}/user/
</mnemonic>"""
    else:
        reminder = """<mnemonic status="active" memories="0">
No memories yet.

REMINDER: Per CLAUDE.md, you MUST capture:
- Decisions when choices are made
- Learnings when problems are solved
- Patterns when conventions are established
Write to ~/.claude/mnemonic/default/{namespace}/user/
</mnemonic>"""

    print(json.dumps({
        "continue": True,
        "systemMessage": reminder
    }))


if __name__ == "__main__":
    main()
