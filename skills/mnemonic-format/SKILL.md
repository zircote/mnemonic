---
name: mnemonic-format
description: MIF Level 3 specification, memory templates, and formatting guidelines
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Glob
---

# Mnemonic Format Skill

MIF Level 3 specification, templates, and formatting guidelines.

## Trigger Phrases

- "memory format"
- "MIF format"
- "frontmatter template"
- "memory template"
- "mnemonic schema"

## Overview

All mnemonic memories follow the **Memory Interchange Format (MIF) Level 3** specification. This ensures consistent structure, rich metadata, and interoperability.

---

## MIF Level 3 Specification

### File Structure

```
{uuid}-{slug}.memory.md
```

- **uuid**: Lowercase UUID v4 (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- **slug**: URL-safe title, max 50 chars (e.g., `use-postgresql-for-storage`)

### Complete Template

```yaml
---
# === REQUIRED FIELDS ===
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
namespace: decisions/project
created: 2026-01-23T10:30:00Z
title: "Human-readable title"

# === RECOMMENDED FIELDS ===
modified: 2026-01-23T14:22:00Z
tags:
  - architecture
  - database

# === BI-TEMPORAL TRACKING ===
temporal:
  valid_from: 2026-01-23T00:00:00Z    # When fact became true
  valid_until: null                    # When fact expired (null = current)
  recorded_at: 2026-01-23T10:30:00Z   # When captured in system
  ttl: P90D                            # ISO 8601 duration until expiry
  decay:
    model: exponential                 # Decay algorithm
    half_life: P7D                     # Time to 50% relevance
    strength: 0.85                     # Current relevance score 0-1
  access_count: 5                      # Times recalled
  last_accessed: 2026-01-23T14:22:00Z # Last recall timestamp

# === PROVENANCE ===
provenance:
  source_type: conversation            # user_explicit | inferred | conversation
  source_ref: file:///path/to/source.ts:42
  agent: claude-opus-4                 # Capturing agent
  confidence: 0.95                     # Certainty score 0-1
  session_id: abc123                   # Claude session ID

# === CODE STRUCTURE AWARENESS ===
code_refs:
  - file: src/auth/handler.ts
    line: 42
    symbol: authenticateUser
    type: function                     # function | class | method | variable | type

# === CITATIONS ===
citations:
  - type: documentation                # paper | documentation | blog | github | stackoverflow | article
    title: "Source Title"
    url: https://example.com/source
    author: "Author Name"              # optional
    date: 2026-01-23                   # publication date, optional
    accessed: 2026-01-23T10:30:00Z     # when accessed, optional
    relevance: 0.90                    # how relevant to memory 0.0-1.0, optional
    note: "Brief description"          # optional context

# === CONFLICT TRACKING ===
conflicts:
  - memory_id: xyz789
    resolution: merged                 # merged | invalidated | skipped
    resolved_at: 2026-01-23T12:00:00Z
---

# Memory Title

Main content in markdown format.

## Section 1

Detailed information...

## Rationale

Why this decision/pattern/learning matters.

## Relationships

- relates-to [[other-memory-id]]
- supersedes [[old-memory-id]]
- derived-from [[source-memory-id]]

## Entities

- mentions @[[PostgreSQL]]
- uses @[[JWT Authentication]]
```

---

## Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier (v4, lowercase) |
| `type` | enum | Cognitive type: `semantic`, `episodic`, `procedural` |
| `namespace` | string | Category/scope: `decisions/project`, `learnings/user`, etc. |
| `created` | ISO 8601 | Creation timestamp with timezone |
| `title` | string | Human-readable title in quotes |

### Recommended Fields

| Field | Type | Description |
|-------|------|-------------|
| `modified` | ISO 8601 | Last modification timestamp |
| `tags` | list | Categorization tags (lowercase, hyphenated) |

### Temporal Fields

| Field | Type | Description |
|-------|------|-------------|
| `valid_from` | ISO 8601 | When the fact actually became true |
| `valid_until` | ISO 8601 | When the fact became outdated (null if current) |
| `recorded_at` | ISO 8601 | When captured in the system |
| `ttl` | ISO 8601 duration | Time-to-live (e.g., P90D = 90 days) |
| `decay.model` | string | `exponential`, `linear`, `step` |
| `decay.half_life` | ISO 8601 duration | Time to 50% relevance |
| `decay.strength` | float | Current relevance 0.0-1.0 |
| `access_count` | integer | Number of recalls |
| `last_accessed` | ISO 8601 | Most recent recall |

### Provenance Fields

| Field | Type | Description |
|-------|------|-------------|
| `source_type` | enum | `user_explicit`, `inferred`, `conversation` |
| `source_ref` | URI | Source location (file, URL, etc.) |
| `agent` | string | Agent that captured (e.g., `claude-opus-4`) |
| `confidence` | float | Certainty score 0.0-1.0 |
| `session_id` | string | Session identifier |

### Code Reference Fields

| Field | Type | Description |
|-------|------|-------------|
| `file` | string | Relative file path |
| `line` | integer | Line number |
| `symbol` | string | Symbol name |
| `type` | enum | `function`, `class`, `method`, `variable`, `type`, `module` |

### Citation Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | `paper`, `documentation`, `blog`, `github`, `stackoverflow`, `article` (required) |
| `title` | string | Human-readable title of source (required) |
| `url` | string | Full URL to source material (required) |
| `author` | string | Author name (optional) |
| `date` | date | Publication date YYYY-MM-DD (optional) |
| `accessed` | ISO 8601 | When source was accessed (optional) |
| `relevance` | float | How relevant to memory 0.0-1.0 (optional) |
| `note` | string | Brief description of what this citation provides (optional) |

---

## Cognitive Memory Types

### Semantic (Facts & Concepts)

**Use for:** API documentation, technical specifications, definitions, configurations

**Indicators:**
- "X is Y"
- Definitions
- Documentation
- Specifications
- Configuration values

**Example:**
```yaml
---
id: abc123
type: semantic
namespace: apis/project
title: "REST API Authentication Endpoint"
tags:
  - api
  - authentication
---

# REST API Authentication Endpoint

POST /api/v1/auth/login

## Request
- email: string (required)
- password: string (required)

## Response
- token: JWT access token
- expires_in: seconds until expiry
```

### Episodic (Events & Experiences)

**Use for:** Debug sessions, incidents, deployments, meetings, discoveries

**Indicators:**
- "On [date], we..."
- "When we tried..."
- Timestamps
- Narratives
- Incident reports

**Example:**
```yaml
---
id: def456
type: episodic
namespace: blockers/project
title: "Database connection timeout incident"
tags:
  - incident
  - database
  - resolved
temporal:
  valid_from: 2026-01-20T14:30:00Z
  recorded_at: 2026-01-20T16:00:00Z
---

# Database Connection Timeout Incident

## What Happened
On 2026-01-20 at 14:30 UTC, production database connections started timing out.

## Root Cause
Connection pool exhaustion due to unclosed connections in the batch processor.

## Resolution
Added connection.close() in finally block. Deployed fix at 15:45 UTC.

## Prevention
- Added connection pool monitoring
- Set max connection lifetime to 5 minutes
```

### Procedural (Processes & Workflows)

**Use for:** Deployment steps, configuration procedures, how-to guides, workflows

**Indicators:**
- "To do X, first..."
- Step-by-step instructions
- Sequences
- Procedures
- Runbooks

**Example:**
```yaml
---
id: ghi789
type: procedural
namespace: patterns/project
title: "Database migration procedure"
tags:
  - database
  - deployment
  - procedure
---

# Database Migration Procedure

## Prerequisites
- Database backup completed
- Maintenance window scheduled
- Rollback script prepared

## Steps

1. Enable maintenance mode
   ```bash
   ./scripts/maintenance.sh enable
   ```

2. Run migrations
   ```bash
   npm run db:migrate
   ```

3. Verify migrations
   ```bash
   npm run db:verify
   ```

4. Disable maintenance mode
   ```bash
   ./scripts/maintenance.sh disable
   ```

## Rollback
If step 3 fails:
```bash
npm run db:rollback
```
```

---

## Namespace Reference

| Namespace | Purpose | Typical Type |
|-----------|---------|--------------|
| `apis/` | API documentation, contracts | semantic |
| `blockers/` | Issues, impediments, incidents | episodic |
| `context/` | Background information, state | semantic |
| `decisions/` | Architectural choices, rationale | semantic |
| `learnings/` | Insights, discoveries, TILs | semantic/episodic |
| `patterns/` | Coding conventions, best practices | procedural |
| `security/` | Security policies, vulnerabilities | semantic |
| `testing/` | Test strategies, edge cases | procedural |
| `episodic/` | General events, experiences | episodic |

### Scope Subdirectories

- `user/` - Personal knowledge, applies across projects
- `project/` - Specific to current codebase

---

## Relationship Syntax

### Memory Links

```markdown
## Relationships

- relates-to [[550e8400-e29b-41d4-a716-446655440000]]
- supersedes [[old-memory-id]]
- derived-from [[source-memory-id]]
- contradicts [[conflicting-memory-id]]
- implements [[design-memory-id]]
```

### Relationship Types

| Type | Meaning |
|------|---------|
| `relates-to` | General association |
| `supersedes` | Replaces older memory |
| `derived-from` | Built upon another memory |
| `contradicts` | Conflicts with another memory |
| `implements` | Realizes a design/decision |
| `blocks` | Dependency relationship |
| `blocked-by` | Inverse dependency |

---

## Entity Syntax

### Entity Mentions

```markdown
## Entities

- mentions @[[PostgreSQL]]
- uses @[[JWT Authentication]]
- authored-by @[[John Smith]]
- located-in @[[src/auth/]]
```

### Entity Types

| Type | Examples |
|------|----------|
| Technology | PostgreSQL, Redis, Kubernetes |
| Pattern | Factory Pattern, Singleton |
| Person | Team members, authors |
| Location | File paths, directories |
| Concept | Microservices, REST, GraphQL |

---

## Validation Rules

### Required Checks

1. `id` must be valid UUID v4 format
2. `type` must be one of: `semantic`, `episodic`, `procedural`
3. `namespace` must follow pattern: `{namespace}/{scope}`
4. `created` must be valid ISO 8601 timestamp
5. `title` must be non-empty string

### Recommended Checks

1. `confidence` should be between 0.0 and 1.0
2. `valid_from` should be before or equal to `recorded_at`
3. `tags` should be lowercase with hyphens
4. `code_refs.file` paths should be relative

### Citation Checks

**Required if citations array exists:**
1. `citations[].type` must be one of: `paper`, `documentation`, `blog`, `github`, `stackoverflow`, `article`
2. `citations[].title` must be non-empty string
3. `citations[].url` must be valid URL format (https:// or http://)

**Optional field validations:**
4. `citations[].relevance` if present, should be between 0.0 and 1.0
5. `citations[].date` if present, should be valid YYYY-MM-DD format
6. `citations[].accessed` if present, should be valid ISO 8601 timestamp

### File Naming

```bash
# Generate compliant filename
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
TITLE="My Memory Title"
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 50)
FILENAME="${UUID}-${SLUG}.memory.md"
```

---

## Quick Templates

### Minimal Memory

```yaml
---
id: {uuid}
type: semantic
namespace: learnings/project
created: {timestamp}
title: "{title}"
---

# {Title}

{Content}
```

### Decision Memory

```yaml
---
id: {uuid}
type: semantic
namespace: decisions/project
created: {timestamp}
title: "Decision: {what}"
tags:
  - architecture
provenance:
  confidence: 0.95
---

# Decision: {What}

## Context
{Why this decision was needed}

## Decision
{What was decided}

## Consequences
{What this means going forward}
```

### Incident Memory

```yaml
---
id: {uuid}
type: episodic
namespace: blockers/project
created: {timestamp}
title: "Incident: {summary}"
tags:
  - incident
temporal:
  valid_from: {when_it_happened}
---

# Incident: {Summary}

## Timeline
- {time}: {event}

## Root Cause
{Why it happened}

## Resolution
{How it was fixed}

## Prevention
{How to prevent recurrence}
```

### Research Memory with Citations

```yaml
---
id: {uuid}
type: semantic
namespace: learnings/project
created: {timestamp}
title: "Learning: {topic}"
tags:
  - research
citations:
  - type: paper
    title: "Research Paper Title"
    url: https://arxiv.org/abs/...
    author: "Smith et al."
    date: 2025-11-15
    accessed: {timestamp}
    relevance: 0.95
    note: "Key finding about X"
  - type: documentation
    title: "Official Documentation"
    url: https://docs.example.com/...
    accessed: {timestamp}
    relevance: 0.85
---

# Learning: {Topic}

## Summary
{What you learned}

## Key Points
- {Point 1 from citation 1}
- {Point 2 from citation 2}

## Application
{How this applies to our project}
```
