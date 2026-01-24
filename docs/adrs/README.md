# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Mnemonic project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences.

## ADR Format

We use the **Structured MADR** format with YAML frontmatter:

```yaml
---
title: "Decision Title"
description: "Brief description"
type: adr
category: architecture|api|format|storage|integration
tags: [tag1, tag2]
status: proposed|accepted|deprecated|superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: Author Name
project: mnemonic
---

# ADR-NNN: Title

## Status
## Context
## Decision Drivers
## Considered Options
## Decision
## Consequences
## Decision Outcome
## Related Decisions
## Links
## More Information
## Audit
```

## Index

| ADR | Title | Status | Category |
|-----|-------|--------|----------|
| [ADR-001](adr-001-filesystem-based-storage.md) | Filesystem-based Storage | Accepted | architecture |
| [ADR-002](adr-002-mif-level-3-format.md) | MIF Level 3 Format | Accepted | architecture |
| [ADR-003](adr-003-agent-coordination-blackboard.md) | Agent Coordination via Blackboard Extension | Accepted | architecture |
| [ADR-004](adr-004-mif-schema-validation.md) | MIF Schema as Single Source of Truth for Validation | Accepted | architecture |
| [ADR-005](adr-005-memory-compression-gc.md) | Memory Compression via GC Extension | Accepted | architecture |
| [ADR-006](adr-006-validation-as-memory.md) | Validation Results as Episodic Memories | Accepted | architecture |
| [ADR-007](adr-007-enhanced-search-agents.md) | Enhanced Search with Agent-Driven Iteration | Accepted | architecture |

## Status Legend

- **Proposed** - Under consideration
- **Accepted** - Approved and in effect
- **Deprecated** - No longer recommended
- **Superseded** - Replaced by another ADR

## Creating a New ADR

Use the `/adr-new` command or:

1. Copy an existing ADR as template
2. Number sequentially (ADR-003, ADR-004, etc.)
3. Use format: `adr-NNN-slug.md`
4. Fill all Structured MADR sections
5. Include audit section for compliance
6. Update this index
