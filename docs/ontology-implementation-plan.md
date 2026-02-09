# Ontology Support Implementation Plan

**Status**: Awaiting Approval
**Target**: Mnemonic v2.0
**Timeline**: 5 weeks

## Executive Summary

This plan details the implementation of custom ontology support for mnemonic, enabling:
- Domain-specific knowledge management
- Entity types with mixin-based inheritance
- Agent-driven entity discovery
- URL-referenced shared ontologies
- Rich entity linking and relationships

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code CLI                        │
├─────────────────────────────────────────────────────────────┤
│  Plugin Layer                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Commands      │  │    Skills       │  │   Agents    │ │
│  │ • capture       │  │ • mnemonic-     │  │ • ontology- │ │
│  │ • ontology      │  │   ontology      │  │   discovery │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           └──────────────┬─────┴───────────────────┘        │
│                          │                                  │
├──────────────────────────┼──────────────────────────────────┤
│  Ontology Layer (NEW)    │                                  │
│  ┌───────────────────────▼───────────────────────────────┐ │
│  │              OntologyRegistry                         │ │
│  │  • Load ontology definitions                          │ │
│  │  • Merge base + user + project ontologies             │ │
│  │  • Resolve namespace → ontology mappings              │ │
│  └─────────────────────┬─────────────────────────────────┘ │
│                        │                                   │
│  ┌─────────────────────▼─────────────────────────────────┐ │
│  │              OntologyValidator                        │ │
│  │  • Validate ontology YAML against meta-schema         │ │
│  │  • Check entity type completeness                     │ │
│  │  • Verify trait compatibility                         │ │
│  └─────────────────────┬─────────────────────────────────┘ │
│                        │                                   │
│  ┌─────────────────────▼─────────────────────────────────┐ │
│  │              EntityResolver                           │ │
│  │  • Link entities across memories                      │ │
│  │  • Index entities for fast lookup                     │ │
│  │  • Resolve @[[entity]] references                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  Storage Layer                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │           Filesystem (.memory.md + .ontology.yaml)     ││
│  │  ┌─────────────────────┐  ┌─────────────────────────┐  ││
│  │  │  ~/.claude/         │  │  $MNEMONIC_ROOT/        │  ││
│  │  │  mnemonic/{org}/    │  │                         │  ││
│  │  │  ├── ontology.yaml  │  │  ├── ontology.yaml      │  ││
│  │  │  └── {namespace}/   │  │  └── {namespace}/       │  ││
│  │  └─────────────────────┘  └─────────────────────────┘  ││
│  └────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

## Phase 1: Core Infrastructure (Week 1-2)

### 1.1 Create Python Library Structure

**Files to create:**

```
lib/
├── __init__.py
├── ontology_registry.py
├── ontology_validator.py
└── entity_resolver.py
```

**lib/ontology_registry.py** (~400 lines):
```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import yaml

@dataclass
class EntityType:
    name: str
    description: str
    base: str  # semantic | episodic | procedural
    traits: List[str] = field(default_factory=list)
    schema: Dict = field(default_factory=dict)

@dataclass
class Trait:
    name: str
    fields: Dict

@dataclass
class Namespace:
    name: str
    description: str
    type_hint: str = "semantic"
    replaces: Optional[str] = None

@dataclass
class Ontology:
    id: str
    version: str
    description: str
    namespaces: Dict[str, Namespace] = field(default_factory=dict)
    entity_types: List[EntityType] = field(default_factory=list)
    traits: Dict[str, Trait] = field(default_factory=dict)
    relationships: Dict = field(default_factory=dict)
    discovery: Dict = field(default_factory=dict)
    schema_url: Optional[str] = None

class OntologyRegistry:
    def __init__(self):
        self._ontologies: Dict[str, Ontology] = {}
        self._namespace_map: Dict[str, str] = {}  # namespace -> ontology_id
        self._base_namespaces = [
            "apis", "blockers", "context", "decisions",
            "learnings", "patterns", "security", "testing", "episodic"
        ]

    def load_ontologies(self, paths: List[Path]) -> None:
        """Load ontologies from multiple paths with precedence."""
        for path in paths:
            self._load_from_path(path)

    def get_ontology(self, ontology_id: str) -> Optional[Ontology]:
        """Get ontology by ID."""
        return self._ontologies.get(ontology_id)

    def get_ontology_for_namespace(self, namespace: str) -> Optional[Ontology]:
        """Get ontology that defines a namespace."""
        ontology_id = self._namespace_map.get(namespace)
        return self._ontologies.get(ontology_id) if ontology_id else None

    def get_all_namespaces(self) -> List[str]:
        """Get all valid namespaces (base + custom)."""
        custom = list(self._namespace_map.keys())
        return list(set(self._base_namespaces + custom))

    def get_entity_type(self, namespace: str, type_name: str) -> Optional[EntityType]:
        """Get entity type definition."""
        ontology = self.get_ontology_for_namespace(namespace)
        if ontology:
            for et in ontology.entity_types:
                if et.name == type_name:
                    return et
        return None

    def is_custom_namespace(self, namespace: str) -> bool:
        """Check if namespace is custom (not base)."""
        return namespace not in self._base_namespaces

    def _load_from_path(self, path: Path) -> None:
        """Load ontology from a path."""
        ontology_file = path / "ontology.yaml"
        if ontology_file.exists():
            with open(ontology_file) as f:
                data = yaml.safe_load(f)
            ontology = self._parse_ontology(data)
            self._register_ontology(ontology)

    def _parse_ontology(self, data: dict) -> Ontology:
        """Parse ontology from YAML data."""
        # Implementation details...
        pass

    def _register_ontology(self, ontology: Ontology) -> None:
        """Register ontology and update mappings."""
        self._ontologies[ontology.id] = ontology
        for ns_name in ontology.namespaces:
            self._namespace_map[ns_name] = ontology.id
```

