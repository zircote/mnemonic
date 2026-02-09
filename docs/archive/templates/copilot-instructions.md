# Project Coding Instructions

## Mnemonic Memory System

This project uses Mnemonic for persistent memory across coding sessions.

### Before Implementing Features

Always search for existing memories:

```bash
# Search by topic
rg -i "<topic>" ${MNEMONIC_ROOT}/ --glob "*.memory.md"

# Check patterns
rg -i "pattern" ${MNEMONIC_ROOT}/*/patterns/

# Check decisions
rg -i "<topic>" ${MNEMONIC_ROOT}/*/decisions/
```

### Memory Capture Requirements

When making decisions or learning something new, create a memory file:

- **Location**: `${MNEMONIC_ROOT}/default/{namespace}/user/`
- **Format**: `.memory.md` with YAML frontmatter
- **Namespaces**: decisions, learnings, patterns, blockers, context

### When to Capture

| Trigger | Namespace |
|---------|-----------|
| Decision made ("let's use X") | decisions/ |
| Lesson learned ("turns out...") | learnings/ |
| Pattern established | patterns/ |
| Blocker encountered | blockers/ |
| Context to remember | context/ |

### Memory File Format

```yaml
---
id: <uuid>
type: semantic|episodic|procedural
namespace: decisions/user
created: <ISO8601>
modified: <ISO8601>
title: "Descriptive title"
tags:
  - tag1
  - tag2
temporal:
  valid_from: <ISO8601>
  recorded_at: <ISO8601>
provenance:
  source_type: conversation
  agent: github-copilot
  confidence: 0.9
---

# Title

Content here in markdown format...

## Context

Why this decision was made or what was learned.

## Details

Specific implementation details or notes.
```

### Memory Types

- **semantic**: Facts, decisions, specifications - things that ARE true
- **episodic**: Events, debug sessions, incidents - things that HAPPENED
- **procedural**: Workflows, patterns, how-tos - things you DO

### Integration Notes

- Search memories before making architectural decisions
- Capture decisions immediately when made
- Reference existing patterns when implementing new features
- Update memories when information changes (increment version)
