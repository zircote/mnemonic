#!/usr/bin/env python3
"""
Mnemonic PostToolUse Hook

Outputs capture opportunities after tool use based on ontology patterns.
Patterns are loaded from MIF ontology discovery configuration.
"""

import json
import os
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_ontology_data() -> dict:
    """Load full ontology data including relationships."""
    plugin_root = Path(__file__).parent.parent
    ontology_paths = [
        plugin_root / "mif" / "ontologies" / "mif-base.ontology.yaml",
        plugin_root / "skills" / "ontology" / "fallback" / "ontologies" / "mif-base.ontology.yaml",
    ]

    for path in ontology_paths:
        if path.exists() and yaml:
            try:
                with open(path) as f:
                    return yaml.safe_load(f)
            except Exception:
                continue
    return {}


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
            "namespaces": ["_semantic/entities"],
            "context": "component"
        },
        {
            "patterns": ["test", "spec"],
            "namespaces": ["_procedural/patterns"],
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
                return config["namespaces"][0] if config["namespaces"] else ""
    return ""


def find_related_memories(context: str) -> list:
    """Find existing memories that might be related to current work."""
    if not context:
        return []

    mnemonic_dir = Path.home() / ".claude" / "mnemonic"
    if not mnemonic_dir.exists():
        return []

    try:
        result = subprocess.run(
            ["rg", "-i", "-l", context, "--glob", "*.memory.md", "--max-count", "1"],
            capture_output=True,
            text=True,
            cwd=str(mnemonic_dir),
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[:3]
    except Exception:
        pass
    return []


def get_relationship_suggestions(ontology_data: dict, context: str) -> str:
    """Get relationship suggestions based on ontology."""
    relationships = ontology_data.get("relationships", {})
    if not relationships:
        return ""

    related = find_related_memories(context)
    if not related:
        return ""

    rel_names = list(relationships.keys())
    rel_str = ", ".join(rel_names[:3])
    return (
        f"\n**ENTITY LINKING:** Found {len(related)} related memories.\n"
        f"Available relationships: {rel_str}\n"
        f"Consider linking with `relates_to:` in frontmatter."
    )


def main():
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
        tool_input = {}

    context_message = None
    ontology_data = load_ontology_data()
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
                    ns_hint = "_semantic/decisions or _procedural/patterns"

                # Extract context for relationship suggestions
                file_context = Path(file_path).stem.replace("-", " ").replace("_", " ")
                rel_suggestion = get_relationship_suggestions(ontology_data, file_context)

                context_message = (
                    f">>> POST-EDIT CHECKPOINT <<<\n"
                    f"File: {file_path}\n\n"
                    f"EVALUATE NOW:\n"
                    f"□ Does this represent a reusable pattern?\n"
                    f"□ Does this reflect an architectural decision?\n\n"
                    f"If YES → Execute: /mnemonic:capture {ns_hint}\n"
                    f"Do not proceed without evaluating."
                    f"{rel_suggestion}"
                )

    # Check for significant Bash operations
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        if "git commit" in command:
            context_message = (
                ">>> POST-COMMIT CHECKPOINT <<<\n\n"
                "EVALUATE NOW:\n"
                "□ Does this commit reflect an architectural decision?\n"
                "□ Does this establish a reusable pattern?\n\n"
                "If YES → Execute: /mnemonic:capture _semantic/decisions\n"
                "         or: /mnemonic:capture _procedural/patterns"
            )
        elif "error" in tool_output.lower() or "failed" in tool_output.lower():
            context_message = (
                ">>> ERROR CHECKPOINT <<<\n\n"
                "EVALUATE NOW:\n"
                "□ If resolved: Capture the fix → /mnemonic:capture _semantic/knowledge\n"
                "□ If blocking: Document blocker → /mnemonic:capture _episodic/blockers"
            )
        elif any(x in command for x in ["install", "build", "deploy", "migrate"]):
            if "error" not in tool_output.lower():
                if "deploy" in command:
                    ns_hint = "_procedural/runbooks"
                elif "migrate" in command:
                    ns_hint = "_procedural/migrations"
                else:
                    ns_hint = "_procedural/patterns"
                context_message = (
                    ">>> OPERATION CHECKPOINT <<<\n\n"
                    "EVALUATE NOW:\n"
                    f"□ Did this establish a reproducible pattern?\n\n"
                    f"If YES → Execute: /mnemonic:capture {ns_hint}"
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
