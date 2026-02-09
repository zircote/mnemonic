# Mnemonic vs Memory Bank: Comparison

Side-by-side comparison of mnemonic with typical Memory Bank setups.

---

## Overview

Memory Bank is a community pattern—markdown files used to give AI coding assistants persistent memory. Mnemonic formalizes this approach with standards, validation, and multi-tool support.

**Key insight**: Memory Bank proved filesystem-based memory works. Mnemonic adds structure without losing simplicity.

---

## Feature Comparison

| Feature | Memory Bank | Mnemonic |
|---------|-------------|----------|
| **Storage** | Markdown files | Markdown files |
| **Format** | Ad-hoc | MIF Level 3 standard |
| **Validation** | None | Schema validation tool |
| **Memory types** | Implicit | semantic/episodic/procedural |
| **Decay model** | None | Exponential decay |
| **Cross-tool** | Manual per tool | 9+ tools supported |
| **Research backing** | Community intuition | 74% benchmark accuracy |
| **Version control** | Optional | Git-native |
| **Metadata** | Varies | Structured YAML |
| **Provenance** | None | Full tracking |
| **Bi-temporal** | No | Yes (valid_from/recorded_at) |

---

## Format Comparison

### Memory Bank (Typical)

```markdown
# Project Memory Bank

## Context
We're building a REST API with Node.js.

## Decisions
- Use PostgreSQL for storage
- JWT for authentication
- Rate limiting at API gateway

## Patterns
- All errors return JSON with `error` key
- Use snake_case for API fields

## Recent Sessions
### 2025-01-15
Fixed the N+1 query bug in user dashboard.
```

### Mnemonic (MIF Level 3)

**Decision memory** (`decisions/user/abc123-use-postgresql.memory.md`):
```yaml
---
id: abc12345-1234-1234-1234-123456789abc
type: semantic
namespace: decisions/user
created: 2026-01-15T10:30:00Z
modified: 2026-01-15T10:30:00Z
title: "Use PostgreSQL for Storage"
tags:
  - database
  - architecture
temporal:
  valid_from: 2026-01-15T10:30:00Z
  recorded_at: 2026-01-15T10:30:00Z
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: 0.95
---

# Use PostgreSQL for Storage

We decided to use PostgreSQL because:
- Strong ACID compliance for transaction integrity
- Excellent JSON support for flexible schemas
- Mature ecosystem with great tooling

## Alternatives Considered
- MongoDB: Rejected due to consistency requirements
- MySQL: Less rich JSON support
```

**Episodic memory** (`episodic/user/def456-n1-query-fix.memory.md`):
```yaml
---
id: def45678-5678-5678-5678-567890123def
type: episodic
namespace: episodic/user
created: 2026-01-15T14:00:00Z
title: "Fixed N+1 Query in User Dashboard"
tags:
  - debugging
  - performance
temporal:
  valid_from: 2026-01-15T14:00:00Z
  recorded_at: 2026-01-15T16:00:00Z
  decay:
    model: exponential
    half_life: P7D
provenance:
  source_type: observation
  agent: claude-opus-4
  confidence: 0.9
---

# Fixed N+1 Query in User Dashboard

## Problem
Dashboard taking 5+ seconds to load.

## Investigation
Found N+1 pattern in UserDashboard component.
Each user row triggered separate query for posts.

## Solution
Added `.includes(:posts, :comments)` to ActiveRecord query.

## Result
Load time: 5s → 200ms
```

---

## Structural Comparison

### Memory Bank Organization

```
~/memory-bank/
├── memory-bank.md        # Everything in one file
├── decisions.md          # Or split by topic
├── patterns.md
└── sessions/
    ├── 2025-01-15.md
    └── 2025-01-16.md
```

### Mnemonic Organization

```
${MNEMONIC_ROOT}/
├── default/                    # Organization
│   ├── decisions/
│   │   ├── user/               # Personal decisions
│   │   ├── project/            # Project-level
│   │   └── shared/             # Team-shared
│   ├── learnings/user/
│   ├── patterns/user/
│   ├── blockers/user/
│   ├── context/user/
│   ├── apis/user/
│   ├── security/user/
│   ├── testing/user/
│   └── episodic/user/
└── .blackboard/                # Session coordination
    ├── active-tasks.md
    ├── session-notes.md
    └── shared-context.md
```

---

## Capability Comparison

### Search

**Memory Bank**:
```bash
# Basic grep
grep -r "authentication" ~/memory-bank/
```

**Mnemonic**:
```bash
# Structured search
/mnemonic:search "authentication"

# Namespace-specific
rg -i "authentication" ${MNEMONIC_ROOT}/*/decisions/

# By memory type
rg "^type: episodic" ${MNEMONIC_ROOT}/ -l
```

### Capture

**Memory Bank**:
```bash
# Manual edit
vim ~/memory-bank/memory-bank.md
# Add to appropriate section
```

**Mnemonic**:
```bash
# Typed capture
/mnemonic:capture decisions "Use JWT for auth"
/mnemonic:capture learnings "PostgreSQL JSONB indexing"
/mnemonic:capture patterns "Error handling convention"
```

