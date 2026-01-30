# Mnemonic Integrations

Mnemonic integrates with popular AI coding assistants through their native configuration mechanisms.

## Supported Tools

| Tool | Integration Method | Guide |
|------|-------------------|-------|
| [Claude Code](https://claude.ai/code) | Native Plugin | Built-in |
| [GitHub Copilot](https://github.com/features/copilot) | `.github/copilot-instructions.md` | [Guide](./github-copilot.md) |
| [OpenAI Codex CLI](https://github.com/openai/codex) | `AGENTS.md` + Skills | [Guide](./codex-cli.md) |
| [Google Gemini CLI](https://github.com/google-gemini/gemini-cli) | MCP Server / Instructions | [Guide](./gemini-cli.md) |
| [OpenCode](https://opencode.ai) | Skills | [Guide](./opencode.md) |
| [Cursor](https://cursor.com) | Rules | [Guide](./cursor.md) |
| [Windsurf/Codeium](https://windsurf.ai) | Memories/Rules | [Guide](./windsurf.md) |
| [Aider](https://aider.chat) | `CONVENTIONS.md` | [Guide](./aider.md) |
| [Continue Dev](https://continue.dev) | `config.yaml` rules | [Guide](./continue.md) |

## Quick Start

### 1. Choose Your Tool

Select the integration guide for your AI coding assistant from the table above.

### 2. Copy Templates

All integrations use templates from the [`templates/`](../../templates/) directory:

```bash
# GitHub Copilot
cp templates/copilot-instructions.md .github/copilot-instructions.md

# Codex CLI / OpenCode
cp -r templates/codex-skill ~/.codex/skills/mnemonic

# Cursor
cp templates/cursor-rule.mdc .cursor/rules/mnemonic.mdc

# Aider
cp templates/CONVENTIONS.md ./CONVENTIONS.md

# Universal (many tools support this)
cp templates/AGENTS.md ./AGENTS.md
```

### 3. Verify

Follow the verification steps in each integration guide to confirm the setup works.

## Universal Memory Format

All integrations use the same MIF Level 3 memory format:

```yaml
---
id: <uuid>
type: semantic|episodic|procedural
namespace: {namespace}/user
created: <ISO8601>
modified: <ISO8601>
title: "Descriptive title"
tags: [tag1, tag2]
temporal:
  valid_from: <ISO8601>
  recorded_at: <ISO8601>
provenance:
  source_type: conversation
  agent: <tool-name>
  confidence: 0.9
---

# Title

Content in markdown...
```

## Memory Storage

All memories are stored at `${MNEMONIC_ROOT}/` with this structure:

```
${MNEMONIC_ROOT}/
└── {org}/                  # Organization from git remote (or "default")
    ├── apis/user/          # API documentation
    ├── blockers/user/      # Issues encountered
    ├── context/user/       # General context
    ├── decisions/user/     # Architectural choices
    ├── learnings/user/     # Insights discovered
    ├── patterns/user/      # Code conventions
    ├── security/user/      # Security policies
    ├── testing/user/       # Test strategies
    └── episodic/user/      # Events, experiences
```

**Note:** The `{org}` directory is derived from your git remote (e.g., `zircote` for `github.com/zircote/repo`). Falls back to `default` if no git remote is configured.

## Templates

| Template | Purpose | Location |
|----------|---------|----------|
| `copilot-instructions.md` | GitHub Copilot | `.github/` |
| `codex-skill/SKILL.md` | Codex CLI, OpenCode | `~/.codex/skills/mnemonic/` |
| `cursor-rule.mdc` | Cursor | `.cursor/rules/` |
| `CONVENTIONS.md` | Aider | Project root |
| `AGENTS.md` | Multiple tools | Project root or `~/.codex/` |

## Migrating from Memory Bank

Already using a Memory Bank pattern in Cursor, Windsurf, or another tool?

- [Quick Start for Memory Bank Users](../community/quickstart-memory-bank.md) - 5-minute setup
- [Full Migration Guide](../community/migration-from-memory-bank.md) - Complete walkthrough
- [Comparison](../community/mnemonic-vs-memory-bank.md) - Side-by-side differences

## Contributing

To add support for a new tool:

1. Create a guide in `docs/integrations/<tool>.md`
2. Add templates to `templates/` if needed
3. Update this README with the new tool
4. Submit a pull request
