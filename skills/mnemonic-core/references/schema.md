# MIF Level 3 Schema

Full Memory Interchange Format specification.

## Minimal Required Fields

```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
title: "Human-readable title"
type: semantic|episodic|procedural
created: 2026-01-23T10:30:00Z
---
```

## Full Schema (All Optional Fields)

```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic|episodic|procedural
namespace: _semantic/decisions/project
created: 2026-01-23T10:30:00Z
modified: 2026-01-23T14:22:00Z
title: "Human-readable title"
tags:
  - tag1
  - tag2

# Bi-temporal tracking (optional)
temporal:
  valid_from: 2026-01-23T00:00:00Z
  valid_until: null
  recorded_at: 2026-01-23T10:30:00Z
  ttl: P90D
  decay:
    model: exponential
    half_life: P7D
    strength: 0.85
  access_count: 5
  last_accessed: 2026-01-23T14:22:00Z

# Provenance (optional)
provenance:
  source_type: user_explicit|inferred|conversation
  source_ref: file:///path/to/source.ts:42
  agent: claude-opus-4
  confidence: 0.95
  session_id: abc123

# Code structure awareness (optional)
code_refs:
  - file: src/auth/handler.ts
    line: 42
    symbol: authenticateUser
    type: function

# Citations - external references (optional)
citations:
  - type: documentation
    title: "Source Title"
    url: https://example.com/source
    accessed: 2026-01-23T10:30:00Z
    relevance: 0.90

# Conflict tracking (optional)
conflicts:
  - memory_id: xyz789
    resolution: merged
    resolved_at: 2026-01-23T12:00:00Z
---
```

## Directory Structure

**Unified structure** (`${MNEMONIC_ROOT}/`):
```
${MNEMONIC_ROOT}/
├── {org}/                     # Organization-level
│   ├── _semantic/             # Org-wide facts/knowledge
│   │   ├── decisions/
│   │   ├── knowledge/
│   │   └── entities/
│   ├── _episodic/             # Org-wide events
│   │   ├── incidents/
│   │   ├── sessions/
│   │   └── blockers/
│   ├── _procedural/           # Org-wide procedures
│   │   ├── runbooks/
│   │   ├── patterns/
│   │   └── migrations/
│   └── {project}/             # Project-specific memories
│       ├── _semantic/
│       │   ├── decisions/
│       │   ├── knowledge/
│       │   └── entities/
│       ├── _episodic/
│       │   ├── incidents/
│       │   ├── sessions/
│       │   └── blockers/
│       ├── _procedural/
│       │   ├── runbooks/
│       │   ├── patterns/
│       │   └── migrations/
│       └── .blackboard/
├── _semantic/knowledge/
├── _procedural/patterns/
├── _episodic/sessions/
└── .blackboard/
```
