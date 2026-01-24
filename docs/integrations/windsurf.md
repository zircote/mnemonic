# Windsurf (Codeium) Integration

Integrate Mnemonic with Windsurf's Cascade AI using Rules and Memories.

## Overview

Windsurf's Cascade has built-in memory capabilities. This integration configures it to use Mnemonic's filesystem-based memory format for portability across tools.

## Setup

### Configure Rules

1. Open Windsurf
2. Navigate to **Settings > Cascade > Rules**
3. Add the following rules:

```
When I ask you to remember something, create a memory file at:
~/.claude/mnemonic/default/{namespace}/user/

Use MIF Level 3 format with YAML frontmatter:
- id: UUID
- type: semantic|episodic|procedural
- namespace: {namespace}/user
- created: ISO8601 timestamp
- title: Descriptive title
- tags: array

Before implementing features, search for relevant memories:
rg -i "<topic>" ~/.claude/mnemonic/ --glob "*.memory.md"

Capture decisions to decisions/, learnings to learnings/, patterns to patterns/.
```

### Memory Namespace Mapping

Map Cascade's built-in memories to Mnemonic namespaces:

| Cascade Memory Type | Mnemonic Namespace |
|--------------------|--------------------|
| Preferences | context/ |
| Decisions | decisions/ |
| Learnings | learnings/ |
| Patterns | patterns/ |

## Usage

### Natural Language

```
"Remember that we're using PostgreSQL for the database"
"What do we know about authentication?"
"Capture this as a pattern: always use dependency injection"
```

### Explicit Commands

```
"Create a mnemonic memory about using REST over GraphQL"
"Search mnemonic for database decisions"
```

## Syncing with Built-in Memories

Windsurf Cascade generates memories automatically. To sync these with Mnemonic:

1. Export Cascade memories periodically
2. Convert to MIF Level 3 format
3. Store in appropriate Mnemonic namespace

## Verification

1. Create a test memory: "Remember that this is a test"
2. Check `~/.claude/mnemonic/default/context/user/` for the file
3. Ask Cascade: "What do you remember about tests?"

## Limitations

- UI-based configuration only
- No direct file system access in some modes
- Automatic memory sync requires manual intervention

## Sources

- [Windsurf Cascade Documentation](https://docs.windsurf.com/windsurf/cascade/cascade)
- [Codeium Documentation](https://codeium.com/documentation)
