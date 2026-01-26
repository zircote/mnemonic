---
name: mnemonic-agent-coordination
description: Multi-agent coordination patterns via blackboard extension for mnemonic system
user-invocable: false
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Mnemonic Agent Coordination Skill

Multi-agent coordination patterns using the blackboard extension model.

## Overview

This skill provides patterns for agents within the mnemonic system to:
- Register their presence and capabilities
- Update their status (active, idle, handoff)
- Hand off tasks with context
- Share state for workflow coordination

All coordination uses existing blackboard files with extended entry format (see ADR-003).

---

## Agent Entry Format

Agent entries extend the standard blackboard entry format:

```markdown
---
**Session:** {session_id}
**Time:** {timestamp}
**Agent:** {agent_id}
**Status:** active|idle|handoff
**Capabilities:** [list, of, capabilities]

## Entry Content

Content describing what the agent is doing or handing off...

---
```

### Required Fields

| Field | Description |
|-------|-------------|
| `Session` | Claude session ID or generated ID |
| `Time` | ISO 8601 timestamp |
| `Agent` | Unique agent identifier (e.g., `memory-curator`, `search-subcall-1`) |
| `Status` | Current agent status |

### Status Values

| Status | Meaning |
|--------|---------|
| `active` | Agent is currently working |
| `idle` | Agent has finished and is available |
| `handoff` | Agent is handing off to another agent |

---

## Registration Pattern

Agents register in `session-notes.md` when starting work.

### Registration Entry

```bash
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
AGENT_ID="memory-curator"

cat >> ~/.claude/mnemonic/.blackboard/session-notes.md << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Agent:** $AGENT_ID
**Status:** active
**Capabilities:** [conflict-detection, deduplication, decay-management]

## Agent Registration

Memory curator agent started.

### Task
Performing scheduled maintenance.

---
EOF
```

### Registration Function

```bash
agent_register() {
    local agent_id="$1"
    local capabilities="$2"
    local task_description="$3"
    local bb_dir="${4:-$HOME/.claude/mnemonic/.blackboard}"

    mkdir -p "$bb_dir"

    local session_id="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat >> "${bb_dir}/session-notes.md" << EOF

---
**Session:** $session_id
**Time:** $timestamp
**Agent:** $agent_id
**Status:** active
**Capabilities:** [$capabilities]

## Agent Registration

$agent_id started.

### Task
$task_description

---
EOF
}

# Usage
agent_register "memory-curator" "conflict-detection, deduplication" "Scheduled maintenance"
```

---

## Status Update Pattern

Agents update status in `session-notes.md` during work.

### Status Entry

```bash
agent_update_status() {
    local agent_id="$1"
    local new_status="$2"
    local message="$3"
    local bb_dir="${4:-$HOME/.claude/mnemonic/.blackboard}"

    local session_id="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat >> "${bb_dir}/session-notes.md" << EOF

---
**Session:** $session_id
**Time:** $timestamp
**Agent:** $agent_id
**Status:** $new_status

## Status Update

$message

---
EOF
}

# Usage
agent_update_status "memory-curator" "idle" "Maintenance complete. Processed 50 memories."
```

---

## Task Handoff Pattern

Agents hand off tasks with context in `active-tasks.md`.

### Handoff Entry

```markdown
---
**Session:** abc123
**Time:** 2026-01-24T10:30:00Z
**Agent:** search-orchestrator
**Status:** handoff
**Target:** search-subcall-1

## Task Handoff

### Task
Execute search iteration 2 for query "authentication"

### Context
- Iteration 1 found 5 memories in decisions namespace
- Need to search patterns and security namespaces
- Looking for related terms: OAuth, JWT

### Instructions
1. Search patterns namespace for "authentication"
2. Search security namespace for "auth"
3. Return JSON findings for aggregation

### State
```json
{
  "query": "authentication",
  "iteration": 2,
  "previous_findings": 5,
  "namespaces_searched": ["decisions"],
  "namespaces_remaining": ["patterns", "security"]
}
```

---
```

### Handoff Function

```bash
agent_handoff() {
    local from_agent="$1"
    local to_agent="$2"
    local task="$3"
    local context="$4"
    local state_json="$5"
    local bb_dir="${6:-$HOME/.claude/mnemonic/.blackboard}"

    mkdir -p "$bb_dir"

    local session_id="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat >> "${bb_dir}/active-tasks.md" << EOF

---
**Session:** $session_id
**Time:** $timestamp
**Agent:** $from_agent
**Status:** handoff
**Target:** $to_agent

## Task Handoff

### Task
$task

### Context
$context

### State
\`\`\`json
$state_json
\`\`\`

---
EOF
}
```

---

## Shared State Pattern

Agents share state in `shared-context.md` for workflow coordination.

### Shared State Entry

```markdown
---
**Session:** abc123
**Time:** 2026-01-24T10:30:00Z
**Agent:** search-enhanced
**Status:** active

## Shared State: Search Workflow

### Workflow ID
search-auth-20260124

### Current State
```json
{
  "phase": "iteration",
  "iteration": 2,
  "total_findings": 7,
  "pending_subcalls": 1,
  "completed_subcalls": 2
}
```

### Findings Accumulated
- decisions/project: 3 memories
- patterns/project: 2 memories
- learnings/project: 2 memories

---
```

