# Mnemonic Library Modules

Shared Python utilities for the mnemonic memory system.

## Overview

The `lib/` directory contains core utilities used across mnemonic's hooks, commands, and tools. This README focuses on the **path resolution** module. For comprehensive documentation of all library modules, see:

📚 **[Complete Library Reference](../docs/library-reference.md)**

Includes detailed API documentation for:
- **paths.py** - Path resolution (this file)
- **config.py** - Configuration management
- **memory_reader.py** - Memory file parsing
- **search.py** - Memory search and ranking
- **relationships.py** - Relationship types and linking
- **ontology.py** - Custom ontology support

---

# Path Resolution Library

Centralized path resolution for all mnemonic memory operations.

## Overview

This library provides a single source of truth for path construction in the mnemonic memory system. It eliminates scattered path logic across 30+ files and enables smooth migration between different path schemes.

## Key Features

- **Single Source of Truth**: All path construction in one place
- **Multiple Scheme Support**: LEGACY and V2 path structures
- **Testable**: Dependency injection for isolated testing
- **Type Safe**: Full Python type hints
- **Well Documented**: Comprehensive docstrings and examples

## Quick Start

### Basic Usage

```python
from lib.paths import PathResolver, Scope

# Create resolver (auto-detects context)
resolver = PathResolver()

# Get memory directory
memory_dir = resolver.get_memory_dir("_semantic/decisions", Scope.PROJECT)
# => /path/to/project/.claude/mnemonic/_semantic/decisions

# Get full memory path
memory_path = resolver.get_memory_path(
    "_semantic/decisions",
    "slug.memory.md",
    Scope.PROJECT
)

# Get search paths (returns list in priority order)
search_paths = resolver.get_search_paths("_semantic/decisions")
# => [project_path, org_path, default_path]

# Get blackboard directory
blackboard = resolver.get_blackboard_dir(Scope.PROJECT)
```

### Convenience Functions

For simple use cases, use convenience functions:

```python
from lib.paths import get_memory_dir, get_search_paths, get_blackboard_dir

# Get memory directory (string scope)
memory_dir = get_memory_dir("_semantic/decisions", scope="project")

# Get search paths
paths = get_search_paths("_semantic/decisions", include_user=True, include_project=True)

# Get blackboard
blackboard = get_blackboard_dir(scope="project")
```

## Architecture

### PathResolver

Central class that computes paths based on context and scheme.

**Key Methods:**

- `get_memory_dir(namespace, scope)` - Directory for storing memories
- `get_memory_path(namespace, filename, scope)` - Full file path
- `get_search_paths(namespace, filters)` - Ordered search paths
- `get_blackboard_dir(scope)` - Blackboard directory
- `get_ontology_paths()` - Ontology files in precedence order
- `get_all_memory_roots()` - All memory root directories

### PathContext

Dataclass holding environment context:

```python
@dataclass
class PathContext:
    org: str              # Organization (from git remote)
    project: str          # Project name (from git remote)
    home_dir: Path        # User home directory
    project_dir: Path     # Current project directory
    scheme: PathScheme    # Path scheme to use
```

Auto-detection:

```python
# Auto-detect context
context = PathContext.detect()

# Or specify scheme
context = PathContext.detect(scheme=PathScheme.V2)
```

### PathScheme

Enum defining supported path schemes:

- `LEGACY` - Current dual-location structure
- `V2` - Target unified structure

### Scope

Enum defining memory scope:

- `USER` - Cross-project memories
- `PROJECT` - Project-specific memories
- `ORG` - Organization-wide memories (V2 only)

## Path Schemes

### LEGACY Scheme (Current)

**User memories**:
```
${MNEMONIC_ROOT}/{org}/{namespace}/
```

**Project memories**:
```
./.claude/mnemonic/{namespace}/
```

**Example**:
```
${MNEMONIC_ROOT}/myorg/_semantic/decisions/
./.claude/mnemonic/_semantic/decisions/
```

### V2 Scheme (Target)

**Project memories**:
```
${MNEMONIC_ROOT}/{org}/{project}/{namespace}/
```

**Org-wide memories**:
```
${MNEMONIC_ROOT}/{org}/{namespace}/
```

**Example**:
```
${MNEMONIC_ROOT}/myorg/myproject/_semantic/decisions/
${MNEMONIC_ROOT}/myorg/_semantic/decisions/
```

## Testing

### Unit Tests

Create isolated test contexts:

