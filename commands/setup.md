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
3. Creates unified mnemonic directory structure under `~/.claude/mnemonic/{org}/{project}/`
4. Initializes git repository for versioning
5. Appends proactive behavior instructions to `~/.claude/CLAUDE.md` (global only)
6. Creates initial project context memory

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

All memories are stored under `~/.claude/mnemonic/` with the unified V2 path structure:

```bash
# Base directories
mkdir -p ~/.claude/mnemonic/"$ORG"/"$PROJECT"
mkdir -p ~/.claude/mnemonic/"$ORG"  # For org-wide memories

# Cognitive triad namespaces (project-specific)
for ns in semantic/decisions semantic/knowledge semantic/entities \
          episodic/incidents episodic/sessions episodic/blockers \
          procedural/runbooks procedural/patterns procedural/migrations; do
    mkdir -p ~/.claude/mnemonic/"$ORG"/"$PROJECT"/"$ns"
done

# Org-wide namespaces (shared across projects)
for ns in semantic/decisions semantic/knowledge semantic/entities \
          episodic/incidents episodic/sessions episodic/blockers \
          procedural/runbooks procedural/patterns procedural/migrations; do
    mkdir -p ~/.claude/mnemonic/"$ORG"/"$ns"
done

# Blackboard for session coordination (per-project)
mkdir -p ~/.claude/mnemonic/"$ORG"/"$PROJECT"/.blackboard

# Ensure .claude directory exists
mkdir -p ~/.claude
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
rg -i "{keywords}" ~/.claude/mnemonic/ --glob "*.memory.md" -l
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

### Step 5: Create Initial Context Memory

```bash
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]' || python3 -c "import uuid; print(uuid.uuid4())")
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

MEMORY_DIR="$HOME/.claude/mnemonic/$ORG/$PROJECT/semantic/knowledge"
mkdir -p "$MEMORY_DIR"

cat > "$MEMORY_DIR/${UUID}-mnemonic-initialized.memory.md" << EOF
---
id: ${UUID}
title: "Mnemonic initialized for ${PROJECT}"
type: semantic
namespace: semantic/knowledge
created: ${DATE}
modified: ${DATE}
tags:
  - setup
  - initialization
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: system
  agent: claude-opus-4
  confidence: 1.0
---

# Mnemonic Initialized

Project ${PROJECT} has been configured to use mnemonic memory.

## Configuration

- **Organization**: ${ORG}
- **Project**: ${PROJECT}
- **Memory Path**: ~/.claude/mnemonic/${ORG}/${PROJECT}/
- **Date**: ${DATE}

## Memory Structure

All memories stored under \`~/.claude/mnemonic/${ORG}/${PROJECT}/\`:

- \`semantic/decisions/\` - Architectural choices
- \`semantic/knowledge/\` - APIs, context, learnings
- \`semantic/entities/\` - Entity definitions
- \`episodic/incidents/\` - Production issues
- \`episodic/sessions/\` - Debug sessions
- \`episodic/blockers/\` - Impediments
- \`procedural/runbooks/\` - Operational procedures
- \`procedural/patterns/\` - Code conventions
- \`procedural/migrations/\` - Migration steps
EOF
```

### Step 6: Commit Changes

```bash
cd ~/.claude/mnemonic && git add -A && git commit -m "Setup mnemonic for project: ${PROJECT}" && cd -
```

## Verification

After running, verify:

```bash
grep -q "## Mnemonic Memory System" ~/.claude/CLAUDE.md && echo "✓ User config"
test -d ~/.claude/mnemonic/.git && echo "✓ Git initialized"
test -d ~/.claude/mnemonic/"$ORG"/"$PROJECT"/semantic/decisions && echo "✓ Project directories"
ls ~/.claude/mnemonic/"$ORG"/"$PROJECT"/semantic/knowledge/*-mnemonic-initialized.memory.md 2>/dev/null && echo "✓ Initial memory"
```

## Output

Report what was configured:
- Organization detected
- Project detected
- Directories created (unified under ~/.claude/mnemonic/)
- CLAUDE.md updated (global only)
- Git repository status
