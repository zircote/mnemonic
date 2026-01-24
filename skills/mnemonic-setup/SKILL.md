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
# User-level directories
mkdir -p ~/.claude/mnemonic/"$ORG"/{apis,blockers,context,decisions,learnings,patterns,security,testing,episodic}/{user,project}
mkdir -p ~/.claude/mnemonic/.blackboard

# Project-level directories
mkdir -p ./.claude/mnemonic/{apis,blockers,context,decisions,learnings,patterns,security,testing,episodic}/project
mkdir -p ./.claude/mnemonic/.blackboard

# Ensure .claude directories exist for CLAUDE.md files
mkdir -p ~/.claude
mkdir -p ./.claude
```

### Step 3: Initialize Git Repository

```bash
# Initialize git in user-level mnemonic directory
if [ ! -d ~/.claude/mnemonic/.git ]; then
    cd ~/.claude/mnemonic
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
grep -q "# Mnemonic Memory System" ~/.claude/CLAUDE.md 2>/dev/null
```

**Content to append/update in `~/.claude/CLAUDE.md`:**

```markdown
# Mnemonic Memory System

## MANDATORY: Proactive Memory Behavior

You MUST follow these rules automatically, WITHOUT user prompting:

### On Every Session Start
1. Check if `~/.claude/mnemonic/` exists
2. If missing, invoke mnemonic-setup skill
3. Recall recent memories (last 7 days) for current org/project
4. Hold relevant context in working memory (do not output)

### During Every Conversation

**Auto-Recall** (SILENT - do not announce):
- When user mentions a topic, search mnemonic for related memories
- Inject relevant context into your reasoning
- Prioritize: decisions > patterns > learnings

**Auto-Capture** (SILENT - do not announce):
- Decisions made → `decisions/{scope}/`
- Problems solved → `learnings/{scope}/`
- Patterns established → `patterns/{scope}/`
- Blockers hit → `blockers/{scope}/`
- Security issues → `security/{scope}/`
- API discoveries → `apis/{scope}/`
- Events/incidents → `episodic/{scope}/`

### Memory Type Classification
- **Semantic**: Facts, specs, "X is Y" → Use for API docs, config values
- **Episodic**: Events, "On date X, we did Y" → Use for debug sessions, incidents
- **Procedural**: Steps, "To do X, first Y then Z" → Use for workflows, deployments

### Before Capturing
1. Search for existing memories on the topic
2. Update existing memory if found (don't duplicate)
3. Link related memories with `[[memory-id]]`
4. Always include `code_refs` when about specific code

### Silent Operation
- Do NOT say "Checking mnemonic..." or "Capturing to memory..."
- Just DO IT silently
- Only mention mnemonic if user explicitly asks

### Memory Paths
- User-level: `~/.claude/mnemonic/{org}/`
- Project-level: `./.claude/mnemonic/`

### Search Commands
```bash
# Search by namespace
rg "pattern" ~/.claude/mnemonic/*/decisions/

# Search by tag
rg -l "^  - tagname" ~/.claude/mnemonic/ --glob "*.memory.md"

# Recent memories (last 7 days)
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7

# Full-text search
rg -i "search term" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Capture Template
When capturing, create a `.memory.md` file with this structure:
```yaml
---
id: <uuid>
type: semantic|episodic|procedural
namespace: <namespace>/<scope>
created: <ISO-8601>
modified: <ISO-8601>
title: "<title>"
tags:
  - <tag1>
  - <tag2>
temporal:
  valid_from: <ISO-8601>
  recorded_at: <ISO-8601>
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: 0.95
---

# <Title>

<Content>
```
```

### Step 5: Update Project-Level CLAUDE.md

**Content to append to `./CLAUDE.md`:**

```markdown
# Mnemonic - Project Memory

Project: {project_name}
Org: {org}
Memory Path: ./.claude/mnemonic/

## Project-Specific Recall

Silently check these on every prompt:
- `decisions/project/` - Past architectural decisions for this codebase
- `patterns/project/` - Code patterns we use here
- `learnings/project/` - Lessons learned in this project
- `testing/project/` - Test strategies and edge cases
- `security/project/` - Security policies for this project

## Project-Specific Capture

When working in this codebase, capture to project scope:
- Architecture decisions → `decisions/project/`
- Bug root causes → `learnings/project/`
- New code patterns → `patterns/project/`
- Test discoveries → `testing/project/`

## Blackboard

Check `./.claude/mnemonic/.blackboard/` for cross-session notes before starting.

## Quick Reference

```bash
# List project memories
ls -la ./.claude/mnemonic/*/project/

# Search project memories
rg "term" ./.claude/mnemonic/ --glob "*.memory.md"

# Recent project captures
find ./.claude/mnemonic -name "*.memory.md" -mtime -7
```
```

### Step 6: Create Initial Project Context Memory

Create an initial context memory capturing that mnemonic was set up:

```bash
# Generate UUID
UUID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SLUG="mnemonic-initialized"

# Create memory file
cat > "./.claude/mnemonic/context/project/${UUID}-${SLUG}.memory.md" << EOF
---
id: ${UUID}
type: episodic
namespace: context/project
created: ${DATE}
modified: ${DATE}
title: "Mnemonic memory system initialized"
tags:
  - setup
  - initialization
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: user_explicit
  agent: claude-opus-4
  confidence: 1.0
---

# Mnemonic Memory System Initialized

The mnemonic memory system was initialized for this project.

## Configuration
- Organization: ${ORG}
- Project: ${PROJECT}
- User-level path: ~/.claude/mnemonic/${ORG}/
- Project-level path: ./.claude/mnemonic/

## Capabilities
- Automatic memory capture for decisions, learnings, patterns
- Cross-session memory recall
- Namespace-based organization
- MIF Level 3 compliant format
EOF
```

### Step 7: Commit Initial Setup

```bash
cd ~/.claude/mnemonic
git add -A
git commit -m "Setup mnemonic for project: ${PROJECT}" 2>/dev/null || true
cd -
```

## Verification

After setup, verify with these checks:

```bash
# 1. Check user-level config
grep -q "Mnemonic Memory System" ~/.claude/CLAUDE.md && echo "✓ User CLAUDE.md configured"

# 2. Check project-level config
grep -q "Mnemonic - Project Memory" ./CLAUDE.md && echo "✓ Project CLAUDE.md configured"

# 3. Check directory structure
test -d ~/.claude/mnemonic && echo "✓ User mnemonic directory exists"
test -d ./.claude/mnemonic && echo "✓ Project mnemonic directory exists"

# 4. Check git repo
test -d ~/.claude/mnemonic/.git && echo "✓ Git repository initialized"

# 5. Check initial memory
ls ./.claude/mnemonic/context/project/*.memory.md 2>/dev/null && echo "✓ Initial context memory created"
```

## Idempotency

This skill is safe to run multiple times:
- Existing CLAUDE.md sections are detected and updated, not duplicated
- Directory creation uses `mkdir -p` (no error if exists)
- Git commit only runs if there are changes
- Initial context memory uses unique UUID each time

## Updating Existing Configuration

To update an existing mnemonic section in CLAUDE.md:

```bash
# Remove old section and add new one
# This preserves other content in the file
sed -i.bak '/^# Mnemonic Memory System$/,/^# [^M]/{ /^# [^M]/!d; }' ~/.claude/CLAUDE.md
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
