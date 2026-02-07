---
name: search
allowed-tools:
- Bash
- Read
- Grep
- Glob
- Write
argument-hint: <pattern> [--namespace ns] [--context 3] [--files-only]
description: Full-text search across all memories
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:search

Direct ripgrep search across mnemonic memories.

## Arguments

- `<pattern>` - Required. Search pattern (supports regex)
- `--namespace` - Limit search to specific namespace
- `--context` - Lines of context around matches (default: 0)
- `--files-only` - Only list matching file paths
- `--case-sensitive` - Case-sensitive search (default: case-insensitive)
- `--scope` - user, project, or all (default: all)

## Procedure

### Step 1: Parse Arguments

```bash
PATTERN="${1:?Error: Pattern required}"
NAMESPACE="${NAMESPACE:-}"
CONTEXT="${CONTEXT:-0}"
FILES_ONLY="${FILES_ONLY:-false}"
CASE_SENSITIVE="${CASE_SENSITIVE:-false}"
SCOPE="${SCOPE:-all}"

ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"
```

### Step 2: Build Search Command

```bash
# Base command
RG_CMD="rg"

# Case sensitivity
[ "$CASE_SENSITIVE" = "false" ] && RG_CMD="$RG_CMD -i"

# Context lines
[ "$CONTEXT" -gt 0 ] && RG_CMD="$RG_CMD -C$CONTEXT"

# Files only
[ "$FILES_ONLY" = "true" ] && RG_CMD="$RG_CMD -l"

# File pattern
RG_CMD="$RG_CMD --glob '*.memory.md'"
```

### Step 3: Determine Search Paths

```bash
# Resolve MNEMONIC_ROOT from config
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    RAW_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '~/.claude/mnemonic'))")
    MNEMONIC_ROOT="${RAW_PATH/#\~/$HOME}"
else
    MNEMONIC_ROOT="$HOME/.claude/mnemonic"
fi
SEARCH_PATHS=""

case "$SCOPE" in
    user)
        SEARCH_PATHS="$MNEMONIC_ROOT/$ORG"
        ;;
    project)
        SEARCH_PATHS="$MNEMONIC_ROOT"
        ;;
    all|*)
        SEARCH_PATHS="$MNEMONIC_ROOT/$ORG $MNEMONIC_ROOT"
        ;;
esac

# Narrow by namespace
if [ -n "$NAMESPACE" ]; then
    NEW_PATHS=""
    for path in $SEARCH_PATHS; do
        [ -d "$path/$NAMESPACE" ] && NEW_PATHS="$NEW_PATHS $path/$NAMESPACE"
    done
    SEARCH_PATHS="$NEW_PATHS"
fi
```

### Step 4: Execute Search

```bash
echo "=== Searching: $PATTERN ==="
echo ""

for path in $SEARCH_PATHS; do
    if [ -d "$path" ]; then
        if [ "$FILES_ONLY" = "true" ]; then
            rg $([[ "$CASE_SENSITIVE" = "false" ]] && echo "-i") -l "$PATTERN" "$path" --glob "*.memory.md" 2>/dev/null
        else
            rg $([[ "$CASE_SENSITIVE" = "false" ]] && echo "-i") $([[ "$CONTEXT" -gt 0 ]] && echo "-C$CONTEXT") "$PATTERN" "$path" --glob "*.memory.md" 2>/dev/null
        fi
    fi
done
```

### Step 5: Count Results

```bash
echo ""
MATCH_COUNT=$(rg -i -l "$PATTERN" $SEARCH_PATHS --glob "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
echo "Found matches in $MATCH_COUNT files"
```

## Example Usage

```bash
# Simple search
/mnemonic:search postgresql

# Case-sensitive
/mnemonic:search PostgreSQL --case-sensitive

# With context
/mnemonic:search "authentication" --context 3

# Files only
/mnemonic:search jwt --files-only

# In specific namespace
/mnemonic:search api --namespace decisions

# Project only
/mnemonic:search bug --scope project

# Regex pattern
/mnemonic:search "function\s+\w+Auth"
```

## Output

For default mode:
- File path and line number
- Matching line content
- Context lines (if specified)

For files-only mode:
- List of file paths

Total match count at end.

## Advanced Patterns

```bash
# Find function references
/mnemonic:search "function\s+\w+"

# Find URLs
/mnemonic:search "https?://[^\s]+"

# Find file paths
/mnemonic:search "src/[^\s]+"

# Find version numbers
/mnemonic:search "\d+\.\d+\.\d+"

# Find TODO items
/mnemonic:search "TODO|FIXME|XXX"

# Find code blocks
/mnemonic:search '```\w+'
```
