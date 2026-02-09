# ADR-009: Unified Path Resolution System

**Status**: Accepted

**Date**: 2026-01-26

**Authors**: Claude (Anthropic)

**Deciders**: Project maintainers

## Context

The mnemonic memory system currently has path construction logic scattered across:
- 18+ Python files (hooks, scripts, tests)
- 16+ command markdown files (bash commands)
- Multiple patterns for the same operations

This creates several problems:

1. **Maintainability**: Changing path structure requires updating many files
2. **Consistency**: Risk of path construction inconsistencies
3. **Testing**: Difficult to test path logic in isolation
4. **Migration**: Hard to support multiple path schemes during transitions
5. **Documentation**: Path conventions not centralized

### Current Path Structure

**User-level** (cross-project memories):
```
${MNEMONIC_ROOT}/{org}/{namespace}/
```

**Project-level** (project-specific memories):
```
$MNEMONIC_ROOT/{namespace}/
```

### Target Path Structure

**Unified user-level** (everything in home directory):
```
${MNEMONIC_ROOT}/{org}/{project}/{semantic,episodic,procedural}/{sub-namespace}/
${MNEMONIC_ROOT}/{org}/{semantic,episodic,procedural}/{sub-namespace}/  # org-wide
${MNEMONIC_ROOT}/{org}/{project}/.blackboard/
```

### Pain Points

1. Each component reimplements organization detection from git remote
2. Path construction duplicated in ~34 locations
3. Tests cannot easily mock path resolution
4. Migration scripts are brittle due to hardcoded paths
5. No clear migration path from current to future structure

## Decision

We will implement a **centralized path resolution library** (`lib/paths.py`) that:

1. **Single Source of Truth**: All path construction logic in one module
2. **Multiple Scheme Support**: Support both LEGACY and V2 path schemes
3. **Dependency Injection**: Accept context for testability
4. **Clean Abstractions**: Clear methods for each use case
5. **Migration Path**: Enable gradual transition between schemes

### Key Components

#### PathResolver Class

Central resolver with methods:
- `get_memory_dir(namespace, scope)` - Get directory for storing memories
- `get_memory_path(namespace, filename, scope)` - Get full file path
- `get_search_paths(namespace, filters)` - Get ordered list of search paths
- `get_blackboard_dir(scope)` - Get blackboard directory
- `get_ontology_paths()` - Get ontology file paths in precedence order
- `get_all_memory_roots()` - Get all root directories containing memories

#### PathContext Dataclass

Encapsulates environment context:
- Organization name (from git remote)
- Project name (from git remote or directory)
- Home directory
- Project directory
- Path scheme (LEGACY or V2)

#### PathScheme Enum

Defines supported path schemes:
- `LEGACY`: Current dual-location structure
- `V2`: Target unified structure

#### Scope Enum

Defines memory scope:
- `USER`: Cross-project memories
- `PROJECT`: Project-specific memories
- `ORG`: Organization-wide memories (V2 only)

### Integration Pattern

Components integrate via dependency injection:

```python
from lib.paths import PathResolver

class MemoryManager:
    def __init__(self, resolver: PathResolver = None):
        self.resolver = resolver or PathResolver()

    def save_memory(self, namespace: str, content: str):
        memory_dir = self.resolver.get_memory_dir(namespace)
        # ...
```

Tests inject custom context:

```python
def test_memory_manager(tmp_path):
    context = PathContext(
        org="testorg",
        project="testproject",
        home_dir=tmp_path / "home",
        project_dir=tmp_path / "project",
        scheme=PathScheme.LEGACY
    )
    resolver = PathResolver(context)
    manager = MemoryManager(resolver=resolver)
    # Test with isolated paths
```

## Consequences

### Positive

1. **Single Source of Truth**
   - All path logic in one place
   - Changes propagate automatically
   - Easier to reason about path structure

2. **Testability**
   - Path logic tested in isolation
   - Components can be tested with mocked paths
   - No file system side effects in unit tests