### 1.2 Create Ontology Meta-Schema

**ontologies/schemas/ontology-meta-schema.json** (~200 lines):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://mnemonic.org/schemas/ontology/v1",
  "title": "Mnemonic Ontology Schema",
  "type": "object",
  "required": ["ontology"],
  "properties": {
    "ontology": {
      "type": "object",
      "required": ["id", "version"],
      "properties": {
        "id": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "description": {"type": "string"},
        "schema_url": {"type": "string", "format": "uri"}
      }
    },
    "namespaces": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "description": {"type": "string"},
          "type_hint": {"enum": ["semantic", "episodic", "procedural"]},
          "replaces": {"type": "string"}
        }
      }
    },
    "entity_types": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "base"],
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "base": {"enum": ["semantic", "episodic", "procedural"]},
          "traits": {"type": "array", "items": {"type": "string"}},
          "schema": {"$ref": "#/$defs/entitySchema"}
        }
      }
    },
    "traits": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["fields"],
        "properties": {
          "fields": {"type": "object"}
        }
      }
    },
    "relationships": {
      "type": "object"
    },
    "discovery": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean"},
        "patterns": {"type": "array"},
        "confidence_threshold": {"type": "number", "minimum": 0, "maximum": 1}
      }
    }
  },
  "$defs": {
    "entitySchema": {
      "type": "object",
      "properties": {
        "required": {"type": "array", "items": {"type": "string"}},
        "properties": {"type": "object"}
      }
    }
  }
}
```

### 1.3 Create Base Ontology

**ontologies/base.ontology.yaml** (~100 lines):
```yaml
ontology:
  id: mnemonic-base
  version: "1.0.0"
  description: "Base mnemonic namespaces (backward compatibility)"

namespaces:
  apis:
    description: "API documentation, contracts, endpoints"
    type_hint: semantic

  blockers:
    description: "Issues, impediments, incidents"
    type_hint: episodic

  context:
    description: "Background information, environment state"
    type_hint: semantic

  decisions:
    description: "Architectural choices with rationale"
    type_hint: semantic

  learnings:
    description: "Insights, discoveries, TILs"
    type_hint: semantic

  patterns:
    description: "Code conventions, best practices"
    type_hint: procedural

  security:
    description: "Security policies, vulnerabilities"
    type_hint: semantic

  testing:
    description: "Test strategies, edge cases"
    type_hint: procedural

  episodic:
    description: "General events, experiences"
    type_hint: episodic

# No custom entity types in base ontology
# No traits in base ontology
# No discovery patterns in base ontology
```

### 1.4 Modify Session Start Hook

**hooks/session_start.py** (add ~30 lines):
```python
# Add to imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from ontology_registry import OntologyRegistry

# Add to startup
def load_ontologies() -> OntologyRegistry:
    """Load ontologies from user and project directories."""
    registry = OntologyRegistry()

    # Load paths in precedence order (later overrides earlier)
    paths = [
        Path(__file__).parent.parent / "ontologies",  # Base ontologies
        Path.home() / ".claude" / "mnemonic",          # User ontologies
        Path.cwd() / ".claude" / "mnemonic",           # Project ontologies
    ]

    registry.load_ontologies(paths)
    return registry

