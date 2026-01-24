# Cursor Integration

Integrate Mnemonic with Cursor using the Rules system.

## Overview

Cursor supports rules that apply to all AI interactions. The mnemonic rule configures Cursor to use the memory system.

## Setup

### Create Cursor Rule

Create `.cursor/rules/mnemonic.mdc`:

```bash
mkdir -p .cursor/rules
cp /path/to/mnemonic/templates/cursor-rule.mdc .cursor/rules/mnemonic.mdc
```

### Alternative: AGENTS.md

Cursor also supports `AGENTS.md` in the project root:

```bash
cp /path/to/mnemonic/templates/AGENTS.md ./AGENTS.md
```

## Rule Content

```markdown
---
description: "Mnemonic memory system for persistent context across sessions"
alwaysApply: true
---

# Mnemonic Memory System

## Memory Storage
All memories stored at `~/.claude/mnemonic/` as `.memory.md` files.

## Required Behavior

### Before Implementing
Search for relevant memories:
```bash
rg -i "<topic>" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Capture Triggers
- Decision made → Create in `decisions/user/`
- Lesson learned → Create in `learnings/user/`
- Pattern established → Create in `patterns/user/`
- Blocker encountered → Create in `blockers/user/`

## Memory Types
- **semantic**: Facts, decisions, specifications
- **episodic**: Events, debug sessions, incidents
- **procedural**: Workflows, patterns, how-tos
```

## Usage

Once the rule is in place:

1. **Recall**: Ask Cursor "What do we know about X?"
2. **Capture**: Tell Cursor "Remember that we decided Y"
3. **Reference**: Use `@mnemonic` in Cursor Chat

## Verification

1. Open a file in Cursor
2. Check Settings > Features > Rules for the mnemonic rule
3. Ask in Composer: "Search for memories about this project"

## Rule Options

| Option | Description |
|--------|-------------|
| `alwaysApply: true` | Apply to all interactions |
| `alwaysApply: false` | Only apply when explicitly referenced |
| `description` | Shown in rule list |

## Sources

- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)
