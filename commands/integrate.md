---
description: Wire mnemonic memory operations into other Claude Code plugins
argument-hint: "<plugin_path> [--analyze|--dry-run|--remove|--migrate|--verify|--rollback]"
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
- `--remove` - Remove mnemonic protocol (delete content between sentinel markers)
- `--migrate` - Convert old marker-less integrations to marker-wrapped format
- `--verify` - Verify integration integrity matches template
- `--rollback` - Revert the last mnemonic integration commit

## Procedure

### Step 1: Call Python Implementation

The integration is handled by the Python library in `skills/integrate/lib/`.

```bash
PLUGIN_PATH="${1:?Error: Plugin path required}"
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $0))}"

# Parse mode from arguments
MODE="integrate"
DRY_RUN=""
for arg in "$@"; do
    case "$arg" in
        --analyze|--dry-run) DRY_RUN="--dry-run" ;;
        --remove) MODE="remove" ;;
        --migrate) MODE="migrate" ;;
        --verify) MODE="verify" ;;
        --rollback) MODE="rollback" ;;
    esac
done

# Validate plugin path
if [ ! -f "${PLUGIN_PATH}/.claude-plugin/plugin.json" ]; then
    echo "Error: Not a valid plugin directory (missing .claude-plugin/plugin.json)"
    exit 1
fi

# Handle rollback separately
if [ "$MODE" = "rollback" ]; then
    cd "${PLUGIN_PATH}"
    if [ ! -d .git ]; then
        echo "Error: No git repository for rollback"
        exit 1
    fi

    # Find the mnemonic integration commit (not just any commit)
    COMMIT=$(git log --oneline --grep="feat(mnemonic)" --grep="chore(mnemonic)" -1 | cut -d' ' -f1)

    if [ -z "$COMMIT" ]; then
        echo "Error: No mnemonic integration commit found"
        echo "Looking for commits with 'feat(mnemonic)' or 'chore(mnemonic)' in message"
        exit 1
    fi

    echo "Found mnemonic integration commit: $COMMIT"
    git show --stat "$COMMIT"
    echo ""
    echo "Reverting this commit..."
    git revert "$COMMIT" --no-edit
    echo "Rollback complete: $(git log -1 --oneline)"
    exit 0
fi

# Run Python integrator
python3 "$PLUGIN_DIR/skills/integrate/lib/integrator.py" \
    "${PLUGIN_PATH}" \
    --mode "$MODE" \
    $DRY_RUN \
    --git-commit
```

### Step 2: Verify Results

After integration, the tool reports:
- Number of files processed
- Actions taken per file (inserted, updated, migrated, removed)
- Any errors or warnings
- Git commit hash (if committed)

## What the Integrator Does

1. **Discovers components** from plugin manifest (`plugin.json`)
2. **Reads template** from `templates/mnemonic-protocol.md`
3. **For each component file:**
   - If markers exist: Updates content between markers
   - If legacy pattern found: Migrates to marker-wrapped format
   - If no markers: Inserts template after frontmatter
4. **Adds required tools** to each file's `allowed-tools` frontmatter
5. **Commits changes** to git (if available)

## Integration Protocol

**CRITICAL: The Python integrator ALWAYS uses the template. Never generate content.**

### Sentinel Markers

All integrated content is wrapped in markers:
```markdown
<!-- BEGIN MNEMONIC PROTOCOL -->

## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.

<!-- END MNEMONIC PROTOCOL -->
```

### Template Content

Located at `${CLAUDE_PLUGIN_ROOT}/templates/mnemonic-protocol.md`:
```markdown
<!-- BEGIN MNEMONIC PROTOCOL -->

## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.

<!-- END MNEMONIC PROTOCOL -->
```

## Verify Mode

Use `--verify` to check integration integrity:
- Confirms markers are present and properly paired
- Validates content between markers matches template
- Checks required tools are in frontmatter

```bash
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --verify
```

## Examples

```bash
# Analyze without changes
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --analyze

# Preview exact changes
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --dry-run

# Apply integration
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/

# Verify integration
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --verify

# Remove integration
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --remove

# Migrate legacy patterns
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --migrate

# Undo integration
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --rollback
```
