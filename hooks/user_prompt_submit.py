#!/usr/bin/env python3
"""
Mnemonic UserPromptSubmit Hook

Reinforces CLAUDE.md by detecting capture opportunities and reminding Claude.
Does NOT capture itself - Claude does per CLAUDE.md instructions.
"""

import json
import os
import re


# Keywords that suggest capture opportunity
CAPTURE_TRIGGERS = {
    "decisions": [
        r"\blet'?s use\b",
        r"\bwe('ll| will| should) use\b",
        r"\bdecided to\b",
        r"\bgoing with\b",
        r"\bchose\b",
        r"\bpicked\b",
        r"\bwe('ll| will) go with\b",
    ],
    "learnings": [
        r"\blearned that\b",
        r"\bturns out\b",
        r"\bapparently\b",
        r"\bTIL\b",
        r"\bdiscovered\b",
        r"\brealized\b",
        r"\bfound out\b",
        r"\bthe fix was\b",
        r"\bthe solution\b",
    ],
    "patterns": [
        r"\balways\b.*\bwhen\b",
        r"\bnever\b.*\bwhen\b",
        r"\bconvention\b",
        r"\bstandard\b",
        r"\bbest practice\b",
        r"\bwe do it this way\b",
        r"\bthe pattern is\b",
    ],
    "blockers": [
        r"\bblocked by\b",
        r"\bstuck on\b",
        r"\bcan'?t figure out\b",
        r"\bissue with\b",
        r"\bproblem\b",
        r"\bbug\b",
        r"\berror\b",
    ],
}

# Keywords that suggest recall needed
RECALL_TRIGGERS = [
    r"\bwhat did we\b",
    r"\bremember\b",
    r"\bpreviously\b",
    r"\blast time\b",
    r"\bbefore\b",
    r"\bearlier\b",
    r"\bwhat was\b",
    r"\bhow did we\b",
]


def detect_triggers(prompt: str) -> dict:
    """Detect capture and recall triggers in prompt."""
    result = {"capture": [], "recall": False}

    # Check capture triggers
    for namespace, patterns in CAPTURE_TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                result["capture"].append(namespace)
                break

    # Check recall triggers
    for pattern in RECALL_TRIGGERS:
        if re.search(pattern, prompt, re.IGNORECASE):
            result["recall"] = True
            break

    return result


def main():
    prompt = os.environ.get("CLAUDE_USER_PROMPT", "")
    if not prompt:
        print(json.dumps({"continue": True}))
        return

    triggers = detect_triggers(prompt)
    reminders = []

    if triggers["recall"]:
        reminders.append("RECALL: User is asking about prior context. Search memories first:")
        reminders.append("  rg -i '<topic>' ~/.claude/mnemonic/ --glob '*.memory.md'")

    if triggers["capture"]:
        namespaces = ", ".join(triggers["capture"])
        reminders.append(f"CAPTURE: Detected {namespaces} content. Per CLAUDE.md, write memory to:")
        for ns in triggers["capture"]:
            reminders.append(f"  ~/.claude/mnemonic/default/{ns}/user/")

    if reminders:
        message = "<mnemonic-prompt-analysis>\n" + "\n".join(reminders) + "\n</mnemonic-prompt-analysis>"
        print(json.dumps({
            "continue": True,
            "systemMessage": message
        }))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
