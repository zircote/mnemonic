#!/usr/bin/env python3
"""
Ontology Registry for Mnemonic

Manages loading, parsing, and querying of custom ontology definitions.
Supports YAML-based ontology files with URL-referenced schemas.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import hashlib
import json
import logging
import os
import re

try:
    import yaml
except ImportError:
    yaml = None  # Handle gracefully in load methods

logger = logging.getLogger(__name__)


@dataclass
class Trait:
    """A mixin/trait that can be composed into entity types."""

    name: str
    fields: Dict[str, Any] = field(default_factory=dict)
    requires: List[str] = field(default_factory=list)
    description: str = ""

    def get_field_names(self) -> List[str]:
        """Get all field names from this trait."""
        return list(self.fields.keys())


@dataclass
class EntityType:
    """An entity type definition with optional trait inheritance."""

    name: str
    base: str  # semantic | episodic | procedural
    description: str = ""
    traits: List[str] = field(default_factory=list)
    schema: Dict[str, Any] = field(default_factory=dict)

    def get_required_fields(self) -> List[str]:
        """Get required fields from schema."""
        return self.schema.get("required", [])

    def get_properties(self) -> Dict[str, Any]:
        """Get property definitions from schema."""
        return self.schema.get("properties", {})


@dataclass
class Namespace:
    """A namespace definition for organizing memories."""

    name: str
    description: str = ""
    type_hint: str = "semantic"  # Default memory type for this namespace
    replaces: Optional[str] = None  # Base namespace this replaces

    @property
    def is_replacement(self) -> bool:
        """Check if this namespace replaces a base namespace."""
        return self.replaces is not None


@dataclass
class Relationship:
    """A relationship type between entities."""

    name: str
    from_types: List[str] = field(default_factory=list)
    to_types: List[str] = field(default_factory=list)
    symmetric: bool = False
    description: str = ""


@dataclass
class DiscoveryPattern:
    """A pattern for discovering entities in content."""

    pattern_type: str  # content_pattern | file_pattern
    pattern: str  # Regex pattern
    suggest_entity: str  # Entity type to suggest


@dataclass
class DiscoveryConfig:
    """Configuration for entity discovery."""

    enabled: bool = False
    patterns: List[DiscoveryPattern] = field(default_factory=list)
    confidence_threshold: float = 0.8


@dataclass
class Ontology:
    """A complete ontology definition."""

    id: str
    version: str
    description: str = ""
    schema_url: Optional[str] = None
    source_path: Optional[Path] = None

    namespaces: Dict[str, Namespace] = field(default_factory=dict)
    entity_types: Dict[str, EntityType] = field(default_factory=dict)
    traits: Dict[str, Trait] = field(default_factory=dict)
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)

    def get_namespace(self, name: str) -> Optional[Namespace]:
        """Get namespace by name."""
        return self.namespaces.get(name)

    def get_entity_type(self, name: str) -> Optional[EntityType]:
        """Get entity type by name."""
        return self.entity_types.get(name)

    def get_trait(self, name: str) -> Optional[Trait]:
        """Get trait by name."""
        return self.traits.get(name)

    def get_entity_type_with_traits(self, name: str) -> tuple[Optional[EntityType], List[Trait]]:
        """Get entity type with its resolved traits."""
        entity_type = self.get_entity_type(name)
        if not entity_type:
            return None, []

        traits = []
        for trait_name in entity_type.traits:
            trait = self.get_trait(trait_name)
            if trait:
                traits.append(trait)

        return entity_type, traits


class OntologyRegistry:
    """
    Registry for managing ontology definitions.

    Loads ontologies from multiple paths with precedence:
    1. Base ontologies (built-in)
    2. User ontologies (~/.claude/mnemonic/)
    3. Project ontologies (./.claude/mnemonic/)

    Later sources override earlier ones for the same namespace.
    """

    BASE_NAMESPACES = [
        "apis",
        "blockers",
        "context",
        "decisions",
        "learnings",
        "patterns",
        "security",
        "testing",
        "episodic",
    ]

    BASE_TYPES = ["semantic", "episodic", "procedural"]

    def __init__(self):
        self._ontologies: Dict[str, Ontology] = {}
        self._namespace_map: Dict[str, str] = {}  # namespace -> ontology_id
        self._url_cache_dir: Optional[Path] = None
        self._loaded = False

    def load_ontologies(self, paths: List[Path]) -> None:
        """
        Load ontologies from multiple paths.

        Args:
            paths: List of paths to search for ontology.yaml files.
                   Later paths have higher precedence.
        """
        if yaml is None:
            logger.warning("PyYAML not installed, ontology loading disabled")
            return

        for path in paths:
            if not path.exists():
                continue
            self._load_from_path(path)

        self._loaded = True
        logger.info(f"Loaded {len(self._ontologies)} ontologies with {len(self._namespace_map)} custom namespaces")

    def load_from_url(self, url: str, cache_dir: Optional[Path] = None) -> Optional[Ontology]:
        """
        Load an ontology from a URL.

        Args:
            url: URL to fetch ontology YAML from
            cache_dir: Directory to cache downloaded ontologies

        Returns:
            Parsed Ontology or None if loading fails
        """
        try:
            import urllib.request

            # Create cache directory
            if cache_dir:
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file = cache_dir / f"{self._url_hash(url)}.yaml"

                # Check cache first
                if cache_file.exists():
                    with open(cache_file) as f:
                        data = yaml.safe_load(f)
                    return self._parse_ontology(data, source_path=cache_file)

            # Fetch from URL
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode("utf-8")

            # Cache if directory provided
            if cache_dir:
                cache_file.write_text(content)

            data = yaml.safe_load(content)
            return self._parse_ontology(data)

        except Exception as e:
            logger.error(f"Failed to load ontology from URL {url}: {e}")
            return None

    def get_ontology(self, ontology_id: str) -> Optional[Ontology]:
        """Get ontology by ID."""
        return self._ontologies.get(ontology_id)

    def get_ontology_for_namespace(self, namespace: str) -> Optional[Ontology]:
        """Get the ontology that defines a namespace."""
        ontology_id = self._namespace_map.get(namespace)
        return self._ontologies.get(ontology_id) if ontology_id else None

    def get_all_namespaces(self) -> List[str]:
        """Get all valid namespaces (base + custom)."""
        custom = list(self._namespace_map.keys())
        return sorted(set(self.BASE_NAMESPACES + custom))

    def get_custom_namespaces(self) -> List[str]:
        """Get only custom namespaces."""
        return sorted(self._namespace_map.keys())

    def get_all_types(self) -> List[str]:
        """Get all valid memory types (base + custom entity types)."""
        custom_types = []
        for ontology in self._ontologies.values():
            custom_types.extend(ontology.entity_types.keys())
        return sorted(set(self.BASE_TYPES + custom_types))

    def get_entity_type(self, namespace: str, type_name: str) -> Optional[EntityType]:
        """Get entity type definition for a namespace."""
        ontology = self.get_ontology_for_namespace(namespace)
        if ontology:
            return ontology.get_entity_type(type_name)
        return None

    def get_entity_types_for_namespace(self, namespace: str) -> List[EntityType]:
        """Get all entity types for a namespace."""
        ontology = self.get_ontology_for_namespace(namespace)
        if ontology:
            return list(ontology.entity_types.values())
        return []

    def is_custom_namespace(self, namespace: str) -> bool:
        """Check if namespace is custom (not a base namespace)."""
        return namespace not in self.BASE_NAMESPACES

    def is_custom_type(self, type_name: str) -> bool:
        """Check if type is a custom entity type."""
        return type_name not in self.BASE_TYPES

    def get_discovery_patterns(self, namespace: Optional[str] = None) -> List[tuple[str, DiscoveryPattern]]:
        """
        Get discovery patterns from all ontologies.

        Args:
            namespace: If provided, only get patterns for this namespace

        Returns:
            List of (ontology_id, pattern) tuples
        """
        patterns = []
        for ontology_id, ontology in self._ontologies.items():
            if not ontology.discovery.enabled:
                continue
            if namespace and namespace not in ontology.namespaces:
                continue
            for pattern in ontology.discovery.patterns:
                patterns.append((ontology_id, pattern))
        return patterns

    def validate_namespace(self, namespace: str) -> bool:
        """Check if a namespace is valid."""
        return namespace in self.get_all_namespaces()

    def validate_type(self, type_name: str) -> bool:
        """Check if a type is valid."""
        return type_name in self.get_all_types()

    def list_ontologies(self) -> List[Dict[str, Any]]:
        """List all loaded ontologies with metadata."""
        return [
            {
                "id": ont.id,
                "version": ont.version,
                "description": ont.description,
                "namespaces": list(ont.namespaces.keys()),
                "entity_types": list(ont.entity_types.keys()),
                "source": str(ont.source_path) if ont.source_path else None,
            }
            for ont in self._ontologies.values()
        ]

    def _load_from_path(self, path: Path) -> None:
        """Load ontology from a path."""
        ontology_file = path / "ontology.yaml"
        if not ontology_file.exists():
            # Also check for .yaml variants in ontologies subdirectory
            ontologies_dir = path / "ontologies"
            if ontologies_dir.exists():
                for yaml_file in ontologies_dir.glob("*.yaml"):
                    self._load_ontology_file(yaml_file)
            return

        self._load_ontology_file(ontology_file)

    def _load_ontology_file(self, file_path: Path) -> None:
        """Load a single ontology file."""
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            if not data:
                return

            ontology = self._parse_ontology(data, source_path=file_path)
            if ontology:
                self._register_ontology(ontology)

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load ontology from {file_path}: {e}")

    def _parse_ontology(self, data: Dict[str, Any], source_path: Optional[Path] = None) -> Optional[Ontology]:
        """Parse ontology from YAML data."""
        ont_data = data.get("ontology", data)

        if "id" not in ont_data:
            logger.warning("Ontology missing required 'id' field")
            return None

        ontology = Ontology(
            id=ont_data.get("id"),
            version=ont_data.get("version", "1.0.0"),
            description=ont_data.get("description", ""),
            schema_url=ont_data.get("schema_url"),
            source_path=source_path,
        )

        # Parse namespaces
        for ns_name, ns_data in data.get("namespaces", {}).items():
            if isinstance(ns_data, str):
                ns_data = {"description": ns_data}
            ontology.namespaces[ns_name] = Namespace(
                name=ns_name,
                description=ns_data.get("description", ""),
                type_hint=ns_data.get("type_hint", "semantic"),
                replaces=ns_data.get("replaces"),
            )

        # Parse entity types
        entity_types_data = data.get("entity_types", [])
        if isinstance(entity_types_data, dict):
            entity_types_data = [{"name": k, **v} for k, v in entity_types_data.items()]

        for et_data in entity_types_data:
            name = et_data.get("name")
            if not name:
                continue
            ontology.entity_types[name] = EntityType(
                name=name,
                base=et_data.get("base", "semantic"),
                description=et_data.get("description", ""),
                traits=et_data.get("traits", []),
                schema=et_data.get("schema", {}),
            )

        # Parse traits
        for trait_name, trait_data in data.get("traits", {}).items():
            ontology.traits[trait_name] = Trait(
                name=trait_name,
                fields=trait_data.get("fields", {}),
                requires=trait_data.get("requires", []),
                description=trait_data.get("description", ""),
            )

        # Parse relationships
        for rel_name, rel_data in data.get("relationships", {}).items():
            if isinstance(rel_data, dict):
                ontology.relationships[rel_name] = Relationship(
                    name=rel_name,
                    from_types=rel_data.get("from", []),
                    to_types=rel_data.get("to", []),
                    symmetric=rel_data.get("symmetric", False),
                    description=rel_data.get("description", ""),
                )

        # Parse discovery config
        discovery_data = data.get("discovery", {})
        if discovery_data:
            patterns = []
            for p in discovery_data.get("patterns", []):
                pattern_type = "content_pattern" if "content_pattern" in p else "file_pattern"
                patterns.append(
                    DiscoveryPattern(
                        pattern_type=pattern_type,
                        pattern=p.get(pattern_type, p.get("pattern", "")),
                        suggest_entity=p.get("suggest_entity", ""),
                    )
                )
            ontology.discovery = DiscoveryConfig(
                enabled=discovery_data.get("enabled", False),
                patterns=patterns,
                confidence_threshold=discovery_data.get("confidence_threshold", 0.8),
            )

        return ontology

    def _register_ontology(self, ontology: Ontology) -> None:
        """Register ontology and update namespace mappings."""
        self._ontologies[ontology.id] = ontology

        for ns_name in ontology.namespaces:
            self._namespace_map[ns_name] = ontology.id
            logger.debug(f"Registered namespace '{ns_name}' -> ontology '{ontology.id}'")

    def _url_hash(self, url: str) -> str:
        """Generate hash for URL caching."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]