# Use in context generation
def get_ontology_context() -> str:
    """Generate ontology context for additionalContext."""
    registry = load_ontologies()
    namespaces = registry.get_all_namespaces()
    custom = [ns for ns in namespaces if registry.is_custom_namespace(ns)]

    if custom:
        return f"**Custom ontology namespaces:** {', '.join(custom)}"
    return ""
```

### 1.5 Unit Tests

**tests/test_ontology_registry.py** (~200 lines):
```python
import pytest
from pathlib import Path
from lib.ontology_registry import OntologyRegistry, Ontology, EntityType

def test_load_base_ontology():
    """Test loading base ontology."""
    registry = OntologyRegistry()
    registry.load_ontologies([Path("ontologies")])

    assert "apis" in registry.get_all_namespaces()
    assert "decisions" in registry.get_all_namespaces()
    assert registry.is_custom_namespace("apis") == False

def test_load_custom_ontology(tmp_path):
    """Test loading custom ontology."""
    ontology_yaml = tmp_path / "ontology.yaml"
    ontology_yaml.write_text("""
ontology:
  id: test-ontology
  version: "1.0.0"

namespaces:
  custom-ns:
    description: "Custom namespace"
    type_hint: semantic
""")

    registry = OntologyRegistry()
    registry.load_ontologies([tmp_path])

    assert "custom-ns" in registry.get_all_namespaces()
    assert registry.is_custom_namespace("custom-ns") == True

def test_namespace_precedence(tmp_path):
    """Test that project ontology overrides user ontology."""
    # Create user ontology
    user_dir = tmp_path / "user"
    user_dir.mkdir()
    (user_dir / "ontology.yaml").write_text("""
ontology:
  id: user-ontology
  version: "1.0.0"

namespaces:
  shared-ns:
    description: "User version"
""")

    # Create project ontology
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "ontology.yaml").write_text("""
ontology:
  id: project-ontology
  version: "1.0.0"

namespaces:
  shared-ns:
    description: "Project version"
""")

    registry = OntologyRegistry()
    registry.load_ontologies([user_dir, project_dir])

    ontology = registry.get_ontology_for_namespace("shared-ns")
    assert ontology.id == "project-ontology"  # Project wins

def test_entity_type_lookup():
    """Test entity type lookup."""
    # Test implementation...
    pass
```

---

## Phase 2: Entity Management (Week 2-3)

### 2.1 Create Entity Resolver

**lib/entity_resolver.py** (~300 lines):
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import re

@dataclass
class Entity:
    id: str
    type: str
    name: str
    memory_path: Path
    ontology_id: str

@dataclass
class EntityLink:
    from_entity: str
    to_entity: str
    relationship: str

class EntityResolver:
    def __init__(self, registry: 'OntologyRegistry'):
        self.registry = registry
        self._index: Dict[str, Entity] = {}
        self._links: List[EntityLink] = []

    def resolve_entity(self, entity_ref: str) -> Optional[Entity]:
        """Resolve @[[entity]] or [[type:id]] reference."""
        # Parse reference format
        if entity_ref.startswith("@[["):
            # Simple entity reference: @[[PostgreSQL]]
            name = entity_ref[3:-2]
            return self._find_by_name(name)
        elif ":" in entity_ref:
            # Typed reference: [[component:stripe-integration]]
            type_name, entity_id = entity_ref.split(":", 1)
            return self._find_by_type_and_id(type_name, entity_id)
        return None

    def index_memory(self, memory_path: Path) -> List[Entity]:
        """Index entities from a memory file."""
        # Parse frontmatter for entity fields
        # Return list of discovered entities
        pass

    def find_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Find all entities of a specific type."""
        return [e for e in self._index.values() if e.type == entity_type]

    def get_relationships(self, entity_id: str) -> List[EntityLink]:
        """Get relationships for an entity."""
        return [l for l in self._links
                if l.from_entity == entity_id or l.to_entity == entity_id]

    def search_entities(self, query: str) -> List[Entity]:
        """Search entities using ripgrep."""
        try:
            result = subprocess.run(
                ["rg", "-i", "-l", f"entity_id:.*{query}", "--glob", "*.memory.md"],
                capture_output=True,
                text=True,
                cwd=str(Path.home() / ".claude" / "mnemonic"),
                timeout=5
            )
            # Parse results...
        except Exception:
            return []

    def _find_by_name(self, name: str) -> Optional[Entity]:
        """Find entity by name (case-insensitive)."""
        for entity in self._index.values():
            if entity.name.lower() == name.lower():
                return entity
        return None

    def _find_by_type_and_id(self, type_name: str, entity_id: str) -> Optional[Entity]:
        """Find entity by type and ID."""
        key = f"{type_name}:{entity_id}"
        return self._index.get(key)
```

