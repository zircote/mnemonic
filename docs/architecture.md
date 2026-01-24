# Mnemonic Architecture

## Overview

Mnemonic is a pure filesystem-based memory system for Claude Code. It provides persistent knowledge storage across sessions using markdown files with YAML frontmatter.

## Design Principles

1. **No External Dependencies**: All operations use standard Unix tools (git, rg, find) and Claude's native capabilities
2. **Skill-First Architecture**: Skills are self-contained and work without hooks or libraries
3. **MIF Level 3 Compliance**: Standardized Memory Interchange Format for interoperability
4. **Filesystem as Database**: Markdown files are the source of truth

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code CLI                        │
├─────────────────────────────────────────────────────────────┤
│  Plugin Layer                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │Commands │  │ Skills  │  │ Agents  │  │  Hooks  │         │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                         │                                   │
├─────────────────────────┼───────────────────────────────────┤
│  Storage Layer          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Filesystem (.memory.md files)           │   │
│  │  ┌─────────────────┐    ┌─────────────────────────┐  │   │
│  │  │  User-Level     │    │  Project-Level          │  │   │
│  │  │  ~/.claude/     │    │  ./.claude/mnemonic/    │  │   │
│  │  │  mnemonic/{org}/│    │                         │  │   │
│  │  └─────────────────┘    └─────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │                    Git Repository                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Commands

Simple slash commands for direct user interaction:

| Command | Purpose |
|---------|---------|
| `/mnemonic:setup` | Initialize and configure mnemonic |
| `/mnemonic:capture` | Create a new memory |
| `/mnemonic:recall` | Retrieve memories |
| `/mnemonic:search` | Full-text search |
| `/mnemonic:status` | System status |
| `/mnemonic:gc` | Garbage collection |
| `/mnemonic:init` | Initialize directories |

### Skills

Self-contained instruction sets that work without external dependencies:

- **mnemonic-core**: Complete memory operations
- **mnemonic-setup**: CLAUDE.md configuration
- **mnemonic-search**: Advanced search patterns
- **mnemonic-format**: MIF Level 3 templates
- **mnemonic-organization**: Namespace management
- **mnemonic-blackboard**: Cross-session coordination

### Hooks

Event-driven automation for proactive behavior:

```
SessionStart ──────► Load relevant memories
                     Check blackboard for pending items

UserPromptSubmit ──► Analyze prompt for recall keywords
                     Detect capture opportunities

PostToolUse ───────► Capture learnings from tool results
                     Update memory access timestamps

Stop ──────────────► Commit pending changes
                     Update blackboard
                     Summarize session
```

### Agents

Autonomous background operations:

- **memory-curator**: Conflict detection, deduplication, decay management

## Memory Model

### MIF Level 3 Format

```yaml
---
id: UUID
type: semantic|episodic|procedural
namespace: category/scope
created: ISO-8601
modified: ISO-8601
title: "Human readable title"
tags: [list, of, tags]
temporal:
  valid_from: ISO-8601
  recorded_at: ISO-8601
  decay:
    model: exponential
    half_life: P7D
    strength: 0.0-1.0
provenance:
  source_type: conversation|user_explicit|inferred
  agent: model-identifier
  confidence: 0.0-1.0
---

# Markdown Content

Body of the memory...
```

### Memory Types

| Type | Description | Decay Rate |
|------|-------------|------------|
| **semantic** | Facts, concepts, specifications | Slow (P30D) |
| **episodic** | Events, experiences, incidents | Fast (P7D) |
| **procedural** | Processes, workflows, how-tos | Medium (P14D) |

### Namespace Hierarchy

```
{root}/
├── apis/           # API documentation
├── blockers/       # Issues, impediments
├── context/        # Background information
├── decisions/      # Architectural choices
├── learnings/      # Insights, discoveries
├── patterns/       # Code conventions
├── security/       # Security policies
├── testing/        # Test strategies
├── episodic/       # General events
└── .blackboard/    # Cross-session coordination
```

## Data Flow

### Capture Flow

```
User/Claude identifies capturable content
           │
           ▼
    ┌──────────────┐
    │ Generate UUID │
    │ Set timestamps│
    │ Classify type │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Write .memory│
    │ .md file     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Git add +    │
    │ commit       │
    └──────────────┘
```

### Recall Flow

```
User query or topic detection
           │
           ▼
    ┌──────────────┐
    │ ripgrep      │
    │ search       │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Parse matches│
    │ Extract meta │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Rank by      │
    │ relevance    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Update access│
    │ timestamps   │
    └──────────────┘
```

## Cross-Session Coordination

The blackboard provides a shared space for session handoffs:

```
Session A                    Session B
    │                            │
    ├── Write to blackboard ─────┤
    │   (active-tasks.md)        │
    │                            │
    └── Stop hook commits ───────┼── SessionStart reads
                                 │   blackboard
                                 │
                                 └── Continues work
```

## Git Integration

All memories are version-controlled:

- **Atomic commits**: Each capture creates a commit
- **History tracking**: Full audit trail of changes
- **Branching**: Support for experimental memories
- **Conflict resolution**: Git merge for concurrent sessions

## Performance Considerations

- **Search**: ripgrep provides fast full-text search
- **Indexing**: Filesystem is the index (no separate DB)
- **Caching**: Recent memories cached in context
- **Decay**: Exponential decay reduces noise over time
