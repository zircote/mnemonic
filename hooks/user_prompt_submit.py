#!/usr/bin/env python3
"""
Mnemonic UserPromptSubmit Hook

Detects capture/recall triggers and provides context hints to Claude.
Claude performs the actual capture using skills (skills-first architecture).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Capture triggers by namespace
CAPTURE_TRIGGERS = {
    "decisions": [
        r"\blet'?s use\b", r"\bwe('ll| will| should) use\b", r"\bdecided to\b",
        r"\bgoing with\b", r"\bchose\b", r"\bpicked\b", r"\bwe('ll| will) go with\b",
        r"\bthe plan is\b", r"\bwe('re| are) going to\b", r"\bour approach\b",
    ],
    "learnings": [
        r"\blearned that\b", r"\bturns out\b", r"\bTIL\b",
        r"\bdiscovered\b", r"\brealized\b", r"\bthe fix was\b",
        r"\bthe solution\b", r"\bgotcha\b", r"\bthe key is\b",
    ],
    "patterns": [
        r"\bshould always\b", r"\balways use\b", r"\bnever\b.*\bwhen\b",
        r"\bconvention\b", r"\bbest practice\b", r"\bwe do it this way\b",
        r"\bthe pattern is\b", r"\bstandard\b.*\bfor\b",
    ],
    "blockers": [
        r"\bblocked by\b", r"\bstuck on\b", r"\bcan'?t figure out\b",
        r"\bcan'?t get .* to work\b",
    ],
    "context": [
        r"\bdon'?t forget\b", r"\bremember this\b", r"\bremember that\b",
        r"\bnote to self\b", r"\bsave this\b",
    ],
}

# Recall triggers
RECALL_TRIGGERS = [
    r"\bremember\b", r"\brecall\b", r"\bwhat did we\b", r"\bhow did we\b",
    r"\bwhat was\b", r"\bpreviously\b", r"\blast time\b", r"\bbefore\b",
]


def get_pending_file() -> Path:
    """Get path to pending capture file - must match stop.py."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return Path("/tmp") / f"mnemonic-pending-{session_id}.json"


def detect_triggers(prompt: str) -> dict:
    """Detect capture and recall triggers."""
    result = {"capture": [], "recall": False}
    for namespace, patterns in CAPTURE_TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                if namespace not in result["capture"]:
                    result["capture"].append(namespace)
                break
    for pattern in RECALL_TRIGGERS:
        if re.search(pattern, prompt, re.IGNORECASE):
            result["recall"] = True
            break
    return result


def extract_topic(prompt: str) -> str:
    """Extract topic keywords for search."""
    words = re.sub(r"[^\w\s]", "", prompt.lower()).split()
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "we", "i", "you", "it",
                 "do", "did", "does", "have", "has", "had", "what", "how", "why", "when",
                 "about", "this", "that", "there", "here", "with", "for", "to", "from",
                 "remember", "recall", "before", "earlier", "previously", "last", "time",
                 "let", "lets", "use", "using", "go", "going", "will", "should", "can"}
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return " ".join(keywords[:5]) if keywords else ""


def search_memories(topic: str) -> list:
    """Search mnemonic for memories matching topic."""
    if not topic:
        return []

    mnemonic_dir = Path.home() / ".claude" / "mnemonic"
    if not mnemonic_dir.exists():
        return []

    try:
        result = subprocess.run(
            ["rg", "-i", "-l", topic, "--glob", "*.memory.md"],
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


def get_memory_title(memory_path: str) -> str:
    """Get title from a memory file."""
    try:
        mnemonic_dir = Path.home() / ".claude" / "mnemonic"
        with open(mnemonic_dir / memory_path, 'r') as f:
            content = f.read(500)
        match = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return Path(memory_path).stem


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    prompt = input_data.get("prompt", os.environ.get("CLAUDE_USER_PROMPT", ""))
    if not prompt:
        print(json.dumps({"continue": True}))
        return

    triggers = detect_triggers(prompt)
    topic = extract_topic(prompt)
    context_lines = []

    # Signal capture requirement and save pending state
    if triggers["capture"]:
        namespaces = ", ".join(triggers["capture"])

        # Save pending capture info for stop hook
        pending_file = get_pending_file()
        pending_file.write_text(json.dumps({
            "namespaces": triggers["capture"],
            "prompt": prompt[:200],
            "topic": topic
        }))

        context_lines.append(f"**MEMORY CAPTURE REQUIRED** - namespace(s): {namespaces}")
        context_lines.append(f"You MUST invoke `/mnemonic:capture {triggers['capture'][0]} \"{topic}\"` to capture this.")
        context_lines.append("Do NOT respond until you have captured this to memory.")
        context_lines.append("")

    # Search for relevant existing memories
    relevant_memories = search_memories(topic) if topic else []

    if relevant_memories:
        context_lines.append("**RELEVANT MEMORIES:**")
        for mem_path in relevant_memories:
            title = get_memory_title(mem_path)
            context_lines.append(f"  - {mem_path}: {title}")
        context_lines.append("Check these before researching externally.")
        context_lines.append("")

    # Add recall context
    if triggers["recall"] and not relevant_memories:
        context_lines.append(f"Recall triggered. Search: rg -i '{topic}' ~/.claude/mnemonic/ --glob '*.memory.md'")

    if context_lines:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n".join(context_lines)
            }
        }
        print(json.dumps(output))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
