---
name: mnemonic-search
description: Advanced search and filtering techniques for mnemonic memories
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Mnemonic Search Skill

Advanced search and filtering techniques for mnemonic memories.

## Trigger Phrases

- "search memories"
- "find in memories"
- "grep memories"
- "ripgrep mnemonic"
- "look for memory"
- "search mnemonic"

## Overview

This skill teaches comprehensive search patterns using ripgrep, grep, find, and other Unix tools to locate and filter memories efficiently.

---

## Frontmatter Search

Memories use YAML frontmatter. Search specific fields:

### Extract YAML Block

```bash
# Get just the frontmatter
sed -n '/^---$/,/^---$/p' /path/to/memory.memory.md

# Or using awk
awk '/^---$/{p=!p; print; next} p' /path/to/memory.memory.md
```

### Search by Namespace

```bash
# Find all decisions
rg "^namespace: semantic/decisions" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
rg "^namespace: semantic/decisions" ./.claude/mnemonic/ --glob "*.memory.md" -l

# Find project-scoped only
rg "^namespace: .*/project" ./.claude/mnemonic/ --glob "*.memory.md" -l

# Find user-scoped only
rg "^namespace: .*/user" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Tag

```bash
# Single tag (in YAML list format)
rg -l "^  - architecture" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Multiple tags (AND - both must exist in file)
rg -l "^  - architecture" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" | xargs rg -l "^  - database"

# Tag containing substring
rg -l "^  - auth" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"
```

### Search by Type

```bash
# Find semantic memories (facts, concepts)
rg "^type: semantic" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Find episodic memories (events, experiences)
rg "^type: episodic" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Find procedural memories (processes, workflows)
rg "^type: procedural" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Date

```bash
# Created in January 2026
rg "^created: 2026-01" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Created in specific date range
rg "^created: 2026-01-(1[5-9]|2[0-9]|3[01])" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Modified recently
rg "^modified: 2026-01-2" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Title

```bash
# Exact phrase in title
rg '^title: ".*PostgreSQL.*"' ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Case-insensitive title search
rg -i '^title: ".*auth.*"' ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Confidence

```bash
# High confidence memories (0.9+)
rg "confidence: 0\.9" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Lower confidence (might need review)
rg "confidence: 0\.[0-7]" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Citations

```bash
# Find all memories with citations
rg -l "^citations:" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Find memories by citation type
rg "type: paper" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
rg "type: documentation" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
rg "type: github" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Find memories citing specific domain
rg "url: https://arxiv.org" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
rg "url: https://docs.python.org" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Find memories by citation author
rg "author: \"Smith" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l

# Find high-relevance citations
rg "relevance: 0\.9" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

---

## Full-Text Search

### Basic Search

```bash
# Simple pattern
rg "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Case-insensitive
rg -i "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Whole word only
rg -w "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"
```

### With Context

```bash
# 3 lines before and after match
rg -C3 "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# 5 lines after (useful for finding related content)
rg -A5 "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# 2 lines before (useful for finding headers)
rg -B2 "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"
```

### Regex Patterns

```bash
# Function names
rg "function\s+\w+" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# URLs
rg "https?://[^\s]+" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# File paths
rg "src/[^\s]+" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Version numbers
rg "\d+\.\d+\.\d+" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"
```

### Files Only (No Content)

```bash
# Just list matching files
rg -l "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Count matches per file
rg -c "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"
```

---

## Combined Filters

### Namespace + Text

```bash
# Decisions about databases
rg "database" ~/.claude/mnemonic/*/decisions/ ./.claude/mnemonic/decisions/project/ --glob "*.memory.md"

# Learnings about testing
rg "test" ~/.claude/mnemonic/*/learnings/ ./.claude/mnemonic/learnings/project/ --glob "*.memory.md"

# Project patterns only
rg "pattern" ./.claude/mnemonic/patterns/project/ --glob "*.memory.md"
```

### Recent + Text

