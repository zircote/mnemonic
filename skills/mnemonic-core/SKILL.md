---
name: mnemonic-core
description: Complete memory system operations including init, capture, recall, search, and status
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Mnemonic Core Skill

Complete memory system operations: init, capture, recall, search, status.

## Trigger Phrases

- "mnemonic"
- "memory system"
- "capture memory"
- "recall memory"
- "remember this"
- "what do we know about"

## Overview

Mnemonic is a pure filesystem-based memory system. All memories are stored as `.memory.md` files with YAML frontmatter following the MIF Level 3 specification.

### Directory Structure

**User-level** (`~/.claude/mnemonic/{org}/`):
```
~/.claude/mnemonic/{org}/
├── apis/user/           # API documentation, contracts
├── blockers/user/       # Issues, impediments
├── context/user/        # Background, state
├── decisions/user/      # Architectural choices
├── learnings/user/      # Insights, discoveries
├── patterns/user/       # Coding conventions
├── security/user/       # Policies, findings
├── testing/user/        # Strategies, edge cases
├── episodic/user/       # Events, experiences
└── .blackboard/         # Cross-session coordination
```

**Project-level** (`./.claude/mnemonic/`):
```
./.claude/mnemonic/
├── apis/project/
├── blockers/project/
├── context/project/
├── decisions/project/
├── learnings/project/
├── patterns/project/
├── security/project/
├── testing/project/
├── episodic/project/
└── .blackboard/
```

---

## Initialization

### Detect Organization

```bash
# From git remote origin
ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"
echo "Organization: $ORG"
```

### Detect Project

```bash
# From git root directory name
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")
echo "Project: $PROJECT"
```

### Create Directory Structure

```bash
ORG="${ORG:-default}"

# User-level
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    mkdir -p ~/.claude/mnemonic/"$ORG"/"$ns"/{user,project}
done
mkdir -p ~/.claude/mnemonic/.blackboard

# Project-level
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    mkdir -p ./.claude/mnemonic/"$ns"/project
done
mkdir -p ./.claude/mnemonic/.blackboard

# Initialize git if needed
if [ ! -d ~/.claude/mnemonic/.git ]; then
    cd ~/.claude/mnemonic && git init && cd -
    echo "*.lock" > ~/.claude/mnemonic/.gitignore
    echo ".blackboard/*.tmp" >> ~/.claude/mnemonic/.gitignore
fi
```

---

## Capture Workflow

### Step 1: Generate UUID

```bash
# macOS/Linux with uuidgen
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')

# Fallback to Python
[ -z "$UUID" ] && UUID=$(python3 -c "import uuid; print(uuid.uuid4())")

echo "Generated UUID: $UUID"
```

### Step 2: Determine Namespace and Scope

| Content Type | Namespace | Example |
|--------------|-----------|---------|
| API documentation | apis | REST endpoint specs |
| Problems/issues | blockers | Bug that blocked progress |
| Background info | context | Project setup, environment |
| Architectural choices | decisions | "We chose PostgreSQL because..." |
| Insights/discoveries | learnings | "TIL that X works better than Y" |
| Code conventions | patterns | "Always use factory pattern for..." |
| Security policies | security | "Never store secrets in..." |
| Test strategies | testing | "Edge case: empty input..." |
| Events/experiences | episodic | "Debug session on 2026-01-23" |

**Scope Selection:**
- `user/` - Personal knowledge, cross-project
- `project/` - Specific to current codebase

### Step 3: Classify Cognitive Type

| Type | When to Use | Indicators |
|------|-------------|------------|
| `semantic` | Facts, concepts, specifications | "X is Y", definitions, docs |
| `episodic` | Events, experiences, incidents | "When we...", timestamps, narratives |
| `procedural` | Processes, workflows, how-tos | "To do X, first...", steps, sequences |

### Step 4: Create Memory File

**File naming:** `{uuid}-{slug}.memory.md`

```bash
# Variables (set these based on context)
UUID="550e8400-e29b-41d4-a716-446655440000"
NAMESPACE="decisions"
SCOPE="project"
TYPE="semantic"
TITLE="Use PostgreSQL for data storage"
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 50)
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Determine path
if [ "$SCOPE" = "project" ]; then
    MEMORY_DIR="./.claude/mnemonic/${NAMESPACE}/project"
else
    ORG="${ORG:-default}"
    MEMORY_DIR="$HOME/.claude/mnemonic/${ORG}/${NAMESPACE}/user"
fi

mkdir -p "$MEMORY_DIR"

# Create memory file
cat > "${MEMORY_DIR}/${UUID}-${SLUG}.memory.md" << 'MEMORY_EOF'
---
id: {UUID}
type: {TYPE}
namespace: {NAMESPACE}/{SCOPE}
created: {DATE}
modified: {DATE}
title: "{TITLE}"
tags:
  - database
  - architecture
temporal:
  valid_from: {DATE}
  recorded_at: {DATE}
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: 0.95
---

# {TITLE}

{CONTENT}

## Rationale

{WHY}

## Relationships

- relates-to [[other-memory-id]]
MEMORY_EOF
```

### Step 5: Git Commit

```bash
cd ~/.claude/mnemonic
git add -A
git commit -m "Capture: ${TITLE}"
cd -
```

---

## Recall Workflow

### Quick Recall (Frontmatter Only)