# Convenience functions for CLI usage
def get_registry(
    base_path: Optional[Path] = None,
    user_path: Optional[Path] = None,
    project_path: Optional[Path] = None,
) -> OntologyRegistry:
    """
    Get a configured OntologyRegistry.

    Args:
        base_path: Path to base ontologies (defaults to plugin ontologies/)
        user_path: Path to user ontologies (defaults to ~/.claude/mnemonic/)
        project_path: Path to project ontologies (defaults to ./.claude/mnemonic/)

    Returns:
        Configured OntologyRegistry
    """
    registry = OntologyRegistry()

    paths = []

    # Base ontologies
    if base_path:
        paths.append(base_path)
    else:
        # Try to find plugin root
        plugin_root = Path(__file__).parent.parent
        if (plugin_root / "ontologies").exists():
            paths.append(plugin_root / "ontologies")

    # User ontologies
    if user_path:
        paths.append(user_path)
    else:
        paths.append(Path.home() / ".claude" / "mnemonic")

    # Project ontologies
    if project_path:
        paths.append(project_path)
    else:
        paths.append(Path.cwd() / ".claude" / "mnemonic")

    registry.load_ontologies(paths)
    return registry


def main():
    """CLI interface for ontology registry."""
    import argparse

    parser = argparse.ArgumentParser(description="Mnemonic Ontology Registry")
    parser.add_argument("--list", action="store_true", help="List all ontologies")
    parser.add_argument("--list-namespaces", action="store_true", help="List all namespaces")
    parser.add_argument("--list-types", action="store_true", help="List all types")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    registry = get_registry()

    if args.list:
        ontologies = registry.list_ontologies()
        if args.json:
            print(json.dumps(ontologies, indent=2))
        else:
            for ont in ontologies:
                print(f"- {ont['id']} v{ont['version']}")
                print(f"  Namespaces: {', '.join(ont['namespaces'])}")
                if ont['entity_types']:
                    print(f"  Entity types: {', '.join(ont['entity_types'])}")

    elif args.list_namespaces:
        namespaces = registry.get_all_namespaces()
        if args.json:
            print(json.dumps(namespaces))
        else:
            for ns in namespaces:
                custom = "(custom)" if registry.is_custom_namespace(ns) else ""
                print(f"  {ns} {custom}")

    elif args.list_types:
        types = registry.get_all_types()
        if args.json:
            print(json.dumps(types))
        else:
            for t in types:
                custom = "(custom)" if registry.is_custom_type(t) else ""
                print(f"  {t} {custom}")


if __name__ == "__main__":
    main()
