#!/usr/bin/env python3
"""
Mnemonic PostToolUse Hook

Auto-captures learnings from tool results:
- Write/Edit: Capture decisions about code structure
- Bash: Capture command patterns, error resolutions

Receives tool info via environment variables:
- CLAUDE_TOOL_NAME: Name of the tool that was used
- CLAUDE_TOOL_INPUT: JSON input to the tool
- CLAUDE_TOOL_OUTPUT: Output from the tool
"""

import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path


def get_org() -> str:
    """Get organization from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5
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


def extract_file_info(tool_input: dict) -> dict:
    """Extract file information from tool input."""
    info = {}

    if "file_path" in tool_input:
        info["file"] = tool_input["file_path"]

    if "command" in tool_input:
        info["command"] = tool_input["command"]

    return info


def should_capture(tool_name: str, tool_input: dict, _tool_output: str) -> bool:
    """Determine if this tool use is worth capturing."""
    # Skip trivial operations
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        # Skip simple read-only commands
        skip_patterns = [
            r"^ls\b",
            r"^cat\b",
            r"^head\b",
            r"^tail\b",
            r"^pwd$",
            r"^echo\b",
            r"^cd\b",
        ]
        for pattern in skip_patterns:
            if re.match(pattern, command):
                return False

        # Capture if command modified something or was complex
        if any(x in command for x in ["&&", "|", ">"]):
            return True
        if any(x in command for x in ["git commit", "npm", "pip", "cargo"]):
            return True

    if tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path", "")
        # Skip temporary files
        if any(x in file_path for x in ["/tmp/", ".cache/", "node_modules/"]):
            return False
        # Capture significant file changes
        return True

    return False


def create_memory(
    title: str,
    content: str,
    namespace: str,
    mem_type: str,
    tags: list,
    code_refs: list | None = None
) -> str:
    """Create a memory file and return its path."""
    memory_id = str(uuid.uuid4())
    slug = re.sub(r'[^a-z0-9-]', '', title.lower().replace(' ', '-'))[:50]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Determine path
    memory_dir = Path.cwd() / ".claude" / "mnemonic" / namespace / "project"
    memory_dir.mkdir(parents=True, exist_ok=True)

    memory_path = memory_dir / f"{memory_id}-{slug}.memory.md"

    # Build frontmatter
    tags_yaml = "\n".join(f"  - {tag}" for tag in tags)

    code_refs_yaml = ""
    if code_refs:
        code_refs_yaml = "code_refs:\n"
        for ref in code_refs:
            code_refs_yaml += f"  - file: {ref.get('file', '')}\n"
            if 'line' in ref:
                code_refs_yaml += f"    line: {ref['line']}\n"

    memory_content = f"""---
id: {memory_id}
type: {mem_type}
namespace: {namespace}/project
created: {timestamp}
modified: {timestamp}
title: "{title}"
tags:
{tags_yaml}
temporal:
  valid_from: {timestamp}
  recorded_at: {timestamp}
provenance:
  source_type: inferred
  agent: claude-opus-4
  confidence: 0.8
{code_refs_yaml}---

# {title}

{content}
"""

    memory_path.write_text(memory_content)
    return str(memory_path)


def main():
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
        tool_input = {}

    # Check if we should capture
    if not should_capture(tool_name, tool_input, tool_output):
        print(json.dumps({"continue": True}))
        return

    # Extract relevant information
    file_info = extract_file_info(tool_input)
    messages = []

    # Auto-capture based on tool type
    if tool_name in ["Write", "Edit"] and "file" in file_info:
        # Note: We don't actually create memories here to avoid noise
        # Instead, we just flag for potential capture
        messages.append(f"File modified: {file_info['file']}")

    if tool_name == "Bash" and "command" in file_info:
        command = file_info["command"]
        # Check for significant commands
        if "git commit" in command:
            messages.append("Git commit detected - consider capturing decision")
        elif "error" in tool_output.lower() or "failed" in tool_output.lower():
            messages.append("Error encountered - capture resolution if fixed")

    # Output result
    if messages:
        result = {
            "continue": True,
            "systemMessage": "**Mnemonic:** " + "; ".join(messages)
        }
    else:
        result = {"continue": True}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
