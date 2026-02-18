---
allowed-tools:
- Bash
- Read
- Glob
- Grep
- Write
- Task
description: >
  This skill should be used when the user says "search memories", "find in memories",
  "grep mnemonic", "look for memory", "deep search", "synthesize knowledge", or asks
  questions like "what do we know about X". Provides progressive disclosure and
  enhanced iterative search with synthesis.
name: search
user-invocable: true
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# Mnemonic Search Skill

Search and filtering for mnemonic memories.

## Trigger Phrases

- "search memories", "find in memories", "grep memories", "search mnemonic"
- "deep search memories", "comprehensive memory search", "synthesize knowledge about"

---

## Core Search Patterns

### By Namespace

```bash
rg "^namespace: _semantic/decisions" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```

### By Tag

```bash
# Single tag
rg -l "^  - architecture" ${MNEMONIC_ROOT}/ --glob "*.memory.md"

# Multiple tags (AND)
rg -l "^  - architecture" ${MNEMONIC_ROOT}/ --glob "*.memory.md" | xargs rg -l "^  - database"
```

### By Type

```bash
rg "^type: semantic" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
rg "^type: episodic" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
rg "^type: procedural" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```

### By Date

```bash
rg "^created: 2026-01" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```

### By Title

```bash
rg -i '^title: ".*auth.*"' ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```

### By Confidence

```bash
rg "confidence: 0\.9" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```

### Full-Text

```bash
rg -i "search term" ${MNEMONIC_ROOT}/ --glob "*.memory.md"
```

### Combined: Namespace + Text

```bash
rg "database" ${MNEMONIC_ROOT} --path "*/_semantic/decisions/" --glob "*.memory.md"
```

### Recent Files

```bash
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime -7
```

---

## Progressive Disclosure Protocol

Always start at Level 1. Expand only if needed.

| Level | What | How |
|-------|------|-----|
| 1 (start here) | Titles only | `rg -l "pattern" ${MNEMONIC_ROOT}/ --glob "*.memory.md"` then extract `^title:` |
| 2 | Frontmatter + summary | Read first ~50 lines of matched files |
| 3 | Full detail | Read entire memory file |

---

## Semantic Search (requires qmd)

If `@tobilu/qmd` is installed (see `/mnemonic:qmd-setup`):

```bash
# BM25 keyword search (ranked)
qmd search "authentication middleware" -n 10

# Semantic vector search (meaning-based)
qmd vsearch "how do we handle user sessions" -n 10

# Hybrid search (BM25 + vector combined)
qmd query "authentication patterns" -n 10

# Scope to collection
qmd search "auth" -c mnemonic-zircote
```

| Tool | Best For | Requires |
|------|----------|----------|
| `rg` | Exact strings, regex, frontmatter fields | Nothing |
| `qmd search` | Ranked keyword search, typo-tolerant | `qmd update` |
| `qmd vsearch` | Conceptual/meaning-based queries | `qmd embed` |
| `qmd query` | Best overall recall, combines both | Both |

After adding memories, run `/mnemonic:qmd-reindex` to update indexes.

---

## Enhanced Search (Iterative with Synthesis)

For complex or multi-faceted queries:

1. **Initial search** with user's query
2. **Analyze results** for gaps
3. **Iterative refinement** (up to 3 rounds via Task tool with `mnemonic-search-subcall` agent)
4. **Synthesize** findings into a coherent answer with source citations

Use when queries span multiple namespaces or need comprehensive coverage.

### Output Format

```markdown
## Synthesized Answer
{Answer drawing from all found memories}

### Sources
| Memory | Namespace | Relevance |
|--------|-----------|-----------|
| [[memory-id]] title | namespace | High/Medium |

### Gaps
- {Topics where no memories were found}
```

