# GitHub Copilot Integration

Integrate Mnemonic with GitHub Copilot to provide persistent memory context in your repositories.

## Overview

GitHub Copilot supports custom instructions through `.github/copilot-instructions.md` files. This integration configures Copilot to reference and create Mnemonic memories.

## Setup

### 1. Create Instructions File

Create `.github/copilot-instructions.md` in your repository:

```bash
mkdir -p .github
# From mnemonic repository root:
cp templates/copilot-instructions.md .github/
```

Or copy from the [template](../../templates/copilot-instructions.md).

### 2. Configure Path-Specific Instructions (Optional)

For memory file editing support, create `.github/instructions/memory.instructions.md`:

```markdown
---
applyTo: ["**/*.memory.md"]
---

This is a Mnemonic memory file using MIF Level 3 format.
Preserve the YAML frontmatter structure when editing.
Required fields: id, type, namespace, created, title, tags.
```

## How It Works

1. **Recall**: Copilot searches `~/.claude/mnemonic/` before implementing features
2. **Capture**: Copilot creates memory files when decisions are made
3. **Format**: All memories use MIF Level 3 format with YAML frontmatter

## Verification

1. Open a file in your repository with Copilot enabled
2. Ask Copilot Chat: "What memories exist about this project?"
3. Verify it references the mnemonic search command

## Limitations

- GitHub Copilot cannot directly execute shell commands
- Instructions are advisory; Copilot may not always follow them
- Works best with Copilot Chat rather than inline completions

## Template

See [templates/copilot-instructions.md](../../templates/copilot-instructions.md) for the full template.

---

## Common Workflows

### Daily Development

```
Morning:
1. Open repository in VS Code/IDE
2. Copilot Chat: "What decisions have been made for this project?"
3. Review relevant memories before starting

During Development:
1. Before implementing: "What patterns exist for [component]?"
2. After decisions: "Document this decision about [topic]"
3. After debugging: "Record this fix for future reference"

Code Review:
1. "What patterns should I look for in this code?"
2. Reference memories in PR comments
```

### Feature Implementation

```
1. Copilot Chat: "Search for patterns related to [feature]"

2. "What architectural decisions affect [area]?"

3. Implement following established patterns

4. "Create a memory documenting our approach to [feature]"
```

### Debugging Session

```
1. Encounter issue
2. "Have we seen similar issues before?"
3. Investigate and resolve
4. "Document this debugging session as a learning"
```

---

## Advanced Patterns

### Repository-Level Context

Add project context to instructions:

```markdown
# .github/copilot-instructions.md

## Project Context
This is a [type] project using [stack].

## Memory References
Before implementing features, check:
- ~/.claude/mnemonic/this-project/decisions/
- ~/.claude/mnemonic/this-project/patterns/

## Capture Requirements
Document all:
- Architectural decisions
- API design choices
- Performance optimizations
```

### Path-Specific Memory Rules

Create specialized rules for different file types:

```markdown
# .github/instructions/api.instructions.md
---
applyTo: ["**/api/**/*.ts"]
---

Check API decisions before implementing:
- ~/.claude/mnemonic/default/apis/

Document new endpoints in apis/ namespace.
```

```markdown
# .github/instructions/tests.instructions.md
---
applyTo: ["**/*.test.ts", "**/*.spec.ts"]
---

Reference testing patterns:
- ~/.claude/mnemonic/default/testing/

Document testing strategies discovered.
```

### Multi-Repository Sharing

Share memories across repositories:

```markdown
# .github/copilot-instructions.md

## Shared Memories (Organization-wide)
Also check: ~/shared-memories/org/

## Team Memories
Check: ~/shared-memories/team-platform/

## Project-Specific
Primary: ~/.claude/mnemonic/this-project/
```

### Copilot Workspace Integration

For Copilot Workspace:

```markdown
# .github/copilot-instructions.md

## Workspace Context
When planning implementations:
1. Check decisions/ for architectural constraints
2. Reference patterns/ for code conventions
3. Review apis/ for integration points

## Multi-file Changes
When modifying multiple files:
1. Verify consistency with patterns/
2. Update affected memories if patterns change
```

---

## Migrating from Other Systems

### From Copilot Memory (Cloud)

If using GitHub Copilot's built-in memory features:

1. **Export current context** from Copilot settings
2. **Convert to MIF format**:
   ```bash
   # Create memory file from exported content
   ./tools/convert-to-mif exported-memory.txt \
     --namespace context/user \
     --type semantic
   ```
3. **Update instructions** to reference local files

### From Repository Memory Files

If you have existing markdown memory files:

```bash
# Migrate existing files
./tools/migrate-memory-bank \
  --source ./docs/memory/ \
  --target ~/.claude/mnemonic/default \
  --namespace context

# Update copilot-instructions.md with new paths
```

### From Memory Bank Pattern

See [Migration Guide](../community/migration-from-memory-bank.md) for detailed steps.

---

## Troubleshooting

### Instructions Not Loading

**Symptom**: Copilot ignores custom instructions

**Solutions**:
1. Verify file location: `.github/copilot-instructions.md`
2. Check repository settings enable custom instructions
3. Ensure file is committed to repository
4. Try refreshing Copilot Chat

### Memory Commands Fail

**Symptom**: Copilot can't execute shell commands

**Note**: GitHub Copilot cannot directly execute shell commands. Instead:

1. Ask Copilot to **show** the command:
   ```
   "What command would search memories for authentication?"
   ```
2. Execute command manually in terminal
3. Share results with Copilot if needed

### Chat vs Inline Completions

**Best practices**:
- Use Copilot Chat for memory-related queries
- Inline completions work best for code generation
- Reference memories in Chat, apply in code

### Path Issues

**Symptom**: Wrong memory paths referenced

**Solutions**:
1. Use absolute paths in instructions
2. Verify `~` expands correctly in your environment
3. Consider project-relative paths:
   ```markdown
   For this project: ./mnemonic/
   For personal: ~/.claude/mnemonic/
   ```

### Format Inconsistencies

**Symptom**: Created memories don't match MIF spec

**Solutions**:
1. Include full template in path-specific instructions
2. Add validation reminder to instructions:
   ```markdown
   After creating memories, validate format matches MIF Level 3.
   ```
3. Run validation periodically:
   ```bash
   ./tools/mnemonic-validate
   ```

### Stale Instructions

**Symptom**: Old instructions still being used

**Solutions**:
1. Refresh Copilot Chat session
2. Verify latest instructions are committed
3. Check for cached versions in IDE

---

## Sources

- [GitHub Docs - Custom Instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [Path-Specific Instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot#creating-a-file-to-define-path-specific-instructions)
- [Memory Bank Migration](../community/migration-from-memory-bank.md)
- [MIF Level 3 Specification](../../skills/mnemonic-format/SKILL.md)
