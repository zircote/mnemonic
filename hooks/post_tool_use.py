#!/usr/bin/env python3
"""
Mnemonic PostToolUse Hook

Outputs capture opportunities after tool use based on ontology patterns.
Patterns are loaded from MIF ontology discovery configuration.
"""

import json
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_file_patterns() -> list:
    """Load file patterns from MIF ontology for namespace suggestions."""
    plugin_root = Path(__file__).parent.parent
    ontology_paths = [
        plugin_root / "mif" / "ontologies" / "mif-base.ontology.yaml",
        plugin_root / "skills" / "ontology" / "fallback" / "ontologies" / "mif-base.ontology.yaml",
    ]

    ontology_file = None
    for path in ontology_paths:
        if path.exists():
            ontology_file = path
            break

    if not ontology_file or not yaml:
        return get_fallback_patterns()

    try:
        with open(ontology_file) as f:
            data = yaml.safe_load(f)

        discovery = data.get("discovery", {})
        if not discovery.get("enabled", False):
            return get_fallback_patterns()

        patterns = []
        for fp in discovery.get("file_patterns", []):
            pattern = fp.get("pattern")
            namespaces = fp.get("namespaces", [])
            context = fp.get("context", "")
            if pattern and namespaces:
                patterns.append({
                    "patterns": pattern.split("|"),
                    "namespaces": namespaces,
                    "context": context
                })

        return patterns if patterns else get_fallback_patterns()

    except Exception:
        return get_fallback_patterns()


def get_fallback_patterns() -> list:
    """Fallback patterns if ontology loading fails."""
    return [
        {
            "patterns": ["service", "component"],
            "namespaces": ["semantic/entities"],
            "context": "component"
        },
        {
            "patterns": ["test", "spec"],
            "namespaces": ["procedural/patterns"],
            "context": "testing"
        },
    ]


def detect_namespace_for_file(file_path: str, file_patterns: list) -> str:
    """Detect suggested namespace based on file path."""
    path_lower = file_path.lower()

    for config in file_patterns:
        for pattern in config["patterns"]:
            if pattern in path_lower:
                # Return first namespace as suggestion
                return config["namespaces"][0] if config["namespaces"] else None
    return None


def main():
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
        tool_input = {}

    context_message = None
    file_patterns = load_file_patterns()

    # Check for significant Write/Edit operations
    if tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path", "")
        skip = ["/tmp/", ".cache/", "node_modules/", ".memory.md"]
        if file_path and not any(x in file_path for x in skip):
            exts = [".py", ".ts", ".js", ".go", ".rs", ".java"]
            if any(ext in file_path for ext in exts):
                # Get namespace suggestion from ontology
                ns_hint = detect_namespace_for_file(file_path, file_patterns)
                if not ns_hint:
                    ns_hint = "semantic/decisions or procedural/patterns"

                context_message = (
                    f"**CODE MODIFIED:** {file_path}\n"
                    f"Evaluate: Does this represent a pattern or decision?\n"
                    f"If yes → `/mnemonic:capture {ns_hint}` immediately."
                )

    # Check for significant Bash operations
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        if "git commit" in command:
            context_message = (
                "**GIT COMMIT COMPLETED**\n"
                "Evaluate: Does this commit reflect a decision or pattern?\n"
                "If yes → `/mnemonic:capture semantic/decisions` or "
                "`/mnemonic:capture procedural/patterns`"
            )
        elif "error" in tool_output.lower() or "failed" in tool_output.lower():
            context_message = (
                "**ERROR DETECTED**\n"
                "When resolved → `/mnemonic:capture semantic/knowledge`\n"
                "If unresolved → `/mnemonic:capture episodic/blockers`"
            )
        elif any(x in command for x in ["install", "build", "deploy", "migrate"]):
            if "error" not in tool_output.lower():
                if "deploy" in command:
                    ns_hint = "procedural/runbooks"
                elif "migrate" in command:
                    ns_hint = "procedural/migrations"
                else:
                    ns_hint = "procedural/patterns"
                context_message = (
                    "**OPERATION COMPLETED**\n"
                    f"If pattern established → `/mnemonic:capture {ns_hint}`"
                )

    if context_message:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context_message
            }
        }
        print(json.dumps(output))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