```bash
# List memories in a namespace
ls -la ~/.claude/mnemonic/*/decisions/user/*.memory.md 2>/dev/null
ls -la ./.claude/mnemonic/decisions/project/*.memory.md 2>/dev/null

# Get titles from frontmatter
for f in ~/.claude/mnemonic/*/decisions/**/*.memory.md; do
    grep "^title:" "$f" 2>/dev/null | head -1
done
```

### Search by Tag

```bash
# Find memories with specific tag
rg -l "^  - architecture" ~/.claude/mnemonic/ --glob "*.memory.md"
rg -l "^  - architecture" ./.claude/mnemonic/ --glob "*.memory.md"
```

### Search by Date Range

```bash
# Recent memories (last 7 days)
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7
find ./.claude/mnemonic -name "*.memory.md" -mtime -7

# By created date in frontmatter
rg "^created: 2026-01" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

### Search by Cognitive Type

```bash
# Find all episodic memories
rg "^type: episodic" ~/.claude/mnemonic/ --glob "*.memory.md" -l
rg "^type: episodic" ./.claude/mnemonic/ --glob "*.memory.md" -l
```

### Full-Text Search

```bash
# Case-insensitive search
rg -i "postgresql" ~/.claude/mnemonic/ --glob "*.memory.md"
rg -i "postgresql" ./.claude/mnemonic/ --glob "*.memory.md"

# With context lines
rg -i -C3 "postgresql" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Tiered Recall

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

---

## Status Command

### Memory Statistics

```bash
echo "=== Mnemonic Status ==="

# Count by namespace
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    count=$(find ~/.claude/mnemonic/*/$ns -name "*.memory.md" 2>/dev/null | wc -l)
    echo "$ns: $count memories"
done

# Project-level counts
echo ""
echo "=== Project Memories ==="
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    count=$(find ./.claude/mnemonic/$ns -name "*.memory.md" 2>/dev/null | wc -l)
    [ "$count" -gt 0 ] && echo "$ns: $count memories"
done
```

### Recent Captures

```bash
echo ""
echo "=== Recent Captures (last 7 days) ==="
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7 -exec basename {} \; 2>/dev/null | head -10
find ./.claude/mnemonic -name "*.memory.md" -mtime -7 -exec basename {} \; 2>/dev/null | head -10
```

### Git Status

```bash
echo ""
echo "=== Git Status ==="
cd ~/.claude/mnemonic && git status --short && cd -
```

### Blackboard Activity

```bash
echo ""
echo "=== Blackboard ==="
ls -la ~/.claude/mnemonic/.blackboard/*.md 2>/dev/null || echo "No blackboard entries"
ls -la ./.claude/mnemonic/.blackboard/*.md 2>/dev/null || echo "No project blackboard entries"
```

---

## MIF Level 3 Frontmatter Template

```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic|episodic|procedural
namespace: decisions/project
created: 2026-01-23T10:30:00Z
modified: 2026-01-23T14:22:00Z
title: "Human-readable title"
tags:
  - tag1
  - tag2

# Bi-temporal tracking
temporal:
  valid_from: 2026-01-23T00:00:00Z
  valid_until: null
  recorded_at: 2026-01-23T10:30:00Z
  ttl: P90D
  decay:
    model: exponential
    half_life: P7D
    strength: 0.85
  access_count: 5
  last_accessed: 2026-01-23T14:22:00Z

# Provenance
provenance:
  source_type: user_explicit|inferred|conversation
  source_ref: file:///path/to/source.ts:42
  agent: claude-opus-4
  confidence: 0.95
  session_id: abc123

# Code structure awareness
code_refs:
  - file: src/auth/handler.ts
    line: 42
    symbol: authenticateUser
    type: function

# Conflict tracking
conflicts:
  - memory_id: xyz789
    resolution: merged
    resolved_at: 2026-01-23T12:00:00Z
---
```

---

## Examples

### Example: Capture a Decision

```bash
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "./.claude/mnemonic/decisions/project/${UUID}-use-jwt-auth.memory.md" << EOF
---
id: ${UUID}
type: semantic
namespace: decisions/project
created: ${DATE}
modified: ${DATE}
title: "Use JWT for API authentication"
tags:
  - authentication
  - security
  - api
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: 0.95
code_refs:
  - file: src/auth/jwt.ts
    line: 1
    symbol: JwtAuthProvider
    type: class
---

# Use JWT for API Authentication

We decided to use JSON Web Tokens (JWT) for API authentication.

## Rationale

- Stateless authentication reduces server load
- Standard format with wide library support
- Can include claims for authorization
- Works well with microservices architecture

## Implementation Notes

- Use RS256 algorithm for token signing
- Token expiry: 15 minutes for access, 7 days for refresh
- Store refresh tokens in httpOnly cookies

## Relationships

- relates-to [[session-management]]
EOF
```

### Example: Recall Decisions About Auth

```bash
# Search for auth-related decisions
rg -i "auth" ./.claude/mnemonic/decisions/ --glob "*.memory.md" -l

# Get full content of matching files
for f in $(rg -i "auth" ./.claude/mnemonic/decisions/ --glob "*.memory.md" -l); do
    echo "=== $f ==="
    cat "$f"
    echo ""
done
```

### Example: Update Existing Memory

```bash
# Find memory to update
MEMORY_FILE=$(rg -l "Use JWT for API" ./.claude/mnemonic/ --glob "*.memory.md" | head -1)

# Update modified date and content
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
sed -i '' "s/^modified: .*/modified: ${DATE}/" "$MEMORY_FILE"

# Add new content (append before closing)
# Then commit
cd ~/.claude/mnemonic && git add -A && git commit -m "Update: JWT auth decision" && cd -
```