```python
import pytest
from pathlib import Path
from lib.paths import PathResolver, PathContext, PathScheme, Scope

@pytest.fixture
def test_resolver(tmp_path):
    """Create test resolver with isolated paths."""
    context = PathContext(
        org="testorg",
        project="testproject",
        home_dir=tmp_path / "home",
        project_dir=tmp_path / "project",
        scheme=PathScheme.LEGACY,
    )
    return PathResolver(context)

def test_memory_operations(test_resolver, tmp_path):
    """Test with isolated file system."""
    memory_dir = test_resolver.get_memory_dir("_semantic/decisions", Scope.PROJECT)
    memory_dir.mkdir(parents=True)

    # Test operations...
    assert memory_dir.exists()
```

### Integration Tests

Test with both schemes:

```python
@pytest.fixture(params=[PathScheme.LEGACY, PathScheme.V2])
def resolver_both_schemes(request, tmp_path):
    """Test with both path schemes."""
    context = PathContext(
        org="testorg",
        project="testproject",
        home_dir=tmp_path / "home",
        project_dir=tmp_path / "project",
        scheme=request.param,
    )
    return PathResolver(context)

def test_path_resolution(resolver_both_schemes):
    """Test that works with both schemes."""
    memory_dir = resolver_both_schemes.get_memory_dir("semantic", Scope.PROJECT)
    # Assertions...
```

## Integration Examples

### Hooks

```python
from lib.paths import PathResolver

def count_memories(resolver: PathResolver) -> dict:
    """Count memories using resolver."""
    counts = {}

    for root in resolver.get_all_memory_roots():
        for memory_file in root.rglob("*.memory.md"):
            # Count logic...
            pass

    return counts

def main():
    resolver = PathResolver()
    counts = count_memories(resolver)
    print(f"Total: {sum(counts.values())}")
```

### Commands

```python
from lib.paths import PathResolver, Scope

def capture_memory(namespace: str, title: str, scope: str = "project"):
    """Capture a new memory."""
    resolver = PathResolver()
    scope_enum = Scope.PROJECT if scope == "project" else Scope.USER

    # Get memory directory
    memory_dir = resolver.get_memory_dir(namespace, scope_enum)
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Create memory file
    memory_path = resolver.get_memory_path(
        namespace,
        f"{slug}.memory.md",
        scope_enum
    )

    # Write content...
```

### Ontology System

```python
from lib.paths import PathResolver

class OntologyRegistry:
    def __init__(self, resolver: PathResolver = None):
        self.resolver = resolver or PathResolver()

    def load_ontologies(self):
        """Load all ontologies in precedence order."""
        for ontology_path in self.resolver.get_ontology_paths():
            if ontology_path.exists():
                yield self._load_ontology_file(ontology_path)
```

## Dependency Injection

Components should accept resolver as optional parameter:

```python
from lib.paths import PathResolver

class MemoryManager:
    def __init__(self, resolver: PathResolver = None):
        """Initialize with optional resolver (for testing)."""
        self.resolver = resolver or PathResolver()

    def save_memory(self, namespace: str, content: str):
        memory_dir = self.resolver.get_memory_dir(namespace)
        # Save logic...
```

This enables easy testing:

```python
def test_memory_manager(test_resolver):
    """Test with isolated paths."""
    manager = MemoryManager(resolver=test_resolver)
    manager.save_memory("_semantic/decisions", "test")
    # Assertions...
```

## Migration

### Analyzing Current Structure

```python
from lib.paths import PathResolver, PathScheme, PathContext

# Get legacy paths
legacy_resolver = PathResolver()  # defaults to LEGACY
legacy_roots = legacy_resolver.get_all_memory_roots()

# Get V2 paths
v2_context = PathContext.detect(scheme=PathScheme.V2)
v2_resolver = PathResolver(v2_context)
v2_root = v2_resolver.get_all_memory_roots()[0]

print(f"Migrating from {len(legacy_roots)} roots to {v2_root}")
```

### Migration Script

See `scripts/migrate_to_v2_paths.py` for complete example:

```python
# Run migration
python scripts/migrate_to_v2_paths.py --dry-run  # preview
python scripts/migrate_to_v2_paths.py            # execute

# Rollback if needed
python scripts/migrate_to_v2_paths.py --rollback /path/to/backup
```

## Performance

### Caching

For hot paths, add caching:

```python
from functools import lru_cache

class PathResolver:
    @lru_cache(maxsize=128)
    def get_memory_dir(self, namespace: str, scope: Scope) -> Path:
        # Implementation...
```

### Lazy Evaluation

Don't create resolvers at module level:

