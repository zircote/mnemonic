# Semantic Search with QMD

Mnemonic integrates with [@tobilu/qmd](https://github.com/tobil4sk/qmd) for semantic vector search over your memories. This enables natural language queries and conceptual similarity matching beyond simple keyword search.

## Overview

QMD provides three search methods:

- **BM25 Search** (`qmd search`): Keyword-based ranking algorithm
- **Vector Search** (`qmd vsearch`): Semantic similarity using embeddings
- **Hybrid Search** (`qmd query`): Combines both for best results

## Setup

### Prerequisites

- Node.js >= 22
- npm (comes with Node.js)

### Installation

```bash
# Install qmd globally
npm i -g @tobilu/qmd

# Run automated setup
/mnemonic:qmd-setup
```

The setup skill will:
1. Verify prerequisites
2. Discover memory roots from `~/.config/mnemonic/config.json`
3. Register collections for each memory root:
   - `${MNEMONIC_ROOT}/{org}/` → `mnemonic-{org}`
   - `${MNEMONIC_ROOT}/default/` → `mnemonic-default`
   - `.claude/mnemonic/` → `mnemonic-project` (if exists)
4. Build search index (`qmd update`)
5. Generate embeddings (`qmd embed`)
6. Validate with test search

**Note:** First `qmd embed` downloads ~2 GB of GGUF models.

### Manual Setup

If you prefer manual configuration:

```bash
# Resolve MNEMONIC_ROOT from config
MNEMONIC_ROOT=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '$HOME/.local/share/mnemonic'))" 2>/dev/null || echo "$HOME/.local/share/mnemonic")

# Register collections
qmd collection add "${MNEMONIC_ROOT}/zircote/" --name mnemonic-zircote
qmd collection add "${MNEMONIC_ROOT}/default/" --name mnemonic-default
qmd collection add ".claude/mnemonic/" --name mnemonic-project  # if in a repo

# Build index and embeddings
qmd update
qmd embed

# Verify
qmd status
```

## Usage

### Basic Search

```bash
# BM25 keyword search
qmd search "authentication middleware"

# Semantic vector search
qmd vsearch "how do we handle user sessions"

# Hybrid search (recommended)
qmd query "database migration strategy"
```

### Scoped Search

Search within specific memory collections:

```bash
# Organization-level memories only
qmd search "api design" -c mnemonic-zircote

# Project-level memories only
qmd search "api design" -c mnemonic-project

# All collections (default)
qmd search "api design"
```

### Result Limiting

```bash
# Top 5 results
qmd search "authentication" -n 5

# Top 10 results (default)
qmd search "authentication"

# Custom limit
qmd query "error handling" -n 3
```

### Advanced Queries

```bash
# Multi-term queries
qmd query "user authentication AND session management"

# Natural language
qmd vsearch "What are our conventions for REST API error codes?"

# Technical concepts
qmd query "dependency injection patterns in Python"
```

## Re-indexing

QMD indexes are **not** automatically updated. Re-index after:

- Capturing new memories
- Bulk imports
- Direct file edits
- Hook-based captures

### Via Skill

```bash
/mnemonic:qmd-reindex
```

### Manual Re-index

```bash
# Full re-index
qmd update && qmd embed

# Index only (skip embeddings for speed)
qmd update

# Specific collection only
qmd update -c mnemonic-project && qmd embed -c mnemonic-project
```

## Collection Management

### List Collections

```bash
qmd collection list
```

### Add Collection

```bash
qmd collection add /path/to/memories --name my-collection
```

### Remove Collection

```bash
qmd collection remove my-collection
```

### Check Status

```bash
# Overview of all collections
qmd status

# Detailed info
qmd collection info mnemonic-zircote
```

## Search Workflow Examples

### Example 1: Find Related Decisions

```bash
# Question: "What decisions have we made about authentication?"
qmd query "authentication decisions" -n 10

# Review results, then drill down with ripgrep
rg "authentication" ${MNEMONIC_ROOT} --glob "*decisions*.memory.md"
```

### Example 2: Discover Patterns

```bash
# Question: "What patterns do we use for error handling?"
qmd vsearch "error handling patterns"

# Get specific files
qmd search "error" -c mnemonic-project | grep "\.memory\.md" | xargs cat
```

### Example 3: Cross-Namespace Search

```bash
# Question: "Everything related to PostgreSQL"
qmd query "postgresql" | grep "\.memory\.md" | while read file; do
  echo "=== $file ==="
  cat "$file"
done
```

## Performance Tuning

### Initial Index Size

| Memory Count | Index Time | Embedding Time | Disk Space |
|--------------|------------|----------------|------------|
| 100 | ~5s | ~30s | ~5 MB |
| 1,000 | ~30s | ~5 min | ~50 MB |
| 10,000 | ~5 min | ~45 min | ~500 MB |

### Incremental Re-indexing

QMD rebuilds the entire index on `update`. For large collections:

```bash
# Index only changed files (manual approach)
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime -1 | xargs qmd update --files
```

### Embedding Cache

Embeddings are cached. Deleting files from memory roots doesn't remove their embeddings until re-index:

```bash
# Force full rebuild
rm -rf ~/.qmd/cache
qmd update && qmd embed
```

## Integration with Mnemonic Commands

### Capture + Re-index

```bash
/mnemonic:capture decisions "Use PostgreSQL for main database"
/mnemonic:qmd-reindex
```

### Search + Recall

```bash
# Semantic search for relevant memories
qmd query "database schema patterns"

# Recall specific memory by ID (from search results)
/mnemonic:recall --id 550e8400-e29b-41d4-a716-446655440000
```

### Enhanced Search Skill

The `/mnemonic:search-enhanced` skill can optionally use qmd for initial search:

```bash
/mnemonic:search-enhanced "comprehensive guide to our authentication system"
```

## Troubleshooting

### qmd command not found

```bash
# Install globally
npm i -g @tobilu/qmd

# Or use npx
npx @tobilu/qmd search "test"
```

### No results returned

```bash
# Check collections are registered
qmd collection list

# Check index exists
qmd status

# Re-index
qmd update && qmd embed
```

### Embeddings not generated

```bash
# Check qmd embed completed successfully
qmd embed

# First run downloads models (~2 GB)
# Ensure sufficient disk space and network connection
```

### Out of date results

```bash
# Re-index to include new memories
qmd update && qmd embed
```

### Performance issues

```bash
# Use keyword search instead of vector search
qmd search "term" instead of qmd vsearch "term"

# Limit results
qmd query "term" -n 5

# Search specific collections
qmd search "term" -c mnemonic-project
```

## Command Reference

| Command | Purpose | Requires Index | Requires Embeddings |
|---------|---------|---------------|---------------------|
| `qmd collection add <path>` | Register directory | No | No |
| `qmd collection list` | Show collections | No | No |
| `qmd collection remove <name>` | Unregister collection | No | No |
| `qmd update` | Build BM25 index | No | No |
| `qmd embed` | Generate embeddings | Yes (update) | No |
| `qmd search <query>` | BM25 keyword search | Yes (update) | No |
| `qmd vsearch <query>` | Vector semantic search | Yes (update) | Yes (embed) |
| `qmd query <query>` | Hybrid search | Yes (update) | Yes (embed) |
| `qmd status` | Show index status | No | No |

## Further Reading

- [@tobilu/qmd Documentation](https://github.com/tobil4sk/qmd)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Vector Embeddings Explained](https://platform.openai.com/docs/guides/embeddings)
- [Mnemonic Search Skill](../skills/mnemonic-search/SKILL.md)
- [Enhanced Search Skill](../skills/mnemonic-search-enhanced/SKILL.md)
