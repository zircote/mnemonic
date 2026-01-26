# Path Resolution Integration Guide

This guide shows how each component integrates with the centralized path resolution library (`lib/paths.py`).

## Integration Pattern

All components that work with file paths should:

1. Import the path resolution library
2. Create a resolver (or use convenience functions)
3. Use resolver methods instead of manual path construction
4. Never hardcode path patterns

## Component Integration Examples

### 1. Hooks Integration

#### Before (session_start.py)

```python
# OLD: Manual path construction scattered throughout
def count_memories_by_namespace(home: Path, org: str) -> dict:
    paths = [
        home / ".claude" / "mnemonic" / org,
        home / ".claude" / "mnemonic" / "default",
        Path.cwd() / ".claude" / "mnemonic",
    ]
    # ...
```

#### After (session_start.py)

```python
from lib.paths import PathResolver, Scope

def count_memories_by_namespace(resolver: PathResolver) -> dict:
    """Count memories using centralized path resolution."""
    counts = {}

    # Get all memory roots automatically
    for root in resolver.get_all_memory_roots():
        for memory_file in root.rglob("*.memory.md"):
            # Count logic...
            pass

    return counts

def main():
    resolver = PathResolver()
    counts = count_memories_by_namespace(resolver)
    # ...
```

### 2. Commands Integration

#### Before (capture.md)

```bash
# OLD: Bash-based path construction
if [ "$SCOPE" = "project" ]; then
    MEMORY_DIR="./.claude/mnemonic/${NAMESPACE}"
else
    MEMORY_DIR="$HOME/.claude/mnemonic/${ORG}/${NAMESPACE}"
fi
```

#### After (capture.md)

Commands can call a Python helper that uses the library:

```bash
# NEW: Use Python helper with centralized paths
MEMORY_DIR=$(python3 -c "
from lib.paths import get_memory_dir
print(get_memory_dir('$NAMESPACE', '$SCOPE'))
")
```

Or better yet, convert capture to a Python command:

```python
# commands/capture.py
from lib.paths import PathResolver, Scope

def capture_memory(namespace: str, title: str, scope: str = "project"):
    resolver = PathResolver()
    scope_enum = Scope.PROJECT if scope == "project" else Scope.USER

    memory_dir = resolver.get_memory_dir(namespace, scope_enum)
    memory_dir.mkdir(parents=True, exist_ok=True)

    memory_path = resolver.get_memory_path(
        namespace,
        f"{uuid}-{slug}.memory.md",
        scope_enum
    )

    # Write memory file...
```

### 3. Search Integration

#### Before (search.md)

```bash
# OLD: Manual path construction
SEARCH_PATHS="$HOME/.claude/mnemonic/$ORG ./.claude/mnemonic"
```

#### After (search.md)

```bash
# NEW: Use Python helper for search paths
SEARCH_PATHS=$(python3 -c "
from lib.paths import get_search_paths
paths = get_search_paths(namespace='$NAMESPACE', include_user=True, include_project=True)
print(' '.join(str(p) for p in paths))
")

rg -i "$PATTERN" $SEARCH_PATHS --glob '*.memory.md'
```

### 4. Ontology Registry Integration

#### Before (ontology_registry.py)

```python
# OLD: Hardcoded paths
def get_ontology_paths():
    return [
        Path.cwd() / ".claude" / "mnemonic" / "ontology.yaml",
        Path.home() / ".claude" / "mnemonic" / "ontology.yaml",
    ]
```

#### After (ontology_registry.py)

```python
from lib.paths import PathResolver

class OntologyRegistry:
    def __init__(self, resolver: PathResolver = None):
        self.resolver = resolver or PathResolver()

    def load_ontologies(self):
        """Load ontologies from all configured paths."""
        for ontology_path in self.resolver.get_ontology_paths():
            if ontology_path.exists():
                yield self._load_ontology_file(ontology_path)
```

### 5. Migration Scripts Integration

#### Before (migrate_scope_paths.py)

```python
# OLD: Hardcoded paths
paths = [
    Path.home() / ".claude" / "mnemonic",
    Path.cwd() / ".claude" / "mnemonic",
]
```

