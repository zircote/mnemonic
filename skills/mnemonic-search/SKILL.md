---
allowed-tools:
- Bash
- Read
- Glob
- Grep
- Write
description: >
  This skill should be used when the user says "search memories", "find in memories",
  "grep mnemonic", "look for memory", or asks questions like "what do we know about X".
  Provides progressive disclosure: Level 1 (titles), Level 2 (frontmatter + summary),
  Level 3 (full content). Start at Level 1 and expand only if needed.
name: mnemonic-search
user-invocable: true
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

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
rg "^namespace: _semantic/decisions" ~/.claude/mnemonic/ --glob "*.memory.md" -l
rg "^namespace: _semantic/decisions" --glob "*.memory.md" -l

# Find project-scoped only
rg "^namespace: .*/project" --glob "*.memory.md" -l

# Find user-scoped only
rg "^namespace: .*/user" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Tag

```bash
# Single tag (in YAML list format)
rg -l "^  - architecture" ~/.claude/mnemonic/ --glob "*.memory.md"

# Multiple tags (AND - both must exist in file)
rg -l "^  - architecture" ~/.claude/mnemonic/ --glob "*.memory.md" | xargs rg -l "^  - database"

# Tag containing substring
rg -l "^  - auth" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Search by Type

```bash
# Find semantic memories (facts, concepts)
rg "^type: semantic" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Find episodic memories (events, experiences)
rg "^type: episodic" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Find procedural memories (processes, workflows)
rg "^type: procedural" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Date

```bash
# Created in January 2026
rg "^created: 2026-01" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Created in specific date range
rg "^created: 2026-01-(1[5-9]|2[0-9]|3[01])" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Modified recently
rg "^modified: 2026-01-2" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Title

```bash
# Exact phrase in title
rg '^title: ".*PostgreSQL.*"' ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Case-insensitive title search
rg -i '^title: ".*auth.*"' ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Confidence

```bash
# High confidence memories (0.9+)
rg "confidence: 0\.9" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Lower confidence (might need review)
rg "confidence: 0\.[0-7]" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Citations

```bash
# Find all memories with citations
rg -l "^citations:" ~/.claude/mnemonic/ --glob "*.memory.md"

# Find memories by citation type
rg "type: paper" ~/.claude/mnemonic/ --glob "*.memory.md" -l
rg "type: documentation" ~/.claude/mnemonic/ --glob "*.memory.md" -l
rg "type: github" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Find memories citing specific domain
rg "url: https://arxiv.org" ~/.claude/mnemonic/ --glob "*.memory.md" -l
rg "url: https://docs.python.org" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Find memories by citation author
rg "author: \"Smith" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Find high-relevance citations
rg "relevance: 0\.9" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

---

## Full-Text Search

### Basic Search

```bash
# Simple pattern
rg "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"

# Case-insensitive
rg -i "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"

# Whole word only
rg -w "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### With Context

```bash
# 3 lines before and after match
rg -C3 "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"

# 5 lines after (useful for finding related content)
rg -A5 "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"

# 2 lines before (useful for finding headers)
rg -B2 "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Regex Patterns

```bash
# Function names
rg "function\s+\w+" ~/.claude/mnemonic/ --glob "*.memory.md"

# URLs
rg "https?://[^\s]+" ~/.claude/mnemonic/ --glob "*.memory.md"

# File paths
rg "src/[^\s]+" ~/.claude/mnemonic/ --glob "*.memory.md"

# Version numbers
rg "\d+\.\d+\.\d+" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Files Only (No Content)

```bash
# Just list matching files
rg -l "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"

# Count matches per file
rg -c "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"
```

---

## Combined Filters

### Namespace + Text

```bash
# Decisions about databases
rg "database" ~/.claude/mnemonic --path "*/_semantic/decisions/" --glob "*.memory.md"

# Knowledge about testing
rg "test" ~/.claude/mnemonic --path "*/_semantic/knowledge/" --glob "*.memory.md"

# Project patterns only
rg "pattern" ~/.claude/mnemonic --path "*/_procedural/patterns/" --glob "*.memory.md"
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
rg -l "^type: episodic" ~/.claude/mnemonic --path "*/_episodic/blockers/" --glob "*.memory.md"

# Procedural memories in patterns (workflows)
rg -l "^type: procedural" ~/.claude/mnemonic --path "*/_procedural/patterns/" --glob "*.memory.md"
```

### Tag + Text

```bash
# Memories tagged "security" mentioning "password"
for f in $(rg -l "^  - security" ~/.claude/mnemonic/ --glob "*.memory.md"); do
    rg -l "password" "$f" 2>/dev/null
done
```

---

## Progressive Disclosure Levels

### Level 1: Quick Answer (Titles Only)

```bash
# List all memory titles
for f in ~/.claude/mnemonic/**/*.memory.md; do
    title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/^title: "//' | sed 's/"$//')
    [ -n "$title" ] && echo "$title"
