# CLI Usage Guide

Access and manage mnemonic memories using standard Unix command-line tools. No AI assistant required.

## Overview

Mnemonic memories are plain Markdown files with YAML frontmatter stored in predictable filesystem locations. This makes them fully accessible with standard CLI tools like `rg` (ripgrep), `find`, `grep`, `cat`, and `git`.

## Memory Locations

```bash
# User-level memories (cross-project)
~/.claude/mnemonic/{org}/{namespace}/{scope}/*.memory.md

# Project-level memories
./.claude/mnemonic/{namespace}/{scope}/*.memory.md
```

**Namespaces:** apis, blockers, context, decisions, learnings, patterns, security, testing, episodic

**Scopes:** user, project

## Searching Memories

### Full-Text Search with ripgrep

```bash
# Search all memories for a keyword
rg "postgresql" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md"

# Case-insensitive search
rg -i "authentication" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md"

# Search with context (3 lines before/after)
rg -C3 "api endpoint" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md"

# List files only (no content)
rg -l "database" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md"

# Search in specific namespace
rg "pattern" ~/.claude/mnemonic/*/decisions ./.claude/mnemonic/decisions/project --glob "*.memory.md"

# Search project-level only
rg "bug fix" ./.claude/mnemonic --glob "*.memory.md"
```

### Search by Frontmatter Fields

```bash
# Find all semantic memories
rg "^type: semantic" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md" -l

# Find memories with specific tag
rg "^  - architecture" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md" -l

# Find memories from a date range
rg "^created: 2026-01" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md" -l

# Find high-confidence memories
rg "confidence: 0.9" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md" -l

# Find memories by title
rg "^title:.*PostgreSQL" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md" -l
```

### Using find for File Operations

```bash
# List all memories
find ~/.claude/mnemonic -name "*.memory.md"

# Find memories modified in last 7 days
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7

# Find memories older than 90 days
find ~/.claude/mnemonic -name "*.memory.md" -mtime +90

# Count memories by namespace
find ~/.claude/mnemonic -name "*.memory.md" | grep -o '/[^/]*/project\|/[^/]*/user' | sort | uniq -c
```

## Reading Memories

### View a Memory

```bash
# Read full memory
cat ~/.claude/mnemonic/zircote/decisions/project/550e8400-*.memory.md

# View just the title
grep "^title:" ~/.claude/mnemonic/zircote/decisions/project/*.memory.md

# View frontmatter only (between --- markers)
sed -n '/^---$/,/^---$/p' path/to/memory.memory.md

# View content only (after frontmatter)
sed '1,/^---$/d;/^---$/,$!d;/^---$/d' path/to/memory.memory.md
```

### Extract Specific Fields

```bash
# Get all memory IDs
grep "^id:" ~/.claude/mnemonic/**/*.memory.md | cut -d: -f3 | tr -d ' '

# Get all unique tags
rg "^  - " ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md" -o | sort -u

# List all titles
grep "^title:" ~/.claude/mnemonic/**/*.memory.md | sed 's/.*title: "//' | sed 's/"$//'
```

## Creating Memories

### Using a Template

```bash
# Generate UUID
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')

# Generate timestamp
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create memory file
cat > ~/.claude/mnemonic/myorg/decisions/project/${UUID}-my-decision.memory.md << EOF
---
id: ${UUID}
type: semantic
namespace: decisions/project
created: ${DATE}
modified: ${DATE}
title: "My Decision Title"
tags:
  - architecture
  - database
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: manual
  agent: cli
  confidence: 0.9
---

# My Decision Title

Description of the decision.

## Rationale

Why this decision was made.
EOF
```

### Quick Capture Script

Save as `~/bin/mnemonic-capture`:

