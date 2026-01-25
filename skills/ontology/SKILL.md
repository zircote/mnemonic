---
name: ontology
description: Custom ontology support for mnemonic memory system
triggers:
  - ontology
  - entity type
  - namespace
  - schema validation
allowed-tools:
  - Bash(python:*)
  - Read
  - Glob
  - Grep
---

# Ontology Skill

Provides custom ontology support for extending mnemonic with domain-specific
knowledge structures.

## Capabilities

- Load and validate ontology definitions (YAML)
- Define custom namespaces beyond the 9 base namespaces
- Create typed entities (semantic, episodic, procedural)
- Establish relationships between entities
- Use traits/mixins for reusable field sets
- Entity discovery patterns

## Cognitive Memory Type Triad

All entity types inherit from one of three base memory types:

| Type | Purpose | Examples |
|------|---------|----------|
| **Semantic** | Facts, concepts | Components, technologies, decisions |
| **Episodic** | Events, experiences | Incidents, debug sessions |
| **Procedural** | Step-by-step processes | Runbooks, deployments |

## Usage

### Validate an ontology file

```bash
python ${SKILL_DIR}/lib/ontology_validator.py path/to/ontology.yaml
```

### List loaded ontologies

```bash
python ${SKILL_DIR}/lib/ontology_registry.py --list
```

### Resolve entity references

```bash
python ${SKILL_DIR}/lib/entity_resolver.py --resolve "@[[PostgreSQL]]"
```

## Entity Reference Syntax

- Simple: `@[[Entity Name]]` - Resolves by name
- Typed: `[[technology:postgres-id]]` - Resolves by type and ID

## Files

- `lib/ontology_registry.py` - Load and manage ontologies
- `lib/ontology_validator.py` - Validate ontology YAML
- `lib/entity_resolver.py` - Resolve entity references
- `ontologies/base.ontology.yaml` - Standard mnemonic namespaces
- `ontologies/schemas/ontology-meta-schema.json` - JSON Schema