done
```

### Level 2: Context (Frontmatter + First Section)

```bash
# Get frontmatter plus first 10 content lines
head -50 /path/to/memory.memory.md
```

### Structured Summary (Key Fields)

```bash
# Extract key fields for quick review
for f in ~/.claude/mnemonic/**/*.memory.md; do
    echo "=== $(basename "$f") ==="
    grep -E "^(id|type|namespace|title|created):" "$f" | head -5
    echo ""
done
```

### Level 3: Full Detail

```bash
# Complete memory content
cat /path/to/memory.memory.md
```

---

## Performance Tips

### Narrow File Set First

```bash
# Use find to limit scope, then search
find ~/.claude/mnemonic -path "*/_semantic/decisions/*" -name "*.memory.md" | xargs rg "pattern"

# Or use directory restriction
rg "pattern" ~/.claude/mnemonic --path "*/_semantic/decisions/" --glob "*.memory.md"
```

### Limit Output

```bash
# First 10 matches only
rg "pattern" ~/.claude/mnemonic/ --glob "*.memory.md" | head -10

# First matching file only
rg -l "pattern" ~/.claude/mnemonic/ --glob "*.memory.md" | head -1
```

### Use File List Mode

```bash
# Get file list first
FILES=$(rg -l "pattern" ~/.claude/mnemonic/ --glob "*.memory.md")

# Then read specific files
for f in $FILES; do
    head -30 "$f"
done
```

### Parallel Search

```bash
# Search multiple namespaces in parallel
rg "pattern" ~/.claude/mnemonic --path "*/_semantic/decisions/" --glob "*.memory.md" &
rg "pattern" ~/.claude/mnemonic --path "*/_semantic/knowledge/" --glob "*.memory.md" &
wait
```

---

## Examples

### Find All Decisions About Authentication

```bash
echo "=== Auth Decisions ==="
rg -i "auth" ~/.claude/mnemonic --path "*/_semantic/decisions/" --glob "*.memory.md" -l
```

### Recent Knowledge in Current Project

```bash
echo "=== Recent Project Knowledge ==="
find ~/.claude/mnemonic -path "*/_semantic/knowledge/*" -name "*.memory.md" -mtime -7 -exec basename {} \;
```

### Episodic Memories From Last Week

```bash
echo "=== Last Week's Events ==="
for f in $(find ~/.claude/mnemonic -path "*/_episodic/*" -name "*.memory.md" -mtime -7 2>/dev/null); do
    grep "^title:" "$f" | sed 's/^title: "//' | sed 's/"$//'
done
```

### High-Confidence Security Knowledge

```bash
echo "=== Trusted Security Knowledge ==="
for f in $(rg -l "confidence: 0\.9" ~/.claude/mnemonic --path "*/_semantic/knowledge/" --glob "*.memory.md" 2>/dev/null); do
    grep "^title:" "$f"
done
```

### Code References in Memories

```bash
echo "=== Memories With Code Refs ==="
rg -l "^code_refs:" ~/.claude/mnemonic/ --glob "*.memory.md"

# Find memories referencing specific file
rg "file: src/auth" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

### Memories With Relationships

```bash
echo "=== Linked Memories ==="
rg "\[\[" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

---

## Search Cheat Sheet

| Goal | Command |
|------|---------|
| All decisions | `rg "^namespace: _semantic/decisions" ~/.claude/mnemonic/ -l` |
| By tag | `rg -l "^  - tagname" ~/.claude/mnemonic/` |
| By type | `rg "^type: semantic" ~/.claude/mnemonic/ -l` |
| Full-text | `rg -i "search term" ~/.claude/mnemonic/` |
| Recent files | `find ~/.claude/mnemonic -mtime -7` |
| Titles only | `rg "^title:" ~/.claude/mnemonic/` |
| High confidence | `rg "confidence: 0\.9" ~/.claude/mnemonic/ -l` |
| With code refs | `rg "^code_refs:" ~/.claude/mnemonic/ -l` |
| With citations | `rg "^citations:" ~/.claude/mnemonic/ -l` |
| Citation type | `rg "type: paper" ~/.claude/mnemonic/ -l` |
| Citation domain | `rg "url: https://arxiv.org" ~/.claude/mnemonic/ -l` |
| Project only | `rg "pattern"` |

---

## Progressive Disclosure Protocol

When searching memories, use progressive disclosure to minimize context usage:

### Level 1: Quick Answer (Titles Only) - START HERE

```bash
# List matching files first
rg -l "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"

# Then get titles
for f in $(rg -l "pattern" ~/.claude/mnemonic/ --glob "*.memory.md"); do
    grep "^title:" "$f" | head -1
done
```

### Level 2: Context (Frontmatter + Summary)

Only expand to Level 2 if Level 1 titles aren't sufficient:

```bash
# Get frontmatter plus first 10 content lines
head -50 /path/to/memory.memory.md
```

### Level 3: Full Detail

Only use full read when absolutely necessary:

```bash
cat /path/to/memory.memory.md
```

**Always start at Level 1. Expand only if needed.**
