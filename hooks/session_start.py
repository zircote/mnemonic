#!/usr/bin/env python3
"""
Mnemonic SessionStart Hook

Outputs hookSpecificOutput.additionalContext for memory system initialization.
Claude sees this context and may use it to inform decisions about memory operations.
"""

import json
import subprocess
from pathlib import Path
import re


def get_org() -> str:
    """Get organization from git remote."""
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5)
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


def get_project_name() -> str:
    """Get project name from git or directory."""
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            url = result.stdout.strip()
            return url.rstrip(".git").split("/")[-1]
    except Exception:
        pass
    return Path.cwd().name


def count_memories_by_namespace(home: Path, org: str) -> dict:
    """Count memories by namespace with fast enumeration."""
    counts = {}
    namespaces = ["decisions", "learnings", "patterns", "blockers", "context", "apis", "security", "testing", "episodic"]

    paths = [
        home / ".claude" / "mnemonic" / org,
        home / ".claude" / "mnemonic" / "default",
        Path.cwd() / ".claude" / "mnemonic",
    ]

    for base_path in paths:
        if not base_path.exists():
            continue
        for memory_file in base_path.rglob("*.memory.md"):
            parts = memory_file.parts
            for part in parts:
                if part in namespaces:
                    counts[part] = counts.get(part, 0) + 1
                    break

    return counts


def calculate_memory_health(home: Path, org: str) -> dict:
    """Calculate memory health metrics (fast heuristics)."""
    total = 0
    decayed = 0
    duplicates_possible = 0
    titles_seen = {}

    paths = [
        home / ".claude" / "mnemonic" / org,
        home / ".claude" / "mnemonic" / "default",
        Path.cwd() / ".claude" / "mnemonic",
    ]

    for base_path in paths:
        if not base_path.exists():
            continue
        for memory_file in base_path.rglob("*.memory.md"):
            total += 1
            try:
                # Read first 30 lines for frontmatter (fast)
                with open(memory_file, 'r') as f:
                    content = ''.join(f.readline() for _ in range(30))

                # Check confidence
                confidence_match = re.search(r'confidence:\s*([\d.]+)', content)
                if confidence_match and float(confidence_match.group(1)) < 0.5:
                    decayed += 1

                # Check for potential duplicates (same title)
                title_match = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
                if title_match:
                    title = title_match.group(1).strip().lower()
                    if title in titles_seen:
                        duplicates_possible += 1
                    titles_seen[title] = True

            except Exception:
                continue

    # Calculate health score (0-100)
    if total == 0:
        health_score = 100
    else:
        decay_penalty = (decayed / total) * 30
        duplicate_penalty = min((duplicates_possible / total) * 20, 20)
        health_score = max(0, 100 - decay_penalty - duplicate_penalty)

    return {
        "total": total,
        "decayed": decayed,
        "duplicates_possible": duplicates_possible,
        "score": round(health_score)
    }


def check_blackboard(home: Path) -> dict:
    """Check blackboard for pending items."""
    bb_dir = home / ".claude" / "mnemonic" / ".blackboard"
    pending = 0
    if bb_dir.exists():
        for _ in bb_dir.glob("*.md"):
            pending += 1
    return {"pending_items": pending}


def get_blackboard_summaries(home: Path) -> dict:
    """Get summaries of key blackboard files for session context."""
    bb_dir = home / ".claude" / "mnemonic" / ".blackboard"
    summaries = {}

    key_files = ["active-tasks.md", "pending-decisions.md", "session-notes.md"]

    for filename in key_files:
        filepath = bb_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    # Read last 500 chars (recent entries)
                    f.seek(0, 2)  # Go to end
                    size = f.tell()
                    if size > 500:
                        f.seek(size - 500)
                        f.readline()  # Skip partial line
                    else:
                        f.seek(0)
                    content = f.read().strip()
                    if content:
                        # Extract last entry (after last ---)
                        parts = content.split("---")
                        if len(parts) > 1:
                            last_entry = parts[-1].strip()
                            if last_entry:
                                summaries[filename.replace(".md", "")] = last_entry[:300]
            except Exception:
                continue

    return summaries


