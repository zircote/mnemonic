---
description: Show mnemonic system status and statistics
allowed-tools:
  - Bash
  - Read
  - Glob
---

# /mnemonic:status

Display status and statistics for the mnemonic memory system.

## Procedure

### Step 1: Detect Context

```bash
ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"

PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")
```

### Step 2: Check Installation

```bash
echo "=== Mnemonic Status ==="
echo ""

echo "Configuration:"
echo "  Organization: $ORG"
echo "  Project: $PROJECT"
echo ""

# Check directories
echo "Directories:"
if [ -d "$HOME/.claude/mnemonic" ]; then
    echo "  ✓ User mnemonic: ~/.claude/mnemonic/"
else
    echo "  ✗ User mnemonic: NOT FOUND"
fi

if [ -d "./.claude/mnemonic" ]; then
    echo "  ✓ Project mnemonic:"
else
    echo "  ✗ Project mnemonic: NOT FOUND"
fi
echo ""
```

### Step 3: Git Status

```bash
echo "Version Control:"
if [ -d "$HOME/.claude/mnemonic/.git" ]; then
    cd "$HOME/.claude/mnemonic"
    BRANCH=$(git branch --show-current 2>/dev/null)
    COMMITS=$(git rev-list --count HEAD 2>/dev/null)
    UNCOMMITTED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
    cd - > /dev/null

    echo "  ✓ Git initialized"
    echo "    Branch: $BRANCH"
    echo "    Commits: $COMMITS"
    echo "    Uncommitted changes: $UNCOMMITTED"
else
    echo "  ✗ Git: NOT INITIALIZED"
fi
echo ""
```

### Step 4: Memory Counts

```bash
echo "Memory Counts (User-level):"
TOTAL_USER=0
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    count=$(find "$HOME/.claude/mnemonic/$ORG/$ns" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
    TOTAL_USER=$((TOTAL_USER + count))
    [ "$count" -gt 0 ] && echo "  $ns: $count"
done
echo "  TOTAL: $TOTAL_USER"
echo ""

echo "Memory Counts (Project-level):"
TOTAL_PROJECT=0
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    count=$(find "~/.claude/mnemonic/$ns" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
    TOTAL_PROJECT=$((TOTAL_PROJECT + count))
    [ "$count" -gt 0 ] && echo "  $ns: $count"
done
echo "  TOTAL: $TOTAL_PROJECT"
echo ""
```

### Step 5: Recent Activity

```bash
echo "Recent Captures (last 7 days):"
RECENT=$(find "$HOME/.claude/mnemonic" "./.claude/mnemonic" -name "*.memory.md" -mtime -7 2>/dev/null | wc -l | tr -d ' ')
echo "  Count: $RECENT"
echo ""

echo "Latest Memories:"
find "$HOME/.claude/mnemonic" "./.claude/mnemonic" -name "*.memory.md" -mtime -7 2>/dev/null | \
    while read f; do
        title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/^title: "//' | sed 's/"$//')
        mtime=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$f" 2>/dev/null || stat -c "%y" "$f" 2>/dev/null | cut -d'.' -f1)
        echo "  [$mtime] $title"
    done | head -5
echo ""
```

### Step 6: Type Distribution

```bash
echo "Memory Types:"
SEMANTIC=$(rg -l "^type: semantic" "$HOME/.claude/mnemonic" "./.claude/mnemonic" --glob "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
EPISODIC=$(rg -l "^type: episodic" "$HOME/.claude/mnemonic" "./.claude/mnemonic" --glob "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
PROCEDURAL=$(rg -l "^type: procedural" "$HOME/.claude/mnemonic" "./.claude/mnemonic" --glob "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')

echo "  Semantic: $SEMANTIC"
echo "  Episodic: $EPISODIC"
echo "  Procedural: $PROCEDURAL"
echo ""
```

### Step 7: Blackboard Status

```bash
echo "Blackboard:"
if [ -d "$HOME/.claude/mnemonic/.blackboard" ]; then
    BB_FILES=$(ls "$HOME/.claude/mnemonic/.blackboard"/*.md 2>/dev/null | wc -l | tr -d ' ')
    echo "  Global: $BB_FILES topic files"
    ls "$HOME/.claude/mnemonic/.blackboard"/*.md 2>/dev/null | while read f; do
        echo "    - $(basename "$f")"
    done
else
    echo "  Global: NOT FOUND"
fi

if [ -d "~/.claude/mnemonic/.blackboard" ]; then
    BB_FILES=$(ls "~/.claude/mnemonic/.blackboard"/*.md 2>/dev/null | wc -l | tr -d ' ')
    echo "  Project: $BB_FILES topic files"
else
    echo "  Project: NOT FOUND"
fi
echo ""
```

### Step 8: CLAUDE.md Status

```bash
echo "CLAUDE.md Configuration:"
if grep -q "Mnemonic Memory System" "$HOME/.claude/CLAUDE.md" 2>/dev/null; then
    echo "  ✓ User CLAUDE.md configured"
else
    echo "  ✗ User CLAUDE.md: mnemonic section missing"
fi

if grep -q "Mnemonic - Project Memory" "./CLAUDE.md" 2>/dev/null; then
    echo "  ✓ Project CLAUDE.md configured"
else
    echo "  ✗ Project CLAUDE.md: mnemonic section missing"
fi
echo ""
```

### Step 9: Health Summary

```bash
echo "=== Health Summary ==="
ISSUES=0

[ ! -d "$HOME/.claude/mnemonic" ] && echo "  ⚠ User mnemonic directory missing" && ISSUES=$((ISSUES + 1))
[ ! -d "$HOME/.claude/mnemonic/.git" ] && echo "  ⚠ Git not initialized" && ISSUES=$((ISSUES + 1))
[ "$UNCOMMITTED" -gt 10 ] && echo "  ⚠ Many uncommitted changes ($UNCOMMITTED)" && ISSUES=$((ISSUES + 1))

if [ $ISSUES -eq 0 ]; then
    echo "  ✓ All systems healthy"
else
    echo ""
    echo "  Run /mnemonic:setup to fix issues"
fi
```

## Output

Displays:
- Configuration (org, project)
- Directory status
- Git status (branch, commits, uncommitted)
- Memory counts by namespace
- Recent activity
- Type distribution
- Blackboard status
- CLAUDE.md configuration status
- Health summary