```bash
#!/bin/bash
set -e

NAMESPACE="${1:?Usage: mnemonic-capture <namespace> <title>}"
TITLE="${2:?Usage: mnemonic-capture <namespace> <title>}"

ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' || echo "default")
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 50)

MEMORY_DIR="$HOME/.claude/mnemonic/$ORG/$NAMESPACE/user"
mkdir -p "$MEMORY_DIR"
MEMORY_FILE="$MEMORY_DIR/${UUID}-${SLUG}.memory.md"

cat > "$MEMORY_FILE" << EOF
---
id: ${UUID}
type: semantic
namespace: ${NAMESPACE}/user
created: ${DATE}
modified: ${DATE}
title: "${TITLE}"
tags:
  - manual
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: manual
  agent: cli
  confidence: 0.9
---

# ${TITLE}

EOF

# Open in editor
${EDITOR:-vim} "$MEMORY_FILE"

echo "Created: $MEMORY_FILE"
```

Usage:
```bash
chmod +x ~/bin/mnemonic-capture
mnemonic-capture decisions "Use Redis for caching"
```

## Managing Memories

### Git Operations

```bash
# View memory history
cd ~/.claude/mnemonic && git log --oneline

# View changes to a specific memory
git log -p -- path/to/memory.memory.md

# Blame a memory (who wrote what)
git blame path/to/memory.memory.md

# Revert a memory to previous version
git checkout HEAD~1 -- path/to/memory.memory.md

# Commit changes
git add -A && git commit -m "Update: memory description"
```

### Backup and Sync

```bash
# Backup all memories
tar -czf mnemonic-backup-$(date +%Y%m%d).tar.gz ~/.claude/mnemonic

# Sync to remote (after setting up remote)
cd ~/.claude/mnemonic
git remote add origin git@github.com:user/mnemonic-memories.git
git push -u origin main

# Clone on new machine
git clone git@github.com:user/mnemonic-memories.git ~/.claude/mnemonic
```

### Cleanup Operations

```bash
# Find memories older than 1 year
find ~/.claude/mnemonic -name "*.memory.md" -mtime +365

# Find empty or small memories (< 100 bytes)
find ~/.claude/mnemonic -name "*.memory.md" -size -100c

# Count memories by type
rg "^type:" ~/.claude/mnemonic ./.claude/mnemonic --glob "*.memory.md" -o | cut -d: -f2 | sort | uniq -c

# Find duplicate titles
grep "^title:" ~/.claude/mnemonic/**/*.memory.md | cut -d: -f3- | sort | uniq -d
```

## Validation

### Validate Memory Format

```bash
# Check for required fields
validate_memory() {
    local file="$1"
    local errors=0

    grep -q "^id:" "$file" || { echo "Missing: id"; errors=1; }
    grep -q "^type:" "$file" || { echo "Missing: type"; errors=1; }
    grep -q "^namespace:" "$file" || { echo "Missing: namespace"; errors=1; }
    grep -q "^created:" "$file" || { echo "Missing: created"; errors=1; }
    grep -q "^title:" "$file" || { echo "Missing: title"; errors=1; }

    return $errors
}

# Validate all memories
for f in ~/.claude/mnemonic/**/*.memory.md; do
    echo "Checking: $f"
    validate_memory "$f" || echo "  INVALID"
done
```

### Use the Validation Tool

```bash
# Validate all memories (from mnemonic repo)
python tools/mnemonic-validate ~/.claude/mnemonic

# Validate with JSON output
python tools/mnemonic-validate --format json ~/.claude/mnemonic

# Validate only changed files
python tools/mnemonic-validate --changed ~/.claude/mnemonic
```

## Useful Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Quick search
alias ms='rg -i --glob "*.memory.md" ~/.claude/mnemonic'

# List recent memories
alias mrecent='find ~/.claude/mnemonic -name "*.memory.md" -mtime -7 -exec grep -l "." {} \;'

# Count memories
alias mcount='find ~/.claude/mnemonic -name "*.memory.md" | wc -l'

# Open memory directory
alias mdir='cd ~/.claude/mnemonic && ls'

