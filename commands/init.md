---
description: Initialize mnemonic directory structure
argument-hint: "[--org <name>] [--project-only]"
allowed-tools:
  - Bash
  - Write
  - Read
---

# /mnemonic:init

Initialize the mnemonic memory system directory structure.

## Arguments

- `--org <name>` - Override auto-detected organization name
- `--project-only` - Only create project-level structure, skip user-level

## Procedure

### Step 1: Detect or Override Organization

```bash
# Use provided org or detect from git
if [ -n "$ORG_OVERRIDE" ]; then
    ORG="$ORG_OVERRIDE"
else
    ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
    [ -z "$ORG" ] && ORG="default"
fi

PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null)
[ -z "$PROJECT" ] && PROJECT=$(basename "$PWD")
```

### Step 2: Create User-Level Structure

Skip if `--project-only` is specified.

```bash
# Namespaces
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    mkdir -p ~/.claude/mnemonic/"$ORG"/"$ns"/{user,project}
done

# Blackboard
mkdir -p ~/.claude/mnemonic/.blackboard

# Initialize standard blackboard topics
touch ~/.claude/mnemonic/.blackboard/active-tasks.md
touch ~/.claude/mnemonic/.blackboard/session-notes.md
touch ~/.claude/mnemonic/.blackboard/shared-context.md
```

### Step 3: Create Project-Level Structure

```bash
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    mkdir -p ./.claude/mnemonic/"$ns"/project
done

mkdir -p ./.claude/mnemonic/.blackboard
```

### Step 4: Initialize Git Repository

```bash
if [ ! -d ~/.claude/mnemonic/.git ]; then
    cd ~/.claude/mnemonic
    git init

    cat > .gitignore << 'EOF'
# Lock files
*.lock

# Temporary files
.blackboard/*.tmp
*.swp
*~

# OS files
.DS_Store
Thumbs.db
EOF

    git add .
    git commit -m "Initialize mnemonic memory system"
    cd -
fi
```

### Step 5: Create/Update Project CLAUDE.md

Add mnemonic instructions to the project's CLAUDE.md file.

```bash
mkdir -p ./.claude

# Check if CLAUDE.md exists and has mnemonic section
if [ -f ./.claude/CLAUDE.md ]; then
    if ! grep -q "## Mnemonic" ./.claude/CLAUDE.md; then
        # Append mnemonic section
        cat >> ./.claude/CLAUDE.md << 'EOF'

---

## Mnemonic

This project uses mnemonic for persistent memory.

- Search before implementing: `rg -i "{topic}" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"`
- Capture decisions, learnings, patterns via `/mnemonic:capture {namespace}`
- See `~/.claude/CLAUDE.md` for full protocol
EOF
        echo "Added mnemonic section to existing .claude/CLAUDE.md"
    else
        echo "Mnemonic section already exists in .claude/CLAUDE.md"
    fi
else
    # Create new CLAUDE.md with mnemonic section
    cat > ./.claude/CLAUDE.md << 'EOF'
# Project Instructions

## Mnemonic

This project uses mnemonic for persistent memory.

- Search before implementing: `rg -i "{topic}" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"`
- Capture decisions, learnings, patterns via `/mnemonic:capture {namespace}`
- See `~/.claude/CLAUDE.md` for full protocol
EOF
    echo "Created .claude/CLAUDE.md with mnemonic section"
fi
```

### Step 6: Verify Structure

```bash
echo "=== Mnemonic Initialized ==="
echo "Organization: $ORG"
echo "Project: $PROJECT"
echo ""
echo "User-level: ~/.claude/mnemonic/$ORG/"
echo "Project-level: ./.claude/mnemonic/"
echo ""
echo "Namespaces:"
ls -1 ~/.claude/mnemonic/"$ORG"/ 2>/dev/null | grep -v "^\."
```

## Output

Display:
- Detected/configured organization
- Detected project name
- Created directory paths
- Namespace list
- CLAUDE.md status
- Git status
