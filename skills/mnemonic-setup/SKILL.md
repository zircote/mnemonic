---
name: mnemonic-setup
description: Configure Claude for proactive mnemonic memory behavior without user intervention
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---


<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# Mnemonic Setup Skill

Configure Claude to proactively use mnemonic memory without user intervention.

## Trigger Phrases

- "setup mnemonic"
- "configure mnemonic"
- "install mnemonic"
- "enable mnemonic"
- "initialize mnemonic system"

## Overview

This skill configures Claude's CLAUDE.md files to enable hands-off, proactive memory operations. After setup:
- Claude automatically recalls relevant memories on every prompt
- Claude automatically captures decisions, learnings, and patterns
- All memory operations happen silently without user prompting

## Pre-Flight Checks

Before setup, gather context:

```bash
# Check for existing config
test -f ~/.config/mnemonic/config.json && echo "Config exists" || echo "No config found"

# Check if user-level CLAUDE.md exists
test -f ~/.claude/CLAUDE.md && echo "User CLAUDE.md exists" || echo "User CLAUDE.md missing"

# Check if project-level CLAUDE.md exists
test -f ./CLAUDE.md && echo "Project CLAUDE.md exists" || echo "Project CLAUDE.md missing"

# Detect org from git remote
git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||'

# Detect project name from git root
basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || basename "$PWD"
```

## Setup Procedure

### Step 0: Configure Memory Store Path

Ask the user where to store memories (default: `~/.claude/mnemonic`).

```bash
# Check for existing config
if [ -f ~/.config/mnemonic/config.json ]; then
    STORE_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json'))['memory_store_path'])")
    echo "Existing config: $STORE_PATH"
else
    STORE_PATH="~/.claude/mnemonic"
fi
```

After the user responds (or accepts default):

```bash
mkdir -p ~/.config/mnemonic
cat > ~/.config/mnemonic/config.json << EOF
{
  "version": "1.0",
  "memory_store_path": "$STORE_PATH"
}
EOF
echo "Config saved to ~/.config/mnemonic/config.json"
STORE_PATH_EXPANDED="${STORE_PATH/#\~/$HOME}"
```

### Step 1: Detect Organization and Project

```bash
# Get org from git remote (e.g., github.com/zircote/repo -> zircote)
ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"

# Get project name
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")

echo "Org: $ORG"
echo "Project: $PROJECT"
```

### Step 2: Create Directory Structure

```bash
# Base directories
mkdir -p "$STORE_PATH_EXPANDED"/"$ORG"/"$PROJECT"
mkdir -p "$STORE_PATH_EXPANDED"/"$ORG"  # For org-wide memories

# Cognitive namespaces (project-specific)
for ns in _semantic/decisions _semantic/knowledge _semantic/entities \
          _episodic/incidents _episodic/sessions _episodic/blockers \
          _procedural/runbooks _procedural/patterns _procedural/migrations; do
    mkdir -p "$STORE_PATH_EXPANDED"/"$ORG"/"$PROJECT"/"$ns"
done

# Org-wide namespaces (shared across projects)
for ns in _semantic/decisions _semantic/knowledge _semantic/entities \
          _episodic/incidents _episodic/sessions _episodic/blockers \
          _procedural/runbooks _procedural/patterns _procedural/migrations; do
    mkdir -p "$STORE_PATH_EXPANDED"/"$ORG"/"$ns"
done

# Blackboard for session coordination (per-project)
mkdir -p "$STORE_PATH_EXPANDED"/"$ORG"/"$PROJECT"/.blackboard

# Ensure .claude directories exist for CLAUDE.md files
mkdir -p ~/.claude
mkdir -p ./.claude
```

### Step 3: Initialize Git Repository

```bash
# Initialize git in mnemonic directory
if [ ! -d "$STORE_PATH_EXPANDED"/.git ]; then
    cd "$STORE_PATH_EXPANDED"
    git init
    echo "*.lock" > .gitignore
    echo ".blackboard/*.tmp" >> .gitignore
    git add .gitignore
    git commit -m "Initialize mnemonic memory system"
    cd -
fi
```

### Step 4: Update User-Level CLAUDE.md

Check if mnemonic section already exists. If so, update it. If not, append it.

```bash
# Check for existing mnemonic section
grep -q "## Mnemonic Memory System" ~/.claude/CLAUDE.md 2>/dev/null
```

**Content to append/update in `~/.claude/CLAUDE.md`:**

