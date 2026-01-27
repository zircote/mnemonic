<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->


# Recall Workflow

Complete workflow for searching and retrieving memories.

## Quick Recall (Frontmatter Only)

```bash
# List memories in a namespace
ls -la ~/.claude/mnemonic/*/decisions/user/*.memory.md 2>/dev/null
ls -la_semantic/decisions/*.memory.md 2>/dev/null

# Get titles from frontmatter
for f in ~/.claude/mnemonic/*/decisions/**/*.memory.md; do
    grep "^title:" "$f" 2>/dev/null | head -1
done
```

## Search by Tag

```bash
# Find memories with specific tag
rg -l "^  - architecture" ~/.claude/mnemonic/ --glob "*.memory.md"
rg -l "^  - architecture" --glob "*.memory.md"
```

## Search by Date Range

```bash
# Recent memories (last 7 days)
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7
find ./.claude/mnemonic -name "*.memory.md" -mtime -7

# By created date in frontmatter
rg "^created: 2026-01" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

## Search by Cognitive Type

```bash
# Find all episodic memories
rg "^type: episodic" ~/.claude/mnemonic/ --glob "*.memory.md" -l
rg "^type: episodic" --glob "*.memory.md" -l
```

## Full-Text Search

```bash
# Case-insensitive search
rg -i "postgresql" ~/.claude/mnemonic/ --glob "*.memory.md"
rg -i "postgresql" --glob "*.memory.md"

# With context lines
rg -i -C3 "postgresql" ~/.claude/mnemonic/ --glob "*.memory.md"
```

## Tiered Recall

**Snippet (minimal context):**
```bash
# Just frontmatter
head -20 /path/to/memory.memory.md | sed -n '/^---$/,/^---$/p'
```

**Summary (frontmatter + first section):**
```bash
# First 50 lines
head -50 /path/to/memory.memory.md
```

**Full (complete memory):**
```bash
# Entire file
cat /path/to/memory.memory.md
```
