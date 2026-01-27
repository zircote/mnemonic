---
allowed-tools:
- Bash
- Write
- Read
- Glob
- Grep
argument-hint: '[--org <name>]'
description: Initialize mnemonic directory structure
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:init

Initialize the mnemonic memory system directory structure.

## Arguments

- `--org <name>` - Override auto-detected organization name

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

### Step 2: Create Unified Directory Structure

All memories are stored under `~/.claude/mnemonic/` with the V2 path structure:

```bash
# Base directories
mkdir -p ~/.claude/mnemonic/"$ORG"/"$PROJECT"
mkdir -p ~/.claude/mnemonic/"$ORG"  # For org-wide memories

# Cognitive triad namespaces (project-specific, prefixed with _ for disambiguation)
for ns in _semantic/decisions _semantic/knowledge _semantic/entities \
          _episodic/incidents _episodic/sessions _episodic/blockers \
          _procedural/runbooks _procedural/patterns _procedural/migrations; do
    mkdir -p ~/.claude/mnemonic/"$ORG"/"$PROJECT"/"$ns"
done

# Org-wide namespaces (shared across projects)
for ns in _semantic/decisions _semantic/knowledge _semantic/entities \
          _episodic/incidents _episodic/sessions _episodic/blockers \
          _procedural/runbooks _procedural/patterns _procedural/migrations; do
    mkdir -p ~/.claude/mnemonic/"$ORG"/"$ns"
done

# Blackboard for session coordination (per-project)
mkdir -p ~/.claude/mnemonic/"$ORG"/"$PROJECT"/.blackboard

# Initialize standard blackboard topics
touch ~/.claude/mnemonic/"$ORG"/"$PROJECT"/.blackboard/active-tasks.md
touch ~/.claude/mnemonic/"$ORG"/"$PROJECT"/.blackboard/session-notes.md
touch ~/.claude/mnemonic/"$ORG"/"$PROJECT"/.blackboard/shared-context.md
```

### Step 3: Initialize Git Repository

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

### Step 4: Verify Structure

```bash
echo "=== Mnemonic Initialized ==="
echo "Organization: $ORG"
echo "Project: $PROJECT"
echo ""
echo "Memory path: ~/.claude/mnemonic/$ORG/$PROJECT/"
echo ""
echo "Namespaces:"
echo "  _semantic/decisions   - Architectural choices"
echo "  _semantic/knowledge   - APIs, context, learnings"
echo "  _semantic/entities    - Entity definitions"
echo "  _episodic/incidents   - Production issues"
echo "  _episodic/sessions    - Debug sessions"
echo "  _episodic/blockers    - Impediments"
echo "  _procedural/runbooks  - Operational procedures"
echo "  _procedural/patterns  - Code conventions"
echo "  _procedural/migrations - Migration steps"
```

## Output

Display:
- Detected/configured organization
- Detected project name
- Memory path (unified under ~/.claude/mnemonic/)
- Namespace list with descriptions
- Git status
