#!/usr/bin/env python3
"""
Mnemonic PostToolUse Hook

Outputs hookSpecificOutput.additionalContext for capture opportunities after tool use.
Claude sees this context and may decide to capture relevant memories.
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

    context_message = None

    # Check for significant Write/Edit operations
    if tool_name in ["Write", "Edit"]:
        file_path = tool_input.get("file_path", "")
        if file_path and not any(x in file_path for x in ["/tmp/", ".cache/", "node_modules/", ".memory.md"]):
            if any(ext in file_path for ext in [".py", ".ts", ".js", ".go", ".rs", ".java"]):
                context_message = (
                    f"**CODE MODIFIED:** {file_path}\n"
                    "Evaluate: Does this represent a pattern, decision, or learning?\n"
                    "If yes → `/mnemonic:capture {{namespace}}` immediately."
                )

    # Check for significant Bash operations
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        if "git commit" in command:
            context_message = (
                "**GIT COMMIT COMPLETED**\n"
                "Evaluate: Does this commit reflect a decision or pattern?\n"
                "If yes → `/mnemonic:capture decisions` or `/mnemonic:capture patterns`"
            )
        elif "error" in tool_output.lower() or "failed" in tool_output.lower():
            context_message = (
                "**ERROR DETECTED**\n"
                "When resolved → `/mnemonic:capture learnings`\n"
                "If unresolved → `/mnemonic:capture blockers`"
            )
        elif any(x in command for x in ["install", "build", "deploy", "migrate"]):
            if "error" not in tool_output.lower():
                context_message = (
                    "**OPERATION COMPLETED**\n"
                    "If pattern established → `/mnemonic:capture patterns`"
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
