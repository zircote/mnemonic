---
adr_paths:
  - docs/adrs

default_format: structured-madr

numbering:
  pattern: "adr-{NNN}-{slug}.md"
  digits: 3
  start_from: 1

statuses:
  workflow:
    - proposed
    - accepted
    - deprecated
    - superseded
  allow_rejected: true

git:
  enabled: true
  auto_commit: false
  commit_template: "docs(adr): {action} ADR-{id} {title}"

templates:
  structured_madr: true
  require_audit: true
  require_frontmatter: true
---

# Mnemonic ADR Context

Architecture Decision Records for the Mnemonic plugin.

## Decision Process

- ADRs are proposed via pull request
- Use Structured MADR format with YAML frontmatter
- Audit sections are required for compliance tracking
- Team review recommended before acceptance

## Categories

- **architecture** - Core system design decisions
- **api** - API design and contracts
- **format** - File format specifications
- **storage** - Data storage decisions
- **integration** - External tool integration

## Existing ADRs

- ADR-001: Filesystem-based Storage (accepted)
- ADR-002: MIF Level 3 Format (accepted)