### 2.2 Update Validator for Ontology

**tools/mnemonic-validate** (add ~150 lines):
```python
# Add import
from lib.ontology_registry import OntologyRegistry

# Modify validate_memory function
def validate_memory_with_ontology(
    file_path: Path,
    schema: MIFSchema,
    registry: OntologyRegistry = None,
    ...
) -> ValidationResult:
    """Validate memory with ontology support."""
    result = ValidationResult(file_path=file_path)

    # ... existing validation ...

    # NEW: Ontology validation
    if registry and "ontology" in frontmatter:
        ontology_data = frontmatter["ontology"]
        ontology_id = ontology_data.get("id")
        entity_type = ontology_data.get("entity_type")

        ontology = registry.get_ontology(ontology_id)
        if not ontology:
            result.warnings.append(ValidationWarning(
                field="ontology.id",
                message=f"Unknown ontology: {ontology_id}"
            ))
        else:
            # Validate entity type
            et = registry.get_entity_type(
                frontmatter.get("namespace", "").split("/")[0],
                entity_type
            )
            if et:
                # Validate required fields from entity schema
                entity_data = frontmatter.get("entity", {})
                for required in et.schema.get("required", []):
                    if required not in entity_data:
                        result.errors.append(ValidationError(
                            field=f"entity.{required}",
                            message=f"Required field missing for {entity_type}"
                        ))

                # Validate trait fields
                for trait_name in et.traits:
                    trait = ontology.traits.get(trait_name)
                    if trait:
                        for field_name in trait.fields:
                            if field_name not in entity_data:
                                result.warnings.append(ValidationWarning(
                                    field=f"entity.{field_name}",
                                    message=f"Trait '{trait_name}' field missing"
                                ))

    return result
```

---

## Phase 3: Commands and Discovery (Week 3-4)

### 3.1 Create Ontology Command

**commands/ontology.md** (~200 lines):
```markdown
---
description: Manage ontologies
argument-hint: "<subcommand> [options]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# /mnemonic:ontology

Manage custom ontologies for mnemonic.

## Subcommands

### list
List active ontologies and their namespaces.

```bash
python3 "$CLAUDE_PLUGIN_ROOT/lib/ontology_registry.py" --list
```

### validate
Validate an ontology definition file.

```bash
python3 "$CLAUDE_PLUGIN_ROOT/lib/ontology_validator.py" \
  --file "${1:-$MNEMONIC_ROOT/ontology.yaml}"
```

### add
Add an ontology from a URL.

```bash
URL="$1"
CACHE_DIR="$MNEMONIC_ROOT/.ontologies/.cache"
mkdir -p "$CACHE_DIR"
curl -sL "$URL" -o "$CACHE_DIR/$(basename $URL)"
echo "Ontology cached. Add to registry to activate."
```

### init
Initialize an ontology template.

```bash
TEMPLATE="${1:-minimal}"
cp "$CLAUDE_PLUGIN_ROOT/ontologies/templates/${TEMPLATE}.yaml" \
   "$MNEMONIC_ROOT/ontology.yaml"
echo "Created $MNEMONIC_ROOT/ontology.yaml from $TEMPLATE template"
```

### namespaces
List all valid namespaces.

```bash
python3 -c "
from lib.ontology_registry import OntologyRegistry
from pathlib import Path

registry = OntologyRegistry()
registry.load_ontologies([
    Path('$CLAUDE_PLUGIN_ROOT/ontologies'),
    Path.home() / '.claude' / 'mnemonic',
    Path.cwd() / '.claude' / 'mnemonic'
])

for ns in sorted(registry.get_all_namespaces()):
    custom = '(custom)' if registry.is_custom_namespace(ns) else ''
    print(f'  {ns} {custom}')
"
```
```

### 3.2 Modify Capture Command

