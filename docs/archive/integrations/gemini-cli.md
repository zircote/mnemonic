# Google Gemini CLI Integration

Integrate Mnemonic with Google Gemini CLI using instructions or MCP servers.

## Overview

Gemini CLI supports:
1. **Instructions file**: Simple text-based instructions
2. **MCP Servers**: Full tool integration (advanced)

## Setup

### Method 1: Instructions File (Recommended)

Create `~/.gemini/instructions.md`:

```bash
mkdir -p ~/.gemini
cat > ~/.gemini/instructions.md << 'EOF'
# Mnemonic Memory System

## Memory Location
All memories are stored at `${MNEMONIC_ROOT}/` as `.memory.md` files.

## Required Behavior
1. Search memories before implementing: `rg -i "<topic>" ${MNEMONIC_ROOT}/`
2. Capture decisions, learnings, patterns immediately
3. Use MIF Level 3 format with YAML frontmatter

## Namespaces
- decisions/ - Architectural choices
- learnings/ - Insights and discoveries
- patterns/ - Code conventions
- blockers/ - Issues and impediments

## Memory Format
```yaml
---
id: <uuid>
type: semantic|episodic|procedural
namespace: {namespace}/user
created: <ISO8601>
title: "Title"
tags: [tag1, tag2]
---

# Title

Content...
```
EOF
```

### Method 2: MCP Server (Advanced)

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "mnemonic": {
      "command": "/path/to/mnemonic-mcp-server",
      "args": ["--memory-path", "${MNEMONIC_ROOT}"],
      "timeout": 30000,
      "trust": true
    }
  }
}
```

Note: MCP server implementation requires additional development.

## Verification

```bash
# Check MCP servers (if using Method 2)
gemini mcp list

# Test memory search
gemini "search for memories about authentication"
```

## Usage Examples

```bash
# Ask Gemini to recall
gemini "What decisions have been made about the database schema?"

# Ask Gemini to capture
gemini "Remember that we decided to use PostgreSQL for the main database"
```

## Limitations

- Instructions file is advisory only
- MCP server requires custom implementation
- Shell command execution depends on Gemini CLI configuration

## Sources

- [Gemini CLI MCP Servers](https://geminicli.com/docs/tools/mcp-server/)
- [GitHub - gemini-cli MCP docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md)
