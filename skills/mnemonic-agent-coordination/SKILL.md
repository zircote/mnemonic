---
name: mnemonic-agent-coordination
description: Agent coordination patterns - native swarm for in-session, blackboard for cross-session handoff
user-invocable: false
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

# Mnemonic Agent Coordination Skill

Agent coordination patterns for the mnemonic system.

## Overview

Agent coordination is split between two mechanisms:

| Scope | Mechanism | Tools |
|-------|-----------|-------|
| **In-session** | Claude Code native swarm | TeamCreate, SendMessage, TaskCreate, TaskUpdate, TaskList |
| **Cross-session** | Mnemonic blackboard handoff | `handoff/latest-handoff.md` via hooks |

### In-Session Coordination (Native Swarm)

For agents working together within a single session, use Claude Code's built-in tools:

- **TeamCreate**: Create a team with shared task list
- **TaskCreate / TaskUpdate / TaskList**: Track and assign work items
- **SendMessage**: Direct messages between agents
- **Task tool**: Spawn specialized subagents

These tools provide real-time coordination, task dependencies, and message delivery. Do **not** duplicate this functionality with blackboard writes.

### Cross-Session Handoff (Blackboard)

For context that must survive across sessions:

```bash
BLACKBOARD=$(tools/mnemonic-paths blackboard)
```

The handoff mechanism is automatic:
1. `hooks/stop.py` writes session summary to `${BLACKBOARD}/handoff/latest-handoff.md`
2. `hooks/session_start.py` reads this file to provide context to the new session

---

## Mnemonic Agents

| Agent | Purpose | Coordination |
|-------|---------|-------------|
| `memory-curator` | Maintenance, deduplication, decay | Standalone or native swarm |
| `mnemonic-search-subcall` | Iterative memory search | Spawned via Task tool |
| `compression-worker` | Memory summarization | Spawned via Task tool |
| `search-enhanced` (orchestrator) | Multi-round search | Uses Task tool to spawn subcalls |

---

## Cross-Session Handoff Format

When ending a session with important context for the next session, the stop hook writes:

```markdown
# Session Handoff

**Session:** {session_id}
**Ended:** {timestamp}
**Project:** {org}/{project}

## What Was Accomplished
- Completed items

## In Progress
- Ongoing work with current state

## Next Steps
- [ ] What the next session should do
```

---

## Best Practices

1. **Use native swarm for in-session work** - Don't write coordination state to blackboard files
2. **Let hooks handle handoff** - The session lifecycle hooks manage cross-session context automatically
3. **Capture persistent knowledge as memories** - If insights should last beyond the next session, use `/mnemonic:capture`
4. **Keep handoffs actionable** - Focus on what the next session needs to continue work

---

## Related

- `mnemonic-blackboard` skill - Blackboard patterns and handoff format
- ADR-003 - Agent Coordination via Blackboard Extension
- ADR-011 - Session-Scoped Blackboard
