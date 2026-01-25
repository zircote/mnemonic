---
name: validate
description: Validate an ontology YAML file against the meta-schema
---

# Validate Ontology

Validates an ontology definition file for correctness.

## Usage

```
/mnemonic-ontology:validate <file> [--json]
```

## Arguments

- `<file>` - Path to ontology YAML file (required)
- `--json` - Output as JSON

## Checks Performed

- Required fields present (id, version)
- ID format (lowercase, hyphens)
- Version follows semver
- Valid base types (semantic, episodic, procedural)
- Traits defined before use
- Relationships reference valid entity types
- Discovery patterns are valid regex

## Procedure

```bash
python ~/.claude/plugins/mnemonic-ontology/skills/ontology/lib/ontology_validator.py \
  "${1}" ${ARGS}
```

## Example Output

```
Validating: my-ontology.yaml
Status: VALID

Warnings (1):
  - [WARNING] traits.cited: Trait has no fields or requires defined
```
