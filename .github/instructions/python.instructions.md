---
applyTo: "**/*.py"
---

# Python Code Guidelines

## Style
- Use ruff for linting and formatting
- Line length: 120 characters
- Target: Python 3.8+
- Use double quotes for strings

## Imports
- Follow isort ordering (handled by ruff)
- Group: stdlib, third-party, local

## Type Hints
- Prefer type hints for function signatures
- Use `from __future__ import annotations` for forward references

## Error Handling
- Use specific exception types
- Log errors before re-raising
- Avoid bare `except:` clauses

## Hook Files (hooks/*.py)
- Must be executable Python scripts
- Should handle `--test` flag for validation
- Use JSON output for structured data
- Exit with appropriate codes (0=success, 1=error)
