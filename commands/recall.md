---
name: recall
allowed-tools:
- Bash
- Read
- Grep
- Glob
- Write
argument-hint: '[query] [--namespace ns] [--tags tag1,tag2] [--since 7d] [--type semantic|episodic|procedural]
  [--scope project|org|all]'
description: Recall memories with filtering and search
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:recall

Search and recall memories from the mnemonic filesystem.

## Arguments

- `[query]` - Optional search term for full-text search
- `--namespace` - Filter by namespace (_semantic/decisions, _semantic/knowledge, _semantic/entities, _episodic/incidents, _episodic/sessions, _episodic/blockers, _procedural/runbooks, _procedural/patterns, _procedural/migrations)
- `--tags` - Filter by tags (comma-separated)
- `--since` - Time filter (7d, 30d, 90d, 1y)
- `--type` - Filter by cognitive type (semantic, episodic, procedural)
- `--scope` - project, org, or all (default: all)
- `--limit` - Maximum results (default: 10)
- `--full` - Show full memory content instead of summary

## Procedure

### Step 1: Parse Arguments

```bash
QUERY="${1:-}"
NAMESPACE="${NAMESPACE:-}"
TAGS="${TAGS:-}"
SINCE="${SINCE:-}"
TYPE="${TYPE:-}"
SCOPE="${SCOPE:-all}"
LIMIT="${LIMIT:-10}"
FULL="${FULL:-false}"

ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"
```

### Step 2: Build Search Paths

```bash
# Resolve MNEMONIC_ROOT from config
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    RAW_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '~/.claude/mnemonic'))")
    MNEMONIC_ROOT="${RAW_PATH/#\~/$HOME}"
else
    MNEMONIC_ROOT="$HOME/.claude/mnemonic"
fi
SEARCH_PATHS=""

# Get project name from git remote or directory
PROJECT=$(git remote get-url origin 2>/dev/null | sed 's|\.git$||' | sed 's|.*/||')
[ -z "$PROJECT" ] && PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")

# All memories are under ${MNEMONIC_ROOT}/
# Path structure:
#   {org}/{project}/ - project-specific memories
#   {org}/ - org-wide memories (shared across projects)
#   default/ - fallback when org detection fails
case "$SCOPE" in
    project)
        SEARCH_PATHS="$MNEMONIC_ROOT/$ORG/$PROJECT"
        ;;
    org)
        SEARCH_PATHS="$MNEMONIC_ROOT/$ORG"
        ;;
    all|*)
        # Search project-specific, then org-wide, then default
        SEARCH_PATHS="$MNEMONIC_ROOT/$ORG/$PROJECT $MNEMONIC_ROOT/$ORG $MNEMONIC_ROOT/default"
        ;;
esac

# Narrow by namespace if specified
if [ -n "$NAMESPACE" ]; then
    NEW_PATHS=""
    for path in $SEARCH_PATHS; do
        NEW_PATHS="$NEW_PATHS $path/$NAMESPACE"
    done
    SEARCH_PATHS="$NEW_PATHS"
fi
```

### Step 3: Apply Filters

#### Time Filter

```bash
if [ -n "$SINCE" ]; then
    case "$SINCE" in
        7d)  MTIME="-mtime -7" ;;
        30d) MTIME="-mtime -30" ;;
        90d) MTIME="-mtime -90" ;;
        1y)  MTIME="-mtime -365" ;;
        *)   MTIME="" ;;
    esac
fi
```

#### Type Filter

```bash
if [ -n "$TYPE" ]; then
    TYPE_PATTERN="^type: $TYPE"
fi
```

#### Tag Filter

```bash
if [ -n "$TAGS" ]; then
    # Convert to pattern for each tag
    TAG_PATTERNS=""
    for tag in $(echo "$TAGS" | tr ',' ' '); do
        TAG_PATTERNS="$TAG_PATTERNS -e '^  - $tag'"
    done
fi
```

### Step 4: Execute Search

#### Full-Text Search (if query provided)

```bash
if [ -n "$QUERY" ]; then
    echo "=== Searching for: $QUERY ==="
    for path in $SEARCH_PATHS; do
        rg -i -l "$QUERY" "$path" --glob "*.memory.md" 2>/dev/null
    done | head -n "$LIMIT"
fi
```

#### Frontmatter-Based Search

```bash
# Find matching files
FILES=""
for path in $SEARCH_PATHS; do
    if [ -n "$MTIME" ]; then
        FILES="$FILES $(find "$path" -name "*.memory.md" $MTIME 2>/dev/null)"
    else
        FILES="$FILES $(find "$path" -name "*.memory.md" 2>/dev/null)"
    fi
done

# Apply type filter
if [ -n "$TYPE_PATTERN" ]; then
    FILES=$(echo "$FILES" | xargs -I{} sh -c "rg -q '$TYPE_PATTERN' '{}' && echo '{}'" 2>/dev/null)
fi

# Apply tag filter
if [ -n "$TAG_PATTERNS" ]; then
    for tag in $(echo "$TAGS" | tr ',' ' '); do
        FILES=$(echo "$FILES" | xargs -I{} sh -c "rg -q '^  - $tag' '{}' && echo '{}'" 2>/dev/null)
    done
fi
```

### Step 5: Format Output

#### Summary Mode (default)

```bash
echo "=== Recalled Memories ==="
count=0
for f in $FILES; do
    [ $count -ge $LIMIT ] && break

    title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/^title: "//' | sed 's/"$//')
    ns=$(grep "^namespace:" "$f" 2>/dev/null | head -1 | sed 's/^namespace: //')
    type=$(grep "^type:" "$f" 2>/dev/null | head -1 | sed 's/^type: //')
    created=$(grep "^created:" "$f" 2>/dev/null | head -1 | sed 's/^created: //')

    echo ""
    echo "[$type] $title"
    echo "  Namespace: $ns"
    echo "  Created: $created"
    echo "  File: $f"

    count=$((count + 1))
done

echo ""
echo "Found $count memories"
```

#### Full Mode

```bash
if [ "$FULL" = "true" ]; then
    for f in $FILES; do
        [ $count -ge $LIMIT ] && break
        echo "=========================================="
        cat "$f"
        echo ""
        count=$((count + 1))
    done
fi
```

## Example Usage

```bash
# Full-text search
/mnemonic:recall authentication

# Filter by namespace
/mnemonic:recall --namespace _semantic/decisions

# Recent knowledge
/mnemonic:recall --namespace _semantic/knowledge --since 7d

# Tagged memories
/mnemonic:recall --tags architecture,database

# Episodic memories only
/mnemonic:recall --type episodic

# Combine filters
/mnemonic:recall auth --namespace _semantic/knowledge --since 30d --type semantic
```

## Output

Display for each matching memory:
- Memory type indicator
- Title
- Namespace
- Created date
- File path
- (Full mode: complete content)

Total count at end.
