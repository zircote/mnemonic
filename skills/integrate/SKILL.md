---
name: integrate
description: |
  This skill should be used when the user asks to "integrate mnemonic", "wire plugin",
  "add memory to plugin", "enable memory capture in plugin", "integrate memory operations",
  "add mnemonic protocol", "remove mnemonic integration", "rollback plugin integration",
  or "migrate legacy memory sections". It wires mnemonic memory capture and recall
  workflows into other Claude Code plugins using sentinel markers.
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

## When to Use

Use this skill when you want to:
- **Add memory to an existing plugin** - Make any plugin mnemonic-aware
- **Enable cross-session learning** - Let plugins recall past decisions and learnings
- **Automate capture triggers** - Set up hooks that suggest memory capture at the right time
- **Migrate legacy integrations** - Convert old marker-less integrations to the new format

**Don't use this skill if:**
- You're building a new plugin from scratch (use the core skill directly)
- You only need to search/capture memories (use `/mnemonic:search` and `/mnemonic:capture`)

## Overview

This skill enables integrating mnemonic memory capture and recall into other Claude Code plugins. Integration happens through two mechanisms:

1. **Markdown Workflow Edits** - Add explicit workflow steps to command/skill/agent markdown files
2. **Event-Driven Hooks** - Add hooks that detect events and inject memory context

Both mechanisms work together: Markdown provides explicit workflow guidance, hooks provide automatic event detection.

## Quick Start

```bash
# Integrate a plugin (adds mnemonic protocol to all components)
/mnemonic:integrate {plugin_path}

# Preview changes without applying
/mnemonic:integrate {plugin_path} --dry-run

# Remove integration
/mnemonic:integrate {plugin_path} --remove

# Rollback last integration (git required)
/mnemonic:integrate {plugin_path} --rollback
```

For detailed options, see "How to Use This Skill" below.

---

