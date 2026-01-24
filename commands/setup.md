---
description: Configure mnemonic for proactive memory operations
argument-hint: "[--force]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# /mnemonic:setup

Configure Claude to proactively use mnemonic memory without user intervention.

## What This Command Does

1. Detects organization from git remote
2. Detects project name from git root
3. Creates mnemonic directory structure (user-level and project-level)
4. Initializes git repository for versioning
5. Appends proactive behavior instructions to `~/.claude/CLAUDE.md`
6. Appends project-specific instructions to `./.claude/CLAUDE.md`
7. Creates initial project context memory

## Arguments

- `--force` - Overwrite existing mnemonic configuration sections

## Procedure

### Step 1: Detect Context

```bash
# Organization from git remote
ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"

# Project from git root
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")

echo "Organization: $ORG"
echo "Project: $PROJECT"
```

### Step 2: Create Directory Structure

```bash
# User-level directories
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    mkdir -p ~/.claude/mnemonic/"$ORG"/"$ns"/{user,project}
done
mkdir -p ~/.claude/mnemonic/.blackboard

# Project-level directories
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    mkdir -p ./.claude/mnemonic/"$ns"/project
done
mkdir -p ./.claude/mnemonic/.blackboard

# Ensure .claude directories exist
mkdir -p ~/.claude
mkdir -p ./.claude
```

### Step 3: Initialize Git

```bash
if [ ! -d ~/.claude/mnemonic/.git ]; then
    cd ~/.claude/mnemonic
    git init
    cat > .gitignore << 'EOF'
*.lock
.blackboard/*.tmp
*.swp
*~
.DS_Store
EOF
    git add .gitignore
    git commit -m "Initialize mnemonic memory system"
    cd -
fi
```

### Step 4: Update User CLAUDE.md

Check for existing section and update or append the mnemonic configuration to `~/.claude/CLAUDE.md`. The content should include:

- Session start behavior (auto-recall)
- Auto-capture rules (silent capture of decisions, learnings, patterns)
- Memory type classification (semantic, episodic, procedural)
- Search commands reference
- Capture template

See the mnemonic-setup skill for the complete content block.

### Step 5: Update Project CLAUDE.md

Append project-specific configuration to `./.claude/CLAUDE.md` including:

- Project name and org
- Project-specific recall instructions
- Project-specific capture rules
- Blackboard reference

### Step 6: Create Initial Context Memory

```bash
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]' || python3 -c "import uuid; print(uuid.uuid4())")
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "./.claude/mnemonic/context/project/${UUID}-mnemonic-initialized.memory.md" << EOF
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

The mnemonic memory system was initialized for this project on ${DATE}.

## Configuration
- Organization: ${ORG}
- Project: ${PROJECT}
- User-level path: ~/.claude/mnemonic/${ORG}/
- Project-level path: ./.claude/mnemonic/
EOF
```

### Step 7: Commit Changes

```bash
cd ~/.claude/mnemonic && git add -A && git commit -m "Setup mnemonic for project: ${PROJECT}" && cd -
```

## Verification

After running, verify:

```bash
grep -q "Mnemonic Memory System" ~/.claude/CLAUDE.md && echo "✓ User config"
grep -q "Mnemonic - Project Memory" ./.claude/CLAUDE.md && echo "✓ Project config"
test -d ~/.claude/mnemonic/.git && echo "✓ Git initialized"
ls ./.claude/mnemonic/context/project/*.memory.md && echo "✓ Initial memory"
```

## Output

Report what was configured:
- Organization detected
- Project detected
- Directories created
- CLAUDE.md files updated
- Git repository status
