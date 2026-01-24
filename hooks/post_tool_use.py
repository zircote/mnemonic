#!/usr/bin/env python3
"""
Mnemonic PostToolUse Hook

Reinforces CLAUDE.md by reminding Claude to capture after significant tool use.
Does NOT capture itself - Claude does per CLAUDE.md instructions.
"""

import json
import os


def main():
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
        tool_input = {}

    reminders = []

    # Check for significant Write/Edit operations
    if tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path", "")
        if file_path and not any(x in file_path for x in ["/tmp/", ".cache/", "node_modules/"]):
            if any(ext in file_path for ext in [".py", ".ts", ".js", ".go", ".rs", ".java", ".md"]):
                reminders.append(f"CAPTURE: Modified {file_path}")
                reminders.append("  If this establishes a pattern, capture to patterns/")
                reminders.append("  If this implements a decision, capture to decisions/")

    # Check for significant Bash operations
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Git commits = decisions
        if "git commit" in command:
            reminders.append("CAPTURE: Git commit detected")
            reminders.append("  Capture the decision/change to decisions/")

        # Errors = potential learnings
        elif "error" in tool_output.lower() or "failed" in tool_output.lower():
            reminders.append("CAPTURE: Error encountered")
            reminders.append("  When resolved, capture the learning to learnings/")

        # Successful installs/builds = procedural knowledge
        elif any(x in command for x in ["install", "build", "deploy", "migrate"]):
            if "error" not in tool_output.lower():
                reminders.append("CAPTURE: Successful command pattern")
                reminders.append("  Consider capturing to patterns/ or learnings/")

    if reminders:
        message = "<mnemonic-tool-analysis>\n" + "\n".join(reminders) + "\n</mnemonic-tool-analysis>"
        print(json.dumps({
            "continue": True,
            "systemMessage": message
        }))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
