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

## Sources

- [GitHub Docs - Custom Instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [Path-Specific Instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot#creating-a-file-to-define-path-specific-instructions)
