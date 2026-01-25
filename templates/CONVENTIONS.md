# Mnemonic Memory Integration

## Overview

This project uses Mnemonic for persistent memories across coding sessions. Mnemonic stores memories as `.memory.md` files with YAML frontmatter at `~/.claude/mnemonic/`.

## Before Implementing

Always search for relevant memories:

```bash
# Search by topic
rg -i "<topic>" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Check decisions
rg -i "<topic>" ~/.claude/mnemonic/*/decisions/ --glob "*.memory.md"

# Check patterns
rg -i "pattern" ~/.claude/mnemonic/*/patterns/ --glob "*.memory.md"
```

## Capture Requirements

### When to Capture

| Trigger | Namespace | Memory Type |
|---------|-----------|-------------|
| Decision made ("let's use X") | decisions/user/ | semantic |
| Lesson learned ("turns out...") | learnings/user/ | semantic |
| Pattern established | patterns/user/ | procedural |
| Blocker encountered | blockers/user/ | episodic |
| Context to remember | context/user/ | semantic |

### Memory File Location

```
~/.claude/mnemonic/default/{namespace}/user/{uuid}-{slug}.memory.md
```

### Memory Format (MIF Level 3)

All memory files must have `.memory.md` extension with YAML frontmatter:

```yaml
---
id: <uuid>
type: semantic|episodic|procedural
namespace: {namespace}/user
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
  agent: aider
  confidence: 0.9
---

# Title

Content in markdown format...

## Context

Why this decision was made or what was learned.

## Details

Specific implementation details or notes.
```

## Memory Types

Choose the correct type for each memory:

- **semantic**: Facts, decisions, specifications - things that ARE true
  - Example: "We use PostgreSQL for the main database"
  - Example: "API endpoints follow REST conventions"

- **episodic**: Events, debug sessions, incidents - things that HAPPENED
  - Example: "Fixed authentication bug by updating token validation"
  - Example: "Deployed v2.0 to production on 2024-01-15"

- **procedural**: Workflows, patterns, how-tos - things you DO
  - Example: "To deploy: run tests, build, push to registry, apply k8s"
  - Example: "Error handling pattern: wrap in try-catch, log, return Result"

## Namespaces

| Namespace | Purpose |
|-----------|---------|
| decisions/ | Architectural and design decisions |
| learnings/ | Insights and discoveries |
| patterns/ | Code conventions and patterns |
| blockers/ | Issues and impediments |
| context/ | General project context |
| apis/ | API documentation and contracts |
| security/ | Security considerations |

## Best Practices

1. **Search first**: Always check existing memories before implementing
2. **Capture immediately**: Don't wait - capture decisions when they're made
3. **Be descriptive**: Use clear titles that are easy to search
4. **Add context**: Include reasoning and background in the content
5. **Use tags**: Add relevant tags for categorization
6. **Update, don't duplicate**: If a memory exists, update it rather than creating a new one

## Integration

This conventions file is designed for use with Aider. Load it with:

```bash
aider --read CONVENTIONS.md
```

Or configure in `.aider.conf.yml`:

```yaml
read: CONVENTIONS.md
```