3. **Migration Support**
   - Support multiple schemes simultaneously
   - Gradual migration without breaking changes
   - Clear upgrade path for users

4. **Type Safety**
   - Python type hints catch errors early
   - IDE autocomplete for path methods
   - Better documentation via types

5. **Maintainability**
   - Self-documenting code
   - Clear separation of concerns
   - Reduced code duplication

### Negative

1. **Upfront Work**
   - New module to implement (~500 lines)
   - Integration work across 30+ files
   - Documentation updates
   - **Estimated effort**: 2-3 weeks full migration

2. **Python Dependency**
   - Bash commands need Python helpers
   - Could convert commands to Python entirely
   - **Mitigation**: Provide Python command equivalents

3. **Learning Curve**
   - New abstraction to learn
   - Dependency injection pattern
   - **Mitigation**: Comprehensive documentation and examples

4. **Migration Complexity**
   - Need to support two schemes during transition
   - Testing both schemes increases test suite size
   - **Mitigation**: Phase out legacy after migration period

### Trade-offs

#### Complexity vs Flexibility

**Trade-off**: Accepting upfront complexity for long-term flexibility

**Rationale**:
- Current state has hidden complexity scattered everywhere
- Centralized complexity is easier to understand and maintain
- Future path changes will be trivial instead of requiring 30+ file edits

#### Purity vs Pragmatism

**Trade-off**: Pure path computation vs convenience features

**Decision**: Keep resolver pure (just path computation)
- No file system checks in core methods
- Existence checks only in `get_search_paths()` (which needs filtering)
- Creates directories at usage sites, not in resolver

**Rationale**:
- Easier to test pure functions
- Clear separation: resolver computes, caller uses
- Avoids hidden I/O operations

#### Abstraction Level

**Trade-off**: High-level convenience vs low-level control

**Decision**: Provide both
- Low-level: `PathResolver` class with full control
- High-level: `get_memory_dir()` convenience functions

**Rationale**:
- Advanced users need control (custom contexts, testing)
- Simple use cases shouldn't require complex setup
- Both can coexist without conflict

## Alternatives Considered

### Alternative 1: Keep Current Scattered Approach

**Pros**:
- No work required
- Familiar to existing contributors
- No risk of breaking changes

**Cons**:
- Technical debt accumulates
- Migration to new structure very difficult
- Testing remains problematic
- Inconsistencies will grow

**Rejected**: Unsustainable long-term

### Alternative 2: Environment Variables

Use environment variables for all paths:
```bash
export MNEMONIC_USER_DIR="$MNEMONIC_ROOT"
export MNEMONIC_PROJECT_DIR="$MNEMONIC_ROOT"
```

**Pros**:
- Simple configuration
- Easy to override for testing

**Cons**:
- Still need logic to construct full paths
- Doesn't solve organization/project detection
- Doesn't support multiple schemes
- Environment pollution

**Rejected**: Too simplistic, doesn't solve core problems

### Alternative 3: Configuration File

Store all paths in `${MNEMONIC_ROOT}/config.yaml`:

```yaml
paths:
  user_base: "${MNEMONIC_ROOT}/{org}"
  project_base: "$MNEMONIC_ROOT"
  blackboard: "${MNEMONIC_ROOT}/.blackboard"
```

**Pros**:
- User-configurable
- No code changes for path modifications

**Cons**:
- Still need parsing and substitution logic
- Doesn't help with testing
- Doesn't support scheme migration
- Adds YAML dependency for basic operations

**Rejected**: Over-engineered for problem scope

### Alternative 4: Hybrid - Config + Library

Combine configuration file with resolver library:

```yaml
# config.yaml
paths:
  scheme: v2  # or "legacy"
```

```python
resolver = PathResolver()  # reads config
```

**Pros**:
- User can choose scheme
- Library still provides abstraction
- Best of both worlds

**Status**: **Partially Accepted**
- Will add config support in Phase 4 (after basic library is proven)
- Config optional, sensible defaults if absent
- Doesn't complicate initial implementation

## Implementation Plan