### State Functions

```bash
agent_write_shared_state() {
    local agent_id="$1"
    local workflow_id="$2"
    local state_json="$3"
    local notes="$4"
    local bb_dir="${5:-$HOME/.claude/mnemonic/.blackboard}"

    mkdir -p "$bb_dir"

    local session_id="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat >> "${bb_dir}/shared-context.md" << EOF

---
**Session:** $session_id
**Time:** $timestamp
**Agent:** $agent_id
**Status:** active

## Shared State: $workflow_id

### Current State
\`\`\`json
$state_json
\`\`\`

### Notes
$notes

---
EOF
}

agent_read_latest_state() {
    local workflow_id="$1"
    local bb_dir="${2:-$HOME/.claude/mnemonic/.blackboard}"

    # Find most recent entry for this workflow
    tac "${bb_dir}/shared-context.md" 2>/dev/null | \
        awk "/^## Shared State: $workflow_id$/,/^---$/" | \
        tac | head -50
}
```

---

## Progress Reporting Pattern

Subcall agents report progress for monitoring.

### Progress Entry (to session-notes.md)

```markdown
---
**Session:** abc123
**Time:** 2026-01-24T10:31:00Z
**Agent:** search-subcall-1
**Status:** active

## Progress Report

### Workflow
search-auth-20260124

### Progress
- Searching namespace: procedural/patterns
- Files processed: 15/23
- Matches found: 2

---
```

### Progress Function

```bash
agent_report_progress() {
    local agent_id="$1"
    local workflow_id="$2"
    local progress_message="$3"
    local bb_dir="${4:-$HOME/.claude/mnemonic/.blackboard}"

    local session_id="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat >> "${bb_dir}/session-notes.md" << EOF

---
**Session:** $session_id
**Time:** $timestamp
**Agent:** $agent_id
**Status:** active

## Progress Report

### Workflow
$workflow_id

### Progress
$progress_message

---
EOF
}
```

---

## Reading Agent Entries

### Find Active Agents

```bash
# Find all currently active agents
grep -B5 "Status: active" ~/.claude/mnemonic/.blackboard/session-notes.md | \
    grep "Agent:" | \
    sed 's/.*Agent: //' | \
    sort -u
```

### Find Agent's Last Status

```bash
# Find last status for specific agent
tac ~/.claude/mnemonic/.blackboard/session-notes.md | \
    grep -A10 "Agent: memory-curator" | \
    head -15
```

### Find Pending Handoffs

```bash
# Find tasks waiting for handoff
grep -A20 "Status: handoff" ~/.claude/mnemonic/.blackboard/active-tasks.md | \
    grep -A15 "Target:"
```

### Find Workflow State

```bash
# Get current state of a workflow
WORKFLOW_ID="search-auth-20260124"
tac ~/.claude/mnemonic/.blackboard/shared-context.md | \
    awk "/^## Shared State: $WORKFLOW_ID$/,/^---$/" | \
    tac
```

---

## Cleanup

### Archive Old Agent Entries

Agent entries should be cleaned up periodically:

```bash
# Archive entries older than 7 days
ARCHIVE_DIR="$HOME/.claude/mnemonic/.blackboard/.archive"
mkdir -p "$ARCHIVE_DIR"

for topic in session-notes active-tasks shared-context; do
    if [ -f "$HOME/.claude/mnemonic/.blackboard/${topic}.md" ]; then
        # Keep last 100 entries, archive rest
        tail -500 "$HOME/.claude/mnemonic/.blackboard/${topic}.md" > \
            "$HOME/.claude/mnemonic/.blackboard/${topic}.md.tmp"
        mv "$HOME/.claude/mnemonic/.blackboard/${topic}.md.tmp" \
           "$HOME/.claude/mnemonic/.blackboard/${topic}.md"
    fi
done
```

---

## Best Practices

1. **Always register**: Agents should register on startup
2. **Update on completion**: Set status to `idle` when done
3. **Include context**: Handoffs should have enough context for receiver
4. **Use workflow IDs**: Enable tracking across multiple entries
5. **Clean up**: Archive old entries to prevent file growth
6. **Minimal writes**: Only write when state changes meaningfully

---

## Example: Search Workflow Coordination

```
1. search-enhanced (orchestrator) starts
   → Registers in session-notes.md with status: active

2. Orchestrator creates workflow state
   → Writes initial state to shared-context.md

3. Orchestrator hands off to search-subcall-1
   → Writes handoff to active-tasks.md with query, iteration, context

4. search-subcall-1 starts
   → Registers in session-notes.md
   → Reports progress periodically
   → Updates shared state with findings
   → Sets status to idle when done

5. Orchestrator reads shared state
   → Aggregates findings
   → Decides on next iteration or synthesis
   → Hands off to next subcall or completes

6. Orchestrator completes
   → Writes final state to shared-context.md
   → Sets status to idle
```

---

## Related

- `mnemonic-blackboard` skill - Base blackboard patterns
- `mnemonic-search-enhanced` skill - Uses coordination for search workflow
- `memory-curator` agent - Uses coordination for maintenance
- ADR-003 - Agent Coordination via Blackboard Extension
