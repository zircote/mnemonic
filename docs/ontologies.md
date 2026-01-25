# Mnemonic Ontology System

Custom ontology support for extending mnemonic with domain-specific knowledge
structures.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Concepts](#concepts)
- [Defining an Ontology](#defining-an-ontology)
- [Using Ontologies](#using-ontologies)
- [Entity Linking](#entity-linking)
- [Discovery](#discovery)
- [Validation](#validation)
- [Examples](#examples)
- [Reference](#reference)

## Overview

The ontology system extends mnemonic beyond its 9 base namespaces, enabling:

- **Custom namespaces** for domain-specific knowledge organization
- **Typed entities** with schemas for structured data capture
- **Relationships** between entities for knowledge graphs
- **Traits/mixins** for reusable field sets
- **Discovery patterns** for agent-driven entity suggestion

### Cognitive Memory Type Triad

All entities inherit from one of three base memory types:

| Type | Purpose | Examples |
|------|---------|----------|
| **Semantic** | Facts, concepts, relationships | Components, technologies, decisions |
| **Episodic** | Events, experiences, timelines | Incidents, debug sessions, meetings |
| **Procedural** | Step-by-step processes | Runbooks, deployments, migrations |

## Quick Start

### 1. Copy the software-engineering ontology

```bash
cp skills/ontology/ontologies/examples/software-engineering.ontology.yaml \
   .claude/mnemonic/ontology.yaml
```

### 2. Capture a memory with an entity type

```bash
/mnemonic:capture dependencies "PostgreSQL Database"
```

When you mention PostgreSQL, Claude will suggest creating a `technology` entity
based on the ontology's discovery patterns.

### 3. Reference entities in other memories

```markdown
The payment service depends on @[[PostgreSQL]] for transaction storage.
```

## Concepts

### Namespaces

Namespaces organize memories by domain. The base mnemonic has 9 namespaces:

- `apis`, `blockers`, `context`, `decisions`, `learnings`
- `patterns`, `security`, `testing`, `episodic`

Custom ontologies add more:

```yaml
namespaces:
  architecture:
    description: "System architecture decisions"
    type_hint: semantic
  
  incidents:
    description: "Production incidents and postmortems"
    type_hint: episodic
```

### Entity Types

Entity types define structured schemas for memories:

```yaml
entity_types:
  - name: technology
    base: semantic
    schema:
      required:
        - name
        - category
      properties:
        name:
          type: string
        category:
          type: string
          enum: [database, framework, language, tool]
```

### Traits

Traits are reusable field sets (mixins) that entity types can include:

```yaml
traits:
  versioned:
    fields:
      version:
        type: string
        pattern: "^\\d+\\.\\d+\\.\\d+$"
      changelog:
        type: array

entity_types:
  - name: component
    base: semantic
    traits:
      - versioned  # Includes version and changelog fields
```

### Relationships

Relationships define how entities can connect:

```yaml
relationships:
  depends_on:
    from: [component]
    to: [component, technology]
    symmetric: false
  
  implements:
    from: [component]
    to: [design-pattern]
```

## Defining an Ontology

Create `.claude/mnemonic/ontology.yaml`:

```yaml
---
ontology:
  id: my-domain
  version: "1.0.0"
  description: "My domain ontology"

namespaces:
  # Custom namespaces
  models:
    description: "ML models"
    type_hint: semantic

entity_types:
  - name: model
    base: semantic
    traits:
      - versioned
    schema:
      required:
        - name
        - framework
      properties:
        name:
          type: string
        framework:
          type: string
          enum: [pytorch, tensorflow, jax]
        accuracy:
          type: number

traits:
  versioned:
    fields:
      version:
        type: string

relationships:
  trained_on:
    from: [model]
    to: [dataset]

discovery:
  enabled: true
  patterns:
    - content_pattern: "\\b(PyTorch|TensorFlow|JAX)\\b"
      suggest_entity: model
```

### Ontology File Locations

| Location | Scope |
|----------|-------|
| `.claude/mnemonic/ontology.yaml` | Project-specific |
| `~/.claude/mnemonic/ontology.yaml` | Global (all projects) |

Project ontologies take precedence over global ones.

## Using Ontologies

### Capturing with Entity Types

When you capture a memory, add ontology metadata:

```yaml
---
id: postgres-7d61fac6
type: semantic
namespace: dependencies/project
title: "PostgreSQL Database"
ontology:
  entity_type: technology
  entity_id: postgres-prod
entity:
  name: PostgreSQL
  category: database
  use_case: "Primary data store"
  version: "15.4"
---

# PostgreSQL

Production database for core application data.
```

### Entity Fields

The `entity` block contains fields defined by the entity type's schema:

```yaml
entity:
  name: PostgreSQL        # required by technology schema
  category: database      # required, must be valid enum
  use_case: "..."         # optional
  version: "15.4"         # from versioned trait
```

## Entity Linking

### Reference Syntax

Link entities in memory content using:

| Syntax | Description | Example |
|--------|-------------|---------|
| `@[[Name]]` | Simple reference by name | `@[[PostgreSQL]]` |
| `[[type:id]]` | Typed reference | `[[technology:postgres-prod]]` |

### Example

```markdown
# Payment Service Architecture

The payment service uses @[[PostgreSQL]] for transaction storage
and @[[Redis]] for session caching.

This implements the [[design-pattern:repository-pattern]] for
data access abstraction.

## Related
- Incident: [[incident-report:payment-outage-2026-01]]
- Runbook: [[runbook:payment-failover]]
```

### Relationship Types

Define relationships between entities:

```markdown
---
entity_links:
  - id: postgres-prod
    type: depends_on
  - id: repository-pattern
    type: implements
---
```

## Discovery

### How Discovery Works

1. Ontology defines discovery patterns (regex or file globs)
2. When you capture content, Claude matches patterns
3. Claude suggests creating entities for matches
4. You confirm, and entity metadata is added

### Discovery Patterns

```yaml
discovery:
  enabled: true
  confidence_threshold: 0.8
  
  patterns:
    # Match technology names in content
    - content_pattern: "\\b(PostgreSQL|MySQL|MongoDB)\\b"
      suggest_entity: technology
    
    # Match files by path
    - file_pattern: "**/services/**/*.py"
      suggest_entity: component
    
    # Match operational terms
    - content_pattern: "\\b(runbook|playbook|SOP)\\b"
      suggest_entity: runbook
```

### User Experience

```
You: /mnemonic:capture decisions "Use PostgreSQL for user data"

Claude: I notice you mentioned PostgreSQL. Would you like me to create
a `technology` entity for it? This allows linking from other memories.

You: Yes

Claude: Created technology entity `postgres-user-data` with:
- name: PostgreSQL
- category: database
- use_case: User data storage
```

## Validation

### Validate an Ontology File

```bash
python skills/ontology/lib/ontology_validator.py .claude/mnemonic/ontology.yaml
```

Output:
```
Validating: .claude/mnemonic/ontology.yaml
Status: VALID
```

### Validation Checks

- Required fields present (`id`, `version`)
- ID format (lowercase, hyphens only)
- Version follows semver
- Base types are valid (`semantic`, `episodic`, `procedural`)
- Referenced traits exist
- Relationship entity types exist
- Discovery patterns are valid regex

### Common Errors

```
[ERROR] ontology.id: ID must be lowercase with hyphens
[ERROR] entity_types.MyComponent.base: Invalid base type
[ERROR] entity_types.component.traits: Reference to undefined trait: versioned
[ERROR] discovery.patterns[0]: Invalid regex pattern
```

## Examples

### Software Engineering Ontology

See `skills/ontology/ontologies/examples/software-engineering.ontology.yaml` for a complete
example with:

- 5 namespaces (architecture, components, incidents, migrations, dependencies)
- 8 entity types (component, decision, incident, technology, pattern, runbook, etc.)
- 6 traits (versioned, documented, dated, cited, timeline, stakeholders)
- 7 relationships (depends_on, implements, caused_by, resolves, etc.)
- 15+ discovery patterns

### Example Memories

**Technology Entity:**
```yaml
---
id: redis-cache-01
type: semantic
namespace: dependencies/project
ontology:
  entity_type: technology
entity:
  name: Redis
  category: database
  use_case: "Session caching and rate limiting"
---
```

**Incident Report:**
```yaml
---
id: outage-2026-01-15
type: episodic
namespace: incidents/project
ontology:
  entity_type: incident-report
entity:
  severity: critical
  impact: "Payment processing unavailable for 45 minutes"
  resolution: "Scaled database connections, added circuit breaker"
  duration_minutes: 45
---
```

**Runbook:**
```yaml
---
id: db-failover-v2
type: procedural
namespace: incidents/project
ontology:
  entity_type: runbook
entity:
  title: "Database Failover Procedure"
  trigger: "Primary database unresponsive >30 seconds"
  severity: critical
  procedure:
    - step: 1
      action: "Verify primary is down"
    - step: 2
      action: "Promote replica"
    - step: 3
      action: "Update connection strings"
---
```

## Reference

### Commands

| Command | Description |
|---------|-------------|
| `/mnemonic:list` | List loaded ontologies and namespaces |
| `/mnemonic:validate <file>` | Validate ontology file |
| `/mnemonic:discover <path>` | Discover entities in files |

### Library API

The ontology library is located in `skills/ontology/lib/`:

```python
import sys
sys.path.insert(0, "skills/ontology/lib")

from ontology_registry import OntologyRegistry
from ontology_validator import OntologyValidator
from entity_resolver import EntityResolver

# Load ontologies
registry = OntologyRegistry()
registry.load_ontologies([Path(".claude/mnemonic")])

# Validate
validator = OntologyValidator()
result = validator.validate_file(Path("ontology.yaml"))

# Resolve references
resolver = EntityResolver(registry)
refs = resolver.extract_references("Uses @[[PostgreSQL]] for storage")
```

### Schema Reference

See `skills/ontology/ontologies/schemas/ontology-meta-schema.json` for the complete JSON Schema.

### See Also

- [ADR-008: Custom Ontologies](adrs/adr-008-custom-ontologies.md)
- [Base Ontology](skills/ontology/ontologies/base.ontology.yaml)
- [Software Engineering Example](skills/ontology/ontologies/examples/software-engineering.ontology.yaml)
