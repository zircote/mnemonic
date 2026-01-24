#!/usr/bin/env python3
"""
Mnemonic UserPromptSubmit Hook

Analyzes user prompts for:
1. Topics that might have relevant memories - injects context
2. Keywords indicating decisions/learnings being discussed - flags for capture

Receives prompt via CLAUDE_USER_PROMPT environment variable.
"""

import json
import os
import re
import subprocess
from pathlib import Path


# Keywords that suggest memory recall opportunity
RECALL_KEYWORDS = [
    r"\bwhat did we\b",
    r"\bremember\b",
    r"\bpreviously\b",
    r"\blast time\b",
    r"\bbefore\b",
    r"\bearlier\b",
    r"\bdecided\b",
    r"\bagreed\b",
    r"\bpattern\b",
    r"\bconvention\b",
]

# Keywords that suggest capture opportunity
CAPTURE_KEYWORDS = {
    "decisions": [
        r"\blet'?s use\b",
        r"\bwe('ll| will) use\b",
        r"\bdecided to\b",
        r"\bgoing with\b",
        r"\bchose\b",
        r"\bpicked\b",
    ],
    "learnings": [
        r"\blearned that\b",
        r"\bturns out\b",
        r"\bapparently\b",
        r"\bTIL\b",
        r"\bdiscovered\b",
        r"\brealized\b",
    ],
    "blockers": [
        r"\bblocked by\b",
        r"\bstuck on\b",
        r"\bcan'?t figure out\b",
        r"\bissue with\b",
        r"\bproblem\b",
        r"\bbug\b",
    ],
    "patterns": [
        r"\balways\b.*\bwhen\b",
        r"\bnever\b.*\bwhen\b",
        r"\bconvention\b",
        r"\bstandard\b",
        r"\bbest practice\b",
    ],
}


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


def search_memories(query: str, org: str, limit: int = 5) -> list:
    """Search memories for relevant context."""
    memories = []
    home = Path.home()
    cwd = Path.cwd()

    search_paths = [
        home / ".claude" / "mnemonic" / org,
        cwd / ".claude" / "mnemonic"
    ]

    # Extract key terms from query
    terms = re.findall(r'\b\w{4,}\b', query.lower())
    if not terms:
        return []

    for search_path in search_paths:
        if not search_path.exists():
            continue

        for memory_file in search_path.rglob("*.memory.md"):
            try:
                content = memory_file.read_text().lower()

                # Check if any terms match
                matches = sum(1 for term in terms if term in content)
                if matches > 0:
                    # Extract title
                    title = ""
                    namespace = ""

                    for line in memory_file.read_text().split("\n"):
                        if line.startswith("title:"):
                            title = line.replace("title:", "").strip().strip('"')
                        elif line.startswith("namespace:"):
                            namespace = line.replace("namespace:", "").strip()

                    if title:
                        memories.append({
                            "title": title,
                            "namespace": namespace,
                            "file": str(memory_file),
                            "relevance": matches
                        })
            except Exception:
                continue

    # Sort by relevance
    memories.sort(key=lambda x: x["relevance"], reverse=True)
    return memories[:limit]


def detect_capture_intent(prompt: str) -> list:
    """Detect if prompt indicates content worth capturing."""
    intents = []

    for namespace, patterns in CAPTURE_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                intents.append(namespace)
                break

    return list(set(intents))


def detect_recall_intent(prompt: str) -> bool:
    """Detect if prompt is asking about previous context."""
    for pattern in RECALL_KEYWORDS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    return False


def main():
    prompt = os.environ.get("CLAUDE_USER_PROMPT", "")
    if not prompt:
        print(json.dumps({"continue": True}))
        return

    org = get_org()
    context_parts = []

    # Check for recall intent
    if detect_recall_intent(prompt):
        memories = search_memories(prompt, org)
        if memories:
            context_parts.append("**Relevant Memories Found:**")
            for mem in memories:
                context_parts.append(f"- {mem['title']} ({mem['namespace']})")
            context_parts.append("")

    # Check for capture intent
    capture_intents = detect_capture_intent(prompt)
    if capture_intents:
        context_parts.append(f"**Capture Opportunity:** {', '.join(capture_intents)}")

    # Build result
    if context_parts:
        result = {
            "continue": True,
            "systemMessage": "\n".join(context_parts)
        }
    else:
        result = {"continue": True}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
