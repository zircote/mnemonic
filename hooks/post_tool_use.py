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
        file_path = file_info["file"]
        # Capture significant file creations/edits
        if any(ext in file_path for ext in [".py", ".ts", ".js", ".go", ".rs", ".java"]):
            # Procedural memory for code patterns
            create_memory(
                title=f"Code pattern in {Path(file_path).name}",
                content=f"Modified `{file_path}`.\n\nThis file was created or updated as part of the current task.",
                namespace="patterns",
                mem_type="procedural",
                tags=["code", "auto-captured"],
                code_refs=[{"file": file_path}]
            )
            messages.append(f"Captured: code pattern for {Path(file_path).name}")

    if tool_name == "Bash" and "command" in file_info:
        command = file_info["command"]
        # Capture git commits as decisions
        if "git commit" in command:
            # Extract commit message if available
            commit_msg = re.search(r'-m ["\']([^"\']+)["\']', command)
            msg = commit_msg.group(1) if commit_msg else "Git commit"
            create_memory(
                title=msg,
                content=f"Committed changes:\n\n```bash\n{command}\n```",
                namespace="decisions",
                mem_type="semantic",
                tags=["git", "commit", "auto-captured"]
            )
            messages.append(f"Captured: decision - {msg[:50]}")

        # Capture error resolutions as learnings
        elif "error" in tool_output.lower() or "failed" in tool_output.lower():
            create_memory(
                title=f"Error encountered: {command[:40]}",
                content=f"Command:\n```bash\n{command}\n```\n\nOutput contained error. Resolution pending.",
                namespace="blockers",
                mem_type="episodic",
                tags=["error", "debugging", "auto-captured"]
            )
            messages.append("Captured: blocker - error encountered")

        # Capture successful complex commands as learnings
        elif "success" in tool_output.lower() or tool_output.strip() and not ("error" in tool_output.lower()):
            if any(x in command for x in ["install", "build", "deploy", "migrate"]):
                create_memory(
                    title=f"Command pattern: {command[:40]}",
                    content=f"Successful command:\n```bash\n{command}\n```",
                    namespace="learnings",
                    mem_type="procedural",
                    tags=["command", "workflow", "auto-captured"]
                )
                messages.append(f"Captured: learning - {command[:30]}")

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
