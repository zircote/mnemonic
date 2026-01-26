---
name: mnemonic-organization
description: Memory organization including directory structure, namespaces, and garbage collection
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Mnemonic Organization Skill

Directory structure, namespaces, maintenance, and garbage collection.

## Trigger Phrases

- "organize memories"
- "memory structure"
- "namespaces"
- "memory cleanup"
- "mnemonic organization"
- "memory maintenance"

## Overview

This skill covers the organizational structure of mnemonic, including directory layouts, namespace conventions, org/project detection, and maintenance operations.

---

## Directory Structure

### User-Level Storage

Location: `~/.claude/mnemonic/{org}/`

```
~/.claude/mnemonic/
├── {org}/                    # Organization (from git remote)
│   ├── apis/
│   │   ├── user/             # Personal API knowledge
│   │   └── project/          # Synced from projects
│   ├── blockers/
│   │   ├── user/
│   │   └── project/
│   ├── context/
│   │   ├── user/
│   │   └── project/
│   ├── decisions/
│   │   ├── user/
│   │   └── project/
│   ├── learnings/
│   │   ├── user/
│   │   └── project/
│   ├── patterns/
│   │   ├── user/
│   │   └── project/
│   ├── security/
│   │   ├── user/
│   │   └── project/
│   ├── testing/
│   │   ├── user/
│   │   └── project/
│   └── episodic/
│       ├── user/
│       └── project/
├── .blackboard/              # Global cross-session coordination
├── .git/                     # Version control
└── .gitignore
```

### Project-Level Storage

Location: `./.claude/mnemonic/`

```
./.claude/mnemonic/
├── apis/
│   └── project/
├── blockers/
│   └── project/
├── context/
│   └── project/
├── decisions/
│   └── project/
├── learnings/
│   └── project/
├── patterns/
│   └── project/
├── security/
│   └── project/
├── testing/
│   └── project/
├── episodic/
│   └── project/
└── .blackboard/              # Project-specific coordination
```

---

## Namespace Reference

### Core Namespaces

| Namespace | Purpose | Examples |
|-----------|---------|----------|
| `apis/` | API documentation, contracts, endpoints | REST specs, GraphQL schemas |
| `blockers/` | Issues, impediments, incidents | Bug reports, outages, blockers |
| `context/` | Background information, environment state | Project setup, configurations |
| `decisions/` | Architectural choices with rationale | "We chose X because Y" |
| `learnings/` | Insights, discoveries, TILs | "Learned that X works better" |
| `patterns/` | Code conventions, best practices | "Always use factory pattern for..." |
| `security/` | Security policies, vulnerabilities | Auth requirements, CVEs |
| `testing/` | Test strategies, edge cases | Test plans, coverage notes |
| `episodic/` | General events, experiences | Debug sessions, meetings |

### Scope Selection

| Scope | Location | Use Case |
|-------|----------|----------|
| user | `~/.claude/mnemonic/{org}/{namespace}/` | Personal knowledge, cross-project |
| project | `./.claude/mnemonic/{namespace}/` | Specific to current codebase |

**Scope is implicit from base path** - no `/user/` or `/project/` subdirectories needed.

**Guidelines:**
- Use `user` scope for reusable knowledge (personal patterns, general learnings)
- Use `project` scope for codebase-specific information (architecture decisions, local patterns)

---

## Organization Detection

### Detect Org from Git Remote

```bash
# Extract org from remote URL
# Handles: git@github.com:org/repo.git, https://github.com/org/repo.git

ORG=$(git remote get-url origin 2>/dev/null | \
      sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | \
      sed 's|\.git$||')

# Fallback to "default" if no remote
[ -z "$ORG" ] && ORG="default"

echo "Organization: $ORG"
```

### Detect Project from Git Root

```bash
# Get project name from git root directory
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)

# Fallback to current directory name
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")

echo "Project: $PROJECT"
```

### Full Context Detection

```bash
#!/bin/bash
# detect_context.sh - Get org, project, and paths

# Organization
ORG=$(git remote get-url origin 2>/dev/null | \
      sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | \
      sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"

# Project
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")

# Paths
USER_MNEMONIC="$HOME/.claude/mnemonic/$ORG"
PROJECT_MNEMONIC="./.claude/mnemonic"

echo "ORG=$ORG"
echo "PROJECT=$PROJECT"
echo "USER_MNEMONIC=$USER_MNEMONIC"
echo "PROJECT_MNEMONIC=$PROJECT_MNEMONIC"
```

