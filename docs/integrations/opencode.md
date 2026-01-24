# OpenCode Integration

Integrate Mnemonic with OpenCode using the Skills system.

## Overview

OpenCode supports skills that can be invoked during coding sessions. The mnemonic skill provides memory capture and recall functionality.

## Setup

### Project-Level Skill

Create `.opencode/skills/mnemonic/SKILL.md`:

```bash
mkdir -p .opencode/skills/mnemonic
cp /path/to/mnemonic/templates/codex-skill/SKILL.md .opencode/skills/mnemonic/
```

### Global Skill

Create `~/.config/opencode/skills/mnemonic/SKILL.md`:

```bash
mkdir -p ~/.config/opencode/skills/mnemonic
cp /path/to/mnemonic/templates/codex-skill/SKILL.md ~/.config/opencode/skills/mnemonic/
```

## Skill Content

```yaml
---
name: mnemonic
description: Capture and recall memories using the MIF Level 3 filesystem memory system.
---

# Mnemonic Memory Skill

## Memory Locations
- Global: `~/.claude/mnemonic/{org}/{namespace}/`
- Project: `./.claude/mnemonic/{namespace}/`

## Commands

### Recall Memories
```bash
rg -i "<topic>" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Capture Memory
Write to `~/.claude/mnemonic/default/{namespace}/user/{uuid}-{slug}.memory.md`

## Capture Triggers
- "let's use X" → decisions/
- "learned that" → learnings/
- "the pattern is" → patterns/
- "blocked by" → blockers/
```

## Usage

Once installed, the skill is automatically available:

```
@mnemonic search authentication
@mnemonic capture "Decided to use OAuth 2.0"
```

## Verification

1. List available skills in OpenCode
2. Invoke `@mnemonic` to verify it's recognized
3. Test search and capture operations

## Compatibility

OpenCode also supports `.claude/skills/` paths, making it compatible with Claude Code skills. The same skill file works in both environments.

## Sources

- [OpenCode Agent Skills](https://opencode.ai/docs/skills)
- [GitHub - opencode-skills](https://github.com/malhashemi/opencode-skills)
