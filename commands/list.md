---
name: list
description: List loaded ontologies and their namespaces
---

# List Ontologies

Lists all loaded ontologies with their namespaces and entity types.

## Usage

```
/mnemonic-ontology:list [--namespaces] [--types] [--json]
```

## Options

- `--namespaces` - Show only namespaces
- `--types` - Show only entity types  
- `--json` - Output as JSON

## Procedure

```bash
python ~/.claude/plugins/mnemonic-ontology/skills/ontology/lib/ontology_registry.py \
  --list ${ARGS}
```

## Example Output

```
Loaded ontologies:
  - mnemonic-base v1.0.0
    Namespaces: apis, blockers, context, decisions, learnings, patterns, security, testing, episodic
    Entity types: (none)
    
  - software-engineering v1.0.0
    Namespaces: architecture, components, incidents, migrations, dependencies
    Entity types: component, architectural-decision, incident-report, technology, design-pattern, deployment-procedure, runbook, migration-guide
```