#### After (migrate_scope_paths.py)

```python
from lib.paths import PathResolver

def migrate_to_v2_scheme():
    """Migrate from legacy to V2 path scheme."""
    # Use legacy resolver to find old paths
    legacy_resolver = PathResolver()  # defaults to LEGACY scheme

    # Get all memory roots from legacy scheme
    for root in legacy_resolver.get_all_memory_roots():
        # Process memories...
        pass

    # Use V2 resolver to compute new paths
    from lib.paths import PathContext, PathScheme
    context = PathContext.detect(scheme=PathScheme.V2)
    v2_resolver = PathResolver(context)

    # Move files to new locations
    # ...
```

### 6. Test Integration

#### Test Setup

```python
# tests/conftest.py
import pytest
from pathlib import Path
from lib.paths import PathResolver, PathContext, PathScheme

@pytest.fixture
def test_resolver(tmp_path):
    """Create a test resolver with isolated paths."""
    context = PathContext(
        org="testorg",
        project="testproject",
        home_dir=tmp_path / "home",
        project_dir=tmp_path / "project",
        scheme=PathScheme.LEGACY,
    )
    return PathResolver(context)

@pytest.fixture
def v2_test_resolver(tmp_path):
    """Create a V2 test resolver."""
    context = PathContext(
        org="testorg",
        project="testproject",
        home_dir=tmp_path / "home",
        project_dir=tmp_path / "project",
        scheme=PathScheme.V2,
    )
    return PathResolver(context)
```

#### Using Test Resolver

```python
def test_memory_capture(test_resolver):
    """Test memory capture with isolated paths."""
    memory_dir = test_resolver.get_memory_dir("semantic/decisions", Scope.PROJECT)
    memory_dir.mkdir(parents=True)

    memory_path = test_resolver.get_memory_path(
        "semantic/decisions",
        "test.memory.md",
        Scope.PROJECT
    )

    # Test memory creation...
    assert memory_path.exists()
```

## Dependency Injection Pattern

For better testability, components should accept a resolver as a parameter:

```python
from lib.paths import PathResolver

class MemoryManager:
    def __init__(self, resolver: PathResolver = None):
        """Initialize with optional resolver for testing."""
        self.resolver = resolver or PathResolver()

    def save_memory(self, namespace: str, content: str):
        memory_dir = self.resolver.get_memory_dir(namespace)
        # Save logic...
```

This enables easy testing:

```python
def test_memory_manager(test_resolver):
    manager = MemoryManager(resolver=test_resolver)
    manager.save_memory("semantic/decisions", "test content")
    # Assertions...
```

## Migration Strategy

### Phase 1: Add Library (Week 1)

1. Create `lib/paths.py` with full implementation
2. Create comprehensive unit tests
3. Add integration documentation
4. No breaking changes - library is additive

**Status**: Complete (this commit)

### Phase 2: Integrate Python Components (Week 2)

Priority order (least risk to most):

1. **Migration scripts** (low risk, not user-facing)
   - `scripts/migrate_scope_paths.py`
   - `scripts/migrate_namespaces.py`
   - `scripts/cleanup_memory_paths.py`

2. **New components** (medium risk, limited usage)
   - `skills/ontology/lib/ontology_registry.py`
   - `skills/ontology/lib/ontology_loader.py`

3. **Hooks** (higher risk, frequently executed)
   - `hooks/session_start.py`
   - `hooks/user_prompt_submit.py`
   - `hooks/pre_tool_use.py`
   - `hooks/post_tool_use.py`
   - `hooks/stop.py`

4. **Tests** (refactor to use test resolvers)
   - `.claude/tests/conftest.py`
   - All test files

### Phase 3: Convert Commands to Python (Week 3)

Convert Bash commands to Python for better path handling:

1. `commands/capture.py` (convert from capture.md)
2. `commands/search.py` (convert from search.md)
3. `commands/init.py` (convert from init.md)
4. `commands/recall.py` (convert from recall.md)

### Phase 4: Enable V2 Scheme (Week 4)

