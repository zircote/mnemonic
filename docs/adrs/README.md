# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Mnemonic project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences.

## ADR Format

We use the MADR (Markdown Any Decision Records) format:

```markdown
# ADR-NNNN: Title

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-NNNN](adr-nnnn-title.md)

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](adr-0001-filesystem-based-storage.md) | Filesystem-based Storage | Accepted |
| [ADR-0002](adr-0002-mif-level-3-format.md) | MIF Level 3 Format | Accepted |

## Creating a New ADR

1. Copy the template above
2. Number sequentially (ADR-0003, ADR-0004, etc.)
3. Use lowercase with hyphens for filename
4. Update this index
