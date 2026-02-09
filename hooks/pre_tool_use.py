#!/usr/bin/env python3
"""
Mnemonic PreToolUse Hook

Detects file patterns from ontology and provides relevant memory paths.
Patterns are loaded from MIF ontology discovery configuration.
"""

import json
import sys
from pathlib import Path

# Add project root to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.memory_reader import get_memory_summary
from lib.ontology import load_file_patterns
from lib.search import detect_file_context, find_memories_for_context


def main():
    # Read hook input from stdin (Claude Code passes JSON via stdin)
    input_data = {}
    try:
        if not sys.stdin.isatty():
            input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        pass

    # Extract tool info from stdin JSON
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only process Write and Edit tools
    if tool_name not in ["Write", "Edit"]:
        print(json.dumps({"continue": True}))
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(json.dumps({"continue": True}))
        return

    # Skip temporary/cache files
    skip_patterns = ["/tmp/", ".cache/", "node_modules/", "__pycache__/", ".git/"]
    if any(p in file_path for p in skip_patterns):
        print(json.dumps({"continue": True}))
        return

    # Load patterns from ontology
    file_patterns = load_file_patterns()

    # Detect file context
    context = detect_file_context(file_path, file_patterns)
    if not context:
        print(json.dumps({"continue": True}))
        return

    # Find relevant memories
    memory_files = find_memories_for_context(context)

    if not memory_files:
        print(json.dumps({"continue": True}))
        return

    # Build context for Claude with title + summary
    context_lines = [
        f"[PRE-EDIT] {context['context_description']} context | {len(memory_files)} related memories:",
    ]
    for f in memory_files:
        info = get_memory_summary(f)
        line = f"  - {info['title']}"
        if info["summary"]:
            line += f": {info['summary']}"
        context_lines.append(line)

    additional_context = "\n".join(context_lines)

    output = {
        "continue": True,
        "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": additional_context},
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
