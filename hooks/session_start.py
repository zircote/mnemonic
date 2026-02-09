#!/usr/bin/env python3
"""
Mnemonic SessionStart Hook

Outputs hookSpecificOutput.additionalContext for memory system initialization.
Claude sees this context and may use it to inform decisions about memory operations.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add project root to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import get_memory_root
from lib.memory_reader import get_memory_summary
from lib.ontology import get_ontology_info, load_ontology_namespaces
from lib.paths import (
    Scope,
    get_all_memory_roots_with_legacy,
    get_v2_resolver,
    migrate_blackboard_to_session_scoped,
)


def get_session_id() -> str:
    """Get session ID from environment or generate one."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if not session_id:
        session_id = f"{int(datetime.now().timestamp())}-{os.getpid()}"
    return session_id


def init_session_blackboard(session_id: str) -> None:
    """Create session blackboard directory and _meta.json."""
    resolver = get_v2_resolver()
    bb_dir = resolver.get_blackboard_dir(Scope.PROJECT)

    # Run migration if needed (idempotent)
    if bb_dir.exists():
        migrate_blackboard_to_session_scoped(bb_dir)

    session_dir = resolver.get_session_blackboard_dir(session_id, Scope.PROJECT)
    session_dir.mkdir(parents=True, exist_ok=True)

    meta_file = session_dir / "_meta.json"
    if not meta_file.exists():
        meta = {
            "session_id": session_id,
            "started": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ended": None,
            "project": resolver.context.project,
            "org": resolver.context.org,
            "status": "active",
        }
        meta_file.write_text(json.dumps(meta, indent=2) + "\n")


def count_memories_by_namespace() -> dict:
    """Count memories by namespace with fast enumeration."""
    counts = {}
    leaf_namespaces = [
        "decisions",
        "knowledge",
        "entities",
        "incidents",
        "sessions",
        "blockers",
        "runbooks",
        "patterns",
        "migrations",
    ]
    custom_namespaces = load_ontology_namespaces()
    all_namespaces = set(leaf_namespaces + custom_namespaces)

    memory_roots = get_all_memory_roots_with_legacy()

    for base_path in memory_roots:
        if not base_path.exists():
            continue
        for memory_file in base_path.rglob("*.memory.md"):
            parts = memory_file.parts
            for part in parts:
                if part in all_namespaces:
                    counts[part] = counts.get(part, 0) + 1
                    break

    return counts


def calculate_memory_health() -> dict:
    """Calculate memory health metrics (fast heuristics)."""
    total = 0
    decayed = 0
    duplicates_possible = 0
    titles_seen = set()

    memory_roots = get_all_memory_roots_with_legacy()

    for base_path in memory_roots:
        if not base_path.exists():
            continue
        for memory_file in base_path.rglob("*.memory.md"):
            total += 1
            try:
                with open(memory_file) as f:
                    content = "".join(f.readline() for _ in range(30))

                confidence_match = re.search(r"confidence:\s*([\d.]+)", content)
                if confidence_match and float(confidence_match.group(1)) < 0.5:
                    decayed += 1

                title_match = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
                if title_match:
                    title = title_match.group(1).strip().lower()
                    if title in titles_seen:
                        duplicates_possible += 1
                    titles_seen.add(title)

            except Exception:
                continue

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
        "score": round(health_score),
    }


def check_blackboard() -> dict:
    """Check blackboard for pending items in current session."""
    resolver = get_v2_resolver()
    session_id = get_session_id()
    session_dir = resolver.get_session_blackboard_dir(session_id, Scope.PROJECT)
    pending = sum(1 for _ in session_dir.glob("*.md")) if session_dir.exists() else 0
    return {"pending_items": pending}


def get_blackboard_summaries() -> dict:
    """Get summaries from handoff file for session context."""
    resolver = get_v2_resolver()
    handoff_dir = resolver.get_handoff_dir(Scope.PROJECT)
    summaries = {}

    latest = handoff_dir / "latest-handoff.md"
    if latest.exists():
        try:
            content = latest.read_text().strip()
            if content:
                # Get last 300 chars of content
                summaries["last-session"] = content[-300:] if len(content) > 300 else content
        except Exception:
            pass

    return summaries


def find_project_relevant_memories(project: str) -> list:
    """Find memories likely relevant to current project."""
    relevant = []
    memory_roots = get_all_memory_roots_with_legacy()
    project_lower = project.lower()

    for base_path in memory_roots:
        if not base_path.exists():
            continue
        for memory_file in base_path.rglob("*.memory.md"):
            try:
                if project_lower in memory_file.name.lower():
                    relevant.append(str(memory_file))
                    continue

                with open(memory_file) as f:
                    header = "".join(f.readline() for _ in range(20))

                if f"/{project}" in header or f"project: {project}" in header.lower():
                    relevant.append(str(memory_file))
                elif "_semantic/decisions" in header or "_procedural/patterns" in header:
                    relevant.append(str(memory_file))

            except Exception:
                continue

            if len(relevant) >= 5:
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
    total_knowledge = counts.get("knowledge", 0)

    if total_decisions > 20 or total_patterns > 15 or total_knowledge > 30:
        suggestions.append("Consider recalling relevant decisions before architectural work")

    return suggestions


