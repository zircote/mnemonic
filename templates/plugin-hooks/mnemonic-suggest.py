#!/usr/bin/env python3
"""
Mnemonic Integration Hook Template

This is a template for creating plugin-specific mnemonic integration hooks.
Copy this file to the target plugin's hooks directory and customize the
detection logic for that plugin's file patterns.

Usage:
1. Copy to {plugin_path}/hooks/mnemonic-suggest.py
2. Add to hooks.json PostToolUse for Write matcher
3. Customize the PLUGIN_PATTERNS dict for your plugin

Hook Contract:
- Receives CLAUDE_TOOL_INPUT with tool parameters as JSON
- Outputs JSON with continue: true and optional additionalContext
- additionalContext is shown to Claude as context for the current turn
"""

import json
import os
import re
from pathlib import Path

# =============================================================================
# CUSTOMIZE THIS SECTION FOR YOUR PLUGIN
# =============================================================================

# Plugin name for context
PLUGIN_NAME = "your-plugin"

# File pattern detection rules
# Each rule maps a file pattern to capture suggestions
PLUGIN_PATTERNS = {
    # Example: ADR files
    r"/adr/.*\.md$": {
        "event": "ADR created",
        "namespace": "decisions",
        "capture_hint": "Capture decision rationale including: decision drivers, chosen option, alternatives considered, consequences",
        "tags": ["architecture", "adr"],
    },
    # Example: Documentation files
    r"/docs/.*\.md$": {
        "event": "Documentation created",
        "namespace": "learnings",
        "capture_hint": "Capture key documentation points for future reference",
        "tags": ["documentation"],
    },
    # Example: Config files
    r"\.config\.(js|ts|json)$": {
        "event": "Configuration created",
        "namespace": "patterns",
        "capture_hint": "Capture configuration pattern and rationale",
        "tags": ["configuration", "patterns"],
    },
    # Add more patterns as needed for your plugin
}

# Namespaces and their typical content
NAMESPACE_HINTS = {
    "decisions": "Architectural choices, technology selections, design decisions",
    "learnings": "Insights, discoveries, documentation, TILs",
    "patterns": "Coding conventions, best practices, workflows",
    "blockers": "Issues, impediments, workarounds",
    "context": "Background information, project state",
}

# =============================================================================
# HOOK IMPLEMENTATION (Usually no changes needed below)
# =============================================================================


def match_pattern(file_path: str) -> dict | None:
    """Match file path against plugin patterns."""
    for pattern, config in PLUGIN_PATTERNS.items():
        if re.search(pattern, file_path, re.IGNORECASE):
            return config
    return None


def get_project_context() -> str:
    """Get current project context for the suggestion."""
    try:
        cwd = os.getcwd()
        project_name = Path(cwd).name
        return f"Project: {project_name}"
    except Exception:
        return "Project: unknown"


def format_capture_suggestion(file_path: str, config: dict) -> str:
    """Format the mnemonic capture suggestion for Claude."""
    namespace = config.get("namespace", "learnings")
    namespace_hint = NAMESPACE_HINTS.get(namespace, "General knowledge")
    tags = config.get("tags", [])
    tags_str = ", ".join(tags) if tags else "relevant-tag"

    return f"""
**MNEMONIC CAPTURE SUGGESTED:**
- Event: {config.get('event', 'File created')}
- File: {file_path}
- Namespace: {namespace} ({namespace_hint})
- Suggested tags: {tags_str}

{config.get('capture_hint', 'Capture key details for future recall.')}

Use progressive disclosure format:
- **Quick Answer:** 1-3 sentence summary
- **Context:** Why this was created, alternatives considered
- **Full Detail:** Implementation notes, related decisions

Capture command template:
```bash
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Write memory to ${MNEMONIC_ROOT}/default/{namespace}/user/${{UUID}}-slug.memory.md
```
"""


def main():
    """Main hook entry point."""
    # Parse tool input from environment
    tool_input_raw = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    try:
        tool_input = json.loads(tool_input_raw)
    except json.JSONDecodeError:
        tool_input = {}

    # Get file path from Write tool input
    file_path = tool_input.get("file_path", "")

    if not file_path:
        # No file path, nothing to suggest
        print(json.dumps({"continue": True}))
        return

    # Check if file matches any plugin patterns
    config = match_pattern(file_path)

    if config:
        # Generate capture suggestion
        context = format_capture_suggestion(file_path, config)
        project_ctx = get_project_context()

        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"{project_ctx}\n{context}"
            }
        }
        print(json.dumps(output))
    else:
        # No matching pattern, continue without suggestion
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
