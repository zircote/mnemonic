---
name: discover
description: Discover entities in content based on ontology patterns
---

# Discover Entities

Scans content or files for entity references and suggests entity types
based on discovery patterns defined in loaded ontologies.

## Usage

```
/mnemonic-ontology:discover <path> [--suggest] [--json]
```

## Arguments

- `<path>` - File or directory to scan
- `--suggest` - Suggest entity types for unlinked mentions
- `--json` - Output as JSON

## Procedure

1. Load ontologies from standard paths
2. Extract discovery patterns
3. Scan content for pattern matches
4. Report found entities and suggestions

```bash
python ~/.claude/plugins/mnemonic-ontology/skills/ontology/lib/entity_resolver.py \
  --search "${1}" ${ARGS}
```

## Example Output

```
Discovered entities in src/services/:

Found references:
  - @[[PostgreSQL]] -> technology:postgres-7d61fac6
  - @[[Redis]] -> technology:redis-cache-01
  
Suggestions (unlinked):
  - "MongoDB" at line 45 -> suggest: technology
  - "Circuit Breaker" at line 89 -> suggest: design-pattern
```
