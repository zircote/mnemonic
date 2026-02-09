---
name: mnemonic-blackboard
description: Cross-session handoff and persistent context via blackboard
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

Cross-session handoff and persistent context.

## Trigger Phrases

- "blackboard"
- "cross-session"
- "session handoff"
- "shared context"

## Overview

The blackboard provides **cross-session persistence** - the ability to hand off context from one Claude Code session to the next. It is not used for in-session agent coordination, which is handled by Claude Code's native swarm tools (TeamCreate, SendMessage, TaskCreate/TaskUpdate).

### Scope

| Concern | Mechanism |
|---------|-----------|
| In-session agent coordination | Native swarm (TeamCreate, SendMessage, TaskCreate) |
| Cross-session context handoff | Blackboard `handoff/latest-handoff.md` |
| Persistent knowledge | Mnemonic memories (`*.memory.md`) |

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

The `sessions/` directory provides an audit trail. The `handoff/` directory is the active coordination surface.

---

## Cross-Session Handoff

### How It Works

1. **Session end** (`hooks/stop.py`): Writes a handoff summary to `handoff/latest-handoff.md`
2. **Session start** (`hooks/session_start.py`): Reads `handoff/latest-handoff.md` to restore context

This is automatic - hooks handle the lifecycle.

### Handoff Entry Format

```markdown
# Session Handoff

**Session:** {session_id}
**Ended:** {timestamp}
**Project:** {org}/{project}

## What Was Accomplished
- Item 1
- Item 2

## In Progress
- Item 3: current state

## Blocked
- Blocker: reason

## Next Steps
- [ ] Action item 1
- [ ] Action item 2

## Important Context
- Key context for next session
```

### Manual Handoff

To explicitly write handoff context for the next session:

```bash
BLACKBOARD=$(tools/mnemonic-paths blackboard)
# Write to handoff/latest-handoff.md
```

---

## Session Metadata

Each session creates `_meta.json` with lifecycle tracking:

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

Status values: `active` (session running), `ended` (session completed).

---

## Best Practices

1. **Let hooks handle it** - Handoff is automatic via session_start and stop hooks
2. **Keep handoffs concise** - Focus on what the next session needs to know
3. **Use memories for persistence** - If something should survive beyond the next session, capture it as a memory
4. **Don't use blackboard for in-session coordination** - Use native swarm tools instead

---

## Related

- ADR-003 - Agent Coordination via Blackboard Extension
- ADR-011 - Session-Scoped Blackboard