def run_filename_migration() -> Optional[dict]:
    """Auto-migrate UUID-prefixed memory files to slug-only naming."""
    try:
        from lib.migrate_filenames import migrate_all, migration_summary

        mnemonic_root = get_memory_root()
        if not mnemonic_root.exists():
            return None

        results = migrate_all(mnemonic_root)
        if not results:
            return None

        summary = migration_summary(results)
        if summary["total"] > 0:
            import subprocess

            git_check = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(mnemonic_root),
                capture_output=True,
                timeout=5,
            )
            if git_check.returncode == 0:
                add_result = subprocess.run(
                    ["git", "add", "-A"],
                    cwd=str(mnemonic_root),
                    capture_output=True,
                    timeout=10,
                )
                if add_result.returncode == 0:
                    subprocess.run(
                        ["git", "commit", "-m", f"migrate: rename {summary['total']} files to slug-only format"],
                        cwd=str(mnemonic_root),
                        capture_output=True,
                        timeout=10,
                    )

        return summary
    except Exception:
        return None


def main():
    resolver = get_v2_resolver()
    org = resolver.context.org
    project = resolver.context.project
    session_id = get_session_id()

    # Initialize session blackboard (includes migration if needed)
    init_session_blackboard(session_id)

    # Auto-migrate UUID-prefixed filenames
    migration_result = run_filename_migration()

    counts = count_memories_by_namespace()
    health = calculate_memory_health()
    blackboard = check_blackboard()
    bb_summaries = get_blackboard_summaries()
    relevant_memories = find_project_relevant_memories(project)
    ontology_info = get_ontology_info()
    suggestions = get_suggestions(health, counts)

    total = sum(counts.values())

    # Build human-readable context for Claude
    context_lines = [
        f"[MNEMONIC] {org}/{project} | {total} memories | health: {health['score']}%",
        "",
    ]

    if counts:
        namespace_summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()) if v > 0)
        context_lines.append(f"- By namespace: {namespace_summary}")

    if health["decayed"] > 0:
        context_lines.append(f"- Decayed memories (confidence < 0.5): {health['decayed']}")

    if health["duplicates_possible"] > 0:
        context_lines.append(f"- Potential duplicates: {health['duplicates_possible']}")

    if ontology_info["loaded"]:
        ont_id = ontology_info.get("id", "custom")
        ont_ver = ontology_info.get("version", "?")
        context_lines.append(f"- Ontology: {ont_id} v{ont_ver}")
        if ontology_info.get("discovery_enabled"):
            context_lines.append("- Discovery patterns: enabled")
        if ontology_info.get("entity_types"):
            ets = ontology_info["entity_types"][:5]
            context_lines.append(f"- Entity types: {', '.join(ets)}")
        if ontology_info.get("traits"):
            trait_names = list(ontology_info["traits"].keys())[:5]
            context_lines.append(f"- Traits: {', '.join(trait_names)}")
        if ontology_info.get("relationships"):
            rel_names = list(ontology_info["relationships"].keys())[:5]
            context_lines.append(f"- Relationships: {', '.join(rel_names)}")

    if blackboard["pending_items"] > 0:
        context_lines.append(f"- Blackboard pending: {blackboard['pending_items']} items")

    # Add handoff summary from previous session
    if bb_summaries:
        context_lines.append("")
        context_lines.append("**PREVIOUS SESSION HANDOFF:**")
        if "last-session" in bb_summaries:
            context_lines.append(bb_summaries["last-session"][:200])

    # Add relevant memories for this project
    if relevant_memories:
        context_lines.append("")
        context_lines.append("**RELEVANT MEMORIES:**")
        for mem in relevant_memories[:3]:
            info = get_memory_summary(mem)
            line = f"  - {info['title']}"
            if info["summary"]:
                line += f": {info['summary']}"
            context_lines.append(line)

    # Resolve memory root for context injection
    memory_root = str(get_memory_root())

    # Add memory-first protocol (compact)
    context_lines.append("")
    context_lines.append(f"MNEMONIC_ROOT: {memory_root}")
    context_lines.append(f'Search before answering: rg -i "{{topic}}" {memory_root}/ --glob "*.memory.md"')

    if migration_result and migration_result.get("total", 0) > 0:
        context_lines.append("")
        context_lines.append("**FILENAME MIGRATION:**")
        context_lines.append(
            f"  Migrated {migration_result['total']} files to slug-only naming "
            f"(renamed: {migration_result['renamed']}, merged: {migration_result['merged']})"
        )

    if suggestions:
        context_lines.append("")
        context_lines.append("Suggestions:")
        for s in suggestions:
            context_lines.append(f"  - {s}")

    additional_context = "\n".join(context_lines)

    # Output using hookSpecificOutput.additionalContext (what Claude sees)
    output = {
        "continue": True,
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": additional_context},
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
