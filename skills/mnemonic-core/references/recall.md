# Recall Workflow

Complete workflow for searching and retrieving memories.

## Quick Recall (Frontmatter Only)

```bash
# List memories in a namespace
ls -la ${MNEMONIC_ROOT}/*/_semantic/decisions/*.memory.md 2>/dev/null

# Get titles from frontmatter
for f in ${MNEMONIC_ROOT}/*/_semantic/decisions/**/*.memory.md; do
    grep "^title:" "$f" 2>/dev/null | head -1
done
```

## Search by Tag

```bash
# Find memories with specific tag
rg -l "^  - architecture" ${MNEMONIC_ROOT}/ --glob "*.memory.md"
rg -l "^  - architecture" --glob "*.memory.md"
```

## Search by Date Range

```bash
# Recent memories (last 7 days)
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime -7
find ./.claude/mnemonic -name "*.memory.md" -mtime -7

# By created date in frontmatter
rg "^created: 2026-01" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```

## Search by Cognitive Type

```bash
# Find all episodic memories
rg "^type: episodic" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
rg "^type: episodic" --glob "*.memory.md" -l
```

## Full-Text Search

```bash
# Case-insensitive search
rg -i "postgresql" ${MNEMONIC_ROOT}/ --glob "*.memory.md"
rg -i "postgresql" --glob "*.memory.md"

# With context lines
rg -i -C3 "postgresql" ${MNEMONIC_ROOT}/ --glob "*.memory.md"
```

## Tiered Recall (Progressive Disclosure)

**Level 1: Quick Answer (frontmatter only):**
```bash
# Just frontmatter
head -20 /path/to/memory.memory.md | sed -n '/^---$/,/^---$/p'
```

**Level 2: Context (frontmatter + context section):**
```bash
# First 50 lines
head -50 /path/to/memory.memory.md
```

**Level 3: Full Detail (complete memory):**
```bash
# Entire file
cat /path/to/memory.memory.md
```

## Semantic Recall (requires qmd)

When `@tobilu/qmd` is installed and indexed, use semantic search for concept-based recall.

```bash
# BM25 keyword search (ranked, typo-tolerant)
qmd search "database migration strategy" -n 10

# Semantic vector search (meaning-based)
qmd vsearch "how do we handle authentication" -n 10

# Hybrid search (best overall recall)
qmd query "error handling patterns" -n 10

# Scope to a specific org or project
qmd search "auth" -c mnemonic-zircote
qmd search "auth" -c mnemonic-project

# JSON output for programmatic use
qmd query "deployment process" --json -n 5
```

Setup: `/mnemonic:qmd-setup` | Re-index: `/mnemonic:reindex` (or `qmd update && qmd embed`)