### Validation

**Memory Bank**:
- No validation
- Format drift over time
- No schema enforcement

**Mnemonic**:
```bash
# Full validation
./tools/mnemonic-validate

# CI integration
./tools/mnemonic-validate --format json | jq '.summary'

# Pre-commit hook
./tools/mnemonic-validate --changed --fast-fail
```

### Multi-Tool Support

**Memory Bank**:
- Each tool needs manual configuration
- Different formats per tool
- No portability

**Mnemonic**:
- 9+ tools supported natively
- Single format, multiple exports
- Switch tools without losing memory

| Tool | Memory Bank Setup | Mnemonic Setup |
|------|------------------|----------------|
| Cursor | Custom .cursor/rules | Native + export |
| Windsurf | Custom .windsurfrules | Native + export |
| Copilot | Custom instructions | Native + export |
| Aider | CONVENTIONS.md | Native + export |
| Continue | config.yaml | Native + export |

---

## Memory Types

### Memory Bank Approach

Typically implicit or section-based:
```markdown
## Decisions     <- Type implied by header
## Learnings     <- Type implied by header
## Sessions      <- Type implied by header
```

### Mnemonic Approach

Explicit typing with cognitive science foundation:

| Type | Use Case | Decay Rate | Example |
|------|----------|------------|---------|
| `semantic` | Facts, decisions, specs | Slow (30d) | "We use PostgreSQL" |
| `episodic` | Events, sessions, incidents | Fast (7d) | "Fixed bug on Jan 15" |
| `procedural` | Patterns, workflows | Medium (14d) | "Deploy via GitHub Actions" |

---

## Decay Model

### Memory Bank

No decay—all memories treated equally regardless of age or relevance.

### Mnemonic

Exponential decay based on memory type:

```yaml
temporal:
  decay:
    model: exponential
    half_life: P7D      # Episodic: halves every 7 days
    strength: 0.85      # Current relevance (0.0-1.0)
```

**Benefits**:
- Recent memories prioritized
- Old memories naturally fade
- Important memories can override decay
- Automatic relevance ranking

---

## Provenance Tracking

### Memory Bank

No tracking—unknown origin for memories.

### Mnemonic

Full provenance for every memory:

```yaml
provenance:
  source_type: conversation    # How it was captured
  agent: claude-opus-4         # Which AI created it
  confidence: 0.95             # How confident
  references:                  # Supporting evidence
    - type: documentation
      url: https://docs.example.com
```

**Benefits**:
- Audit trail for compliance
- Confidence-weighted retrieval
- Source verification
- Citation support

---

## Bi-Temporal Tracking

### Memory Bank

Single timestamp (if any).

### Mnemonic

Two time dimensions per SQL:2011 standard:

```yaml
temporal:
  valid_from: 2026-01-10T00:00:00Z    # When this became true
  recorded_at: 2026-01-15T10:30:00Z  # When we recorded it
```

**Use cases**:
- "When was this decision made?" (valid_from)
- "When did we learn this?" (recorded_at)
- Backfilling historical decisions
- Compliance auditing

---

## Research Validation

### Memory Bank

Community intuition—no formal benchmarks.

### Mnemonic

Research-validated approach:

| Benchmark | Filesystem (Mnemonic) | Graph-Based (Mem0) |
|-----------|----------------------|-------------------|
| LoCoMo Accuracy | **74.0%** | 68.5% |

**Academic foundation**:
- Unix philosophy (arXiv:2601.11672)
- Cognitive memory types (arXiv:2411.00489)
- Bi-temporal theory (SQL:2011)

---

## Migration Path

Memory Bank → Mnemonic is additive, not replacement:

1. **Keep existing files** - No need to delete
2. **Install mnemonic** - Adds structure on top
3. **Migrate incrementally** - Convert as you use
4. **Validate** - Ensure format compliance

See [Migration Guide](./migration-from-memory-bank.md) for details.

---

## When to Use Each

### Stick with Memory Bank if:

- Simple, single-project setup
- No need for cross-tool support
- Minimal compliance requirements
- Prefer complete flexibility

### Move to Mnemonic if:

- Multiple AI tools in your workflow
- Team collaboration needed
- Compliance or audit requirements
- Want research-backed approach
- Value validation and structure

---

## Summary

| Aspect | Memory Bank | Mnemonic |
|--------|-------------|----------|
| Philosophy | DIY flexibility | Structured standards |
| Learning curve | Lower | Slightly higher |
| Validation | None | Built-in |
| Multi-tool | Manual | Native |
| Research backing | Community | Academic |
| Best for | Simple setups | Professional use |

**Bottom line**: Mnemonic validates what Memory Bank proved while adding the structure needed for professional and team use.

---

## Related Documentation

- [Quick Start](./quickstart-memory-bank.md) - 5-minute setup
- [Migration Guide](./migration-from-memory-bank.md) - Full walkthrough
- [Research Validation](../enterprise/research-validation.md) - Academic backing
- [Main Documentation](../../README.md) - Complete reference

[← Back to Community](./README.md)
