# Contributing to Mnemonic

Thank you for considering contributing to Mnemonic! This document outlines the process and guidelines for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Claude Code CLI
- Git
- Python 3.8+ (for hooks)
- ripgrep (recommended)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/zircote/mnemonic.git
cd mnemonic

# Load the plugin for testing
claude --plugin-dir .

# Run setup
/mnemonic:setup
```

## Project Structure

```
mnemonic/
├── .claude-plugin/
│   └── plugin.json      # Plugin manifest
├── agents/
│   └── *.md             # Agent definitions
├── commands/
│   └── *.md             # Slash command definitions
├── hooks/
│   ├── hooks.json       # Hook configuration
│   └── *.py             # Hook implementations
├── skills/
│   └── */SKILL.md       # Skill definitions
├── docs/
│   └── *.md             # Documentation
└── README.md
```

## Contribution Types

### Bug Reports

1. Check existing issues first
2. Include reproduction steps
3. Provide environment details (OS, Claude Code version)
4. Include relevant logs or error messages

### Feature Requests

1. Describe the use case
2. Explain the expected behavior
3. Consider backwards compatibility
4. Discuss alternatives considered

### Code Contributions

#### Commands

Commands are markdown files in `commands/`:

```markdown
---
description: Brief description
argument-hint: "<args>"
allowed-tools:
  - Bash
  - Read
  - Write
---

# /mnemonic:command-name

Full description and procedure...
```

#### Skills

Skills are self-contained in `skills/{name}/SKILL.md`:

```markdown
---
name: skill-name
description: What this skill does
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# Skill Name

Complete instructions and embedded code...
```

**Key principle**: Skills must be fully self-contained. All code and logic should be inline - no external library dependencies.

#### Hooks

Hooks are Python scripts in `hooks/`:

1. Must output valid JSON
2. Must handle errors gracefully
3. Must respect timeouts
4. Should be idempotent

```python
#!/usr/bin/env python3
import json
import os

def main():
    # Your logic here
    result = {"continue": True}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

#### Agents

Agents are markdown files in `agents/`:

```markdown
---
name: agent-name
description: What this agent does
trigger: When to invoke
allowed-tools:
  - Read
  - Write
  - Bash
---

# Agent Name

Task definitions and workflows...
```

## Development Guidelines

### File Naming

- Commands: `{verb}.md` (e.g., `capture.md`)
- Skills: `mnemonic-{name}/SKILL.md`
- Hooks: `{event_name}.py` (e.g., `session_start.py`)
- Agents: `{name}.md`

### Memory Format

All memories must follow MIF Level 3:

```yaml
---
id: UUID
type: semantic|episodic|procedural
namespace: category/scope
created: ISO-8601
modified: ISO-8601
title: "Title"
tags: []
temporal:
  valid_from: ISO-8601
  recorded_at: ISO-8601
provenance:
  source_type: conversation|user_explicit|inferred
  agent: model-identifier
  confidence: 0.0-1.0
---
```

### Testing

1. Test commands manually with `claude --plugin-dir .`
2. Validate plugin with `claude plugin validate .`
3. Test hooks in isolation
4. Verify memory files are valid YAML

```bash
# Validate plugin
claude plugin validate .

# Test a command
/mnemonic:status

# Check hook output
python3 hooks/session_start.py
```

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/my-feature`)
3. **Make** your changes
4. **Test** thoroughly
5. **Commit** with clear messages
6. **Push** to your fork
7. **Open** a Pull Request

### PR Checklist

- [ ] Plugin validates (`claude plugin validate .`)
- [ ] Commands/skills have proper frontmatter
- [ ] Code follows project style
- [ ] Documentation updated if needed
- [ ] No breaking changes (or clearly documented)

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add memory export command
fix: correct namespace path in recall
docs: update architecture diagram
refactor: simplify hook configuration
```

## Documentation

- Update README.md for user-facing changes
- Update docs/architecture.md for structural changes
- Add inline comments for complex logic
- Include examples in command/skill definitions

## Questions?

Open an issue for discussion or clarification.