```bash
# Files modified in last 7 days containing "api"
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7 -exec rg -l "api" {} \;

# Files modified today
find ~/.claude/mnemonic -name "*.memory.md" -mtime 0 -exec rg -l "pattern" {} \;
```

### Type + Namespace

```bash
# Episodic memories in blockers (incident reports)
rg -l "^type: episodic" ~/.claude/mnemonic/*/blockers/ ./.claude/mnemonic/blockers/project/ --glob "*.memory.md"

# Procedural memories in patterns (workflows)
rg -l "^type: procedural" ~/.claude/mnemonic/*/patterns/ ./.claude/mnemonic/patterns/project/ --glob "*.memory.md"
```

### Tag + Text

```bash
# Memories tagged "security" mentioning "password"
for f in $(rg -l "^  - security" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"); do
    rg -l "password" "$f" 2>/dev/null
done
```

---

## Compressed Recall

### Snippet (Minimal - Titles Only)

```bash
# List all memory titles
for f in ~/.claude/mnemonic/**/*.memory.md; do
    title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/^title: "//' | sed 's/"$//')
    [ -n "$title" ] && echo "$title"
done
```

### Summary (Frontmatter + First Section)

```bash
# Get frontmatter plus first 10 content lines
head -50 /path/to/memory.memory.md
```

### Structured Summary

```bash
# Extract key fields for quick review
for f in ~/.claude/mnemonic/**/*.memory.md; do
    echo "=== $(basename "$f") ==="
    grep -E "^(id|type|namespace|title|created):" "$f" | head -5
    echo ""
done
```

### Full Recall

```bash
# Complete memory content
cat /path/to/memory.memory.md
```

---

## Performance Tips

### Narrow File Set First

```bash
# Use find to limit scope, then search
find ~/.claude/mnemonic/*/decisions -name "*.memory.md" | xargs rg "pattern"

# Or use directory restriction
rg "pattern" ~/.claude/mnemonic/*/decisions/ ./.claude/mnemonic/decisions/project/ --glob "*.memory.md"
```

### Limit Output

```bash
# First 10 matches only
rg "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" | head -10

# First matching file only
rg -l "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" | head -1
```

### Use File List Mode

```bash
# Get file list first
FILES=$(rg -l "pattern" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md")

# Then read specific files
for f in $FILES; do
    head -30 "$f"
done
```

### Parallel Search

```bash
# Search multiple namespaces in parallel
rg "pattern" ~/.claude/mnemonic/*/decisions/ ./.claude/mnemonic/decisions/project/ --glob "*.memory.md" &
rg "pattern" ~/.claude/mnemonic/*/learnings/ ./.claude/mnemonic/learnings/project/ --glob "*.memory.md" &
wait
```

---

## Examples

### Find All Decisions About Authentication

```bash
echo "=== Auth Decisions ==="
rg -i "auth" ~/.claude/mnemonic/*/decisions/ ./.claude/mnemonic/decisions/project/ --glob "*.memory.md" -l
rg -i "auth" ./.claude/mnemonic/decisions/project/ --glob "*.memory.md" -l
```

### Recent Learnings in Current Project

```bash
echo "=== Recent Project Learnings ==="
find ./.claude/mnemonic/learnings/project -name "*.memory.md" -mtime -7 -exec basename {} \;
```

### Episodic Memories From Last Week

```bash
echo "=== Last Week's Events ==="
for f in $(find ~/.claude/mnemonic/*/episodic -name "*.memory.md" -mtime -7 2>/dev/null); do
    grep "^title:" "$f" | sed 's/^title: "//' | sed 's/"$//'
done
```

### High-Confidence Security Memories

```bash
echo "=== Trusted Security Knowledge ==="
for f in $(rg -l "confidence: 0\.9" ~/.claude/mnemonic/*/security/ ./.claude/mnemonic/security/project/ --glob "*.memory.md" 2>/dev/null); do
    grep "^title:" "$f"
done
```

### Code References in Memories

```bash
echo "=== Memories With Code Refs ==="
rg -l "^code_refs:" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Find memories referencing specific file
rg "file: src/auth" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Memories With Relationships

```bash
echo "=== Linked Memories ==="
rg "\[\[" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

