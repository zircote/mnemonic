# Global Agent Instructions

## Mnemonic Memory System

You have access to a persistent memory system at `~/.claude/mnemonic/`. This system stores memories as `.memory.md` files with YAML frontmatter (MIF Level 3 format).

## Required Behavior

### Before Starting Any Task

Search for relevant memories:

```bash
# Search by topic
rg -i "<topic>" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Check specific namespaces
rg -i "<topic>" ~/.claude/mnemonic/*/decisions/ --glob "*.memory.md"
rg -i "<topic>" ~/.claude/mnemonic/*/patterns/ --glob "*.memory.md"
```

### Capture Requirements

Create memories immediately when:

| Trigger | Namespace | Type |
|---------|-----------|------|
| Decision made ("let's use X") | decisions/ | semantic |
| Lesson learned ("turns out...") | learnings/ | semantic |
| Pattern established | patterns/ | procedural |
| Blocker encountered | blockers/ | episodic |
| Context to remember | context/ | semantic |

### Memory Format

Use MIF Level 3 format with YAML frontmatter:

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
  agent: <agent-name>
  confidence: 0.9
---

# Title

Content here...
```

### Memory Types

- **semantic**: Facts, decisions, specifications - things that ARE true
- **episodic**: Events, debug sessions, incidents - things that HAPPENED
- **procedural**: Workflows, patterns, how-tos - things you DO

### Capture Script

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
tags: []
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: conversation
  agent: codex-cli
  confidence: 0.9
---

# ${TITLE}

Content...
EOF
```

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

## Do Not

- Skip searching before implementing
- Announce that you're capturing (just do it silently)
- Forget to capture decisions when made
- Create memories without proper frontmatter

## Memory Locations

- **Global**: `~/.claude/mnemonic/{org}/{namespace}/`
- **Project**: `./.claude/mnemonic/{namespace}/`

Use global for cross-project knowledge, project-local for project-specific context.
