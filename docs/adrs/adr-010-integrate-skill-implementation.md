# ADR-010: Integrate Skill Python Implementation

**Status**: Accepted

**Date**: 2026-01-27

**Authors**: Claude (Anthropic)

**Deciders**: Project maintainers

## Context

The mnemonic integrate skill enables automated integration of memory protocol into other Claude Code plugins. The original implementation relied on:

1. **Inline bash commands** in skill documentation
2. **Ad-hoc content generation** with risk of inconsistency
3. **No programmatic validation** of integration results
4. **Conflicting examples** showing different patterns (Pattern A/B/C)

### Problems Identified

1. **Inconsistent Behavior**: Skill sometimes generated content without sentinel markers
2. **No Verification**: No way to validate integrations match template
3. **Manual Rollback**: Failed integrations required manual cleanup
4. **Template Drift**: Examples in documentation diverged from actual template
5. **Security Gaps**: No path validation or symlink protection

### Requirements

1. Single source of truth for integration content
2. Atomic operations with rollback support
3. Verification against template
4. CLI and programmatic access
5. Security hardening for path operations

## Decision

We will implement a **Python library** (`skills/integrate/lib/`) that provides:

### 1. Modular Architecture

```
skills/integrate/lib/
├── __init__.py
├── integrator.py        # Main orchestrator
├── marker_parser.py     # Sentinel marker operations
├── template_validator.py # Template validation
└── frontmatter_updater.py # YAML frontmatter tools
```

### 2. Clear Separation of Concerns

| Module | Responsibility |
|--------|----------------|
| `integrator.py` | Workflow orchestration, file discovery, git operations |
| `marker_parser.py` | Marker detection, extraction, replacement, migration |
| `template_validator.py` | Template structure validation, insertion verification |
| `frontmatter_updater.py` | YAML parsing, tool list management |

### 3. Template as Single Source of Truth

The template at `templates/mnemonic-protocol.md` is the ONLY source of integration content. The library:
- Reads template on every operation
- Validates template structure before use
- Never generates content - only inserts template verbatim

### 4. Marker-Based Operations

All integrations use sentinel markers:
```markdown
<!-- BEGIN MNEMONIC PROTOCOL v1.0 -->
{template content}
<!-- END MNEMONIC PROTOCOL v1.0 -->
```

Version suffix supports future protocol upgrades.

### 5. Security Measures

- **Path validation**: All paths checked to be within plugin root
- **Symlink protection**: Symlinks pointing outside root rejected
- **Template scanning**: Detect suspicious executable patterns
- **Rollback on failure**: Automatic file restoration

### 6. Transaction-Like Behavior

```python
# Files are backed up before modification
backups = {path: content for path, content in original_files}

# On any failure, rollback
if not result.success:
    for path, content in backups.items():
        path.write_text(content)
```

### 7. Integration Manifest

After successful integration, write `.mnemonic-integration-manifest.json`:
```json
{
  "version": "1.0.0",
  "integrated_at": "2026-01-27T10:30:00Z",
  "files": [...]
}
```

## Consequences

### Positive

1. **Consistency**: All integrations use same template
2. **Verifiable**: Integration can be validated programmatically
3. **Reversible**: Failed operations automatically rolled back
4. **Testable**: Each component has unit tests
5. **Secure**: Path validation prevents directory traversal
6. **Extensible**: Modular design allows future enhancements

### Negative

1. **Complexity**: More code to maintain than inline bash
2. **Dependencies**: Requires Python 3.8+, optional ruamel.yaml
3. **Learning Curve**: Contributors must understand library structure

### Neutral

1. **CLI Interface**: Each module has standalone CLI for debugging
2. **Fallback Parsing**: Regex fallback when YAML libraries unavailable

## Alternatives Considered

### Alternative 1: Pure Bash Implementation

**Rejected** because:
- Complex string manipulation is error-prone in bash
- No structured validation
- Difficult to test
- Security hardening harder to implement

### Alternative 2: Single Monolithic Script

**Rejected** because:
- Violates single responsibility principle
- Harder to test individual components
- More difficult to extend

### Alternative 3: External Tool Integration

**Rejected** because:
- Adds external dependency
- Less control over integration behavior
- May not support all required operations

## Implementation Notes

### Running Tests

```bash
pytest tests/test_marker_parser.py
pytest tests/test_template_validator.py
pytest tests/test_frontmatter_updater.py
pytest tests/test_integrator.py
pytest tests/test_integration_e2e.py
```

### CLI Usage

```bash
# Full integration
python3 skills/integrate/lib/integrator.py /path/to/plugin

# Verify
python3 skills/integrate/lib/integrator.py /path/to/plugin --mode verify

# JSON output
python3 skills/integrate/lib/integrator.py /path/to/plugin --json
```

## Related ADRs

- ADR-008: Custom Ontologies (namespace support)
- ADR-009: Unified Path Resolution (path handling patterns)
