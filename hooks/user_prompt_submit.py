#!/usr/bin/env python3
"""
Mnemonic UserPromptSubmit Hook

Detects capture/recall triggers from ontology and provides context hints.
Patterns are loaded from MIF ontology discovery configuration.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Add project root to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import yaml
except ImportError:
    yaml = None

# Import path resolution from lib
try:
    from lib.paths import PathResolver, PathContext, PathScheme
    USE_LIB_PATHS = True
except ImportError:
    USE_LIB_PATHS = False


def _get_path_resolver() -> "PathResolver | None":
    """Get a PathResolver instance, returning None if lib not available."""
    if not USE_LIB_PATHS:
        return None
    # Use V2 scheme - unified path structure
    context = PathContext.detect(scheme=PathScheme.V2)
    return PathResolver(context)


def _get_memory_roots() -> list:
    """Get all memory root paths for searching."""
    resolver = _get_path_resolver()
    if resolver:
        roots = resolver.get_all_memory_roots()
        # Also check legacy paths during migration period
        home = Path.home()
        org = resolver.context.org
        legacy_roots = [
            home / ".claude" / "mnemonic" / org,
            home / ".claude" / "mnemonic" / "default",
            Path.cwd() / ".claude" / "mnemonic",
        ]
        return list(set(roots + [p for p in legacy_roots if p.exists()]))

    # Fallback to default path
    mnemonic_dir = Path.home() / ".claude" / "mnemonic"
    return [mnemonic_dir] if mnemonic_dir.exists() else []


def load_ontology_patterns() -> dict:
    """Load content patterns from MIF ontology."""
    patterns = {}

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
        return get_fallback_patterns()

    try:
        with open(ontology_file) as f:
            data = yaml.safe_load(f)

        discovery = data.get("discovery", {})
        if not discovery.get("enabled", False):
            return get_fallback_patterns()

        for cp in discovery.get("content_patterns", []):
            namespace = cp.get("namespace")
            pattern = cp.get("pattern")
            if namespace and pattern:
                if namespace not in patterns:
                    patterns[namespace] = []
                patterns[namespace].append(pattern)

        return patterns if patterns else get_fallback_patterns()

    except Exception:
        return get_fallback_patterns()


def get_fallback_patterns() -> dict:
    """Fallback patterns if ontology loading fails."""
    return {
        "_semantic/decisions": [
            r"\blet'?s use\b", r"\bwe'?ll use\b", r"\bdecided to\b",
            r"\bgoing with\b", r"\bdecision:\b", r"\bselected\b",
        ],
        "_semantic/knowledge": [
            r"\blearned that\b", r"\bturns out\b", r"\bthe fix was\b",
        ],
        "_procedural/patterns": [
            r"\bshould always\b", r"\balways use\b", r"\bconvention\b",
        ],
        "_episodic/blockers": [
            r"\bblocked by\b", r"\bstuck on\b",
        ],
        "_episodic/incidents": [
            r"\boutage\b", r"\bincident\b", r"\bpostmortem\b",
        ],
        "_procedural/runbooks": [
            r"\brunbook\b", r"\bplaybook\b", r"\bSOP\b",
        ],
    }


# Recall triggers (not in ontology yet)
RECALL_TRIGGERS = [
    r"\bremember\b", r"\brecall\b", r"\bwhat did we\b", r"\bhow did we\b",
    r"\bwhat was\b", r"\bpreviously\b", r"\blast time\b", r"\bbefore\b",
]


def get_pending_file() -> Path:
    """Get path to pending capture file - must match stop.py."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return Path("/tmp") / f"mnemonic-pending-{session_id}.json"


def detect_triggers(prompt: str, capture_patterns: dict) -> dict:
    """Detect capture and recall triggers."""
    result = {"capture": [], "recall": False}
    for namespace, patterns in capture_patterns.items():
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
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "we", "i", "you", "it",
        "do", "did", "does", "have", "has", "had", "what", "how", "why", "when",
        "about", "this", "that", "there", "here", "with", "for", "to", "from",
        "remember", "recall", "before", "earlier", "previously", "last", "time",
        "let", "lets", "use", "using", "go", "going", "will", "should", "can",
    }
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return " ".join(keywords[:5]) if keywords else ""


def search_memories(topic: str) -> list:
    """Search mnemonic for memories matching topic."""
    if not topic:
        return []

    memory_roots = _get_memory_roots()
    if not memory_roots:
        return []

    results = []
    for mnemonic_dir in memory_roots:
        if not mnemonic_dir.exists():
            continue
        try:
            result = subprocess.run(
                ["rg", "-i", "-l", topic, "--glob", "*.memory.md"],
                capture_output=True,
                text=True,
                cwd=str(mnemonic_dir),
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                # Prefix paths with their root directory
                for rel_path in result.stdout.strip().split("\n"):
                    results.append(str(mnemonic_dir / rel_path))
                    if len(results) >= 3:
                        break
        except Exception:
            pass
        if len(results) >= 3:
            break
    return results[:3]


def get_memory_title(memory_path: str) -> str:
    """Get title from a memory file."""
    try:
        full_path = Path(memory_path)
        if not full_path.is_absolute():
            # Search in memory roots
            for root in _get_memory_roots():
                candidate = root / memory_path
                if candidate.exists():
                    full_path = candidate
                    break
        with open(full_path, 'r') as f:
            content = f.read(500)
        match = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return Path(memory_path).stem


def main():
    # Load patterns from ontology
    capture_patterns = load_ontology_patterns()

    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    prompt = input_data.get("prompt", os.environ.get("CLAUDE_USER_PROMPT", ""))
    if not prompt:
        print(json.dumps({"continue": True}))
        return

    triggers = detect_triggers(prompt, capture_patterns)
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

        context_lines.append("!!! >>> MEMORY CAPTURE REQUIRED <<< !!!")
        context_lines.append(f"Namespace(s): {namespaces}")
        context_lines.append("")
        context_lines.append(f">>> EXECUTE NOW: /mnemonic:capture {triggers['capture'][0]} \"{topic}\"")
        context_lines.append("")
        context_lines.append("Do NOT proceed with your response until capture is complete.")
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
        context_lines.append(
            f"Recall triggered. Search: rg -i '{topic}' "
            "~/.claude/mnemonic/ --glob '*.memory.md'"
        )

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
