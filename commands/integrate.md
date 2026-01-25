---
description: Wire mnemonic memory operations into other Claude Code plugins
argument-hint: "<plugin_path> [--analyze|--dry-run|--rollback]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /mnemonic:integrate

Integrate mnemonic memory capture and recall into another Claude Code plugin.

## Arguments

- `<plugin_path>` - Required. Path to target plugin directory
- `--analyze` - Show proposed changes without applying
- `--dry-run` - Show detailed diff of what would change
- `--rollback` - Revert the last mnemonic integration commit

## Procedure

### Step 1: Parse Arguments

```bash
PLUGIN_PATH="${1:?Error: Plugin path required}"
MODE="apply"  # default

# Parse flags
for arg in "$@"; do
    case "$arg" in
        --analyze) MODE="analyze" ;;
        --dry-run) MODE="dry-run" ;;
        --rollback) MODE="rollback" ;;
    esac
done

# Validate plugin path
if [ ! -f "${PLUGIN_PATH}/.claude-plugin/plugin.json" ]; then
    echo "Error: Not a valid plugin directory (missing .claude-plugin/plugin.json)"
    exit 1
fi
```

### Step 2: Read Plugin Manifest

```bash
cat "${PLUGIN_PATH}/.claude-plugin/plugin.json"
```

### Step 3: List Components

```bash
ls -la "${PLUGIN_PATH}/commands/" "${PLUGIN_PATH}/skills/" "${PLUGIN_PATH}/agents/" 2>/dev/null
```

### Step 4: Analyze Integration Points

For each component, determine integration pattern:
- Creates files → Add capture section (Pattern A)
- Makes decisions → Add recall before, capture after (Pattern B)
- Needs auto-detection → Add event hooks (Pattern C)

### Step 5: Apply Based on Mode

- If `--analyze`: Show proposed changes without applying
- If `--dry-run`: Display detailed diff of what would change and exit
- If `--rollback`: Find and revert the mnemonic integration commit
- Otherwise: Apply modifications using Edit tool

### Step 6: Update Tool Access

Update component `allowed-tools` to include: Bash, Glob, Grep, Read, Write

### Step 7: Git Commit (if applicable)

```bash
cd "${PLUGIN_PATH}"
if [ -d .git ]; then
    git add -A
    git commit -m "feat(mnemonic): integrate memory capture and recall"
    echo "Committed: $(git log -1 --oneline)"
else
    echo "Warning: No git repository - changes not committed"
fi
```

### Step 8: Report Results

Report results with commit hash (if applicable) and list of modified files

## Integration Patterns

**Key principles:**
- Insert at TOP of file (after frontmatter), not end
- Minimal (2-4 lines), imperative language
- Direct commands, not suggestions

### Pattern A: Capture After Creation

Add to commands/skills that **create files** (adr-new, doc-create, etc.):

```markdown
## Memory

After completing: `/mnemonic:capture {namespace} "{title}"`
```

### Pattern B: Recall Before Action

Add to agents/skills that **make decisions or research**:

```markdown
## Memory

Before starting: `rg -i "{topic}" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"`
After completing: `/mnemonic:capture {namespace} "{title}"`
```

### Pattern C: Both (Full Protocol)

For components that both research AND create:

```markdown
## Memory

Search first: `rg -i "{topic}" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"`
Capture after: `/mnemonic:capture {namespace} "{title}"`
```

## Git Workflow

If target plugin has git:
- Stage all changes: `git add -A`
- Commit: `git commit -m "feat(mnemonic): integrate memory capture and recall"`

If no git:
- Warn user but proceed
- List modified files for manual review

## Rollback

```bash
cd {plugin_path}
git revert HEAD  # Reverts the integration commit
```

## Examples

```bash
# Analyze without changes
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --analyze

# Preview exact changes
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --dry-run

# Apply integration
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/

# Undo integration
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --rollback
```
