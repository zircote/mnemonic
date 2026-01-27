---
allowed-tools:
- Bash(python3 *)
- Read
- Glob
- Grep
- Bash
- Write
description: 'This skill should be used when the user asks to "create custom entity
  types",

  "define namespaces", "validate ontology files", "resolve entity references",

  "extend mnemonic schemas", or "work with typed memories". Also trigger for

  questions about "entity relationships", "traits", "mixins", "discovery patterns",

  or "cognitive memory types" (semantic, episodic, procedural).

  '
name: ontology
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# Ontology Skill

Provides custom ontology support for extending mnemonic with domain-specific
knowledge structures.

## Requirements

- **PyYAML** - Optional but recommended for YAML parsing. The library works without it but with limited functionality.

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
- `lib/ontology_loader.py` - Centralized loading with MIF submodule support
- `lib/entity_resolver.py` - Resolve entity references
- `fallback/ontologies/mif-base.ontology.yaml` - Standard mnemonic namespaces
- `fallback/schema/ontology/ontology.schema.json` - JSON Schema
