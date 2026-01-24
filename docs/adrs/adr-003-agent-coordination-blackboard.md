---
title: "Agent Coordination via Blackboard Extension"
description: "Extend existing blackboard files with agent entries for multi-agent coordination"
type: adr
category: architecture
tags:
  - agents
  - coordination
  - blackboard
  - multi-agent
status: accepted
created: 2026-01-24
updated: 2026-01-24
author: zircote
project: mnemonic
technologies:
  - markdown
  - bash
audience:
  - developers
  - architects
related:
  - adr-001-filesystem-based-storage.md
  - adr-002-mif-level-3-format.md
---

# ADR-003: Agent Coordination via Blackboard Extension

## Status

Accepted

## Context

### Background and Problem Statement

As the mnemonic system grows to include multiple agents (memory-curator, mnemonic-search-subcall, future agents), these agents need to coordinate their work across sessions. Without coordination, agents may duplicate work, conflict on resources, or lose context during handoffs.

### Current Limitations

- No mechanism for agents to register their presence
- No way to track agent status (active, idle, handoff)
- Task handoffs between agents lose context
- No shared state for workflow coordination

## Decision Drivers

### Primary Decision Drivers

1. **Pattern Consistency**: Must align with existing blackboard patterns
2. **Simplicity**: Must not require new infrastructure or formats
3. **Traceability**: Must track which agent did what and when
4. **Handoff Support**: Must enable seamless context transfer between agents

### Secondary Decision Drivers

1. **Minimal Changes**: Prefer extending existing files over creating new ones
2. **Backward Compatible**: Must not break existing blackboard usage
3. **Human Readable**: Developers should understand agent coordination logs

## Considered Options

### Option 1: New Agent Directory Structure

**Description**: Create a dedicated `.blackboard/agents/` subdirectory with per-agent files.

**Technical Characteristics**:
- `~/.claude/mnemonic/.blackboard/agents/{agent-id}.md` per agent
- Separate registry file for active agents
- Custom message format for agent communication

**Advantages**:
- Clean separation of agent data
- Easy to find agent-specific information
- Can scale to many agents

**Disadvantages**:
- New directory structure to maintain
- New format to learn and document
- Diverges from existing blackboard patterns
- More files to manage

**Risk Assessment**:
- **Complexity Risk**: High. New patterns to maintain.
- **Adoption Risk**: Medium. Different from existing patterns.
- **Maintenance Risk**: High. More files to track.

### Option 2: Extend Existing Blackboard Files (Selected)

**Description**: Add agent-specific entries to existing blackboard topic files using extended entry format.

**Technical Characteristics**:
- Agent entries appended to session-notes.md, active-tasks.md
- Extended entry format with Agent, Status, Capabilities fields
- Same append-only pattern as existing entries

**Advantages**:
- Consistent with existing blackboard patterns
- No new directories or files
- Single source for session/task information
- Easy to grep for agent activity

**Disadvantages**:
- Files may grow larger with agent entries
- Mixed content (human and agent entries)

**Risk Assessment**:
- **Complexity Risk**: Low. Extends existing pattern.
- **Adoption Risk**: Low. Follows familiar patterns.
- **Maintenance Risk**: Low. Same cleanup as existing.

### Option 3: External Coordination Service

**Description**: Use Redis/SQLite for agent coordination.

**Technical Characteristics**:
- External service for state management
- Real-time updates
- Structured queries

**Advantages**:
- Scalable coordination
- Real-time awareness
- Structured queries

**Disadvantages**:
- Adds external dependency (violates ADR-001)
- More complex setup
- Overkill for current needs

**Risk Assessment**:
- **Dependency Risk**: High. Violates pure-filesystem principle.
- **Complexity Risk**: High. Significant infrastructure.

## Decision

We will extend existing blackboard files with agent-specific entry fields rather than creating new directory structures.

### Extended Entry Format

Agent entries use the same append-only pattern with additional fields:

```markdown
---
**Session:** {session_id}
**Time:** {timestamp}
**Agent:** {agent_id}
**Status:** active|idle|handoff
**Capabilities:** [list of capabilities]

## Entry Content

Description of what this agent is doing or handing off...

### Context (for handoffs)
- Key context point 1
- Key context point 2

### Next Steps (for handoffs)
- [ ] Action item 1
- [ ] Action item 2

---
```

### Usage Patterns

1. **Agent Registration** (append to session-notes.md)
2. **Status Updates** (append to session-notes.md)
3. **Task Handoffs** (append to active-tasks.md with context)
4. **Shared State** (append to shared-context.md)

## Consequences

### Positive

1. **Consistency**: Same patterns as existing blackboard usage
2. **Simple**: No new infrastructure needed
3. **Traceable**: All agent activity visible in standard files
4. **Searchable**: Standard grep/rg works for agent entries

### Negative

1. **File Growth**: Blackboard files may grow larger
2. **Mixed Content**: Human and agent entries in same files

### Neutral

1. **Parsing**: Slightly more complex entry format

## Decision Outcome

Extending blackboard files achieves coordination without new infrastructure:
- Agents register in session-notes.md
- Task handoffs include context in active-tasks.md
- Shared workflow state in shared-context.md
- Standard blackboard cleanup applies

## Related Decisions

- [ADR-001: Filesystem-based Storage](adr-001-filesystem-based-storage.md) - No external dependencies
- [ADR-002: MIF Level 3 Format](adr-002-mif-level-3-format.md) - Memory format (separate from blackboard)

## Links

- [Blackboard Pattern](https://en.wikipedia.org/wiki/Blackboard_(design_pattern)) - Classic AI coordination pattern

## More Information

- **Date:** 2026-01-24
- **Source:** Multi-agent coordination requirements

## Audit

### 2026-01-24

**Status:** Pending implementation

**Findings:** N/A - New ADR

**Action Required:** Implement agent coordination skill