```python
# BAD - creates on import
_resolver = PathResolver()

# GOOD - create when needed
def get_resolver() -> PathResolver:
    return PathResolver()
```

## Design Principles

### 1. Pure Functions

Path resolution is pure computation - no I/O operations:

```python
# Resolver just computes paths
path = resolver.get_memory_dir("semantic")  # No mkdir

# Caller handles I/O
path.mkdir(parents=True, exist_ok=True)
```

### 2. Explicit Over Implicit

Be explicit about scope and scheme:

```python
# Clear and explicit
resolver.get_memory_dir("semantic", Scope.PROJECT)

# Not implicit defaults
resolver.get_memory_dir("semantic")  # would need default
```

### 3. Fail Fast

Invalid inputs should raise early:

```python
# Type system catches errors
resolver.get_memory_dir("semantic", "invalid")  # Type error!
resolver.get_memory_dir("semantic", Scope.PROJECT)  # OK
```

### 4. Testability First

Design for testing with dependency injection:

```python
class Component:
    def __init__(self, resolver: PathResolver = None):
        self.resolver = resolver or PathResolver()
```

## Common Patterns

### Pattern: Search Across All Scopes

```python
# Get all search paths in priority order
search_paths = resolver.get_search_paths(
    namespace="_semantic/decisions",
    include_user=True,
    include_project=True,
    include_org=True  # V2 only
)

# Search with ripgrep
for path in search_paths:
    subprocess.run(["rg", pattern, str(path)])
```

### Pattern: Create Memory

```python
def create_memory(namespace: str, content: str, scope: Scope):
    resolver = PathResolver()

    # Get directory and create if needed
    memory_dir = resolver.get_memory_dir(namespace, scope)
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Get full path
    filename = f"{slug}.memory.md"
    memory_path = resolver.get_memory_path(namespace, filename, scope)

    # Write content
    memory_path.write_text(content)
```

### Pattern: Load Ontology

```python
def load_ontology():
    resolver = PathResolver()

    # Try paths in precedence order
    for ontology_path in resolver.get_ontology_paths():
        if ontology_path.exists():
            return yaml.safe_load(ontology_path.read_text())

    # Use default
    return get_default_ontology()
```

### Pattern: Health Check

```python
def health_check():
    resolver = PathResolver()
    stats = {"total": 0, "by_root": {}}

    for root in resolver.get_all_memory_roots():
        count = len(list(root.rglob("*.memory.md")))
        stats["total"] += count
        stats["by_root"][str(root)] = count

    return stats
```

## Troubleshooting

### Import Errors

Add lib to Python path:

```python
import sys
from pathlib import Path

# Add lib directory to path
lib_dir = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_dir))

from lib.paths import PathResolver
```

### Path Not Found

Resolver computes paths, doesn't check existence:

```python
# This always succeeds (just computation)
path = resolver.get_memory_dir("semantic")

# Check existence when needed
if not path.exists():
    path.mkdir(parents=True)
```

### Wrong Scheme

Explicitly specify scheme if auto-detection wrong:

```python
from lib.paths import PathContext, PathScheme

context = PathContext.detect(scheme=PathScheme.V2)
resolver = PathResolver(context)
```

## API Reference

See inline docstrings in `lib/paths.py` for complete API documentation.

### PathResolver Methods

- `get_memory_dir(namespace, scope)` - Memory directory path
- `get_memory_path(namespace, filename, scope)` - Full memory file path
- `get_search_paths(namespace, filters)` - Search paths in priority order
- `get_blackboard_dir(scope)` - Blackboard directory
- `get_ontology_paths()` - Ontology paths in precedence order
- `get_all_memory_roots()` - All memory root directories

### Convenience Functions

- `get_default_resolver()` - Get resolver with auto-detected context
- `get_memory_dir(namespace, scope)` - Shortcut for get_memory_dir
- `get_search_paths(namespace, filters)` - Shortcut for get_search_paths
- `get_blackboard_dir(scope)` - Shortcut for get_blackboard_dir

## Related Documentation

- [ADR-009: Unified Path Resolution](../docs/adrs/adr-009-unified-path-resolution.md) - Architecture decision
- [Integration Guide](../docs/architecture/path-resolution-integration.md) - Component integration
- [Migration Script](../scripts/migrate_to_v2_paths.py) - V2 migration tool
- [Unit Tests](../tests/unit/test_paths.py) - Test examples

## Contributing

When adding new path-related functionality:

1. Add method to `PathResolver` class
2. Add unit tests for new method
3. Update this README with examples
4. Document in ADR if significant change

## License

MIT - Same as mnemonic project
