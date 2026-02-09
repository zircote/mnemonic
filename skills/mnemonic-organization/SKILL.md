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


<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

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

All memories are stored under `${MNEMONIC_ROOT}/` with a unified path structure.

### Unified Storage Layout

```
${MNEMONIC_ROOT}/
├── default/                           # Fallback when org detection fails
│   └── {namespace}/                   # Cognitive namespaces
├── {org}/                             # Organization-level
│   ├── _semantic/                     # Org-wide facts/knowledge
│   │   ├── decisions/
│   │   ├── knowledge/
│   │   └── entities/
│   ├── _episodic/                     # Org-wide events
│   │   ├── incidents/
│   │   ├── sessions/
│   │   └── blockers/
│   ├── _procedural/                   # Org-wide procedures
│   │   ├── runbooks/
│   │   ├── patterns/
│   │   └── migrations/
│   └── {project}/                     # Project-specific memories
│       ├── _semantic/
│       │   ├── decisions/
│       │   ├── knowledge/
│       │   └── entities/
│       ├── _episodic/
│       │   ├── incidents/
│       │   ├── sessions/
│       │   └── blockers/
│       ├── _procedural/
│       │   ├── runbooks/
│       │   ├── patterns/
│       │   └── migrations/
│       └── .blackboard/               # Project session coordination
└── .git/                              # Version control
```

### Memory Scope Hierarchy

| Scope | Path | Use Case |
|-------|------|----------|
| Project | `{org}/{project}/{namespace}/` | Project-specific memories (default) |
| Organization | `{org}/{namespace}/` | Shared across projects in org |
| Default | `default/{namespace}/` | Fallback when org detection fails |

---

## Namespace Reference

### Cognitive Memory Types

| Type | Purpose | Examples |
|------|---------|----------|
| **Semantic** | Facts, concepts, specifications | API docs, decisions, config values |
| **Episodic** | Events, experiences, incidents | Debug sessions, deployments |
| **Procedural** | Processes, workflows, how-tos | Deployment steps, runbooks |

### Core Namespaces

| Namespace | Purpose | Memory Type |
|-----------|---------|-------------|
| `_semantic/decisions/` | Architectural choices with rationale | Semantic |
| `_semantic/knowledge/` | APIs, context, learnings, security | Semantic |
| `_semantic/entities/` | Entity definitions (technologies, components) | Semantic |
| `_episodic/incidents/` | Production issues, postmortems | Episodic |
| `_episodic/sessions/` | Debug sessions, work sessions | Episodic |
| `_episodic/blockers/` | Impediments, issues | Episodic |
| `_procedural/runbooks/` | Operational procedures | Procedural |
| `_procedural/patterns/` | Code conventions, testing strategies | Procedural |
| `_procedural/migrations/` | Migration steps, upgrade procedures | Procedural |

### Scope Selection

| Scope | Path | Use Case |
|-------|------|----------|
| project | `{org}/{project}/{namespace}/` | Project-specific (default) |
| org | `{org}/{namespace}/` | Shared across all projects in organization |

**Guidelines:**
- Use `project` scope for codebase-specific information (architecture decisions, local patterns)
- Use `org` scope for reusable knowledge (org-wide standards, shared patterns)

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
# Resolve MNEMONIC_ROOT from config
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    RAW_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '~/.claude/mnemonic'))")
    MNEMONIC_ROOT="${RAW_PATH/#\~/$HOME}"
else
    MNEMONIC_ROOT="$HOME/.claude/mnemonic"
fi
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
USER_MNEMONIC="$MNEMONIC_ROOT/$ORG"
PROJECT_MNEMONIC="$MNEMONIC_ROOT"

echo "ORG=$ORG"
echo "PROJECT=$PROJECT"
echo "USER_MNEMONIC=$USER_MNEMONIC"
echo "PROJECT_MNEMONIC=$PROJECT_MNEMONIC"
```

---

## Blackboard

The blackboard is a shared coordination space for cross-session communication.

### Location

- Project: `${MNEMONIC_ROOT}/{org}/{project}/.blackboard/`
- Organization: `${MNEMONIC_ROOT}/{org}/.blackboard/`

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

cat >> ${MNEMONIC_ROOT}/.blackboard/active-tasks.md << EOF

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
tail -50 ${MNEMONIC_ROOT}/.blackboard/active-tasks.md

# Entries from specific session
grep -A20 "Session: $SESSION_ID" ${MNEMONIC_ROOT}/.blackboard/active-tasks.md
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
cd ${MNEMONIC_ROOT}

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
cd ${MNEMONIC_ROOT}
git add -A
git commit -m "Memory update: $(date +%Y-%m-%d)"
```