def find_project_relevant_memories(home: Path, org: str, project: str) -> list:
    """Find memories likely relevant to current project."""
    relevant = []
    paths = [
        home / ".claude" / "mnemonic" / org,
        home / ".claude" / "mnemonic" / "default",
        Path.cwd() / ".claude" / "mnemonic",
    ]

    # Look for memories mentioning project name or in project namespace
    project_lower = project.lower()

    for base_path in paths:
        if not base_path.exists():
            continue
        for memory_file in base_path.rglob("*.memory.md"):
            try:
                # Check filename for project reference
                if project_lower in memory_file.name.lower():
                    relevant.append(str(memory_file))
                    continue

                # Check first 20 lines for project namespace or mentions
                with open(memory_file, 'r') as f:
                    header = ''.join(f.readline() for _ in range(20))

                if f"/{project}" in header or f"project: {project}" in header.lower():
                    relevant.append(str(memory_file))
                elif "namespace: decisions" in header or "namespace: patterns" in header:
                    # Include key decision/pattern memories
                    relevant.append(str(memory_file))

            except Exception:
                continue

            if len(relevant) >= 5:  # Limit to 5 relevant memories
                break

        if len(relevant) >= 5:
            break

    return relevant[:5]


def get_suggestions(health: dict, counts: dict) -> list:
    """Generate context-appropriate suggestions."""
    suggestions = []

    if health["decayed"] > 5:
        suggestions.append(f"{health['decayed']} memories have low confidence - consider running /mnemonic:gc")

    if health["duplicates_possible"] > 2:
        suggestions.append(f"{health['duplicates_possible']} potential duplicates detected")

    if health["score"] < 70:
        suggestions.append("Memory health is below optimal - maintenance recommended")

    total_decisions = counts.get("decisions", 0)
    total_patterns = counts.get("patterns", 0)

    if total_decisions > 20 or total_patterns > 15:
        suggestions.append("Consider recalling relevant decisions before architectural work")

    return suggestions


def main():
    home = Path.home()
    org = get_org()
    project = get_project_name()

    counts = count_memories_by_namespace(home, org)
    health = calculate_memory_health(home, org)
    blackboard = check_blackboard(home)
    bb_summaries = get_blackboard_summaries(home)
    relevant_memories = find_project_relevant_memories(home, org, project)
    suggestions = get_suggestions(health, counts)

    total = sum(counts.values())

    # Build human-readable context for Claude
    context_lines = [
        f"Mnemonic Memory System Active:",
        f"- Organization: {org}",
        f"- Project: {project}",
        f"- Total memories: {total}",
    ]

    if counts:
        namespace_summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()) if v > 0)
        context_lines.append(f"- By namespace: {namespace_summary}")

    context_lines.append(f"- Memory health: {health['score']}%")

    if health["decayed"] > 0:
        context_lines.append(f"- Decayed memories (confidence < 0.5): {health['decayed']}")

    if health["duplicates_possible"] > 0:
        context_lines.append(f"- Potential duplicates: {health['duplicates_possible']}")

    if blackboard["pending_items"] > 0:
        context_lines.append(f"- Blackboard pending: {blackboard['pending_items']} items")

    # Add blackboard summaries for active work context
    if bb_summaries:
        context_lines.append("")
        context_lines.append("**ACTIVE WORK (from blackboard):**")
        if "active-tasks" in bb_summaries:
            context_lines.append(f"Active Tasks: {bb_summaries['active-tasks'][:150]}...")
        if "pending-decisions" in bb_summaries:
            context_lines.append(f"Pending Decisions: {bb_summaries['pending-decisions'][:150]}...")
        if "session-notes" in bb_summaries:
            context_lines.append(f"Last Session: {bb_summaries['session-notes'][:150]}...")

    # Add relevant memories for this project
    if relevant_memories:
        context_lines.append("")
        context_lines.append("**RELEVANT MEMORIES:**")
        for mem in relevant_memories[:3]:
            # Show just filename for brevity
            context_lines.append(f"  - {Path(mem).name}")

    # Add memory-first protocol
    context_lines.append("")
    context_lines.append("**MEMORY-FIRST PROTOCOL:**")
    context_lines.append("Before researching or implementing:")
    context_lines.append("1. Search mnemonic: rg -i \"{topic}\" ~/.claude/mnemonic/ --glob \"*.memory.md\"")
    context_lines.append("2. If found: Read memory, use Level 1 (Quick Answer) first")
    context_lines.append("3. Expand to Level 2 (Context) or Level 3 (Full Detail) only if needed")
    context_lines.append("4. Research externally only if memory is insufficient")

    if suggestions:
        context_lines.append("")
        context_lines.append("Suggestions:")
        for s in suggestions:
            context_lines.append(f"  - {s}")

    additional_context = "\n".join(context_lines)

    # Output using hookSpecificOutput.additionalContext (what Claude sees)
    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context
        }
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
