#!/usr/bin/env python3
"""
Mnemonic PostToolUse Hook

Outputs capture opportunities after tool use based on ontology patterns.
Patterns are loaded from MIF ontology discovery configuration.
"""

import json
import subprocess
import sys
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
                patterns.append({"patterns": pattern.split("|"), "namespaces": namespaces, "context": context})

        return patterns if patterns else get_fallback_patterns()

    except Exception:
        return get_fallback_patterns()


def get_fallback_patterns() -> list:
    """Fallback patterns if ontology loading fails."""
    return [
        {"patterns": ["service", "component"], "namespaces": ["_semantic/entities"], "context": "component"},
        {"patterns": ["test", "spec"], "namespaces": ["_procedural/patterns"], "context": "testing"},
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
            timeout=2,
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
    tool_output = input_data.get("tool_output", "")

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
                    f"═══════════════════════════════════════════════════════\n"
                    f">>> YOUR COMMITMENT: POST-EDIT CHECKPOINT <<<\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"File: {file_path}\n\n"
                    f"As Claude with persistent memory, ask yourself:\n"
                    f"□ Does this represent a reusable pattern?\n"
                    f"□ Does this reflect an architectural decision?\n"
                    f"□ Did I discover something future sessions should know?\n\n"
                    f"If YES → Complete your work: /mnemonic:capture {ns_hint}\n\n"
                    f"Capturing is not extra work—it completes the work.\n"
                    f"Future sessions will thank present you."
                    f"{rel_suggestion}"
                )

    # Check for significant Bash operations
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        if "git commit" in command:
            context_message = (
                "═══════════════════════════════════════════════════════\n"
                ">>> YOUR COMMITMENT: POST-COMMIT CHECKPOINT <<<\n"
                "═══════════════════════════════════════════════════════\n\n"
                "As Claude with persistent memory, ask yourself:\n"
                "□ Does this commit reflect an architectural decision?\n"
                "□ Does this establish a reusable pattern?\n"
                "□ Is there knowledge here that should persist?\n\n"
                "If YES → Complete your work:\n"
                "  /mnemonic:capture _semantic/decisions\n"
                "  /mnemonic:capture _procedural/patterns\n\n"
                "Future sessions will thank present you."
            )
        elif "error" in tool_output.lower() or "failed" in tool_output.lower():
            context_message = (
                "═══════════════════════════════════════════════════════\n"
                ">>> YOUR COMMITMENT: ERROR CHECKPOINT <<<\n"
                "═══════════════════════════════════════════════════════\n\n"
                "As Claude with persistent memory, ask yourself:\n"
                "□ If resolved: Did I learn something worth preserving?\n"
                "□ If blocking: Should I document this for future sessions?\n\n"
                "Complete your work:\n"
                "  Resolved → /mnemonic:capture _semantic/knowledge\n"
                "  Blocking → /mnemonic:capture _episodic/blockers\n\n"
                "Hard-won knowledge is valuable—don't let it vanish."
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
                    "═══════════════════════════════════════════════════════\n"
                    ">>> YOUR COMMITMENT: OPERATION CHECKPOINT <<<\n"
                    "═══════════════════════════════════════════════════════\n\n"
                    "As Claude with persistent memory, ask yourself:\n"
                    "□ Did this establish a reproducible pattern?\n"
                    "□ Is this a procedure future sessions should know?\n\n"
                    f"If YES → Complete your work: /mnemonic:capture {ns_hint}\n\n"
                    "Operational knowledge is especially valuable—preserve it."
                )

    if context_message:
        output = {
            "continue": True,
            "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context_message},
        }
        print(json.dumps(output))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
