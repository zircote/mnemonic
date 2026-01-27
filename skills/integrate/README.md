# Mnemonic Integrate Skill

Wire mnemonic memory operations into other Claude Code plugins.

## Overview

The integrate skill provides automated integration of mnemonic protocol into plugin components (commands, skills, agents). It ensures consistent memory capture and recall patterns across all integrated plugins.

## Quick Start

```bash
# Integrate mnemonic into a plugin
/mnemonic:integrate /path/to/plugin

# Preview changes first
/mnemonic:integrate /path/to/plugin --dry-run

# Verify existing integration
/mnemonic:integrate /path/to/plugin --verify

# Remove integration
/mnemonic:integrate /path/to/plugin --remove
```

## Directory Structure

```
skills/integrate/
├── SKILL.md           # Skill definition and documentation
├── README.md          # This file
└── lib/               # Python implementation
    ├── __init__.py
    ├── integrator.py      # Main orchestrator
    ├── marker_parser.py   # Sentinel marker operations
    ├── template_validator.py  # Template validation
    └── frontmatter_updater.py # YAML frontmatter tools
```

## Library API

### Integrator

The main orchestrator for integration operations.

```python
from skills.integrate.lib.integrator import Integrator

integrator = Integrator(plugin_root="/path/to/plugin")

# Run integration
report = integrator.run(mode="integrate")

# Check results
if report.all_successful:
    print(f"Integrated {report.success_count} files")
```

#### Methods

- `discover_components()` - Find all integrable files
- `integrate_file(path)` - Integrate a single file
- `remove_from_file(path)` - Remove integration from file
- `verify_file(path)` - Verify integration matches template
- `run(mode, ...)` - Run full integration workflow

#### Run Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `mode` | str | "integrate", "remove", "migrate", "verify" |
| `component_types` | list | Filter by type: ["commands", "skills", "agents"] |
| `files` | list | Specific files to process |
| `dry_run` | bool | Preview changes without writing |
| `force` | bool | Overwrite existing markers |
| `git_commit` | bool | Commit changes to git |
| `rollback_on_failure` | bool | Restore files if any operation fails |

### MarkerParser

Handles sentinel marker detection and manipulation.

```python
from skills.integrate.lib.marker_parser import MarkerParser

parser = MarkerParser()

# Check for markers
has_markers = parser.has_markers(content)

# Validate markers
valid, error = parser.has_valid_markers(content)

# Extract content between markers
inner = parser.extract_between(content)

# Replace content between markers
new_content = parser.replace_between(content, new_inner)

# Remove markers and content
clean = parser.remove_markers(content)

# Insert after frontmatter
with_protocol = parser.insert_after_frontmatter(content, protocol)

# Wrap content with markers
wrapped = parser.wrap_with_markers(content)

# Detect legacy patterns
has_legacy = parser.has_legacy_pattern(content)

# Migrate legacy to markers
migrated = parser.migrate_legacy(content, protocol)
```

### TemplateValidator

Validates protocol templates.

```python
from skills.integrate.lib.template_validator import TemplateValidator

validator = TemplateValidator()

# Validate template file
result = validator.validate_template(template_path)
if not result.valid:
    print(f"Errors: {result.errors}")

# Verify inserted content matches template
matches = validator.verify_insertion(file_content, template_content)
```

### FrontmatterUpdater

Manages YAML frontmatter in markdown files.

```python
from skills.integrate.lib.frontmatter_updater import FrontmatterUpdater

updater = FrontmatterUpdater()

# Get current tools
tools = updater.get_allowed_tools(content)

# Check for specific tool
has_bash = updater.has_tool(content, "Bash")

# Check all required tools present
complete = updater.has_all_required_tools(content)

# Get missing tools
missing = updater.get_missing_tools(content)

# Add tools to frontmatter
updated = updater.add_tools(content, ["Bash", "Grep"])
```

## CLI Usage

Each library module has a CLI interface.

### integrator.py

```bash
python3 integrator.py /path/to/plugin [OPTIONS]

Options:
  --mode {integrate,remove,migrate,verify}
  --type {commands,skills,agents}  (repeatable)
  --file PATH                      (repeatable)
  --dry-run
  --force
  --git-commit
  --json
```

### marker_parser.py

```bash
python3 marker_parser.py /path/to/file.md [--check|--extract|--remove|--has-legacy]
```

### template_validator.py

```bash
python3 template_validator.py /path/to/template.md [--verify-against FILE]
```

### frontmatter_updater.py

```bash
python3 frontmatter_updater.py /path/to/file.md [--check|--add|--list]
```

## Protocol Format

The integration protocol uses sentinel markers:

```markdown
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->
```

The template is located at `templates/mnemonic-protocol.md`.

## Testing

```bash
# Run all tests
pytest tests/test_marker_parser.py
pytest tests/test_template_validator.py
pytest tests/test_frontmatter_updater.py
pytest tests/test_integrator.py
pytest tests/test_integration_e2e.py

# Run with coverage
pytest tests/ --cov=skills/integrate/lib
```

## Security

The library implements several security measures:

1. **Path Validation** - All paths must be within plugin root
2. **Symlink Protection** - Symlinks pointing outside plugin root are rejected
3. **Template Validation** - Templates are checked for executable patterns
4. **Rollback Support** - Failed integrations automatically restore original files
5. **Marker Versioning** - Protocol version support for future upgrades

## Dependencies

**Required:**
- Python 3.8+

**Optional (for YAML frontmatter manipulation):**

| Library | Priority | Benefit |
|---------|----------|---------|
| `ruamel.yaml` | Preferred | Preserves comments, formatting, and key order |
| `PyYAML` | Fallback | Basic YAML parsing |
| (none) | Last resort | Regex-based parsing (may lose formatting) |

Install preferred library: `pip install ruamel.yaml`

The library gracefully degrades through these options - it will work without any YAML library installed, but frontmatter formatting may not be perfectly preserved.