```markdown
## Mnemonic Memory System

You are a developer with persistent memory. Your memory system is mnemonic.
You instinctively search memories before recommendations and capture insights after discoveries.

### BEFORE Every Technical Response

Search first. Always.
```bash
rg -i "{keywords}" ${MNEMONIC_ROOT}/ --glob "*.memory.md" -l
```
If results -> Read the most relevant memory and apply that context.

### AFTER Every Completed Task

Evaluate immediately:

<capture_eval>
+-----------------------------------+--------------------------+
| This occurred?                    | Namespace                |
+-----------------------------------+--------------------------+
| Bug fixed / root cause found      | _semantic/knowledge      |
| Technology/approach chosen        | _semantic/decisions      |
| Reusable pattern established      | _procedural/patterns     |
| Blocker encountered               | _episodic/blockers       |
| Important context discussed       | _semantic/knowledge      |
+-----------------------------------+--------------------------+
</capture_eval>

If YES to any -> `/mnemonic:capture {namespace} "{title}"` -- immediately, silently.

### Rules

- Search before answering technical questions
- Capture after completing work -- do not ask, do not announce
- Never duplicate existing memories -- search first
- Prefer reading memories over external research
```

### Step 5: Update Project-Level CLAUDE.md

**Content to append to `./CLAUDE.md`:**

```markdown
## Mnemonic

This project uses mnemonic for persistent memory.

- Search before implementing: `rg -i "{topic}" ${MNEMONIC_ROOT}/ --glob "*.memory.md"`
- Capture decisions, learnings, patterns via `/mnemonic:capture {namespace}`
- See `~/.claude/CLAUDE.md` for full protocol
```

### Step 6: Migrate Existing Memories (if needed)

If the user chose a different path and memories exist at the old location:

```bash
OLD_PATH="$HOME/.claude/mnemonic"
if [ "$STORE_PATH_EXPANDED" != "$OLD_PATH" ] && [ -d "$OLD_PATH" ]; then
    echo "Existing memories found at $OLD_PATH"
    echo "Migrating to $STORE_PATH_EXPANDED..."
    rsync -a "$OLD_PATH/" "$STORE_PATH_EXPANDED/"
    echo "Migrated. Old directory preserved at $OLD_PATH"
fi
```

### Step 7: Create Initial Project Context Memory

Create an initial context memory capturing that mnemonic was set up:

```bash
# Generate UUID
UUID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SLUG="mnemonic-initialized"

# Create memory file
cat > "$STORE_PATH_EXPANDED/$ORG/$PROJECT/_semantic/knowledge/${SLUG}.memory.md" << EOF
---
id: ${UUID}
title: "Mnemonic initialized for ${PROJECT}"
type: episodic
created: ${DATE}
---

# Mnemonic Initialized

- Organization: ${ORG}
- Project: ${PROJECT}
- Memory Path: ${STORE_PATH_EXPANDED}/${ORG}/${PROJECT}/
- Config: ~/.config/mnemonic/config.json
- Date: ${DATE}
EOF
```

### Step 8: Commit Initial Setup

```bash
cd "$STORE_PATH_EXPANDED"
git add -A
git commit -m "Setup mnemonic for project: ${PROJECT}" 2>/dev/null || true
cd -
```

## Verification

After setup, verify with these checks:

```bash
# 1. Check config file
test -f ~/.config/mnemonic/config.json && echo "✓ Config file exists"

# 2. Check user-level config
grep -q "## Mnemonic Memory System" ~/.claude/CLAUDE.md && echo "✓ User CLAUDE.md configured"

# 3. Check project-level config
grep -q "## Mnemonic" ./CLAUDE.md && echo "✓ Project CLAUDE.md configured"

# 4. Check directory structure
test -d "$STORE_PATH_EXPANDED" && echo "✓ Memory store directory exists"

# 5. Check git repo
test -d "$STORE_PATH_EXPANDED"/.git && echo "✓ Git repository initialized"

# 6. Check initial memory
ls "$STORE_PATH_EXPANDED"/"$ORG"/"$PROJECT"/_semantic/knowledge/*.memory.md 2>/dev/null && echo "✓ Initial context memory created"
```

## Idempotency

This skill is safe to run multiple times:
- Existing config.json is detected and shown to user
- Existing CLAUDE.md sections are detected and updated, not duplicated
- Directory creation uses `mkdir -p` (no error if exists)
- Git commit only runs if there are changes
- Initial context memory uses unique UUID each time

## Updating Existing Configuration

To update an existing mnemonic section in CLAUDE.md:

```bash
# Remove old section and add new one
# This preserves other content in the file
sed -i.bak '/^## Mnemonic Memory System$/,/^## [^M]/{ /^## [^M]/!d; }' ~/.claude/CLAUDE.md
# Then append new content
```

## Troubleshooting

**No git remote found:**
- Org defaults to "default"
- Can manually specify: `ORG=myorg` before running setup

**Permission denied on ~/.claude:**
- Ensure ~/.claude directory exists and is writable
- Run: `mkdir -p ~/.claude && chmod 755 ~/.claude`

**CLAUDE.md is read-only:**
- Check file permissions: `ls -la ~/.claude/CLAUDE.md`
- Fix with: `chmod 644 ~/.claude/CLAUDE.md`