1. Add configuration option for path scheme
2. Create migration command: `/mnemonic:migrate --to-v2`
3. Update documentation
4. Provide rollback capability

### Phase 5: Deprecate Legacy (Future)

1. Set V2 as default for new installations
2. Auto-migrate on first run (with user confirmation)
3. Remove legacy scheme support (major version bump)

## Configuration

Add path scheme configuration to `.claude/mnemonic/config.yaml`:

```yaml
# Path scheme configuration
paths:
  scheme: legacy  # or "v2"
  custom_home: null  # optional override for testing

# Migration settings
migration:
  auto_migrate: false
  backup_before_migrate: true
```

Load config in PathContext:

```python
@classmethod
def detect(cls, config_path: Optional[Path] = None) -> "PathContext":
    """Detect context from environment and config."""
    scheme = PathScheme.LEGACY  # default

    if config_path and config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
            scheme_str = config.get("paths", {}).get("scheme", "legacy")
            scheme = PathScheme.V2 if scheme_str == "v2" else PathScheme.LEGACY

    return cls(
        org=_detect_org(),
        project=_detect_project(),
        home_dir=Path.home(),
        project_dir=Path.cwd(),
        scheme=scheme
    )
```

## Benefits Summary

### Developer Experience

- **Single source of truth**: All path logic in one place
- **Type safety**: Python type hints catch errors early
- **Easy testing**: Dependency injection enables isolated tests
- **Clear interfaces**: Explicit methods for each use case

### Maintenance

- **Easier refactoring**: Change paths once, affects all components
- **Migration support**: Support multiple schemes during transition
- **Documentation**: Self-documenting code with clear method names
- **Debugging**: Centralized logging and error handling

### Future-Proofing

- **Extensible**: Easy to add new path schemes or configurations
- **Configurable**: Support user preferences and environment overrides
- **Backward compatible**: Legacy scheme support during migration
- **Clean abstractions**: Future changes isolated to one module

## Performance Considerations

### Caching

For frequently accessed paths, consider caching:

```python
from functools import lru_cache

class PathResolver:
    @lru_cache(maxsize=128)
    def get_memory_dir(self, namespace: str, scope: Scope) -> Path:
        # Implementation...
```

### Lazy Evaluation

Don't create resolvers unnecessarily:

```python
# BAD: Creates resolver on module import
_resolver = PathResolver()

# GOOD: Create resolver when needed
def get_resolver() -> PathResolver:
    return PathResolver()
```

### File System Operations

The resolver only computes paths - it doesn't check existence by default. Use `get_search_paths()` which filters non-existent paths only when needed for search operations.

## Troubleshooting

### Common Integration Issues

1. **Import errors**: Ensure `lib/` is in Python path
2. **Test isolation**: Always use fixtures with tmp_path
3. **Circular imports**: Import paths in functions, not at module level if needed
4. **Path scheme confusion**: Explicitly pass scheme in tests

### Debugging

Add logging to resolver:

```python
import logging

logger = logging.getLogger(__name__)

class PathResolver:
    def get_memory_dir(self, namespace: str, scope: Scope) -> Path:
        path = self._get_memory_dir_impl(namespace, scope)
        logger.debug(f"Resolved {namespace}/{scope} -> {path}")
        return path
```

## Questions & Decisions

### Q: Should we support custom path schemes?

**Decision**: Not in v1. Keep it simple with LEGACY and V2. Custom schemes can be added later if needed.

### Q: How do we handle Windows paths?

**Decision**: Python's `pathlib.Path` handles cross-platform paths automatically. No special handling needed.

### Q: What about symlinks?

**Decision**: Follow symlinks by default. Use `Path.resolve()` if absolute resolution needed.

### Q: Should paths be validated?

**Decision**: No validation in resolver - keep it pure path computation. Validation happens at usage sites (create directory, open file, etc).

## Related Documents

- [lib/paths.py](../../lib/paths.py) - Core implementation
- [tests/unit/test_paths.py](../../tests/unit/test_paths.py) - Unit tests
- [ADR-009: Unified Path Resolution](../adrs/adr-009-unified-path-resolution.md) - Architecture decision record
