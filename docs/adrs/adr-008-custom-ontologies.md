# ADR-008: Custom Ontology Support

**Status**: Proposed
**Date**: 2026-01-25
**Deciders**: Development Team
**Context**: Mnemonic currently has 9 hardcoded namespaces limiting domain-specific knowledge management

## Context and Problem Statement

Mnemonic's current architecture uses 9 hardcoded namespaces (apis, blockers, context, decisions, learnings, patterns, security, testing, episodic) defined across 10+ files. This limits mnemonic's ability to:

1. Support domain-specific taxonomies (medical, legal, finance)
2. Enable custom entity types with specialized validation
3. Provide rich entity linking and relationship tracking
4. Discover and document domain knowledge automatically

Users want Palantir Foundry-like capabilities for ontology management without sacrificing mnemonic's core principles.

## Decision Drivers

- **Maintain zero external dependencies** (core mnemonic principle)
- **Skills-first architecture** (self-contained markdown workflows)
- **Filesystem as database** (human-readable, git-versioned)
- **Backward compatibility** (existing memories continue to work)
- **Progressive disclosure** (start simple, add complexity as needed)
- **URL-referenced schemas** (shared ontology definitions)
- **Mixins/traits inheritance** (composable type system)

## Considered Options

### Option 1: Minimal Changes
- Inject ontology loading at 3 strategic code points
- Single `ontology.yaml` config file
- ~10 hours implementation
- **Rejected**: Limited extensibility, doesn't support full feature set

### Option 2: Clean Architecture (Chosen)
- Layered registry system with proper separation of concerns
- OntologyRegistry + OntologyValidator + EntityResolver services
- ~5 weeks implementation
- **Chosen**: Best long-term maintainability, proper abstractions

### Option 3: Pragmatic Balance
- Registry-based with YAML definitions
- Phased rollout over 4 weeks
- **Rejected**: Slightly less elegant architecture, but faster

## Decision

Implement **Clean Architecture** with the following components:

### Core Components

1. **OntologyRegistry** (`lib/ontology_registry.py`)
   - Load and parse ontology definitions
   - Maintain catalog of available ontologies
   - Resolve namespace-to-ontology mappings
   - Handle precedence (base < user < project)

2. **OntologyValidator** (`lib/ontology_validator.py`)
   - Validate ontology definition files against meta-schema
   - Check entity type definitions for completeness
   - Verify trait/mixin compatibility
   - Validate relationships and hierarchies

3. **EntityResolver** (`lib/entity_resolver.py`)
   - Link entities across memories
   - Resolve entity references to canonical forms
   - Maintain entity index for fast lookups
   - Support entity aliasing

4. **Discovery Agent** (`agents/ontology-discovery.md`)
   - Analyze code/docs to suggest entity captures
   - Interactive user confirmation workflow
   - Writes suggestions to blackboard
   - Updates ontology registry on confirmation

### Ontology Definition Format

```yaml
ontology:
  id: software-engineering
  version: "1.2.0"
  schema_url: https://github.com/org/ontologies/se.yaml
  description: "Software engineering domain ontology"

  # Custom namespace definitions
  namespaces:
    architecture:
      description: "System architecture and design patterns"
      type_hint: "semantic"

    incidents:
      description: "Production incidents and postmortems"
      type_hint: "episodic"

  # Entity types with inheritance
  entity_types:
    - name: component
      description: "Software component or module"
      base: semantic  # Inherits from base type
      traits: [versioned, documented]  # Composable mixins
      schema:
        required: [name, responsibility, dependencies]
        properties:
          name: {type: string}
          responsibility: {type: string}
          dependencies: {type: array, items: {type: string}}

    - name: incident-report
      base: episodic
      traits: [timeline, stakeholders]
      schema:
        required: [severity, impact, resolution]

  # Reusable traits (mixins)
  traits:
    versioned:
      fields:
        version: {type: string, pattern: "^\\d+\\.\\d+\\.\\d+$"}
        changelog: {type: array}

    documented:
      fields:
        documentation_url: {type: string, format: uri}

    timeline:
      fields:
        timeline:
          type: array
          items:
            type: object
            properties:
              timestamp: {type: string, format: date-time}
              event: {type: string}

  # Relationship types
  relationships:
    depends_on:
      from: [component]
      to: [component]
      symmetric: false

    implements:
      from: [component]
      to: [pattern]
      symmetric: false

  # Discovery patterns
  discovery:
    enabled: true
    patterns:
      - file_pattern: "**/*.architecture.md"
        suggest_entity: component
      - content_pattern: "\\b(PostgreSQL|Redis|Kubernetes)\\b"
        suggest_entity: technology
    confidence_threshold: 0.8
```

### Extended MIF Level 3 Fields

```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
namespace: architecture/project  # Custom namespace

# New ontology extension fields
ontology:
  id: software-engineering
  entity_type: component
  entity_id: stripe-payment-integration

# Entity-specific fields (validated by ontology schema)
entity:
  name: StripePaymentIntegration
  responsibility: Handle payment processing
  dependencies: [stripe-sdk, payment-validator]
  version: 2.1.0
  documentation_url: https://docs.company.com/stripe

# Standard MIF fields preserved
tags: [payment, api]
created: 2026-01-25T10:30:00Z
---
```