> **[CRITICAL] PROTOCOL CONTENT MUST BE VERBATIM**
>
> For the mnemonic protocol section (## Memory), you MUST:
> 1. Read `templates/mnemonic-protocol.md` - this is the single source of truth
> 2. Insert its content EXACTLY as-is, including sentinel markers
> 3. Never abbreviate, modify, or "improve" the protocol text
>
> **Exception:** Event-driven hooks (Pattern D) are optional and use the provided template code.

---

## Sentinel Markers

All integrations use sentinel markers for clean updates and removal:

```markdown
<!-- BEGIN MNEMONIC PROTOCOL -->

## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.

<!-- END MNEMONIC PROTOCOL -->
```

**Benefits:**
- **Updates:** Replace content between markers without affecting rest of file
- **Removal:** Delete everything between markers cleanly
- **Detection:** Identify already-integrated files
- **Migration:** Convert old integrations to marker-wrapped format

**Template Source:** `templates/mnemonic-protocol.md` is the single source of truth.

---

## Integration Workflow

> **For most users:** Skip to "How to Use This Skill" below for command-line usage. This section details the internal steps the skill performs.

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

### Phase 3: Read Template (MANDATORY)

**Use the template verbatim - do not modify the protocol content.**

```bash
# Read the template - this is the ONLY content to insert
cat "${CLAUDE_PLUGIN_ROOT}/templates/mnemonic-protocol.md"
```

The template already contains:
- `<!-- BEGIN MNEMONIC PROTOCOL -->` start marker
- `<!-- END MNEMONIC PROTOCOL -->` end marker
- Complete protocol content between markers (see "Sentinel Markers" section above)

### Phase 4: Insert Template With Markers

For each target file:

1. **Check for existing markers:**
   ```bash
   grep -l "BEGIN MNEMONIC PROTOCOL" {file}
   ```

2. **If markers exist:** Replace content BETWEEN markers with template content

3. **If no markers:** Insert the COMPLETE template (including markers) after frontmatter

**NEVER insert content without the sentinel markers.**

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

**MANDATORY RULES (Non-negotiable):**

1. **Use template verbatim** - Read `templates/mnemonic-protocol.md` and insert exactly as-is
2. **Keep sentinel markers** - Template content must stay within `<!-- BEGIN/END MNEMONIC PROTOCOL -->` markers
3. **Insert at TOP** - Immediately after frontmatter, before any other content
4. **Don't modify protocol** - The protocol text is standardized; only hooks (Pattern D) may be customized

### Standard Protocol (From Template)

**Read and insert template content with markers:**

```bash
# Read template content
PROTOCOL=$(cat "${CLAUDE_PLUGIN_ROOT}/templates/mnemonic-protocol.md")

# Insert after frontmatter with markers
```

See template content in "Sentinel Markers" section above.

**Namespaces:** Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies. Base namespaces include `_semantic/*`, `_episodic/*`, and `_procedural/*` from mif-base ontology.

### Graceful Fallthrough

The template uses `/mnemonic:search` and `/mnemonic:capture` skills which:
- Fail gracefully if mnemonic plugin is uninstalled (skills simply won't be available)
- No errors or crashes in integrated plugins
- Seamless degradation - agent continues without memory operations

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
    if "/adr/" in file_path: namespace = "_semantic/decisions"
    elif "/docs/" in file_path: namespace = "_semantic/knowledge"

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

All integrations use the standard template from `templates/mnemonic-protocol.md` with sentinel markers.

### ADR Plugin
**Files to modify:** `commands/adr-new.md`, `agents/adr-author.md`

Insert template after frontmatter. Replace `{relevant_keywords}` with `{decision_topic}` if needed.

### Documentation Review Plugin
**Files to modify:** `commands/doc-create.md`, `commands/doc-review.md`

Insert template after frontmatter. Use generic keywords.

### Feature Dev Plugin
**Files to modify:** `agents/*.md`, `skills/*.md`

Insert template after frontmatter. Replace `{relevant_keywords}` with `{feature}` if needed.

---

## How to Use This Skill

### Insert/Update Mode (Default)

```
/mnemonic:integrate {plugin_path}
```

Inserts or updates mnemonic protocol with sentinel markers. If markers already exist, updates content between them.

### Remove Mode

```
/mnemonic:integrate {plugin_path} --remove
```

Cleanly removes mnemonic protocol by deleting everything between sentinel markers.

### Migrate Mode

```
/mnemonic:integrate {plugin_path} --migrate
```

Finds old marker-less integrations and replaces them with marker-wrapped version from template.

**Detection patterns for migration:**
- `## Memory Operations` or `## Memory` section without markers
- Content containing `rg -i`, `/mnemonic:capture`, `${MNEMONIC_ROOT}/`

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

**Safety Considerations:**
- ⚠️ Rollback only works if plugin has git (non-git plugins warn at integration time)
- ⚠️ If you've made manual changes since integration, rollback will revert those too
- ⚠️ Failed rollbacks leave partial state - check `git status` and resolve manually
- ✅ Rollback is non-destructive by default (creates revert commit)
- ✅ Original integration is preserved in git history for reference

---

## Workflow Steps

> **Note:** This section describes internal mechanics. For usage instructions, see "How to Use This Skill" above.

When invoked, this skill:

**Standard Mode (Insert/Update):**
1. **Read template** - Load `templates/mnemonic-protocol.md` as source of truth
2. **Read plugin manifest** - Parse `.claude-plugin/plugin.json`
3. **List components** - Find all commands, skills, agents, hooks
4. **For each component:**
   - Check for existing sentinel markers
   - If markers exist: Update content between them
   - If no markers: Insert after frontmatter with markers
5. **Update tool access** - Add required tools (Bash, Glob, Grep, Read, Write)
6. **Commit changes** - Create atomic git commit for rollback
7. **Report results** - Summarize what was integrated and commit hash

**Remove Mode (`--remove`):**
1. **List components** - Find all commands, skills, agents, hooks
2. **For each component:**
   - Find sentinel markers (`<!-- BEGIN/END MNEMONIC PROTOCOL -->`)
   - Delete everything between markers (inclusive)
3. **Commit changes** - Create git commit for the removal
4. **Report results** - Summarize what was removed

**Migrate Mode (`--migrate`):**
1. **List components** - Find all commands, skills, agents, hooks
2. **For each component:**
   - Detect old patterns: `## Memory Operations` or `## Memory` without markers
   - Detect content indicators: `rg -i`, `/mnemonic:capture`, `${MNEMONIC_ROOT}/`
   - Replace old section with marker-wrapped version from template
3. **Commit changes** - Create git commit
4. **Report results** - Summarize migrated files

**Dry Run Mode (`--dry-run`):**
1. **Perform analysis** - Same as standard/remove/migrate mode
2. **Display changes** - Show what WOULD be modified (with diffs)
3. **Exit** - No changes applied

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

```
# Verify memory was created
/mnemonic:status

# Search for content
/mnemonic:search {topic}
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

# Stage only the specific modified files (not git add -A for security)
git add SKILL.md README.md hooks/*.py  # Example - list actual modified files

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

---

## Implementation Library

The integrate skill is backed by a Python library located at `skills/integrate/lib/`.

### Library Components

| Module | Purpose |
|--------|---------|
| `integrator.py` | Main orchestrator - handles full integration workflow |
| `marker_parser.py` | Sentinel marker detection, extraction, replacement |
| `template_validator.py` | Template validation and content verification |
| `frontmatter_updater.py` | YAML frontmatter manipulation for tools |

### Using the Library

The library can be invoked directly via command line:

```bash
# Integrate a plugin
python3 skills/integrate/lib/integrator.py /path/to/plugin --mode integrate

# Verify integration
python3 skills/integrate/lib/integrator.py /path/to/plugin --mode verify

# Remove integration
python3 skills/integrate/lib/integrator.py /path/to/plugin --mode remove

# Dry run (preview changes)
python3 skills/integrate/lib/integrator.py /path/to/plugin --mode integrate --dry-run

# JSON output
python3 skills/integrate/lib/integrator.py /path/to/plugin --json
```

### Individual Tool Usage

```bash
# Check for markers
python3 skills/integrate/lib/marker_parser.py /path/to/file.md --check

# Extract content between markers
python3 skills/integrate/lib/marker_parser.py /path/to/file.md --extract

# Validate template
python3 skills/integrate/lib/template_validator.py /path/to/template.md

# List tools in frontmatter
python3 skills/integrate/lib/frontmatter_updater.py /path/to/file.md --list
```

### Integration Manifest

After successful integration, a `.mnemonic-integration-manifest.json` file is created in the plugin root:

```json
{
  "version": "1.0.0",
  "integrated_at": "2026-01-27T10:30:00Z",
  "template_path": "templates/mnemonic-protocol.md",
  "files": [
    {"path": "commands/example.md", "action": "inserted", "success": true}
  ],
  "tools_required": ["Bash", "Glob", "Grep", "Read", "Write"]
}
```

### Security Features

The library includes several security measures:
- **Path validation** - All file paths are validated to be within plugin root
- **Symlink protection** - Symlinks pointing outside plugin root are rejected
- **Rollback support** - Failed integrations can be automatically rolled back
- **Template validation** - Templates are checked for executable code patterns
