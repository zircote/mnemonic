---
name: query
allowed-tools:
- Bash
- Read
- Glob
- Grep
- Write
argument-hint: '[--type TYPE] [--tag TAG] [--confidence VALUE] [--namespace NS]'
description: Structured frontmatter queries using yq
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:query

Structured queries on memory frontmatter fields using yq for YAML parsing.

## Arguments

- `--type` - Filter by memory type (semantic, episodic, procedural)
- `--namespace` - Filter by namespace pattern (supports wildcards like `decisions/*`)
- `--tag` - Filter by tag (can be specified multiple times)
- `--confidence` - Filter by confidence with operators (>, >=, <, <=, ..)
- `--created` - Filter by created date with operators
- `--modified` - Filter by modified date with operators
- `--title` - Filter by title pattern (regex)
- `--scope` - Limit to user, project, or all (default: all)
- `--format` - Output format: paths, titles, json, count (default: paths)
- `--limit` - Limit output to N results

## Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `=` (implicit) | `--confidence 0.9` | Exact match |
| `!=` | `--type "!=episodic"` | Not equal |
| `>` | `--confidence ">0.8"` | Greater than |
| `>=` | `--confidence ">=0.9"` | Greater or equal |
| `<` | `--confidence "<0.5"` | Less than |
| `<=` | `--confidence "<=0.7"` | Less or equal |
| `..` | `--confidence "0.7..0.9"` | Range (inclusive) |

## Procedure

### Step 1: Check yq Installation

```bash
if ! command -v yq &>/dev/null; then
    echo "Error: yq is required. Install: brew install yq"
    exit 1
fi
```

### Step 2: Execute Query

```bash
# Run mnemonic-query with provided arguments
./tools/mnemonic-query "$@"
```

## Example Usage

```bash
# Find all semantic memories
/mnemonic:query --type semantic

# Find high-confidence memories
/mnemonic:query --confidence ">0.8"

# Find memories in confidence range
/mnemonic:query --confidence "0.5..0.9"

# Find by tag and type
/mnemonic:query --tag architecture --type semantic

# Find decisions with security tag
/mnemonic:query --namespace "_semantic/decisions" --tag security

# Exclude episodic memories
/mnemonic:query --type "!=episodic"

# Find memories created in date range
/mnemonic:query --created "2026-01-01..2026-01-31"

# Get count only
/mnemonic:query --type semantic --format count

# Get titles
/mnemonic:query --tag architecture --format titles

# Limit results
/mnemonic:query --type semantic --limit 10

# Pipe to content search
/mnemonic:query --tag security | xargs rg "password"
```

## Output Formats

### paths (default)
```
/path/to/memory1.memory.md
/path/to/memory2.memory.md
```

### titles
```
Use PostgreSQL for storage
Implement JWT authentication
```

### json
```json
[
  {
    "path": "/path/to/memory.memory.md",
    "title": "Use PostgreSQL for storage",
    "type": "semantic",
    "namespace": "decisions/project",
    "confidence": 0.9,
    "created": "2026-01-23T10:30:00Z",
    "tags": ["database", "architecture"]
  }
]
```

### count
```
42
```

## Combining with rg

The real power comes from combining structured queries with content search:

```bash
# Find security decisions mentioning passwords
/mnemonic:query --namespace "_semantic/decisions" --tag security | xargs rg "password"

# Find high-confidence memories about authentication
/mnemonic:query --confidence ">0.8" | xargs rg -i "auth"

# Search recent memories for specific content
/mnemonic:query --created ">2026-01-01" | xargs rg "api"
```

## Requirements

- `yq` - YAML processor (install: `brew install yq`)
- Python 3.8+