### Entity Linking Syntax

In memory body (markdown):
```markdown
## Entities
- technology: @[[PostgreSQL]]
- pattern: @[[Repository Pattern]]
- implements: [[component:stripe-integration]]
```

### File Structure

```
mnemonic/
├── lib/                              # NEW: Python library modules
│   ├── __init__.py
│   ├── ontology_registry.py          # Registry service
│   ├── ontology_validator.py         # Schema validator
│   └── entity_resolver.py            # Entity resolution
├── ontologies/                       # NEW: Ontology definitions
│   ├── schemas/
│   │   └── ontology-meta-schema.json # Meta-schema for ontologies
│   ├── base.ontology.yaml            # Base 9 namespaces as ontology
│   └── examples/
│       ├── software-engineering.yaml
│       └── research.yaml
├── agents/
│   └── ontology-discovery.md         # NEW: Discovery agent
├── commands/
│   ├── capture.md                    # MODIFIED: Ontology-aware
│   └── ontology.md                   # NEW: Ontology management
├── skills/
│   └── mnemonic-ontology/            # NEW: Ontology skill
│       ├── SKILL.md
│       └── references/
│           └── ontology-format.md
├── tools/
│   └── mnemonic-validate             # MODIFIED: Ontology validation
└── docs/
    ├── ontologies.md                 # NEW: User guide
    └── adrs/
        └── adr-008-custom-ontologies.md  # This ADR
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- Create `lib/ontology_registry.py` with OntologyRegistry class
- Implement ontology YAML parser
- Define ontology meta-schema (JSON Schema)
- Create `lib/ontology_validator.py` with schema validation
- Add ontology loading to session_start hook
- Create `ontologies/base.ontology.yaml` (base namespaces)
- Unit tests for registry and validator

### Phase 2: Entity Management (Week 2-3)
- Create `lib/entity_resolver.py` with entity indexing
- Implement entity reference syntax `@[[entity]]` and `[[type:id]]`
- Add entity resolution to recall flow
- Update mnemonic-validate for ontology support
- Integration tests for entity resolution

### Phase 3: Commands and Discovery (Week 3-4)
- Create `commands/ontology.md` with subcommands
- Update `commands/capture.md` for ontology-aware capture
- Create `agents/ontology-discovery.md` agent
- Implement pattern matching for entity suggestions
- Add blackboard integration for suggestions
- End-to-end tests for discovery workflow

### Phase 4: Documentation and Examples (Week 4-5)
- Create example ontologies (software-engineering, research)
- Write ontology authoring guide (`docs/ontologies.md`)
- Create `skills/mnemonic-ontology/SKILL.md`
- Update README with ontology features
- Create ADR documentation
- Migration guide from hardcoded namespaces

## Migration Strategy

### One-Time Migration
1. Run `scripts/migrate_namespaces.py` to convert existing memories
2. Registry uses MIF base ontology from submodule
3. Custom ontologies extend base namespaces

### Adoption
1. Users create `.claude/mnemonic/ontology.yaml` for custom entities
2. Custom ontologies extend base namespaces
3. Discovery agent suggests, never forces

## Consequences

### Positive
- Domain-specific knowledge management (medical, legal, finance)
- Rich entity relationships and linking
- Agent-driven entity discovery
- Shareable ontology packages via URLs
- Type-safe entity validation
- Maintains zero external dependencies (uses only Python stdlib + YAML)

### Negative
- Increased codebase complexity (~3000 lines new code)
- Learning curve for ontology authoring
- Potential namespace conflicts with custom ontologies

### Neutral
- Requires 5-week implementation timeline
- Adds new skill and agent to maintain
- Ontology definitions need versioning discipline

## Files Changed

### New Files (15)
1. `lib/__init__.py`
2. `lib/ontology_registry.py`
3. `lib/ontology_validator.py`
4. `lib/entity_resolver.py`
5. `ontologies/schemas/ontology-meta-schema.json`
6. `ontologies/base.ontology.yaml`
7. `ontologies/examples/software-engineering.yaml`
8. `ontologies/examples/research.yaml`
9. `agents/ontology-discovery.md`
10. `commands/ontology.md`
11. `skills/mnemonic-ontology/SKILL.md`
12. `skills/mnemonic-ontology/references/ontology-format.md`
13. `docs/ontologies.md`
14. `tests/test_ontology_registry.py`
15. `tests/test_entity_resolver.py`

### Modified Files (5)
1. `hooks/session_start.py` - Load ontologies
2. `commands/capture.md` - Ontology-aware capture
3. `tools/mnemonic-validate` - Ontology validation
4. `skills/format/SKILL.md` - Document ontology fields
5. `.claude-plugin/plugin.json` - Register new components

## Validation

Success criteria:
- [ ] Custom namespaces can be defined and used in captures
- [ ] Entity types with traits are validated correctly
- [ ] Entity linking syntax works in memories
- [ ] Discovery agent suggests entities from code/docs
- [ ] URL-referenced ontologies load and cache correctly
- [ ] Existing memories continue to validate
- [ ] Performance: <100ms ontology loading, <50ms entity resolution
