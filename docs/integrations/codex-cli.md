# OpenAI Codex CLI Integration

Integrate Mnemonic with OpenAI Codex CLI using AGENTS.md and Skills.

## Overview

Codex CLI supports two integration methods:
1. **AGENTS.md**: Global instructions for all sessions
2. **Skills**: Reusable commands invokable with `$mnemonic`

## Setup

### Method 1: AGENTS.md (Global Instructions)

Create `~/.codex/AGENTS.md`:

```bash
mkdir -p ~/.codex
cp /path/to/mnemonic/templates/AGENTS.md ~/.codex/
```

### Method 2: Mnemonic Skill

Create the skill directory and file:

```bash
mkdir -p ~/.codex/skills/mnemonic
cp /path/to/mnemonic/templates/codex-skill/SKILL.md ~/.codex/skills/mnemonic/
```

## Skill Usage

Once installed, invoke the skill:

```
$mnemonic search authentication
$mnemonic capture decision "Use JWT for auth"
```

## AGENTS.md Content

The AGENTS.md file instructs Codex to:

1. Search memories before implementing features
2. Capture decisions, learnings, and patterns
3. Use MIF Level 3 format for all memories

See [templates/AGENTS.md](../../templates/AGENTS.md) for the full template.

## Skill Content

The skill provides:

1. `search` - Find relevant memories
2. `capture` - Create new memories
3. `list` - View memories by namespace

See [templates/codex-skill/SKILL.md](../../templates/codex-skill/SKILL.md) for the full template.

## Verification

```bash
# Verify AGENTS.md is loaded
codex --show-agents

# List available skills
codex /skills

# Test skill invocation
$mnemonic search test
```

## Best Practices

1. Use both AGENTS.md and Skills for complete integration
2. Place project-specific agents in repository root
3. Use global agents for cross-project memory access

## Sources

- [Codex AGENTS.md Guide](https://developers.openai.com/codex/guides/agents-md)
- [Codex Skills Documentation](https://developers.openai.com/codex/skills/)
- [Create Skills](https://developers.openai.com/codex/skills/create-skill/)
