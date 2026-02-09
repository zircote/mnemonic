# Aider Integration

Integrate Mnemonic with Aider using CONVENTIONS.md.

## Overview

Aider supports a CONVENTIONS.md file that provides project-specific instructions. This integration configures Aider to use Mnemonic for persistent memory.

## Setup

### Create CONVENTIONS.md

Create `CONVENTIONS.md` in your project root:

```bash
cp /path/to/mnemonic/templates/CONVENTIONS.md ./CONVENTIONS.md
```

### Configure Auto-Loading

Add to `.aider.conf.yml`:

```yaml
read: CONVENTIONS.md
```

Or pass explicitly:

```bash
aider --read CONVENTIONS.md
```

## CONVENTIONS.md Content

```markdown
# Mnemonic Memory Integration

## Memory System
This project uses Mnemonic for persistent memories at `${MNEMONIC_ROOT}/`.

## Before Implementing
Always search for relevant memories:
```bash
rg -i "<topic>" ${MNEMONIC_ROOT}/ --glob "*.memory.md"
```

## Capture Requirements

### When to Capture
- Decision made: Save to `decisions/user/`
- Lesson learned: Save to `learnings/user/`
- Pattern established: Save to `patterns/user/`
- Blocker found: Save to `blockers/user/`

### Memory Format (MIF Level 3)
Files must have `.memory.md` extension with YAML frontmatter:

```yaml
---
id: <uuid>
type: semantic|episodic|procedural
namespace: {namespace}/user
created: <ISO8601>
title: "Descriptive title"
tags: [tag1, tag2]
---

# Title

Content...
```
```

## Usage

### Start Aider with Conventions

```bash
aider --read CONVENTIONS.md
```

### Commands During Session

```
/read CONVENTIONS.md  # Re-read conventions
/add file.md          # Add files to context
```

### Memory Operations

Ask Aider naturally:
- "What decisions have been made about the API?"
- "Remember that we're using TypeScript strict mode"
- "Search for patterns related to error handling"

## Best Practices

1. Keep CONVENTIONS.md in version control
2. Update conventions as project evolves
3. Use `.aider.conf.yml` for consistent loading
4. Combine with `.aider.watch` for auto-context

## Verification

```bash
# Start aider with conventions
aider --read CONVENTIONS.md

# Ask about memories
> What do we know about this project?

# Create a memory
> Remember that we decided to use PostgreSQL
```

## Sources

- [Aider CONVENTIONS.md](https://aider.chat/docs/usage/conventions.html)
- [Aider Configuration](https://aider.chat/docs/config.html)