### View History

```bash
cd ${MNEMONIC_ROOT}

# Recent commits
git log --oneline -20

# Changes to specific memory
git log --oneline -- "*/_semantic/decisions/*auth*.memory.md"

# Show specific version
git show HEAD~3:zircote/_semantic/decisions/abc123-use-jwt.memory.md
```

### Restore Previous Version

```bash
cd ${MNEMONIC_ROOT}

# Restore specific file from history
git checkout HEAD~1 -- zircote/_semantic/decisions/abc123-use-jwt.memory.md

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
for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
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

for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
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
ARCHIVE_DIR=${MNEMONIC_ROOT}/.archive/$(date +%Y-%m)
mkdir -p "$ARCHIVE_DIR"

for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
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
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime +365 -type f

# Dry run
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime +365 -type f -exec echo "Would delete: {}" \;

# Actual delete (with confirmation)
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime +365 -type f -exec rm -i {} \;
```

---

## Conflict Detection

### Find Similar Memories

```bash
# Search for memories with similar titles
TITLE="authentication"
rg -i "^title:.*$TITLE" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```

### Detect Contradictions

```bash
# Find memories that might conflict
# Look for opposite patterns in same namespace

# Example: Find all auth decisions
AUTH_DECISIONS=$(rg -l "auth" ${MNEMONIC_ROOT} --path "*/_semantic/decisions/" --glob "*.memory.md" 2>/dev/null)

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
test -d ${MNEMONIC_ROOT} && echo "✓ User mnemonic exists" || echo "✗ User mnemonic missing"

# Git status
cd ${MNEMONIC_ROOT}
git status --short 2>/dev/null || echo "✗ Git not initialized"
cd - > /dev/null

# Memory counts by cognitive type
echo ""
echo "=== Memory Counts by Type ==="
SEMANTIC=$(find ${MNEMONIC_ROOT} -path "*/_semantic/*" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
EPISODIC=$(find ${MNEMONIC_ROOT} -path "*/_episodic/*" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
PROCEDURAL=$(find ${MNEMONIC_ROOT} -path "*/_procedural/*" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
echo "_semantic: $SEMANTIC"
echo "_episodic: $EPISODIC"
echo "_procedural: $PROCEDURAL"

# Memory counts by namespace
echo ""
echo "=== Memory Counts by Namespace ==="
for ns in _semantic/decisions _semantic/knowledge _semantic/entities \
          _episodic/incidents _episodic/sessions _episodic/blockers \
          _procedural/runbooks _procedural/patterns _procedural/migrations; do
    count=$(find ${MNEMONIC_ROOT} -path "*/$ns/*" -name "*.memory.md" 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -gt 0 ] && echo "$ns: $count"
done

# Recent activity
echo ""
echo "=== Recent Captures (7 days) ==="
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime -7 2>/dev/null | wc -l | tr -d ' '
```

### Rebuild Index (if needed)

```bash
# Generate manifest of all memories
cat > ${MNEMONIC_ROOT}/.manifest.json << 'EOF'
{
  "generated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "memories": [
EOF

first=true
for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
    id=$(grep "^id:" "$f" | sed 's/id: //')
    title=$(grep "^title:" "$f" | sed 's/title: "//' | sed 's/"$//')
    ns=$(grep "^namespace:" "$f" | sed 's/namespace: //')

    [ "$first" = true ] && first=false || echo "," >> ${MNEMONIC_ROOT}/.manifest.json
    echo "    {\"id\": \"$id\", \"title\": \"$title\", \"namespace\": \"$ns\", \"file\": \"$f\"}" >> ${MNEMONIC_ROOT}/.manifest.json
done

echo "  ]" >> ${MNEMONIC_ROOT}/.manifest.json
echo "}" >> ${MNEMONIC_ROOT}/.manifest.json
```

### Validate Memories

```bash
# Check all memories have required fields
for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
    VALID=true
    grep -q "^id:" "$f" || VALID=false
    grep -q "^type:" "$f" || VALID=false
    grep -q "^namespace:" "$f" || VALID=false
    grep -q "^created:" "$f" || VALID=false
    grep -q "^title:" "$f" || VALID=false

    [ "$VALID" = false ] && echo "Invalid: $f"
done
```