### Phase 1: Core Library (Week 1) ✅

- [x] Create `lib/paths.py` with full implementation
- [x] Create comprehensive unit tests (`tests/unit/test_paths.py`)
- [x] Add integration documentation
- [x] No breaking changes - library is additive

**Status**: Complete (this commit)

### Phase 2: Python Components (Week 2)

Integrate library in priority order:

1. **Migration scripts** (low risk)
   - [ ] `scripts/migrate_scope_paths.py`
   - [ ] `scripts/migrate_namespaces.py`
   - [ ] `scripts/cleanup_memory_paths.py`
   - [ ] Add V2 migration script

2. **Ontology system** (medium risk)
   - [ ] `skills/ontology/lib/ontology_registry.py`
   - [ ] `skills/ontology/lib/ontology_loader.py`
   - [ ] `skills/ontology/lib/entity_resolver.py`

3. **Hooks** (higher risk)
   - [ ] `hooks/session_start.py`
   - [ ] `hooks/user_prompt_submit.py`
   - [ ] `hooks/pre_tool_use.py`
   - [ ] `hooks/post_tool_use.py`
   - [ ] `hooks/stop.py`

4. **Tests** (refactor)
   - [ ] `.claude/tests/conftest.py` - Add resolver fixtures
   - [ ] Update all test files to use test resolvers

### Phase 3: Command Migration (Week 3)

Convert Bash commands to Python:

- [ ] `commands/capture.py` (from capture.md)
- [ ] `commands/search.py` (from search.md)
- [ ] `commands/init.py` (from init.md)
- [ ] `commands/recall.py` (from recall.md)
- [ ] Update command manifests

### Phase 4: V2 Scheme Enablement (Week 4)

- [ ] Add config file support
- [ ] Create migration command: `/mnemonic:migrate --to-v2`
- [ ] Update all documentation
- [ ] Create migration guide
- [ ] Add rollback capability

### Phase 5: Cleanup & Optimization (Week 5)

- [ ] Performance testing and optimization
- [ ] Add caching if needed (LRU cache)
- [ ] Remove deprecated code paths
- [ ] Update README and guides
- [ ] Create video walkthrough

### Phase 6: Legacy Deprecation (Future - v2.0.0)

- [ ] Set V2 as default for new installations
- [ ] Auto-migrate on first run (with confirmation)
- [ ] Remove legacy scheme support
- [ ] Major version bump

## Success Metrics

### Code Quality

- [ ] All path construction goes through resolver
- [ ] Zero hardcoded path patterns in new code
- [ ] 100% test coverage of path resolution logic
- [ ] All Python components pass type checking

### Testing

- [ ] All unit tests use isolated paths
- [ ] No file system dependencies in unit tests
- [ ] Integration tests cover both schemes
- [ ] Migration tests verify data integrity

### Documentation

- [ ] Integration guide for each component type
- [ ] Migration guide for users
- [ ] ADR documenting decision
- [ ] Updated README with new structure

### User Experience

- [ ] Zero breaking changes during migration
- [ ] Migration command completes successfully
- [ ] Rollback works if migration fails
- [ ] Performance same or better than current

## Related Documents

- [lib/paths.py](../../lib/paths.py) - Implementation
- [tests/unit/test_paths.py](../../tests/unit/test_paths.py) - Tests
- [docs/architecture/path-resolution-integration.md](../architecture/path-resolution-integration.md) - Integration guide
- [ADR-004: MIF Schema Validation](adr-004-mif-schema-validation.md) - Related MIF schema decision

## References

- [Martin Fowler - Dependency Injection](https://martinfowler.com/articles/injection.html)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [Test Double - Growing Object-Oriented Software](http://www.growing-object-oriented-software.com/)

## Approval

This ADR represents the architectural direction for path resolution in mnemonic. Implementation will proceed in phases as outlined above, with the core library considered stable and ready for integration.

**Next Steps**:
1. Merge core library to main branch
2. Begin Phase 2 integration with migration scripts
3. Update progress in this ADR as phases complete