---

## Blackboard

The blackboard is a shared coordination space for cross-session communication.

### Location

- Global: `~/.claude/mnemonic/.blackboard/`
- Project: `./.claude/mnemonic/.blackboard/`

### Structure

One markdown file per topic:

```
.blackboard/
├── active-tasks.md
├── pending-decisions.md
├── shared-context.md
└── session-notes.md
```

### Write to Blackboard

```bash
# Append entry with session info
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat >> ~/.claude/mnemonic/.blackboard/active-tasks.md << EOF

---
## Session: $SESSION_ID
**Time:** $TIMESTAMP

- Task 1: Description
- Task 2: Description

EOF
```

### Read from Blackboard

```bash
# Recent entries
tail -50 ~/.claude/mnemonic/.blackboard/active-tasks.md

# Entries from specific session
grep -A20 "Session: $SESSION_ID" ~/.claude/mnemonic/.blackboard/active-tasks.md
```

### Topic Conventions

| File | Purpose |
|------|---------|
| `active-tasks.md` | Current work items |
| `pending-decisions.md` | Decisions awaiting input |
| `shared-context.md` | Background for all sessions |
| `session-notes.md` | Handoff notes between sessions |
| `blockers.md` | Known impediments |

---

## Git Versioning

### Initialize Repository

```bash
cd ~/.claude/mnemonic

# Initialize if needed
[ ! -d .git ] && git init

# Configure gitignore
cat > .gitignore << 'EOF'
*.lock
.blackboard/*.tmp
*.swp
*~
.DS_Store
EOF

# Initial commit
git add -A
git commit -m "Initialize mnemonic memory system"
```

### Commit Changes

```bash
cd ~/.claude/mnemonic
git add -A
git commit -m "Memory update: $(date +%Y-%m-%d)"
```

### View History

```bash
cd ~/.claude/mnemonic

# Recent commits
git log --oneline -20

# Changes to specific memory
git log --oneline -- "*/decisions/*auth*.memory.md"

# Show specific version
git show HEAD~3:zircote/decisions/project/abc123-use-jwt.memory.md
```

### Restore Previous Version

```bash
cd ~/.claude/mnemonic

# Restore specific file from history
git checkout HEAD~1 -- zircote/decisions/project/abc123-use-jwt.memory.md

# Or restore and commit
git checkout <commit-hash> -- path/to/memory.memory.md
git commit -m "Restore: memory title"
```

---

## Garbage Collection

### Find Expired Memories (TTL)

```bash
# Current timestamp for comparison
NOW=$(date +%s)

# Find memories with ttl field
for f in ~/.claude/mnemonic/**/*.memory.md; do
    TTL=$(grep "^  ttl:" "$f" 2>/dev/null | sed 's/.*ttl: //')
    CREATED=$(grep "^created:" "$f" 2>/dev/null | sed 's/created: //')

    if [ -n "$TTL" ] && [ -n "$CREATED" ]; then
        # Parse and check expiry (simplified - real impl needs date math)
        echo "Check: $f (TTL: $TTL, Created: $CREATED)"
    fi
done
```

### Apply Decay Model

```bash
# Update decay strength based on last access
# strength = initial * (0.5 ^ (days_since_access / half_life_days))

for f in ~/.claude/mnemonic/**/*.memory.md; do
    LAST_ACCESS=$(grep "last_accessed:" "$f" 2>/dev/null | sed 's/.*last_accessed: //')
    HALF_LIFE=$(grep "half_life:" "$f" 2>/dev/null | sed 's/.*half_life: //')

    if [ -n "$LAST_ACCESS" ]; then
        echo "Decay check: $f"
        # Calculate new strength and update file
    fi
done
```

### Archive Low-Relevance Memories