# Search by namespace
mns() {
    rg -i "$1" ~/.claude/mnemonic/*/"$2" ./.claude/mnemonic/"$2"/project --glob "*.memory.md"
}
# Usage: mns "pattern" decisions
```

## Integration with Other Tools

### Structured Queries with yq

For structured frontmatter queries, use the `mnemonic-query` tool which leverages `yq` for proper YAML parsing:

```bash
# Install yq (required)
brew install yq       # macOS
apt install yq        # Ubuntu/Debian
pip install yq        # Python

# Basic queries
mnemonic-query --type semantic
mnemonic-query --tag architecture
mnemonic-query --namespace "decisions/*"

# Comparison operators
mnemonic-query --confidence ">0.8"
mnemonic-query --confidence ">=0.9"
mnemonic-query --confidence "<0.5"

# Range queries
mnemonic-query --confidence "0.7..0.9"
mnemonic-query --created "2026-01-01..2026-01-31"

# Inequality
mnemonic-query --type "!=episodic"

# Combine filters (AND)
mnemonic-query --type semantic --tag architecture --confidence ">0.8"

# Pipe to content search
mnemonic-query --tag security | xargs rg "password"
```

#### Query Operators

| Operator | Example | Description |
|----------|---------|-------------|
| `=` (implicit) | `--confidence 0.9` | Exact match |
| `!=` | `--type "!=episodic"` | Not equal |
| `>` | `--confidence ">0.8"` | Greater than |
| `>=` | `--confidence ">=0.9"` | Greater or equal |
| `<` | `--confidence "<0.5"` | Less than |
| `<=` | `--confidence "<=0.7"` | Less or equal |
| `..` | `--confidence "0.7..0.9"` | Range (inclusive) |

#### Output Formats

```bash
# File paths (default)
mnemonic-query --type semantic

# Titles only
mnemonic-query --type semantic --format titles

# JSON with full metadata
mnemonic-query --type semantic --format json

# Count only
mnemonic-query --type semantic --format count

# Limit results
mnemonic-query --type semantic --limit 10
```

### Raw yq for Manual YAML Parsing

```bash
# Extract frontmatter as JSON
sed -n '/^---$/,/^---$/p' memory.memory.md | yq -o=json

# Query specific fields
sed -n '/^---$/,/^---$/p' memory.memory.md | yq '.tags[]'

# Extract confidence value
sed -n '/^---$/,/^---$/p' memory.memory.md | yq '.provenance.confidence'

# Check if tag exists
sed -n '/^---$/,/^---$/p' memory.memory.md | yq '.tags | contains(["security"])'
```

### Generate Reports

```bash
# Memory summary report
echo "# Memory Report - $(date +%Y-%m-%d)"
echo ""
echo "## Counts by Namespace"
find ~/.claude/mnemonic -name "*.memory.md" | \
    sed 's|.*/\([^/]*\)/[^/]*/[^/]*$|\1|' | sort | uniq -c | sort -rn

echo ""
echo "## Recent Activity (7 days)"
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7 -exec grep "^title:" {} \;
```

### Watch for Changes

```bash
# Monitor memory directory for changes (requires fswatch)
fswatch -o ~/.claude/mnemonic | while read; do
    echo "Memory change detected at $(date)"
done
```

## Troubleshooting

### Common Issues

**"No memories found"**
```bash
# Check if directory exists
ls -la ~/.claude/mnemonic

# Check organization detection
git remote get-url origin | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|'
```

**"ripgrep not found"**
```bash
# Install ripgrep
brew install ripgrep    # macOS
apt install ripgrep     # Ubuntu/Debian
```

**"Git not initialized"**
```bash
cd ~/.claude/mnemonic
git init
git add .
git commit -m "Initialize mnemonic"
```

## See Also

- [Architecture](architecture.md) - System design overview
- [Validation](validation.md) - MIF schema validation
- [Agent Coordination](agent-coordination.md) - Multi-agent patterns
