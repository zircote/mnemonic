---
name: integrate
description: Wire mnemonic memory operations into other Claude Code plugins
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - Edit
---

# Integrate Skill

Wire mnemonic memory operations into other Claude Code plugins.

## Trigger Phrases

- "integrate mnemonic"
- "wire plugin"
- "add memory to plugin"
- "plugin integration"

## Overview

This skill enables integrating mnemonic memory capture and recall into other Claude Code plugins. Integration happens through two mechanisms:

1. **Markdown Workflow Edits** - Add explicit workflow steps to command/skill/agent markdown files
2. **Event-Driven Hooks** - Add hooks that detect events and inject memory context

Both mechanisms work together: Markdown provides explicit workflow guidance, hooks provide automatic event detection.

---

## Integration Workflow

### Phase 1: Analyze Target Plugin

```bash
# Read plugin manifest
cat {plugin_path}/.claude-plugin/plugin.json

# List all components
ls -la {plugin_path}/commands/ {plugin_path}/skills/ {plugin_path}/agents/ 2>/dev/null
```

For each component, determine:
- **Does it CREATE something?** → Candidate for capture after
- **Does it MAKE DECISIONS?** → Candidate for capture after
- **Does it RESEARCH something?** → Candidate for recall before

### Phase 2: Identify Integration Points

| Component Type | Integration Pattern |
|----------------|---------------------|
| Command that creates files | Add capture section at end |
| Agent that makes decisions | Add recall before, capture after |
| Skill with workflows | Add memory search step |
| Hook on tool use | Add capture trigger |

### Phase 3: Generate Integration Code

For each integration point:
1. Read the original file
2. Generate mnemonic integration code
3. Determine insertion point (usually end of workflow)

### Phase 4: Apply Modifications

Use Edit tool to insert integration code into target files.

### Phase 5: Update Tool Access

Mnemonic operations require certain tools. Add them to target component's `allowed-tools`:

**Required tools for mnemonic integration:**
- `Bash` - For git operations and memory file creation
- `Glob` - For finding memory files
- `Grep` - For searching memory content
- `Read` - For reading memory files
- `Write` - For creating memory files

**How to update:**

For agents/skills with frontmatter:
```yaml
---
name: some-agent
allowed-tools:
  - Bash    # Add if missing
  - Glob    # Add if missing
  - Grep    # Add if missing
  - Read    # Add if missing
  - Write   # Add if missing
  # ... existing tools
---
```

Check existing `allowed-tools` and add only what's missing.

---

## Integration Patterns

**Key principles:**
- Insert at **TOP** of file (immediately after frontmatter)
- Minimal (2-4 lines), imperative language
- Direct commands, not suggestions or workflows

### Pattern A: Capture After Creation

**Applies to:** Commands/skills that create files (adr-new, doc-create, etc.)

**Add immediately after frontmatter:**

```markdown
## Memory

After completing: `/mnemonic:capture {namespace} "{title}"`
```

**Namespace mapping:**
- ADRs → `semantic/decisions`
- Documentation → `semantic/knowledge`
- Code patterns → `procedural/patterns`
- Issues/bugs → `episodic/blockers`

### Pattern B: Recall Before Action

**Applies to:** Agents/skills that make decisions or implement features

**Add immediately after frontmatter:**

```markdown
## Memory

Before starting: `rg -i "{topic}" ~/.claude/mnemonic/ --glob "*.memory.md"`
After completing: `/mnemonic:capture {namespace} "{title}"`
```

### Pattern C: Full Protocol

**Applies to:** Components that both research AND create

**Add immediately after frontmatter:**

```markdown
## Memory

Search first: `rg -i "{topic}" ~/.claude/mnemonic/ --glob "*.memory.md"`
Capture after: `/mnemonic:capture {namespace} "{title}"`
```

### Pattern D: Event-Driven Hooks (Optional)

**Applies to:** Plugins that need automatic capture signals

**Note:** Hooks provide signals only. The markdown patterns above are primary.

**Create `hooks/mnemonic-signal.py`:**

```python
#!/usr/bin/env python3
import json, os

def main():
    tool_input = json.loads(os.environ.get("CLAUDE_TOOL_INPUT", "{}"))
    file_path = tool_input.get("file_path", "")

    # Detect capture-worthy files
    namespace = None
    if "/adr/" in file_path: namespace = "semantic/decisions"
    elif "/docs/" in file_path: namespace = "semantic/knowledge"

    if namespace:
        print(json.dumps({
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"**CAPTURE:** `/mnemonic:capture {namespace}`"
            }
        }))
    else:
        print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
```