```bash
# Move memories with strength < 0.2 to archive
ARCHIVE_DIR=~/.claude/mnemonic/.archive/$(date +%Y-%m)
mkdir -p "$ARCHIVE_DIR"

for f in ~/.claude/mnemonic/**/*.memory.md; do
    STRENGTH=$(grep "strength:" "$f" 2>/dev/null | sed 's/.*strength: //')
    if [ -n "$STRENGTH" ]; then
        # Compare strength (bash can't do float comparison easily)
        if python3 -c "exit(0 if $STRENGTH < 0.2 else 1)" 2>/dev/null; then
            mv "$f" "$ARCHIVE_DIR/"
            echo "Archived: $f"
        fi
    fi
done
```

### Delete Expired

```bash
# Find and delete truly expired memories (past TTL + grace period)
find ~/.claude/mnemonic -name "*.memory.md" -mtime +365 -type f

# Dry run
find ~/.claude/mnemonic -name "*.memory.md" -mtime +365 -type f -exec echo "Would delete: {}" \;

# Actual delete (with confirmation)
find ~/.claude/mnemonic -name "*.memory.md" -mtime +365 -type f -exec rm -i {} \;
```

---

## Conflict Detection

### Find Similar Memories

```bash
# Search for memories with similar titles
TITLE="authentication"
rg -i "^title:.*$TITLE" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Detect Contradictions

```bash
# Find memories that might conflict
# Look for opposite patterns in same namespace

# Example: Find all auth decisions
AUTH_DECISIONS=$(rg -l "auth" ~/.claude/mnemonic/*/decisions/ ./.claude/mnemonic/decisions/project/ --glob "*.memory.md")

echo "Review these for potential conflicts:"
for f in $AUTH_DECISIONS; do
    grep "^title:" "$f"
done
```

### Mark Conflict in Memory

```yaml
conflicts:
  - memory_id: xyz789
    resolution: merged
    resolved_at: 2026-01-23T12:00:00Z
```

### Resolution Strategies

| Strategy | When to Use |
|----------|-------------|
| `merged` | Combined information from both |
| `invalidated` | Marked conflicting memory as outdated |
| `skipped` | Kept existing, ignored new |

---

## Maintenance Commands

### Health Check

```bash
#!/bin/bash
echo "=== Mnemonic Health Check ==="

# Directory exists
test -d ~/.claude/mnemonic && echo "✓ User mnemonic exists" || echo "✗ User mnemonic missing"
test -d ./.claude/mnemonic && echo "✓ Project mnemonic exists" || echo "✗ Project mnemonic missing"

# Git status
cd ~/.claude/mnemonic
git status --short 2>/dev/null || echo "✗ Git not initialized"
cd - > /dev/null

# Memory counts
echo ""
echo "=== Memory Counts ==="
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    count=$(find ~/.claude/mnemonic/*/$ns -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
    echo "$ns: $count"
done

# Recent activity
echo ""
echo "=== Recent Captures (7 days) ==="
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7 2>/dev/null | wc -l | tr -d ' '
```

### Rebuild Index (if needed)

```bash
# Generate manifest of all memories
cat > ~/.claude/mnemonic/.manifest.json << 'EOF'
{
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "memories": [
EOF

first=true
for f in ~/.claude/mnemonic/**/*.memory.md; do
    id=$(grep "^id:" "$f" | sed 's/id: //')
    title=$(grep "^title:" "$f" | sed 's/title: "//' | sed 's/"$//')
    ns=$(grep "^namespace:" "$f" | sed 's/namespace: //')

    [ "$first" = true ] && first=false || echo "," >> ~/.claude/mnemonic/.manifest.json
    echo "    {\"id\": \"$id\", \"title\": \"$title\", \"namespace\": \"$ns\", \"file\": \"$f\"}" >> ~/.claude/mnemonic/.manifest.json
done

echo "  ]" >> ~/.claude/mnemonic/.manifest.json
echo "}" >> ~/.claude/mnemonic/.manifest.json
```

### Validate Memories

```bash
# Check all memories have required fields
for f in ~/.claude/mnemonic/**/*.memory.md; do
    VALID=true
    grep -q "^id:" "$f" || VALID=false
    grep -q "^type:" "$f" || VALID=false
    grep -q "^namespace:" "$f" || VALID=false
    grep -q "^created:" "$f" || VALID=false
    grep -q "^title:" "$f" || VALID=false

    [ "$VALID" = false ] && echo "Invalid: $f"
done
```
