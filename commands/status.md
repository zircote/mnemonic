---
name: status
allowed-tools:
- Bash
- Read
- Glob
- Grep
- Write
description: Show mnemonic system status and statistics
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:status

Display status and statistics for the mnemonic memory system.

## Procedure

### Step 1: Detect Context and Resolve Paths

```bash
# Resolve MNEMONIC_ROOT from config
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    RAW_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '~/.claude/mnemonic'))")
    MNEMONIC_ROOT="${RAW_PATH/#\~/$HOME}"
else
    MNEMONIC_ROOT="$HOME/.claude/mnemonic"
fi

# Organization from git remote
ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"

# Project from git remote, then toplevel, then cwd
PROJECT=$(git remote get-url origin 2>/dev/null | sed 's|\.git$||' | sed 's|.*/||')
[ -z "$PROJECT" ] && PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")

PROJECT_DIR="$MNEMONIC_ROOT/$ORG/$PROJECT"
```

### Step 2: Check Installation

```bash
echo "=== Mnemonic Status ==="
echo ""

echo "  Configuration:"
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    echo "    Config: ~/.config/mnemonic/config.json"
    echo "    Store:  $MNEMONIC_ROOT"
else
    echo "    Config: NOT FOUND (using default)"
    echo "    Store:  $MNEMONIC_ROOT"
fi
echo "    Organization: $ORG"
echo "    Project: $PROJECT"
echo ""

# Check directories
echo "  Directories:"
if [ -d "$MNEMONIC_ROOT" ]; then
    echo "    ✓ Memory store: $MNEMONIC_ROOT/"
else
    echo "    ✗ Memory store: NOT FOUND"
fi

if [ -d "$MNEMONIC_ROOT/$ORG" ]; then
    echo "    ✓ Org directory: $MNEMONIC_ROOT/$ORG/"
else
    echo "    ✗ Org directory: NOT FOUND"
fi

if [ -d "$PROJECT_DIR" ]; then
    echo "    ✓ Project directory: $PROJECT_DIR/"
else
    echo "    ✗ Project directory: NOT FOUND"
fi
echo ""
```

### Step 3: Git Status

```bash
echo "  Version Control:"
if [ -d "$MNEMONIC_ROOT/.git" ]; then
    cd "$MNEMONIC_ROOT"
    BRANCH=$(git branch --show-current 2>/dev/null)
    COMMITS=$(git rev-list --count HEAD 2>/dev/null)
    UNCOMMITTED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
    cd - > /dev/null

    STATUS="✓ Git initialized ($BRANCH, $COMMITS commits"
    [ "$UNCOMMITTED" -gt 0 ] && STATUS="$STATUS, $UNCOMMITTED uncommitted"
    STATUS="$STATUS)"
    echo "    $STATUS"
else
    echo "    ✗ Git: NOT INITIALIZED"
fi
echo ""
```

### Step 4: Memory Counts

```bash
echo "  Memory Counts:"

# Count by cognitive type with sub-namespace breakdown
for type in _semantic _episodic _procedural; do
    TYPE_TOTAL=$(find "$MNEMONIC_ROOT" -path "*/$type/*" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
    DETAILS=""
    for ns in $(find "$MNEMONIC_ROOT" -path "*/$type/*" -name "*.memory.md" 2>/dev/null | \
                sed "s|.*/$type/||" | sed 's|/.*||' | sort -u); do
        count=$(find "$MNEMONIC_ROOT" -path "*/$type/$ns/*" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
        [ -n "$DETAILS" ] && DETAILS="$DETAILS, "
        DETAILS="$DETAILS$ns: $count"
    done
    [ -n "$DETAILS" ] && echo "    $type: $TYPE_TOTAL  ($DETAILS)" || echo "    $type: $TYPE_TOTAL"
done

TOTAL=$(find "$MNEMONIC_ROOT" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
echo "    TOTAL: $TOTAL"
echo ""
```

### Step 5: Recent Activity

```bash
echo "  Recent: $(find "$MNEMONIC_ROOT" -name "*.memory.md" -mtime -7 2>/dev/null | wc -l | tr -d ' ') memories modified in last 7 days"
echo ""
```

### Step 6: Blackboard Status

```bash
echo "  Blackboard:"
BB_MSG=""
if [ -d "$MNEMONIC_ROOT/.blackboard" ]; then
    BB_FILES=$(ls "$MNEMONIC_ROOT/.blackboard"/*.md 2>/dev/null | wc -l | tr -d ' ')
    BB_MSG="$BB_FILES global topic files"
else
    BB_MSG="No global blackboard"
fi

if [ -d "$PROJECT_DIR/.blackboard" ]; then
    PBB_FILES=$(ls "$PROJECT_DIR/.blackboard"/*.md 2>/dev/null | wc -l | tr -d ' ')
    BB_MSG="$BB_MSG | $PBB_FILES project topic files"
else
    BB_MSG="$BB_MSG | No project blackboard"
fi
echo "    $BB_MSG"
echo ""
```

### Step 7: CLAUDE.md Status

```bash
echo "  CLAUDE.md:"
if grep -q "Mnemonic" "$HOME/.claude/CLAUDE.md" 2>/dev/null; then
    echo "    ✓ Configured"
else
    echo "    ✗ mnemonic section missing"
fi
echo ""
```

### Step 8: Health Summary

```bash
ISSUES=0

[ ! -d "$MNEMONIC_ROOT" ] && echo "  ⚠ Memory store directory missing" && ISSUES=$((ISSUES + 1))
[ ! -d "$MNEMONIC_ROOT/.git" ] && echo "  ⚠ Git not initialized" && ISSUES=$((ISSUES + 1))
[ -n "$UNCOMMITTED" ] && [ "$UNCOMMITTED" -gt 10 ] && echo "  ⚠ Many uncommitted changes ($UNCOMMITTED)" && ISSUES=$((ISSUES + 1))
[ ! -f "$HOME/.config/mnemonic/config.json" ] && echo "  ⚠ No config file (using defaults)" && ISSUES=$((ISSUES + 1))

if [ $ISSUES -eq 0 ]; then
    echo "  Health: ✓ All systems healthy"
else
    echo ""
    echo "  Run /mnemonic:setup to fix issues"
fi
```

## Output

Displays:
- Configuration (config path, store path, org, project)
- Directory status (store, org, project — all under unified ${MNEMONIC_ROOT})
- Git status (branch, commits, uncommitted)
- Memory counts by cognitive type and namespace
- Recent activity
- Blackboard status (global and project)
- CLAUDE.md configuration status
- Health summary
