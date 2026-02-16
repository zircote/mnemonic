# Python API Reference

Complete reference for Mnemonic's Python libraries.

## Overview

Mnemonic provides Python libraries for path resolution, memory operations, search, ontology loading, and relationship management. These libraries power the hooks and can be used to extend the system.

## lib.paths

Centralized path resolution for all mnemonic memory operations.

### Classes

#### PathScheme

Path scheme versions for migration support.

````python
from lib.paths import PathScheme

PathScheme.LEGACY  # Current: dual location, flat namespace
PathScheme.V2      # Target: unified user-level, project hierarchy
````

#### Scope

Memory scope for organization.

````python
from lib.paths import Scope

Scope.USER     # Cross-project memories
Scope.PROJECT  # Project-specific memories
Scope.ORG      # Organization-wide memories (V2 only)
````

#### PathContext

Context information for path resolution.

````python
from lib.paths import PathContext

# Auto-detect context
context = PathContext.detect()

# Specify scheme
context = PathContext.detect(scheme=PathScheme.V2)

# Fields
context.org          # Organization name (from git remote)
context.project      # Project name (from git remote)
context.home_dir     # User home directory
context.project_dir  # Current project directory
context.scheme       # PathScheme to use
````

#### PathResolver

Central path resolver for all mnemonic operations.

````python
from lib.paths import PathResolver, Scope

# Initialize with auto-detected context
resolver = PathResolver()

# Initialize with custom context
resolver = PathResolver(context=custom_context)
````

**Methods:**

- **`get_memory_dir(namespace: str, scope: Scope) -> Path`**
  
  Get directory for storing memories.
  
  ````python
  memory_dir = resolver.get_memory_dir("_semantic/decisions", Scope.PROJECT)
  # Returns: /path/to/project/.claude/mnemonic/_semantic/decisions
  ````

- **`get_memory_path(namespace: str, filename: str, scope: Scope) -> Path`**
  
  Get full path for a memory file.
  
  ````python
  path = resolver.get_memory_path("_semantic/decisions", "slug.memory.md", Scope.PROJECT)
  ````

- **`get_search_paths(namespace: str, include_user: bool = True, include_project: bool = True, include_org: bool = False) -> list[Path]`**
  
  Get ordered list of paths to search for memories.
  
  ````python
  paths = resolver.get_search_paths("_semantic/decisions")
  # Returns: [project_path, user_path] (in priority order)
  ````

- **`get_blackboard_dir(scope: Scope) -> Path`**
  
  Get blackboard directory for cross-session coordination.
  
  ````python
  blackboard = resolver.get_blackboard_dir(Scope.PROJECT)
  ````

- **`get_ontology_paths() -> list[Path]`**
  
  Get ordered list of ontology file paths to check (project > user/org levels).
  Does not include the bundled MIF base ontology, which is resolved separately via `lib.ontology.get_ontology_file()`.

- **`get_all_memory_roots() -> list[Path]`**
  
  Get all memory root directories.

### Convenience Functions

````python
from lib.paths import (
    get_memory_dir,
    get_search_paths,
    get_blackboard_dir,
    get_all_memory_roots_with_legacy,
)

# Get memory directory (string scope)
memory_dir = get_memory_dir("_semantic/decisions", scope="project")

# Get full memory path
path = get_memory_path("_semantic/decisions", "slug.memory.md", scope="project")

# Get search paths
paths = get_search_paths("_semantic/decisions", include_user=True)

# Get blackboard
blackboard = get_blackboard_dir(scope="project")

# Get all memory roots
roots = get_all_memory_roots()
````

## lib.config

Configuration management.

### Classes

#### MnemonicConfig

````python
from lib.config import MnemonicConfig

# Load configuration
config = MnemonicConfig.load()

# Access fields
config.memory_store_path  # Path to memory root directory
````

### Functions

- **`get_memory_root() -> Path`**
  
  Get configured memory root directory.

## lib.memory_reader

Memory file metadata extraction.

### Functions

