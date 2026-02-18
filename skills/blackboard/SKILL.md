---
name: blackboard
description: Cross-session handoff, persistent context via blackboard, and agent coordination patterns
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# Mnemonic Blackboard Skill

Cross-session handoff, persistent context, and agent coordination.

## Trigger Phrases

- "blackboard", "cross-session", "session handoff", "shared context"

## Coordination Overview

| Scope | Mechanism | Tools |
|-------|-----------|-------|
| **In-session** | Claude Code native swarm | TeamCreate, SendMessage, TaskCreate, TaskUpdate |
| **Cross-session** | Mnemonic blackboard handoff | `handoff/latest-handoff.md` via hooks |
| **Persistent knowledge** | Mnemonic memories | `*.memory.md` files |

---

## Path Resolution

```bash
MNEMONIC_ROOT=$(tools/mnemonic-paths root)
BLACKBOARD=$(tools/mnemonic-paths blackboard)
HANDOFF_DIR=${BLACKBOARD}/handoff
```

---

## Directory Structure

```
${BLACKBOARD}/
├── _legacy/                      # Pre-migration files (frozen)
├── sessions/
│   └── {session_id}/
│       ├── session-notes.md      # Session activity log
│       └── _meta.json            # Session lifecycle metadata
├── handoff/
│   ├── latest-handoff.md         # Cross-session context (overwritten each session end)
│   └── handoff-{session_id}.md   # Archived per-session handoffs
└── .archive/                     # Archived entries
```

---

## Cross-Session Handoff

### How It Works

1. **Session end** (`hooks/stop.py`): Writes summary to `handoff/latest-handoff.md`
2. **Session start** (`hooks/session_start.py`): Reads `handoff/latest-handoff.md` to restore context

This is automatic via hooks.

### Handoff Format

```markdown
# Session Handoff

**Session:** {session_id}
**Ended:** {timestamp}
**Project:** {org}/{project}

## What Was Accomplished
- Completed items

## In Progress
- Ongoing work with current state

## Blocked
- Blocker: reason

## Next Steps
- [ ] Action item 1
- [ ] Action item 2

## Important Context
- Key context for next session
```

---

## Mnemonic Agents

| Agent | Purpose | Invocation |
|-------|---------|------------|
| `memory-curator` | Maintenance, deduplication, decay | Standalone or native swarm |
| `mnemonic-search-subcall` | Iterative memory search | Spawned via Task tool |
| `compression-worker` | Memory summarization | Spawned via Task tool |
| `ontology-discovery` | Entity discovery from codebase | Spawned via Task tool |

---

## Session Metadata

Each session creates `_meta.json`:

```json
{
  "session_id": "abc-123",
  "started": "2026-01-15T10:00:00Z",
  "ended": "2026-01-15T11:30:00Z",
  "project": "zircote/mnemonic",
  "org": "zircote",
  "status": "ended"
}
```

---

## Best Practices

- **Native swarm for in-session work** — don't write coordination state to blackboard
- **Let hooks handle handoff** — session lifecycle hooks manage cross-session context automatically
- **Memories for persistence** — if something should survive beyond the next session, capture it as a memory
- **Keep handoffs actionable** — focus on what the next session needs to continue work
