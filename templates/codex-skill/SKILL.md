---
name: mnemonic
description: Capture and recall memories from the filesystem-based memory system at ~/.claude/mnemonic. Use for decisions, learnings, patterns, and blockers.
---

# Mnemonic Memory Skill

This skill provides access to the Mnemonic memory system for persistent context across coding sessions.

## Memory Locations

- **Global**: `~/.claude/mnemonic/{org}/{namespace}/`
- **Project**: `./.claude/mnemonic/{namespace}/`

## Commands

### Search Memories

```bash
# By topic
rg -i "<topic>" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# By namespace
ls ~/.claude/mnemonic/default/{decisions,learnings,patterns}/user/

# By tag (in frontmatter)
rg "tags:.*<tag>" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Recent memories
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7
```

### Capture Memory

Create a new memory file:

```bash
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
NAMESPACE="decisions"  # or: learnings, patterns, blockers, context
TITLE="Your descriptive title"
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | head -c 50)

cat > ~/.claude/mnemonic/default/${NAMESPACE}/user/${UUID}-${SLUG}.memory.md << EOF
---
id: ${UUID}
type: semantic
namespace: ${NAMESPACE}/user
created: ${DATE}
modified: ${DATE}
title: "${TITLE}"
tags:
  - tag1
  - tag2
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: conversation
  agent: codex-cli
  confidence: 0.9
---

# ${TITLE}

Content here...
EOF
```

### List Memories

```bash
# All memories
find ~/.claude/mnemonic -name "*.memory.md" | head -20

# By namespace
ls ~/.claude/mnemonic/default/decisions/user/
ls ~/.claude/mnemonic/default/learnings/user/
ls ~/.claude/mnemonic/default/patterns/user/
```

## Memory Types

| Type | Use For | Example |
|------|---------|---------|
| semantic | Facts, decisions, specs | "We use PostgreSQL" |
| episodic | Events, experiences | "Debug session on auth bug" |
| procedural | Workflows, patterns | "How to deploy to prod" |

## Namespaces

| Namespace | Purpose |
|-----------|---------|
| decisions/ | Architectural choices |
| learnings/ | Insights discovered |
| patterns/ | Code conventions |
| blockers/ | Issues encountered |
| context/ | General context |
| apis/ | API documentation |
| security/ | Security considerations |

## Capture Triggers

Automatically capture when:
- "let's use X" or "we'll go with X" → decisions/
- "I learned" or "turns out" → learnings/
- "the pattern is" or "convention" → patterns/
- "blocked by" or "issue with" → blockers/

## Best Practices

1. Search before implementing to check for existing decisions
2. Capture decisions immediately when made
3. Use descriptive titles for easy searching
4. Add relevant tags for categorization
5. Include context and reasoning in content
