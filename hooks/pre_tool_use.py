#!/usr/bin/env python3
"""
Mnemonic PreToolUse Hook

Detects file patterns from ontology and provides relevant memory paths.
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


def load_file_patterns() -> list:
    """Load file patterns from MIF ontology."""
    # Search paths for ontology
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
        return get_fallback_file_patterns()

    try:
        with open(ontology_file) as f:
            data = yaml.safe_load(f)

        discovery = data.get("discovery", {})
        if not discovery.get("enabled", False):
            return get_fallback_file_patterns()

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

        return patterns if patterns else get_fallback_file_patterns()

    except Exception:
        return get_fallback_file_patterns()


def get_fallback_file_patterns() -> list:
    """Fallback patterns if ontology loading fails."""
    return [
        {
            "patterns": ["auth", "login", "session", "jwt", "oauth"],
            "namespaces": ["_semantic/knowledge", "_semantic/decisions"],
            "context": "authentication"
        },
        {
            "patterns": ["api", "endpoint", "route", "controller"],
            "namespaces": ["_semantic/knowledge", "_semantic/decisions"],
            "context": "API design"
        },
        {
            "patterns": ["db", "database", "model", "schema", "migration"],
            "namespaces": ["_semantic/decisions", "_procedural/migrations"],
            "context": "database"
        },
        {
            "patterns": ["test", "spec", "mock", "fixture"],
            "namespaces": ["_procedural/patterns"],
            "context": "testing"
        },
        {
            "patterns": ["config", "settings", "env"],
            "namespaces": ["_semantic/decisions", "_semantic/knowledge"],
            "context": "configuration"
        },
        {
            "patterns": ["deploy", "docker", "kubernetes", "helm"],
            "namespaces": ["_procedural/runbooks", "_semantic/decisions"],
            "context": "deployment"
        },
        {
            "patterns": ["security", "encrypt", "hash", "sanitize"],
            "namespaces": ["_semantic/knowledge", "_semantic/decisions"],
            "context": "security"
        },
        {
            "patterns": ["service", "component", "module"],
            "namespaces": ["_semantic/entities", "_semantic/decisions"],
            "context": "components"
        },
    ]


def get_org() -> str:
    """Get organization from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5
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


def detect_file_context(file_path: str, file_patterns: list) -> dict | None:
    """Detect which context a file belongs to based on path patterns."""
    path_lower = file_path.lower()

    for config in file_patterns:
        for pattern in config["patterns"]:
            if pattern in path_lower:
                return {
                    "context_description": config["context"],
                    "namespaces": config["namespaces"]
                }

    return None


def find_memories_for_context(context: dict, home: Path, org: str) -> list:
    """Find relevant memory files using fast ripgrep search."""
    memory_files = []

    search_paths = [
        str(home / ".claude" / "mnemonic" / org),
        str(home / ".claude" / "mnemonic" / "default"),
        str(Path.cwd() / ".claude" / "mnemonic"),
    ]

    # Filter to existing paths
    existing_paths = [p for p in search_paths if Path(p).exists()]
    if not existing_paths:
        return []

    # Search for memories in relevant namespaces
    for namespace in context["namespaces"]:
        try:
            cmd = [
                "rg", "-l",
                f"namespace:.*{namespace}",
                "--glob", "*.memory.md",
                "--max-count", "1"
            ] + existing_paths

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and line.endswith(".memory.md"):
                        memory_files.append(line)
                        if len(memory_files) >= 5:
                            break
        except Exception:
            continue

        if len(memory_files) >= 5:
            break

    return memory_files[:5]


def main():
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")

    # Only process Write and Edit tools
    if tool_name not in ["Write", "Edit"]:
        print(json.dumps({"continue": True}))
        return

    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
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
    home = Path.home()
    org = get_org()
    memory_files = find_memories_for_context(context, home, org)

    if not memory_files:
        print(json.dumps({"continue": True}))
        return

    # Build context for Claude
    context_lines = [
        f"Relevant memories for {context['context_description']} context:",
    ]
    for f in memory_files:
        context_lines.append(f"  - {f}")
    context_lines.append("")
    context_lines.append("These may contain patterns or decisions for this edit.")

    additional_context = "\n".join(context_lines)

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": additional_context
        }
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
