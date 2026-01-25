#!/usr/bin/env python3
"""
Mnemonic PreToolUse Hook

Detects file patterns and provides relevant memory file paths via additionalContext.
Claude sees this context and may read those memories before proceeding.
"""

import json
import os
import subprocess
from pathlib import Path


# File patterns mapped to memory contexts
FILE_PATTERNS = {
    "auth": {
        "patterns": ["auth", "login", "logout", "session", "jwt", "oauth", "token", "credential", "password"],
        "namespaces": ["security", "decisions", "patterns"],
        "context": "authentication"
    },
    "api": {
        "patterns": ["api", "endpoint", "route", "controller", "handler", "rest", "graphql"],
        "namespaces": ["apis", "decisions", "patterns"],
        "context": "API design"
    },
    "database": {
        "patterns": ["db", "database", "model", "schema", "migration", "query", "sql", "orm", "entity"],
        "namespaces": ["decisions", "patterns"],
        "context": "database"
    },
    "test": {
        "patterns": ["test", "spec", "mock", "fixture", "jest", "pytest", "vitest"],
        "namespaces": ["testing", "patterns"],
        "context": "testing"
    },
    "config": {
        "patterns": ["config", "settings", "env", "environment", ".env", "configuration"],
        "namespaces": ["decisions", "context"],
        "context": "configuration"
    },
    "deploy": {
        "patterns": ["deploy", "docker", "kubernetes", "k8s", "helm", "ci", "cd", "pipeline", "workflow"],
        "namespaces": ["decisions", "patterns"],
        "context": "deployment"
    },
    "security": {
        "patterns": ["security", "encrypt", "decrypt", "hash", "sanitize", "validate", "xss", "csrf"],
        "namespaces": ["security", "decisions"],
        "context": "security"
    },
}


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


def detect_file_context(file_path: str) -> dict | None:
    """Detect which context a file belongs to based on path patterns."""
    path_lower = file_path.lower()

    for context_name, config in FILE_PATTERNS.items():
        for pattern in config["patterns"]:
            if pattern in path_lower:
                return {
                    "name": context_name,
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
            # Use ripgrep to find memories in this namespace
            cmd = [
                "rg", "-l",
                f"namespace:.*{namespace}",
                "--glob", "*.memory.md",
                "--max-count", "1"  # Just check if pattern exists
            ] + existing_paths

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and line.endswith(".memory.md"):
                        memory_files.append(line)
                        if len(memory_files) >= 5:  # Limit to 5 files
                            break
        except Exception:
            continue

        if len(memory_files) >= 5:
            break

    # If namespace search didn't find enough, search by context keywords
    if len(memory_files) < 3:
        try:
            context_keyword = context["name"]
            cmd = [
                "rg", "-l", "-i",
                context_keyword,
                "--glob", "*.memory.md",
            ] + existing_paths

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and line.endswith(".memory.md") and line not in memory_files:
                        memory_files.append(line)
                        if len(memory_files) >= 5:
                            break
        except Exception:
            pass

    return memory_files[:5]  # Return at most 5


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

    # Detect file context
    context = detect_file_context(file_path)
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
    context_lines.append("These may contain patterns or decisions applicable to this edit.")

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