- **`get_memory_summary(path: str, max_summary: int = 300) -> dict`**
  
  Extract summary from memory file.
  
  ````python
  from lib.memory_reader import get_memory_summary
  
  summary = get_memory_summary("/path/to/memory.memory.md")
  # Returns: {"path": "...", "title": "...", "summary": "...", ...}
  ````

- **`get_memory_metadata(path: str, max_summary: int = 300) -> Optional[dict]`**
  
  Extract frontmatter metadata from memory file.
  
  ````python
  from lib.memory_reader import get_memory_metadata
  
  metadata = get_memory_metadata("/path/to/memory.memory.md")
  # Returns: {"id": "...", "type": "...", "title": "...", ...}
  ````

## lib.search

Memory search and scoring.

### Functions

- **`search_memories(topic: str, max_results: int = 3) -> list[str]`**
  
  Search mnemonic for memories matching topic.
  
  ````python
  from lib.search import search_memories
  
  results = search_memories("authentication", max_results=5)
  # Returns: ["/path/to/memory1.memory.md", "/path/to/memory2.memory.md", ...]
  ````

- **`find_related_memories(context: str, max_results: int = 3) -> list[str]`**
  
  Find memories related to given context.

- **`find_memories_for_context(context: dict) -> list[str]`**
  
  Find memories for file context dictionary.
  
  ````python
  from lib.search import find_memories_for_context
  
  context = {
      "file_path": "src/auth/login.py",
      "namespace": "_semantic/decisions",
      "keywords": "authentication login"
  }
  results = find_memories_for_context(context)
  ````

- **`detect_file_context(file_path: str, file_patterns: list) -> Optional[dict]`**
  
  Detect namespace and keywords from file path using ontology patterns.

- **`detect_namespace_for_file(file_path: str, file_patterns: list) -> str`**
  
  Detect namespace for a file path.

- **`extract_keywords_from_path(file_path: str) -> str`**
  
  Extract keywords from file path.

- **`extract_topic(prompt: str) -> str`**
  
  Extract topic keywords from user prompt.

- **`find_related_memories_scored(context: str, max_results: int = 10, threshold: float = 0.3) -> list[tuple[str, float]]`**
  
  Find related memories with relevance scores.
  
  ````python
  from lib.search import find_related_memories_scored
  
  results = find_related_memories_scored("database migration", max_results=10, threshold=0.5)
  # Returns: [("/path/to/memory.memory.md", 0.85), ...]
  ````

- **`find_duplicates(namespace: str = None, threshold: float = 0.8) -> list[tuple[str, str, float]]`**
  
  Find potential duplicate memories.

## lib.relationships

Memory relationship management.

### Functions

- **`to_pascal(snake: str) -> str`**
  
  Convert snake_case to PascalCase.

- **`to_snake(pascal: str) -> str`**
  
  Convert PascalCase to snake_case.

- **`get_inverse(rel_type: str) -> str`**
  
  Get inverse of a relationship type.
  
  ````python
  from lib.relationships import get_inverse
  
  inverse = get_inverse("supersedes")  # Returns: "SupersededBy"
  ````

- **`is_valid_type(rel_type: str) -> bool`**
  
  Check if relationship type is valid.

- **`is_symmetric(rel_type: str) -> bool`**
  
  Check if relationship type is symmetric.

- **`get_all_valid_types() -> set[str]`**
  
  Get all valid relationship types.

- **`add_relationship(memory_path: str, rel_type: str, target_id: str, label: str = None) -> bool`**
  
  Add a relationship to a memory file.
  
  ````python
  from lib.relationships import add_relationship
  
  success = add_relationship(
      memory_path="/path/to/source.memory.md",
      rel_type="relates_to",
      target_id="550e8400-e29b-41d4-a716-446655440000",
      label="Related decision"
  )
  ````

- **`add_bidirectional_relationship(source_path: str, target_path: str, rel_type: str, label: str = None) -> tuple[bool, bool]`**
  
  Add bidirectional relationship between two memories.

## lib.ontology

Ontology loading and management for the bundled MIF base ontology and any project/user ontologies.

### Functions

- **`get_ontology_file() -> Optional[Path]`**
  
  Get the path to the bundled MIF base ontology used as the fallback ontology.
  This does not return project or user custom ontology paths; those are
  discovered via `PathResolver.get_ontology_paths()`.

