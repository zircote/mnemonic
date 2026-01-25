---
name: validate
description: Validate an ontology YAML file against the meta-schema
allowed-tools:
  - Bash
  - Read
---

# Validate Ontology

Validates an ontology definition file for correctness.

## Usage

```
/mnemonic:validate <file> [--json]
```

## Arguments

- `<file>` - Path to ontology YAML file (required). Defaults to `.claude/mnemonic/ontology.yaml`
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
ONTOLOGY_FILE="${1:-.claude/mnemonic/ontology.yaml}"
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $0))}"

python3 "$PLUGIN_DIR/skills/ontology/lib/ontology_validator.py" "$ONTOLOGY_FILE" ${ARGS}
```

If Python validation unavailable, perform basic YAML checks:

```bash
# Check file exists
if [ ! -f "$ONTOLOGY_FILE" ]; then
    echo "Error: File not found: $ONTOLOGY_FILE"
    exit 1
fi

# Check required fields
if ! grep -q "^ontology:" "$ONTOLOGY_FILE"; then
    echo "Error: Missing 'ontology:' section"
    exit 1
fi

if ! grep -q "id:" "$ONTOLOGY_FILE"; then
    echo "Error: Missing 'id' field"
    exit 1
fi

echo "Basic validation passed for: $ONTOLOGY_FILE"
```

## Example Output

```
Validating: my-ontology.yaml
Status: VALID

Warnings (1):
  - [WARNING] traits.cited: Trait has no fields or requires defined
```
