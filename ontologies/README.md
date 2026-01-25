---
# Mnemonic Ontology System

Custom ontology support for extending mnemonic with domain-specific
knowledge structures.

## Overview

The ontology system allows you to:

- Define custom namespaces beyond the 9 base namespaces
- Create typed entities with schemas (component, incident, technology, etc.)
- Establish relationships between entities
- Use traits/mixins for reusable field sets
- Enable agent-driven entity discovery

## Cognitive Memory Type Triad

All entity types inherit from one of three base memory types:

| Type | Purpose | Examples |
|------|---------|----------|
| **Semantic** | Facts, concepts, relationships | Components, technologies, decisions |
| **Episodic** | Events, experiences, timelines | Incidents, debug sessions, meetings |
| **Procedural** | Step-by-step processes | Runbooks, deployments, migrations |

## Directory Structure

```
ontologies/
├── base.ontology.yaml      # Standard mnemonic namespaces
├── schemas/
│   └── ontology-meta-schema.json  # JSON Schema for validation
├── examples/
│   └── software-engineering.ontology.yaml  # Full example
└── README.md               # This file
```

## Quick Start

### 1. Copy base ontology to your project

```bash
cp ontologies/base.ontology.yaml .claude/mnemonic/ontology.yaml
```

### 2. Extend with custom namespaces

```yaml
namespaces:
  architecture:
    description: "System architecture decisions"
    type_hint: semantic
```

### 3. Define entity types

```yaml
entity_types:
  - name: component
    base: semantic
    traits:
      - versioned
    schema:
      required:
        - name
        - responsibility
      properties:
        name:
          type: string
        responsibility:
          type: string
```

### 4. Add discovery patterns

```yaml
discovery:
  enabled: true
  patterns:
    - content_pattern: "\\b(PostgreSQL|MySQL|MongoDB)\\b"
      suggest_entity: technology
```

## Library Usage

```python
from lib import OntologyRegistry, OntologyValidator, EntityResolver

# Load ontologies
registry = OntologyRegistry()
registry.load_ontologies()

# Validate an ontology file
validator = OntologyValidator()
result = validator.validate_file(Path("my-ontology.yaml"))

# Resolve entity references
resolver = EntityResolver(registry)
entity = resolver.resolve_reference("@[[PostgreSQL]]")
```

## Entity Reference Syntax

- Simple: `@[[Entity Name]]` - Resolves by name
- Typed: `[[technology:postgres-id]]` - Resolves by type and ID

## See Also

- [ADR-008: Custom Ontologies](../docs/adrs/adr-008-custom-ontologies.md)
- [Implementation Plan](../docs/ontology-implementation-plan.md)
- [Software Engineering Example](examples/software-engineering.ontology.yaml)