- **`load_ontology_data() -> dict`**
  
  Load ontology data starting from the bundled base ontology, and then apply
  any project/user ontologies discovered via `PathResolver.get_ontology_paths()`.

- **`load_file_patterns() -> list`**
  
  Load file discovery patterns from the effective ontology (base plus any
  discovered custom ontologies).

- **`load_content_patterns() -> dict`**
  
  Load content discovery patterns from the effective ontology.

- **`load_ontology_namespaces() -> list`**
  
  Load namespace hierarchy from the effective ontology.

- **`get_fallback_file_patterns() -> list`**
  
  Get default file patterns if no ontology exists.

- **`get_fallback_content_patterns() -> dict`**
  
  Get default content patterns if no ontology exists.

## Usage Examples

### Complete Memory Capture Workflow

````python
from lib.paths import PathResolver, Scope
from lib.ontology import load_ontology_data
from lib.relationships import add_relationship
import uuid
from datetime import datetime

# Initialize resolver
resolver = PathResolver()

# Generate memory metadata
memory_id = str(uuid.uuid4())
timestamp = datetime.utcnow().isoformat() + "Z"

# Get memory directory
namespace = "_semantic/decisions"
memory_dir = resolver.get_memory_dir(namespace, Scope.PROJECT)
memory_dir.mkdir(parents=True, exist_ok=True)

# Create memory file
filename = f"{memory_id[:8]}-use-postgresql.memory.md"
memory_path = resolver.get_memory_path(namespace, filename, Scope.PROJECT)

# Write memory with frontmatter
content = f"""---
id: {memory_id}
type: semantic
namespace: {namespace}
created: {timestamp}
modified: {timestamp}
title: "Use PostgreSQL for storage"
tags:
  - database
  - architecture
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: 0.95
---

# Use PostgreSQL for Storage

We decided to use PostgreSQL for our data storage needs.

## Rationale
- Strong ACID compliance
- Excellent JSON support
- Mature ecosystem
"""

memory_path.write_text(content)

# Add relationship to another memory
add_relationship(
    source_path=str(memory_path),
    target_id="a5e46807-6883-4fb2-be45-09872ae1a994",
    rel_type="relates_to",
    label="Related caching decision"
)
````

### Search and Retrieve Memories

````python
from lib.search import search_memories, find_related_memories_scored
from lib.memory_reader import get_memory_metadata

# Search for memories
results = search_memories("database", max_results=5)

# Get scored results
scored_results = find_related_memories_scored("authentication security", threshold=0.5)

# Read metadata
for path, score in scored_results[:3]:
    metadata = get_memory_metadata(path)
    if metadata:
        print(f"Title: {metadata['title']} (Score: {score:.2f})")
        print(f"Tags: {', '.join(metadata.get('tags', []))}")
````

### Custom Ontology Integration

````python
from lib.ontology import load_ontology_data, load_file_patterns
from lib.search import detect_file_context

# Load ontology
ontology = load_ontology_data()
file_patterns = load_file_patterns()

# Detect context for a file
context = detect_file_context("src/auth/login.py", file_patterns)
if context:
    print(f"Namespace: {context['namespace']}")
    print(f"Keywords: {context['keywords']}")
````

## Testing

All libraries support dependency injection for testing:

````python
from lib.paths import PathResolver, PathContext, PathScheme
from pathlib import Path

# Create test context
test_context = PathContext(
    org="test-org",
    project="test-project",
    home_dir=Path("/tmp/test-home"),
    project_dir=Path("/tmp/test-project"),
    scheme=PathScheme.V2
)

# Create resolver with test context
resolver = PathResolver(context=test_context)

# Now all paths use test context
memory_dir = resolver.get_memory_dir("_semantic/decisions", Scope.PROJECT)
# Returns: /tmp/test-project/.claude/mnemonic/_semantic/decisions
````

## See Also

- [Architecture](architecture.md) - System architecture overview
- [CLI Usage](cli-usage.md) - Command-line operations
- [lib/README.md](../lib/README.md) - Path resolution library details
- [Validation](validation.md) - Memory validation guide
