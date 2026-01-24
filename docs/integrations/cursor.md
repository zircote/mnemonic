# Cursor Integration

Integrate Mnemonic with Cursor using the Rules system.

## Overview

Cursor supports rules that apply to all AI interactions. The mnemonic rule configures Cursor to use the memory system.

## Setup

### Create Cursor Rule

Create `.cursor/rules/mnemonic.mdc`:

```bash
mkdir -p .cursor/rules
cp /path/to/mnemonic/templates/cursor-rule.mdc .cursor/rules/mnemonic.mdc
```

### Alternative: AGENTS.md

Cursor also supports `AGENTS.md` in the project root:

```bash
cp /path/to/mnemonic/templates/AGENTS.md ./AGENTS.md
```

## Rule Content

```markdown
---
description: "Mnemonic memory system for persistent context across sessions"
alwaysApply: true
---

# Mnemonic Memory System

## Memory Storage
All memories stored at `~/.claude/mnemonic/` as `.memory.md` files.

## Required Behavior

### Before Implementing
Search for relevant memories:
```bash
rg -i "<topic>" ~/.claude/mnemonic/ --glob "*.memory.md"
```

### Capture Triggers
- Decision made → Create in `decisions/user/`
- Lesson learned → Create in `learnings/user/`
- Pattern established → Create in `patterns/user/`
- Blocker encountered → Create in `blockers/user/`

## Memory Types
- **semantic**: Facts, decisions, specifications
- **episodic**: Events, debug sessions, incidents
- **procedural**: Workflows, patterns, how-tos
```

## Usage

Once the rule is in place:

1. **Recall**: Ask Cursor "What do we know about X?"
2. **Capture**: Tell Cursor "Remember that we decided Y"
3. **Reference**: Use `@mnemonic` in Cursor Chat

## Verification

1. Open a file in Cursor
2. Check Settings > Features > Rules for the mnemonic rule
3. Ask in Composer: "Search for memories about this project"

## Rule Options

| Option | Description |
|--------|-------------|
| `alwaysApply: true` | Apply to all interactions |
| `alwaysApply: false` | Only apply when explicitly referenced |
| `description` | Shown in rule list |

---

## Common Workflows

### Daily Development

```
Morning:
1. Open project in Cursor
2. Ask: "What decisions have we made about this project?"
3. Continue where you left off

During Development:
1. Before implementing: "Search memories for [feature]"
2. After decisions: "Remember that we're using [approach]"
3. After debugging: "Capture this fix as a learning"

End of Day:
1. Review: "What did we learn today?"
2. Verify memories captured
```

### Feature Implementation

```
1. "What patterns do we use for [component type]?"
   → Cursor searches patterns/user/

2. "What decisions affect [feature]?"
   → Cursor searches decisions/user/

3. Implement feature following established patterns

4. "Remember this pattern: [description]"
   → Creates new pattern memory
```

### Debugging Session

```
1. Encounter bug
2. "Search memories for similar issues"
3. Investigate and fix
4. "Capture this debugging session as a learning"
   → Creates episodic memory with:
   - Problem description
   - Investigation steps
   - Solution
```

---

## Advanced Patterns

### Memory-Aware Code Review

Add to your Cursor rule:

```markdown
When reviewing code:
1. Check patterns/user/ for established conventions
2. Reference decisions/user/ for architectural context
3. Flag violations of documented patterns
```

### Context Switching

When switching between projects:

```bash
# Each project can have its own namespace
~/.claude/mnemonic/project-a/decisions/user/
~/.claude/mnemonic/project-b/decisions/user/
```

Configure rule to use project-specific paths:

```markdown
Memory path for this project: ~/.claude/mnemonic/project-a/
```

### Team Patterns

Share patterns across team:

```bash
# Clone shared patterns
git clone git@github.com:team/patterns.git ~/.claude/mnemonic/shared

# Rule references both personal and shared
Memory paths:
- Personal: ~/.claude/mnemonic/default/
- Shared: ~/.claude/mnemonic/shared/
```

---

## Migrating from Cursor Memory Bank

If you've been using a Memory Bank pattern in Cursor:

### Step 1: Export Current Memories

Your Memory Bank files are typically in:
- `.cursor/memory-bank/`
- `.cursorrules` (memory section)
- Project-specific markdown files

### Step 2: Convert to MIF Format

```bash
# Use migration tool
./tools/migrate-memory-bank \
  --source .cursor/memory-bank \
  --target ~/.claude/mnemonic/default \
  --namespace context
```

### Step 3: Update Cursor Rules

Replace old memory references with mnemonic paths:

**Before:**
```markdown
Check .cursor/memory-bank/ for context
```

**After:**
```markdown
Check ~/.claude/mnemonic/default/ for context
Use MIF Level 3 format for new memories
```

### Step 4: Verify Migration

```bash
# Validate converted memories
./tools/mnemonic-validate ~/.claude/mnemonic/default/

# Test in Cursor
"What do we know about [topic from old memory bank]?"
```

See [Migration Guide](../community/migration-from-memory-bank.md) for complete details.

---

## Troubleshooting

### Rules Not Loading

**Symptom**: Cursor doesn't follow mnemonic instructions

**Solutions**:
1. Check rule location: `.cursor/rules/mnemonic.mdc`
2. Verify `alwaysApply: true` is set
3. Restart Cursor after adding rules
4. Check Settings > Features > Rules to confirm loading

### Memory Files Not Found

**Symptom**: "No memories found for [topic]"

**Solutions**:
1. Verify memory directory exists:
   ```bash
   ls -la ~/.claude/mnemonic/
   ```
2. Check file permissions
3. Ensure `.memory.md` extension
4. Try explicit path in query

### Format Errors

**Symptom**: Cursor creates invalid memory files

**Solutions**:
1. Add format examples to rule
2. Run validation after capture:
   ```bash
   ./tools/mnemonic-validate --changed
   ```
3. Include YAML template in rule

### Search Not Working

**Symptom**: ripgrep commands fail

**Solutions**:
1. Verify ripgrep installed:
   ```bash
   which rg || brew install ripgrep
   ```
2. Check path in rule matches actual location
3. Try broader search pattern

### Rule Conflicts

**Symptom**: Multiple rules interfering

**Solutions**:
1. Use unique description for mnemonic rule
2. Set priority with rule ordering
3. Check for conflicting `alwaysApply` rules

---

## Sources

- [Cursor Rules Documentation](https://cursor.com/docs/context/rules)
- [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules)
- [Memory Bank Migration](../community/migration-from-memory-bank.md)
- [MIF Level 3 Specification](../../skills/mnemonic-format/SKILL.md)
