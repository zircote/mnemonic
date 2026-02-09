# Multi-Agent Coordination

This document describes how agents in the mnemonic system coordinate their work.

## Coordination Model

Agent coordination uses two distinct mechanisms based on scope:

| Scope | Mechanism | When |
|-------|-----------|------|
| **In-session** | Claude Code native swarm | Agents working together in a single session |
| **Cross-session** | Mnemonic blackboard handoff | Passing context to the next session |

### In-Session: Native Swarm

For real-time coordination between agents within a single session, use Claude Code's built-in tools:

- **TeamCreate**: Create a team with shared task list
- **TaskCreate / TaskUpdate / TaskList**: Track and assign work items
- **SendMessage**: Direct messages between agents
- **Task tool**: Spawn specialized subagents

These tools handle registration, status tracking, task handoff, shared state, and progress reporting natively. The mnemonic blackboard is **not** used for in-session coordination.

### Cross-Session: Blackboard Handoff

For context that must survive between sessions, the blackboard provides automatic handoff:

```
${MNEMONIC_ROOT}/.blackboard/
├── sessions/{session_id}/        # Session audit trail
│   ├── session-notes.md          # Activity log
│   └── _meta.json                # Lifecycle metadata
└── handoff/
    ├── latest-handoff.md         # Active handoff (overwritten each session)
    └── handoff-{session_id}.md   # Archived handoffs
```

**Lifecycle:**
1. `hooks/session_start.py` reads `handoff/latest-handoff.md` at session start
2. `hooks/stop.py` writes handoff summary at session end

This is fully automatic via hooks.

## Agents

| Agent | Purpose |
|-------|---------|
| `memory-curator` | Maintenance, conflict detection, deduplication |
| `mnemonic-search-subcall` | Individual search iterations |
| `compression-worker` | Memory summarization |
| `search-enhanced` (orchestrator) | Coordinates multi-round search |

## Path Resolution

Use `lib.paths.PathResolver` or the CLI tool:

```bash
MNEMONIC_ROOT=$(tools/mnemonic-paths root)
BLACKBOARD=$(tools/mnemonic-paths blackboard)
HANDOFF_DIR=${BLACKBOARD}/handoff
```

## Best Practices

1. **Use native swarm for in-session work** - TeamCreate, SendMessage, TaskCreate
2. **Let hooks handle cross-session handoff** - Automatic via session lifecycle
3. **Capture persistent knowledge as memories** - Insights that outlast the next session belong in `*.memory.md`
4. **Keep handoffs actionable** - Focus on what the next session needs

## Related Documentation

- [Blackboard Skill](../skills/mnemonic-blackboard/SKILL.md) - Blackboard patterns and handoff format
- [Agent Coordination Skill](../skills/mnemonic-agent-coordination/SKILL.md) - Coordination patterns
- [ADR-003](adrs/adr-003-agent-coordination-blackboard.md) - Original blackboard decision
- [ADR-011](adrs/adr-011-session-scoped-blackboard.md) - Session-scoped blackboard decision
