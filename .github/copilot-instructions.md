# GitHub Copilot Instructions

## Project Overview

Mnemonic is a pure filesystem-based memory system for AI coding assistants. It provides persistent memory using markdown files with YAML frontmatter, following the Memory Interchange Format (MIF) Level 3 specification.

## Technology Stack

- **Language**: Python 3.8+ (hooks), Markdown (commands, skills, docs)
- **Package Manager**: pip (no requirements.txt - minimal dependencies)
- **Linter**: ruff
- **Formatter**: ruff format
- **Test Runner**: pytest
- **Build Tool**: Make

## Development Commands

```bash
# Setup
make setup          # Install dev dependencies (ruff, pytest)

# Quality
make lint           # Lint Python files with ruff
make format         # Format Python files with ruff
make format-check   # Check formatting without changes

# Testing
make test           # Run pytest and validate hooks
make validate       # Validate plugin structure

# Maintenance
make clean          # Remove __pycache__ and .pyc files
make audit          # Security audit
```

## Code Style

- Python: ruff with line length 120, target Python 3.8
- Markdown: YAML frontmatter required for commands and skills
- Quotes: Double quotes for Python strings
- Imports: isort ordering via ruff

## Project Structure

```
mnemonic/
├── .claude-plugin/plugin.json  # Plugin manifest (required)
├── commands/*.md               # Slash commands with YAML frontmatter
├── skills/*/SKILL.md          # Skills with YAML frontmatter
├── hooks/*.py                 # Python lifecycle hooks
├── agents/*.md                # Agent definitions
├── docs/                      # Documentation
└── tests/                     # Pytest tests
```

## Plugin Architecture Patterns

### Commands
- Located in `commands/*.md`
- Must have YAML frontmatter with `name`, `description`
- Implement user-facing slash commands

### Skills
- Located in `skills/{skill-name}/SKILL.md`
- Must have YAML frontmatter with `name`, `description`
- Contain domain knowledge and procedures

### Hooks
- Located in `hooks/*.py`
- Python scripts for lifecycle events
- Must be valid Python with proper syntax

## Memory File Format (MIF Level 3)

When creating or editing memory files (`.memory.md`):

```yaml
---
id: <uuid>
type: semantic|episodic|procedural
namespace: {category}/user
created: <ISO8601>
modified: <ISO8601>
title: "Title"
tags: [tag1, tag2]
temporal:
  valid_from: <ISO8601>
  recorded_at: <ISO8601>
provenance:
  source_type: conversation
  agent: <model-id>
  confidence: 0.0-1.0
---

# Title

Content in markdown...
```

## Testing Requirements

- All Python hooks must have valid syntax
- Commands must have YAML frontmatter
- Skills must have YAML frontmatter
- Plugin manifest must exist at `.claude-plugin/plugin.json`

## Key Files

- `Makefile` - All development commands
- `pyproject.toml` - Python/ruff configuration
- `.github/workflows/ci.yml` - CI pipeline
- `docs/adrs/` - Architecture Decision Records
