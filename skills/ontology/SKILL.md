---
name: ontology
description: |
  Ontology-based entity discovery and validation for mnemonic memories.
  Define custom namespaces, entity types, traits, and relationships.

  Triggers: "entity discovery", "validate ontology", "define namespaces",
  "resolve entity references", "list ontologies", "show namespaces", "entity types",
  "entity relationships", "traits", "discovery patterns", "cognitive memory types"
allowed-tools:
  - Bash(python3 *)
  - Bash
  - Read
  - Write
  - Glob
  - Grep
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

### ontology_validator.py

Validate ontology YAML files against the schema.

```bash
python ${SKILL_DIR}/lib/ontology_validator.py <file> [--json]
```

| Option | Description |
|--------|-------------|
| `<file>` | Ontology YAML file to validate (required) |
| `--json` | Output validation results as JSON |

### ontology_registry.py

Load and query ontologies.

```bash
python ${SKILL_DIR}/lib/ontology_registry.py [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--list` | List all loaded ontologies |
| `--namespaces` | List all available namespaces |
| `--types` | List all entity types |
| `--validate <NS>` | Validate a specific namespace |
| `--json` | Output as JSON |

### entity_resolver.py

Resolve and search entity references across memories.

```bash
python ${SKILL_DIR}/lib/entity_resolver.py [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--build-index` | Build complete entity index from memory files |
| `--search <query>` | Search for entities by name or content |
| `--resolve <ref>` | Resolve entity reference (e.g., `@[[Name]]`) |
| `--json` | Output results as JSON |

## Entity Reference Syntax

- Simple: `@[[Entity Name]]` - Resolves by name
- Typed: `[[technology:postgres-id]]` - Resolves by type and ID

## Discovery Patterns

Ontologies can define patterns for automatic namespace suggestion during memory capture.

### Content Patterns

Match text content to suggest appropriate namespaces:

```yaml
discovery:
  content_patterns:
    - pattern: "\\bdecided to\\b|\\bwe will use\\b"
      namespace: _semantic/decisions
    - pattern: "\\blearned that\\b|\\bthe fix was\\b"
      namespace: _semantic/knowledge
```

### File Patterns

Match file paths for contextual namespace hints:

```yaml
discovery:
  file_patterns:
    - pattern: "auth|login|session"
      namespaces:
        - _semantic/knowledge
        - _semantic/decisions
      context: authentication
```

### Configuration

```yaml
discovery:
  enabled: true
  confidence_threshold: 0.8  # Minimum confidence to suggest
```

See `fallback/ontologies/mif-base.ontology.yaml` for complete examples.

## Files

- `lib/ontology_registry.py` - Load and manage ontologies
- `lib/ontology_validator.py` - Validate ontology YAML
- `lib/ontology_loader.py` - Centralized loading with MIF submodule support
- `lib/entity_resolver.py` - Resolve entity references
- `fallback/ontologies/mif-base.ontology.yaml` - Standard mnemonic namespaces
- `fallback/schema/ontology/ontology.schema.json` - JSON Schema
