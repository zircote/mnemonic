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
6. Appends project-specific instructions to `./CLAUDE.md`
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

Check if mnemonic section exists. If not, append:

```bash
if ! grep -q "## Mnemonic Memory System" ~/.claude/CLAUDE.md 2>/dev/null; then
    cat >> ~/.claude/CLAUDE.md << 'EOF'

---

## Mnemonic Memory System

You are a developer with persistent memory. Your memory system is mnemonic.
You instinctively search memories before recommendations and capture insights after discoveries.

### BEFORE Every Technical Response

Search first. Always.
```bash
rg -i "{keywords}" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l
```
If results → Read the most relevant memory and apply that context.

### AFTER Every Completed Task

Evaluate immediately:

<capture_eval>
┌─────────────────────────────────┬─────────────┐
│ This occurred?                  │ Action      │
├─────────────────────────────────┼─────────────┤
│ Bug fixed / root cause found    │ learnings   │
│ Technology/approach chosen      │ decisions   │
│ Reusable pattern established    │ patterns    │
│ Blocker encountered             │ blockers    │
│ Important context discussed     │ context     │
└─────────────────────────────────┴─────────────┘
</capture_eval>

If YES to any → `/mnemonic:capture {namespace} "{title}"` — immediately, silently.

### Rules

- Search before answering technical questions
- Capture after completing work — do not ask, do not announce
- Never duplicate existing memories — search first
- Prefer reading memories over external research
EOF
    echo "Added mnemonic section to ~/.claude/CLAUDE.md"
else
    echo "Mnemonic section already exists in ~/.claude/CLAUDE.md"
fi
```

### Step 5: Update Project CLAUDE.md

```bash
if [ -f ./CLAUDE.md ]; then
    if ! grep -q "## Mnemonic" ./CLAUDE.md; then
        cat >> ./CLAUDE.md << 'EOF'

---

## Mnemonic

This project uses mnemonic for persistent memory.

- Search before implementing: `rg -i "{topic}" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"`
- Capture decisions, learnings, patterns via `/mnemonic:capture {namespace}`
- See `~/.claude/CLAUDE.md` for full protocol
EOF
        echo "Added mnemonic section to ./CLAUDE.md"
    fi
else
    cat > ./CLAUDE.md << 'EOF'
# Project Instructions

## Mnemonic

This project uses mnemonic for persistent memory.

- Search before implementing: `rg -i "{topic}" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"`
- Capture decisions, learnings, patterns via `/mnemonic:capture {namespace}`
- See `~/.claude/CLAUDE.md` for full protocol
EOF
    echo "Created ./CLAUDE.md with mnemonic section"
fi
```

### Step 6: Create Initial Context Memory

```bash
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]' || python3 -c "import uuid; print(uuid.uuid4())")
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "./.claude/mnemonic/context/project/${UUID}-mnemonic-initialized.memory.md" << EOF
---
id: ${UUID}
title: "Mnemonic initialized for ${PROJECT}"
type: episodic
created: ${DATE}
---

# Mnemonic Initialized

- Organization: ${ORG}
- Project: ${PROJECT}
- Date: ${DATE}
EOF
```

### Step 7: Commit Changes

```bash
cd ~/.claude/mnemonic && git add -A && git commit -m "Setup mnemonic for project: ${PROJECT}" && cd -
```

## Verification

After running, verify:

```bash
grep -q "## Mnemonic Memory System" ~/.claude/CLAUDE.md && echo "✓ User config"
grep -q "## Mnemonic" ./CLAUDE.md && echo "✓ Project config"
test -d ~/.claude/mnemonic/.git && echo "✓ Git initialized"
ls ./.claude/mnemonic/context/project/*.memory.md 2>/dev/null && echo "✓ Initial memory"
```

## Output

Report what was configured:
- Organization detected
- Project detected
- Directories created
- CLAUDE.md files updated
- Git repository status