---

## Target Plugin Examples

### ADR Plugin

**Files to modify:** `commands/adr-new.md`, `agents/adr-author.md`

**Add after frontmatter:**

```markdown
## Memory

Search first: `rg -i "{decision_topic}" ~/.claude/mnemonic/ --glob "*.memory.md"`
Capture after: `/mnemonic:capture decisions "ADR-{number}: {title}"`
```

### Documentation Review Plugin

**Files to modify:** `commands/doc-create.md`, `commands/doc-review.md`

**Add after frontmatter:**

```markdown
## Memory

After completing: `/mnemonic:capture learnings "{doc_title}"`
```

### Feature Dev Plugin

**Files to modify:** `agents/*.md`, `skills/*.md`

**Add after frontmatter:**

```markdown
## Memory

Search first: `rg -i "{feature}" ~/.claude/mnemonic/ --glob "*.memory.md"`
Capture after: `/mnemonic:capture patterns "{pattern_name}"`
```

---

## How to Use This Skill

### Analyze Only Mode

```
/mnemonic:integrate {plugin_path} --analyze
```

Outputs proposed modifications without making changes.

### Dry Run Mode

```
/mnemonic:integrate {plugin_path} --dry-run
```

Shows exactly what changes would be made without applying them. Useful for reviewing integration before committing.

**Dry run output includes:**
- Files that would be created
- Files that would be modified (with diff preview)
- Tools that would be added to allowed-tools
- Git commit that would be created

**Example output:**
```
DRY RUN - No changes will be made

Plugin: ~/.claude/plugins/cache/zircote/adr/0.2.0/
Git repo: ✓ Found

Changes that would be made:

1. MODIFY: commands/adr-new.md
   + ## Post-Creation: Capture to Mnemonic
   + After creating the file, capture the key details...
   (15 lines added)

2. MODIFY: agents/adr-author.md
   + ## Before Starting: Check Related Memories
   + Use mnemonic recall workflow...
   (12 lines added)

   TOOLS: Would add [Bash, Glob, Grep, Read, Write] to allowed-tools

3. CREATE: hooks/mnemonic-suggest.py
   (45 lines, template from mnemonic/templates/plugin-hooks/)

4. CREATE/MERGE: hooks/hooks.json
   + PostToolUse matcher for Write tool

Git commit that would be created:
  feat(mnemonic): integrate memory capture and recall

To apply these changes, run without --dry-run flag.
```

### Full Integration Mode

```
/mnemonic:integrate {plugin_path}
```

Analyzes plugin and applies all integration modifications.

### Specific Component

```
/mnemonic:integrate {plugin_path}/commands/adr-new.md
```

Integrates mnemonic into a specific command/skill file.

### Rollback Mode

```
/mnemonic:integrate {plugin_path} --rollback
```

Reverts the last mnemonic integration commit. Only works if plugin has git.

**Rollback workflow:**

1. **Find integration commit** - Search for commits with "feat(mnemonic)" message
2. **Show what will be reverted** - Display the commit diff
3. **Confirm with user** - Ask before reverting
4. **Revert commit** - Use `git revert` to cleanly undo changes
5. **Report** - Show reverted files and new commit hash

**Example:**
```
/mnemonic:integrate ~/.claude/plugins/cache/zircote/adr/ --rollback
```

**Output:**
```
Found mnemonic integration commit:
  abc1234 feat(mnemonic): integrate memory capture and recall
  Date: 2026-01-24 15:30
  Files: 4 changed

This will revert:
  - commands/adr-new.md (remove capture section)
  - agents/adr-author.md (remove recall section)
  - hooks/mnemonic-suggest.py (delete file)
  - hooks/hooks.json (remove PostToolUse entry)

Proceed with rollback? [y/N]
```

**Rollback implementation:**

```bash
cd {plugin_path}

# Find the mnemonic integration commit
COMMIT=$(git log --oneline --grep="feat(mnemonic)" -1 | cut -d' ' -f1)

if [ -z "$COMMIT" ]; then
  echo "No mnemonic integration commit found"
  exit 1
fi

# Show what will be reverted
echo "Will revert commit: $COMMIT"
git show --stat $COMMIT

# Revert the commit (creates a new revert commit)
git revert --no-edit $COMMIT

echo "✓ Rollback complete"
git log -1 --oneline
```

