# Multi-Agent Coordination

This document describes how agents within the mnemonic system coordinate their work using the blackboard pattern.

## Overview

The mnemonic system includes multiple agents that may run concurrently or hand off work to each other:

| Agent | Purpose |
|-------|---------|
| `memory-curator` | Maintenance, conflict detection, deduplication |
| `mnemonic-search-subcall` | Individual search iterations |
| `compression-worker` | Memory summarization |
| `search-enhanced` (orchestrator) | Coordinates multi-round search |

Agents coordinate using the existing blackboard files with extended entry format (see ADR-003).

## Blackboard Files

All coordination happens through append-only entries in these files:

```
~/.claude/mnemonic/.blackboard/
├── session-notes.md    # Agent registration, status updates
├── active-tasks.md     # Task handoffs with context
├── shared-context.md   # Workflow state
└── blockers.md         # Coordination blockers
```

## Agent Entry Format

Agent entries extend the standard blackboard format:

```markdown
---
**Session:** {session_id}
**Time:** {timestamp}
**Agent:** {agent_id}
**Status:** active|idle|handoff
**Capabilities:** [list, of, capabilities]

## Entry Content

...

---
```

## Coordination Patterns

### 1. Registration

Agents register when starting work:

```bash
cat >> ~/.claude/mnemonic/.blackboard/session-notes.md << EOF

---
**Session:** $SESSION_ID
**Time:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Agent:** memory-curator
**Status:** active
**Capabilities:** [conflict-detection, deduplication]

## Agent Registration

Started scheduled maintenance.

---
EOF
```

### 2. Status Updates

Agents update their status during work:

```bash
cat >> ~/.claude/mnemonic/.blackboard/session-notes.md << EOF

---
**Session:** $SESSION_ID
**Time:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Agent:** memory-curator
**Status:** idle

## Status Update

Maintenance complete. Processed 50 memories.

---
EOF
```

### 3. Task Handoff

Agents hand off tasks with context:

```bash
cat >> ~/.claude/mnemonic/.blackboard/active-tasks.md << EOF

---
**Session:** $SESSION_ID
**Time:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Agent:** search-enhanced
**Status:** handoff
**Target:** search-subcall-1

## Task Handoff

### Task
Execute search iteration 2

### Context
- Previous iteration found 5 memories
- Need to search patterns namespace

### State
\`\`\`json
{"iteration": 2, "query": "authentication"}
\`\`\`

---
EOF
```

### 4. Shared State

Agents share workflow state:

```bash
cat >> ~/.claude/mnemonic/.blackboard/shared-context.md << EOF

---
**Session:** $SESSION_ID
**Time:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Agent:** search-enhanced
**Status:** active

## Shared State: search-auth-20260124

### Current State
\`\`\`json
{
  "phase": "iteration",
  "iteration": 2,
  "total_findings": 7
}
\`\`\`

---
EOF
```

## Example: Search Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    search-enhanced (orchestrator)            │
├─────────────────────────────────────────────────────────────┤
│ 1. Register in session-notes.md                              │
│ 2. Initialize workflow state in shared-context.md            │
│ 3. Hand off iteration 1 to search-subcall via active-tasks   │
│    ┌───────────────────────────────────────────────────────┐ │
│    │ search-subcall-1                                      │ │
│    │ - Register in session-notes.md                        │ │
│    │ - Execute search                                      │ │
│    │ - Report progress (optional)                          │ │
│    │ - Return JSON findings                                │ │
│    │ - Update status to idle                               │ │
│    └───────────────────────────────────────────────────────┘ │
│ 4. Aggregate findings                                        │
│ 5. Update shared state                                       │
│ 6. Hand off iteration 2 (if needed)                         │
│    ┌───────────────────────────────────────────────────────┐ │
│    │ search-subcall-2                                      │ │
│    │ ...                                                   │ │
│    └───────────────────────────────────────────────────────┘ │
│ 7. Synthesize results                                        │
│ 8. Update final state                                        │
│ 9. Set status to idle                                        │
└─────────────────────────────────────────────────────────────┘
```

## Finding Agent Information

```bash
# Find active agents
grep -B5 "Status: active" ~/.claude/mnemonic/.blackboard/session-notes.md | \
    grep "Agent:" | sed 's/.*Agent: //'

# Find last status for an agent
tac ~/.claude/mnemonic/.blackboard/session-notes.md | \
    grep -A10 "Agent: memory-curator" | head -15

# Find pending handoffs
grep -A20 "Status: handoff" ~/.claude/mnemonic/.blackboard/active-tasks.md

# Get workflow state
WORKFLOW_ID="search-auth-20260124"
tac ~/.claude/mnemonic/.blackboard/shared-context.md | \
    awk "/^## Shared State: $WORKFLOW_ID$/,/^---$/" | tac
```

## Best Practices

1. **Always register** - Agents should register on startup
2. **Update on completion** - Set status to `idle` when done
3. **Include context** - Handoffs should have enough context for receiver
4. **Use workflow IDs** - Enable tracking across entries
5. **Clean up** - Archive old entries periodically
6. **Minimal writes** - Only write when state changes meaningfully

## Cleanup

Blackboard files grow over time. Clean up periodically:

```bash
# Archive old entries (run as part of gc)
ARCHIVE_DIR="$HOME/.claude/mnemonic/.blackboard/.archive"
mkdir -p "$ARCHIVE_DIR"

for topic in session-notes active-tasks shared-context; do
    if [ -f "$HOME/.claude/mnemonic/.blackboard/${topic}.md" ]; then
        tail -500 "$HOME/.claude/mnemonic/.blackboard/${topic}.md" > \
            "$HOME/.claude/mnemonic/.blackboard/${topic}.md.tmp"
        mv "$HOME/.claude/mnemonic/.blackboard/${topic}.md.tmp" \
           "$HOME/.claude/mnemonic/.blackboard/${topic}.md"
    fi
done
```

## Related Documentation

- [Blackboard Skill](../skills/mnemonic-blackboard/SKILL.md) - Base blackboard patterns
- [Agent Coordination Skill](../skills/mnemonic-agent-coordination/SKILL.md) - Full coordination patterns
- [ADR-003](adrs/adr-003-agent-coordination-blackboard.md) - Architectural decision
