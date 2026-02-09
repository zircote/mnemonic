---
allowed-tools:
- Bash
- Read
- Grep
- Glob
- Write
description: Discover entities in content based on ontology patterns
name: discover
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# Discover Entities

Scans content or files for entity references and suggests entity types
based on discovery patterns defined in loaded ontologies.

## Usage

```
/mnemonic:discover [<path>] [--suggest] [--json]
```

## Arguments

- `<path>` - File or directory to scan (defaults to current directory)
- `--suggest` - Suggest entity types for unlinked mentions
- `--json` - Output as JSON

## Procedure

1. Load ontology from `$MNEMONIC_ROOT/ontology.yaml`
2. Extract discovery patterns
3. Scan content for pattern matches
4. Report found entities and suggestions

```bash
# Resolve MNEMONIC_ROOT from config
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    RAW_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '~/.claude/mnemonic'))")
    MNEMONIC_ROOT="${RAW_PATH/#\~/$HOME}"
else
    MNEMONIC_ROOT="$HOME/.claude/mnemonic"
fi
SCAN_PATH="${1:-.}"
ONTOLOGY_FILE="$MNEMONIC_ROOT/ontology.yaml"

# Check for ontology
if [ ! -f "$ONTOLOGY_FILE" ]; then
    echo "No ontology found at $ONTOLOGY_FILE"
    echo "Copy an ontology to enable discovery:"
    echo "  cp skills/ontology/ontologies/examples/software-engineering.ontology.yaml $MNEMONIC_ROOT/ontology.yaml"
    exit 1
fi

echo "Scanning $SCAN_PATH for entity patterns..."
echo ""

# Extract and run discovery patterns from ontology
# Technology patterns
echo "## Technologies Found"
rg -i '\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b' "$SCAN_PATH" --glob '*.{md,py,js,ts,yaml,yml}' -l 2>/dev/null | head -10

echo ""
echo "## Design Patterns Found"
rg -i '\b(Factory|Singleton|Observer|Repository|Adapter|Strategy)\s+Pattern\b' "$SCAN_PATH" --glob '*.{md,py,js,ts}' -l 2>/dev/null | head -10

echo ""
echo "## Incidents/Postmortems Found"
rg -i '\b(outage|incident|postmortem|RCA)\b' "$SCAN_PATH" --glob '*.md' -l 2>/dev/null | head -10

echo ""
echo "## Runbooks Found"
rg -i '\b(runbook|playbook|SOP|procedure)\b' "$SCAN_PATH" --glob '*.md' -l 2>/dev/null | head -10
```

## Suggestions

When patterns match, Claude will suggest:

```
I found mentions of these technologies that could be captured as entities:
- PostgreSQL (mentioned in src/database.py)
- Redis (mentioned in src/cache.py)

Would you like me to create technology entities for these?
```