**Note:** Rollback creates a new revert commit, preserving history. To completely remove the integration commit, use `git reset --hard HEAD~1` instead (destructive).

---

## Workflow Steps

When invoked, this skill:

**Standard Mode:**
1. **Read plugin manifest** - Parse `.claude-plugin/plugin.json`
2. **List components** - Find all commands, skills, agents, hooks
3. **Analyze each component** - Determine integration pattern
4. **Generate modifications** - Create markdown sections and hook scripts
5. **Show proposed changes** - Display what will be modified
6. **Apply modifications** - Use Edit tool to insert integration code
7. **Update tool access** - Add required tools (Bash, Glob, Grep, Read, Write) to components
8. **Commit changes** - Create atomic git commit for rollback (see Git Workflow below)
9. **Report results** - Summarize what was integrated and commit hash

**Dry Run Mode (`--dry-run`):**
1. **Read plugin manifest** - Parse `.claude-plugin/plugin.json`
2. **List components** - Find all commands, skills, agents, hooks
3. **Analyze each component** - Determine integration pattern
4. **Generate modifications** - Create markdown sections and hook scripts
5. **Display changes** - Show what WOULD be modified (with diffs)
6. **Exit** - No changes applied

**Rollback Mode (`--rollback`):**
1. **Check git repository** - Verify plugin has git
2. **Find integration commit** - Search for "feat(mnemonic)" commit
3. **Display changes** - Show what will be reverted
4. **Confirm** - Ask user to confirm rollback
5. **Revert commit** - Run `git revert` on integration commit
6. **Report** - Show reverted files and new commit hash

---

## Verification

After integration, verify by:

1. **Run integrated command** - Execute the modified command
2. **Check for capture prompt** - Verify Claude suggests memory capture
3. **Create a memory** - Confirm memory is created correctly
4. **Test recall** - Search for the new memory

```bash
# Verify memory was created
ls -la ~/.claude/mnemonic/*/decisions/*.memory.md | tail -5

# Search for content
rg -i "{topic}" ~/.claude/mnemonic/ --glob "*.memory.md"
```

---

## Best Practices

1. **Always analyze first** - Use `--analyze` to preview changes
2. **Test integration** - Run modified commands to verify
3. **Keep sections minimal** - Integration text should be concise
4. **Use consistent patterns** - All capture sections should follow same format
5. **Don't duplicate** - Check if integration already exists
6. **Document changes** - Note which files were modified

---

## Git Workflow for Plugin Modifications

When integrating mnemonic into a plugin, track changes with git for clean rollback.

### Check for Git Repository

```bash
cd {plugin_path}

# Check if git repo exists
if [ -d .git ]; then
  echo "✓ Git repository found"
else
  echo "⚠ No git repository - changes will not be committed"
  echo "  Consider: git init"
fi
```

### Atomic Commit Pattern

If git repository exists, create single atomic commit with all integration changes:

```bash
cd {plugin_path}

# Stage modified files
git add -A

# Create descriptive commit
git commit -m "feat(mnemonic): integrate memory capture and recall" \
           -m "Added mnemonic integration via integrate skill" \
           -m "Enables persistent memory across Claude sessions"
```

Or for more detailed commit messages, use a heredoc:

```bash
git commit -F - << 'EOF'
feat(mnemonic): integrate memory capture and recall

Added mnemonic integration:
- Capture workflow for [list components]
- Recall pattern for [list components]
- Event hooks for [list triggers]

Enables persistent memory across Claude sessions.
Integration by: mnemonic integrate skill
EOF
```

### Non-Git Plugins

If target plugin has no git repository:

1. **Warn user** but proceed with integration
2. **List changes** made for manual review
3. **Suggest** initializing git for future modifications

Example output:
```
⚠ Warning: Plugin has no git repository
  Integration complete but changes are not tracked.
  Files modified:
    - commands/adr-new.md
    - agents/adr-author.md
    - hooks/mnemonic-suggest.py
  Consider: cd {plugin_path} && git init
```

### Rollback

If integration needs to be undone:

```bash
cd {plugin_path}

# View what was changed
git show HEAD

# Undo the integration commit
git revert HEAD

# Or reset completely (discards commit)
git reset --hard HEAD~1
```

### Verification

After commit, verify integration:

```bash
# Show commit details
git log -1 --stat

# Show what changed
git diff HEAD~1
```
