#!/usr/bin/env python3
"""
Mnemonic UserPromptSubmit Hook

Detects capture/recall triggers from ontology and provides context hints.
Patterns are loaded from MIF ontology discovery configuration.
"""

import json
import os
import re
import sys
from pathlib import Path

# Add project root to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import get_memory_root
from lib.memory_reader import get_memory_summary
from lib.ontology import load_content_patterns
from lib.search import extract_topic, find_duplicates, search_memories

# Recall triggers (not in ontology yet)
RECALL_TRIGGERS = [
    r"\bremember\b",
    r"\brecall\b",
    r"\bwhat did we\b",
    r"\bhow did we\b",
    r"\bwhat was\b",
    r"\bpreviously\b",
    r"\blast time\b",
    r"\bbefore\b",
]


def get_pending_file() -> Path:
    """Get path to pending capture file - must match stop.py."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return Path("/tmp") / f"mnemonic-pending-{session_id}.json"


def detect_triggers(prompt: str, capture_patterns: dict) -> dict:
    """Detect capture and recall triggers."""
    result = {"capture": [], "recall": False}
    for namespace, patterns in capture_patterns.items():
        for pattern in patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                if namespace not in result["capture"]:
                    result["capture"].append(namespace)
                break
    for pattern in RECALL_TRIGGERS:
        if re.search(pattern, prompt, re.IGNORECASE):
            result["recall"] = True
            break
    return result


def main():
    # Load patterns from ontology
    capture_patterns = load_content_patterns()

    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    prompt = input_data.get("prompt", os.environ.get("CLAUDE_USER_PROMPT", ""))
    if not prompt:
        print(json.dumps({"continue": True}))
        return

    triggers = detect_triggers(prompt, capture_patterns)
    topic = extract_topic(prompt)
    context_lines = []

    # Signal capture opportunity and save pending state
    if triggers["capture"]:
        namespaces = ", ".join(triggers["capture"])

        # Save pending capture info for stop hook
        pending_file = get_pending_file()
        pending_file.write_text(json.dumps({"namespaces": triggers["capture"], "prompt": prompt[:200], "topic": topic}))

        context_lines.append(f"[CAPTURE] Namespace: {namespaces} | Topic: {topic}")
        context_lines.append(f'  /mnemonic:capture {triggers["capture"][0]} "{topic}"')

        # Dedup check: surface existing similar memories to prevent duplicates
        if topic:
            dupes = find_duplicates(topic, namespace=triggers["capture"][0], threshold=0.4, max_results=3)
            if dupes:
                context_lines.append("  **DEDUP WARNING — similar memories exist (update instead of creating new):**")
                for d in dupes:
                    context_lines.append(f"    - [{d['similarity']:.0%}] {d['title']} ({d['namespace']})")

        context_lines.append("")

    # Search for relevant existing memories
    relevant_memories = search_memories(topic) if topic else []

    if relevant_memories:
        context_lines.append("**RELEVANT MEMORIES:**")
        for mem_path in relevant_memories:
            info = get_memory_summary(mem_path)
            line = f"  - {info['title']}"
            if info["summary"]:
                line += f": {info['summary']}"
            context_lines.append(line)
        context_lines.append("")

    # Add recall context
    if triggers["recall"] and not relevant_memories:
        memory_root = str(get_memory_root())
        context_lines.append(f"Recall triggered. Search: rg -i '{topic}' {memory_root}/ --glob '*.memory.md'")

    if context_lines:
        output = {
            "continue": True,
            "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "\n".join(context_lines)},
        }
        print(json.dumps(output))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