---

## Search Cheat Sheet

| Goal | Command |
|------|---------|
| All decisions | `rg "^namespace: semantic/decisions" ~/.claude/mnemonic/ ./.claude/mnemonic/ -l` |
| By tag | `rg -l "^  - tagname" ~/.claude/mnemonic/ ./.claude/mnemonic/` |
| By type | `rg "^type: semantic" ~/.claude/mnemonic/ ./.claude/mnemonic/ -l` |
| Full-text | `rg -i "search term" ~/.claude/mnemonic/ ./.claude/mnemonic/` |
| Recent files | `find ~/.claude/mnemonic -mtime -7` |
| Titles only | `rg "^title:" ~/.claude/mnemonic/ ./.claude/mnemonic/` |
| High confidence | `rg "confidence: 0\.9" ~/.claude/mnemonic/ ./.claude/mnemonic/ -l` |
| With code refs | `rg "^code_refs:" ~/.claude/mnemonic/ ./.claude/mnemonic/ -l` |
| With citations | `rg "^citations:" ~/.claude/mnemonic/ ./.claude/mnemonic/ -l` |
| Citation type | `rg "type: paper" ~/.claude/mnemonic/ ./.claude/mnemonic/ -l` |
| Citation domain | `rg "url: https://arxiv.org" ~/.claude/mnemonic/ ./.claude/mnemonic/ -l` |
| Project only | `rg "pattern" ./.claude/mnemonic/` |

---

## Structured Queries with mnemonic-query

For complex frontmatter queries, use `mnemonic-query` which leverages `yq` for proper YAML parsing.

### Basic Structured Queries

```bash
# Find all semantic memories
mnemonic-query --type semantic

# Find by tag
mnemonic-query --tag architecture

# Find by namespace pattern
mnemonic-query --namespace "decisions/*"

# Combine filters (AND logic)
mnemonic-query --type semantic --tag architecture
```

### Comparison Operators

```bash
# Greater than
mnemonic-query --confidence ">0.8"

# Greater or equal
mnemonic-query --confidence ">=0.9"

# Less than
mnemonic-query --confidence "<0.5"

# Less or equal
mnemonic-query --confidence "<=0.7"

# Not equal
mnemonic-query --type "!=episodic"
```

### Range Queries

```bash
# Confidence range (inclusive)
mnemonic-query --confidence "0.7..0.9"

# Date range
mnemonic-query --created "2026-01-01..2026-01-31"

# Modified date range
mnemonic-query --modified "2026-01-15..2026-01-31"
```

### Output Formats

```bash
# File paths (default)
mnemonic-query --type semantic

# Titles only
mnemonic-query --type semantic --format titles

# JSON with full metadata
mnemonic-query --type semantic --format json

# Count only
mnemonic-query --type semantic --format count
```

### Combining with Content Search

The real power comes from combining structured queries with rg:

```bash
# Find security decisions mentioning passwords
mnemonic-query --namespace "semantic/decisions" --tag security | xargs rg "password"

# Find high-confidence memories about authentication
mnemonic-query --confidence ">0.8" | xargs rg -i "auth"

# Search recent memories for specific content
mnemonic-query --created ">2026-01-01" | xargs rg "api"

# Find memories by type and search content
mnemonic-query --type procedural | xargs rg "step"
```

### Structured Query Cheat Sheet

| Goal | Command |
|------|---------|
| By type | `mnemonic-query --type semantic` |
| By tag | `mnemonic-query --tag architecture` |
| By namespace | `mnemonic-query --namespace "decisions/*"` |
| High confidence | `mnemonic-query --confidence ">0.8"` |
| Confidence range | `mnemonic-query --confidence "0.7..0.9"` |
| Recent memories | `mnemonic-query --created ">2026-01-01"` |
| Not episodic | `mnemonic-query --type "!=episodic"` |
| Combined filters | `mnemonic-query --type semantic --tag security` |
| Pipe to rg | `mnemonic-query --tag api \| xargs rg "endpoint"` |
