# Continue Dev Integration

Integrate Mnemonic with Continue Dev using config.yaml rules and custom commands.

## Overview

Continue Dev supports system messages and custom commands. This integration adds mnemonic memory capabilities to your Continue configuration.

## Setup

### Edit Configuration

Add to `~/.continue/config.yaml`:

```yaml
models:
  - provider: anthropic
    name: claude-sonnet-4-20250514

chatOptions:
  baseSystemMessage: |
    You have access to a Mnemonic memory system at ~/.claude/mnemonic/.

    BEFORE implementing anything:
    - Search: rg -i "<topic>" ~/.claude/mnemonic/ --glob "*.memory.md"

    CAPTURE immediately when:
    - Decision made → decisions/user/
    - Lesson learned → learnings/user/
    - Pattern established → patterns/user/

    Memory format: .memory.md files with MIF Level 3 YAML frontmatter
    (id, type, namespace, created, title, tags)

customCommands:
  - name: mnemonic-search
    description: Search mnemonic memories
    prompt: |
      Search for memories related to: {{input}}
      Use: rg -i "{{input}}" ~/.claude/mnemonic/ --glob "*.memory.md"

  - name: mnemonic-capture
    description: Capture a new memory
    prompt: |
      Create a memory in ~/.claude/mnemonic/default/{{namespace}}/user/
      with MIF Level 3 format for: {{input}}

  - name: mnemonic-list
    description: List memories by namespace
    prompt: |
      List memories in namespace: {{input}}
      Use: ls ~/.claude/mnemonic/default/{{input}}/user/
```

## Custom Commands

### Search Memories

```
/mnemonic-search authentication
```

### Capture Memory

```
/mnemonic-capture decisions Use JWT for authentication
```

### List by Namespace

```
/mnemonic-list decisions
```

## Context Provider (Advanced)

Add a custom context provider for deeper integration:

```yaml
contextProviders:
  - name: mnemonic
    params:
      path: ~/.claude/mnemonic
      pattern: "*.memory.md"
```

## Usage

### In Chat

```
What memories exist about the database schema?
Remember that we decided to use PostgreSQL
Search for patterns related to API design
```

### With Commands

```
/mnemonic-search database
/mnemonic-capture patterns Always validate input at API boundaries
```

## Verification

1. Open Continue in your IDE
2. Run `/mnemonic-search test`
3. Verify the search command is executed
4. Create a test memory with `/mnemonic-capture`

## Best Practices

1. Use `baseSystemMessage` for always-on instructions
2. Create custom commands for frequent operations
3. Consider context providers for large memory sets

## Sources

- [Continue Dev Documentation](https://docs.continue.dev/)
- [Continue Configuration](https://docs.continue.dev/reference/config)
