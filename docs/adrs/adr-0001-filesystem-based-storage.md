---
title: "Filesystem-based Storage"
description: "Use filesystem with markdown files for persistent memory storage"
type: adr
category: architecture
tags:
  - storage
  - filesystem
  - git
  - markdown
status: accepted
created: 2026-01-24
updated: 2026-01-24
author: zircote
project: mnemonic
technologies:
  - filesystem
  - git
  - ripgrep
audience:
  - developers
  - architects
related: []
---

# ADR-0001: Filesystem-based Storage

## Status

Accepted

## Context

### Background and Problem Statement

Mnemonic needs a storage mechanism for persistent memories that AI coding assistants can read and write across sessions. The storage must support structured metadata, flexible content, and version control.

### Current Limitations

Without a defined storage mechanism:
- Memories are lost between sessions
- No way to share memories across projects
- No audit trail of memory changes
- Difficult to backup or migrate

## Decision Drivers

### Primary Decision Drivers

1. **Zero Dependencies**: Must not require external databases or services
2. **Human Readability**: Developers must be able to read and edit memories directly
3. **Version Control**: Full history and audit trail required
4. **Tool Compatibility**: Must work with standard Unix tools

### Secondary Decision Drivers

1. **Portability**: Easy to backup, restore, or migrate
2. **Simplicity**: Minimal learning curve for new users
3. **Debuggability**: Easy to inspect and troubleshoot

## Considered Options

### Option 1: SQLite Database

**Description**: Use SQLite as an embedded database for memory storage.

**Technical Characteristics**:
- ACID-compliant transactions
- Structured query language
- Single file database

**Advantages**:
- Complex queries and joins
- Transaction support
- Familiar SQL interface

**Disadvantages**:
- Binary format not human-readable
- Git diffs are meaningless
- Adds dependency on SQLite libraries
- Concurrent access can be problematic

**Risk Assessment**:
- **Technical Risk**: Low. SQLite is mature and well-tested.
- **Usability Risk**: High. Users cannot easily inspect memories.
- **Ecosystem Risk**: Low. Wide platform support.

### Option 2: JSON Files

**Description**: Store each memory as a JSON file.

**Technical Characteristics**:
- Standard data interchange format
- Native support in many languages
- Single-file per memory

**Advantages**:
- Machine-readable
- Easy to parse programmatically
- No schema required

**Disadvantages**:
- Poor for large text content
- No native support for multi-line strings
- Escaping issues with complex content
- Less human-readable than markdown

**Risk Assessment**:
- **Technical Risk**: Low. JSON is ubiquitous.
- **Usability Risk**: Medium. Readable but not writable by humans.
- **Content Risk**: High. Complex content requires escaping.

### Option 3: Markdown Files with YAML Frontmatter

**Description**: Use markdown files with YAML frontmatter for metadata.

**Technical Characteristics**:
- Human-readable and writable
- Structured metadata in YAML
- Flexible content in markdown body
- One file per memory

**Advantages**:
- Fully human-readable and editable
- Git-friendly with meaningful diffs
- Works with any text editor
- Standard Unix tools work out of the box
- No dependencies beyond filesystem

**Disadvantages**:
- No complex queries (SQL-style joins)
- Performance may degrade at scale
- No built-in transactions
- Requires manual or tool-based indexing

**Risk Assessment**:
- **Technical Risk**: Low. Filesystem operations are well-understood.
- **Performance Risk**: Medium. May need optimization at scale.
- **Usability Risk**: Low. Familiar format for developers.

### Option 4: External Service

**Description**: Use an external database or API service.

**Technical Characteristics**:
- Network-dependent
- Requires authentication
- Scalable infrastructure

**Advantages**:
- Scalable storage
- Advanced query capabilities
- Managed infrastructure

**Disadvantages**:
- Requires network connectivity
- Needs credentials management
- Privacy/security concerns
- Vendor lock-in potential
- Cost implications

**Risk Assessment**:
- **Technical Risk**: Medium. Network dependencies add failure modes.
- **Privacy Risk**: High. Data leaves local machine.
- **Cost Risk**: Medium. Ongoing service costs.

## Decision

We will use the filesystem with markdown files (`.memory.md`) containing YAML frontmatter.

The implementation will use:
- **File path structure**: `~/.claude/mnemonic/{org}/{namespace}/{scope}/{uuid}-{slug}.memory.md`
- **ripgrep** for fast full-text search
- **git** for version control and conflict resolution
- **YAML frontmatter** for structured metadata
- **Markdown body** for flexible content

Each memory is a standalone file that can be:
- Read with `cat`, `head`, or any text editor
- Searched with `grep`, `rg`, or `find`
- Versioned with `git`
- Edited manually if needed

## Consequences

### Positive

1. **Zero Dependencies**: Uses only filesystem and git, both universally available
2. **Human Readable**: Memories can be read and edited directly with any text editor
3. **Git Integration**: Full version history with meaningful diffs
4. **Tool Compatibility**: Works with any Unix tool (grep, find, sed, awk)
5. **Portability**: Easy to backup, restore, migrate, or share

### Negative

1. **No Complex Queries**: Cannot perform SQL-style joins or aggregations
2. **Scale Concerns**: Performance may degrade with thousands of files
3. **No Transactions**: Concurrent writes could conflict
4. **Manual Indexing**: No automatic full-text index

### Neutral

1. **Learning Curve**: Users need to understand the file structure
2. **Search Performance**: Depends on ripgrep availability

## Decision Outcome

Filesystem-based storage achieves our primary objectives:
- Zero external dependencies
- Full human readability
- Native git integration
- Standard tool compatibility

Mitigations for negative consequences:
- Use ripgrep for fast full-text search
- Organize by namespace to limit search scope
- Use git for conflict resolution
- Consider indexing layer if scale becomes an issue

## Related Decisions

- [ADR-0002: MIF Level 3 Format](adr-0002-mif-level-3-format.md) - Defines the file format used

## Links

- [ripgrep](https://github.com/BurntSushi/ripgrep) - Fast grep alternative
- [YAML](https://yaml.org/) - Frontmatter format

## More Information

- **Date:** 2026-01-24
- **Source:** Initial architecture design
- **Related ADRs:** ADR-0002

## Audit

### 2026-01-24

**Status:** Compliant

**Findings:**

| Finding | Files | Lines | Assessment |
|---------|-------|-------|------------|
| Memory files use .memory.md extension | `skills/mnemonic-core/SKILL.md` | L152-L176 | compliant |
| YAML frontmatter structure defined | `skills/mnemonic-format/SKILL.md` | L1-L50 | compliant |
| Git integration in capture workflow | `commands/capture.md` | L131-L138 | compliant |
| Namespace directory structure | `commands/setup.md` | L47-L58 | compliant |

**Summary:** Storage implementation follows ADR specifications.

**Action Required:** None