**commands/capture.md** (modify ~50 lines):
```markdown
### Step 2: Validate Namespace (MODIFIED)

```bash
# Load namespaces from ontology registry
VALID_NS=$(python3 -c "
import sys
sys.path.insert(0, '$CLAUDE_PLUGIN_ROOT/lib')
from ontology_registry import OntologyRegistry
from pathlib import Path

registry = OntologyRegistry()
registry.load_ontologies([
    Path('$CLAUDE_PLUGIN_ROOT/ontologies'),
    Path.home() / '.claude' / 'mnemonic',
    Path.cwd() / '.claude' / 'mnemonic'
])
print(' '.join(registry.get_all_namespaces()))
")

if ! echo "$VALID_NS" | grep -qw "$NAMESPACE"; then
    echo "Error: Invalid namespace '$NAMESPACE'"
    echo "Valid namespaces: $VALID_NS"
    echo ""
    echo "To add custom namespaces, create $MNEMONIC_ROOT/ontology.yaml"
    exit 1
fi
```

### Step 6b: Entity Type Validation (NEW)

```bash
# If namespace is custom, check for entity type
IS_CUSTOM=$(python3 -c "
from lib.ontology_registry import OntologyRegistry
# ... check if namespace is custom and requires entity type
")

if [ "$IS_CUSTOM" = "true" ] && [ -n "$ENTITY_TYPE" ]; then
    # Get entity schema and validate required fields
    ENTITY_SCHEMA=$(python3 -c "
from lib.ontology_registry import OntologyRegistry
# ... get entity type schema
")

    # Prompt for required entity fields
    for FIELD in $REQUIRED_FIELDS; do
        read -p "$FIELD: " VALUE
        ENTITY_FIELDS="$ENTITY_FIELDS
  $FIELD: $VALUE"
    done
fi
```

### Step 7: Create Memory File (MODIFIED)

Add ontology section to frontmatter:

```yaml
---
id: {UUID}
type: {TYPE}
namespace: {NAMESPACE}/{SCOPE}
created: {DATE}
title: "{TITLE}"

# NEW: Ontology metadata (if custom namespace)
ontology:
  id: {ONTOLOGY_ID}
  entity_type: {ENTITY_TYPE}
  entity_id: {ENTITY_ID}

# NEW: Entity-specific fields (if entity type)
entity:
{ENTITY_FIELDS}

tags:
{TAGS_YAML}
---
```
```

### 3.3 Create Discovery Agent

**agents/ontology-discovery.md** (~250 lines):
```markdown
---
description: Discover and suggest entities from memory content
model: haiku
allowed-tools:
  - Bash
  - Grep
  - Read
  - Write
---

# Ontology Discovery Agent

Autonomous agent for discovering and suggesting entities from memory content.

## Purpose

Analyze memory content to identify potential entities based on ontology patterns.
Suggest entities to user for confirmation. Create entity memories when confirmed.

## Workflow

### 1. Load Discovery Patterns

```bash
# Get patterns from active ontologies
PATTERNS=$(python3 -c "
from lib.ontology_registry import OntologyRegistry
from pathlib import Path
import json

registry = OntologyRegistry()
registry.load_ontologies([
    Path('$CLAUDE_PLUGIN_ROOT/ontologies'),
    Path.home() / '.claude' / 'mnemonic',
    Path.cwd() / '.claude' / 'mnemonic'
])

patterns = {}
for ontology_id, ontology in registry._ontologies.items():
    if ontology.discovery.get('enabled'):
        for pattern in ontology.discovery.get('patterns', []):
            patterns[pattern['suggest_entity']] = pattern['content_pattern']

print(json.dumps(patterns))
")
```

### 2. Scan Memory Content

```bash
# For each pattern, search memories
for ENTITY_TYPE in $(echo $PATTERNS | jq -r 'keys[]'); do
    PATTERN=$(echo $PATTERNS | jq -r ".[\"$ENTITY_TYPE\"]")

    # Find matches using ripgrep
    MATCHES=$(rg -i "$PATTERN" ${MNEMONIC_ROOT}/ $MNEMONIC_ROOT/ \
        --glob "*.memory.md" -o | sort | uniq -c | sort -rn | head -10)

    echo "Potential $ENTITY_TYPE entities:"
    echo "$MATCHES"
done
```

### 3. Suggest to User

For each discovered entity with confidence above threshold:

```markdown
**Entity Discovery Results**

I found the following potential entities:

| Entity | Type | Mentions | Confidence |
|--------|------|----------|------------|
| PostgreSQL | technology | 12 | 0.95 |
| Repository Pattern | pattern | 8 | 0.88 |
| Redis | technology | 5 | 0.75 |

Would you like me to create entity memories for any of these?
Reply with entity names to confirm (e.g., "PostgreSQL, Repository Pattern")
```

### 4. Create Entity Memories

When user confirms:

```bash
# Create entity memory
/mnemonic:capture apis "$ENTITY_NAME" \
  --type semantic \
  --tags entity,$ENTITY_TYPE \
  --scope user
```

### 5. Update Source Memories with Links

```bash
# Find memories mentioning the entity
MEMORIES=$(rg -l "$ENTITY_NAME" ${MNEMONIC_ROOT}/ --glob "*.memory.md")

for MEMORY in $MEMORIES; do
    # Add entity_links to frontmatter
    # This is done by reading and rewriting the memory
done
```

## Trigger Conditions

- Manual: `/mnemonic:ontology discover`
- Automatic: After session with 5+ new captures
- Scheduled: Weekly curation via memory-curator agent

## Output

Reports discovered entities and actions taken:

```json
{
  "discovered": [
    {"entity": "PostgreSQL", "type": "technology", "mentions": 12, "action": "created"},
    {"entity": "Repository Pattern", "type": "pattern", "mentions": 8, "action": "linked"},
    {"entity": "Redis", "type": "technology", "mentions": 5, "action": "skipped"}
  ],
  "memories_updated": 15,
  "new_entities_created": 2
}
```
```

---

## Phase 4: Documentation (Week 4-5)

### 4.1 User Guide

**docs/ontologies.md** (~800 lines):
- Introduction to custom ontologies
- Ontology definition format reference
- Step-by-step guide for creating ontologies
- Entity types and traits explained
- Discovery configuration
- Example ontologies for common domains
- Migration from hardcoded namespaces
- Troubleshooting guide

### 4.2 Ontology Skill

**skills/mnemonic-ontology/SKILL.md** (~300 lines):
- Trigger phrases
- Available operations
- Ontology management workflow
- Entity linking syntax
- Best practices

### 4.3 Example Ontologies

**ontologies/examples/software-engineering.yaml** (~150 lines):
```yaml
ontology:
  id: software-engineering
  version: "1.0.0"
  description: "Software engineering domain ontology"

namespaces:
  architecture:
    description: "System architecture decisions"
    type_hint: semantic

  components:
    description: "Software components and modules"
    type_hint: semantic

  incidents:
    description: "Production incidents"
    type_hint: episodic

entity_types:
  - name: component
    base: semantic
    traits: [versioned, documented]
    schema:
      required: [name, responsibility]
      properties:
        name: {type: string}
        responsibility: {type: string}
        dependencies: {type: array}
        interfaces: {type: array}

  - name: architectural-decision
    base: semantic
    traits: [dated, cited]
    schema:
      required: [decision, rationale]
      properties:
        decision: {type: string}
        rationale: {type: string}
        alternatives: {type: array}
        consequences: {type: object}

traits:
  versioned:
    fields:
      version: {type: string}
      changelog: {type: array}

  documented:
    fields:
      documentation_url: {type: string, format: uri}

  dated:
    fields:
      decision_date: {type: string, format: date}

  cited:
    requires: [citations]

relationships:
  depends_on:
    from: [component]
    to: [component]
  implements:
    from: [component]
    to: [architectural-decision]

discovery:
  enabled: true
  patterns:
    - content_pattern: "\\b(PostgreSQL|MySQL|Redis|MongoDB|Elasticsearch)\\b"
      suggest_entity: technology
    - content_pattern: "\\b(Factory|Singleton|Observer|Repository|Adapter)\\s+Pattern\\b"
      suggest_entity: pattern
  confidence_threshold: 0.8
```

---

## Success Criteria

- [ ] Custom namespaces work in capture command
- [ ] Entity types with traits validate correctly
- [ ] Entity linking syntax (`@[[entity]]`) resolves
- [ ] Discovery agent suggests entities from code/docs
- [ ] URL-referenced ontologies load and cache
- [ ] Existing memories continue to validate
- [ ] Performance: <100ms ontology load, <50ms entity resolution

## Testing Plan

1. **Unit Tests**: Registry, validator, resolver
2. **Integration Tests**: Full capture flow with custom ontology
3. **Fixture Ontologies**: Test YAML files in CI/CD
4. **Backward Compatibility**: Existing memories still valid
5. **Performance**: Benchmark with 1000+ memories

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Ontology conflicts | Clear precedence rules (project > user > base) |
| Schema complexity | Start simple, progressive disclosure |
| Discovery false positives | User confirmation required, confidence threshold |
| Performance degradation | Lazy loading, caching, ripgrep |
