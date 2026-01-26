---
name: list
description: List loaded ontologies and their namespaces
allowed-tools:
  - Bash
  - Read
---

# List Ontologies

Lists all loaded ontologies with their namespaces and entity types.

## Usage

```
/mnemonic:list [--namespaces] [--types] [--json]
```

## Options

- `--namespaces` - Show only namespaces
- `--types` - Show only entity types
- `--json` - Output as JSON

## Procedure

```bash
# Find and run the ontology registry from the plugin directory
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $0))}"
python3 "$PLUGIN_DIR/skills/ontology/lib/ontology_registry.py" --list ${ARGS}
```

If the Python script is not available, parse ontology files directly:

```bash
# Check project ontology
if [ -f ".claude/mnemonic/ontology.yaml" ]; then
    echo "Project ontology:"
    grep -E "^  id:|^  version:|^  [a-z]+:" .claude/mnemonic/ontology.yaml | head -20
fi

# Check user ontology
if [ -f "$HOME/.claude/mnemonic/ontology.yaml" ]; then
    echo "User ontology:"
    grep -E "^  id:|^  version:|^  [a-z]+:" "$HOME/.claude/mnemonic/ontology.yaml" | head -20
fi
```

## Example Output

```
Loaded ontologies:
  - mif-base v1.0.0
    Namespaces: semantic/, semantic/decisions, semantic/knowledge, semantic/entities,
                episodic/, episodic/incidents, episodic/sessions, episodic/blockers,
                procedural/, procedural/runbooks, procedural/patterns, procedural/migrations
    Traits: timestamped, confidence, provenance
    Relationships: relates_to, supersedes, derived_from

  - software-engineering v1.0.0 (extends mif-base)
    Entity types: component, architectural-decision, incident-report, technology
```
