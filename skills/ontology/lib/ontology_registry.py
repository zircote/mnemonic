#!/usr/bin/env python3
"""
Ontology Registry for Mnemonic

Manages loading, parsing, and querying of custom ontology definitions.
Supports YAML-based ontology files with URL-referenced schemas.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

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
    """A pattern for discovering entities in content or files."""

    pattern_type: str  # "content" or "file"
    pattern: str  # Regex or glob pattern
    suggest_entity: str  # Entity type to suggest
    suggest_namespace: Optional[str] = None  # Namespace path suggestion
    compiled_regex: Any = field(default=None, repr=False)

    def matches_content(self, content: str) -> bool:
        """Check if pattern matches content (for content_pattern)."""
        if self.pattern_type != "content":
            return False
        if self.compiled_regex is None:
            try:
                self.compiled_regex = re.compile(self.pattern, re.IGNORECASE)
            except re.error:
                return False
        return bool(self.compiled_regex.search(content))

    def matches_file(self, file_path: str) -> bool:
        """Check if pattern matches file path (for file_pattern)."""
        if self.pattern_type != "file":
            return False
        from fnmatch import fnmatch

        return fnmatch(file_path, self.pattern)


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
    2. User ontologies (${MNEMONIC_ROOT}/)
    3. Project ontologies (${MNEMONIC_ROOT}/)

    Later sources override earlier ones for the same namespace.
    """

    # Cognitive triad hierarchy (prefixed with _ for filesystem disambiguation)
    BASE_NAMESPACES = [
        "_semantic",
        "_semantic/decisions",
        "_semantic/knowledge",
        "_semantic/entities",
        "_episodic",
        "_episodic/incidents",
        "_episodic/sessions",
        "_episodic/blockers",
        "_procedural",
        "_procedural/runbooks",
        "_procedural/patterns",
        "_procedural/migrations",
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

    # URL loading retry configuration
    URL_MAX_RETRIES = 3
    URL_INITIAL_DELAY = 1.0  # seconds
    URL_BACKOFF_FACTOR = 2.0

    def load_from_url(self, url: str, cache_dir: Optional[Path] = None) -> Optional[Ontology]:
        """
        Load an ontology from a URL with retry logic.

        Args:
            url: URL to fetch ontology YAML from
            cache_dir: Directory to cache downloaded ontologies

        Returns:
            Parsed Ontology or None if loading fails
        """
        import time
        import urllib.error
        import urllib.request

        # Create cache directory
        cache_file: Optional[Path] = None
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"{self._url_hash(url)}.yaml"

            # Check cache first
            if cache_file.exists():
                try:
                    with open(cache_file) as f:
                        data = yaml.safe_load(f)
                    return self._parse_ontology(data, source_path=cache_file)
                except (OSError, yaml.YAMLError) as e:
                    logger.warning(f"Cache read failed, fetching from URL: {e}")

        # Validate URL scheme (prevent SSRF via file://, etc.)
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            logger.error(f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed.")
            return None

        # Fetch from URL with retry logic
        last_error = None
        delay = self.URL_INITIAL_DELAY

        for attempt in range(1, self.URL_MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    content = response.read().decode("utf-8")

                # Cache if directory provided and cache_file was defined
                if cache_dir and cache_file:
                    try:
                        cache_file.write_text(content)
                    except OSError as e:
                        logger.warning(f"Failed to cache ontology: {e}")

                data = yaml.safe_load(content)
                return self._parse_ontology(data)

            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                last_error = e
                if attempt < self.URL_MAX_RETRIES:
                    logger.warning(f"URL fetch attempt {attempt} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= self.URL_BACKOFF_FACTOR

            except (yaml.YAMLError, ValueError) as e:
                # Non-retryable errors (bad content)
                logger.error(f"Failed to parse ontology from URL {url}: {e}")
                return None

        logger.error(f"Failed to load ontology from URL {url} after {self.URL_MAX_RETRIES} attempts: {last_error}")
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
                resolved_dir = ontologies_dir.resolve()
                for yaml_file in ontologies_dir.glob("*.yaml"):
                    # Security: Validate file is within the expected directory
                    try:
                        yaml_file.resolve().relative_to(resolved_dir)
                    except ValueError:
                        logger.warning(f"Skipping file outside ontologies directory: {yaml_file}")
                        continue
                    self._load_ontology_file(yaml_file)
            return

        self._load_ontology_file(ontology_file)

    # Maximum file size for YAML files (10MB) to prevent DoS attacks
    MAX_YAML_SIZE = 10 * 1024 * 1024

    def _load_ontology_file(self, file_path: Path) -> None:
        """Load a single ontology file."""
        try:
            # Security: Validate file size before parsing to prevent DoS
            file_size = file_path.stat().st_size
            if file_size > self.MAX_YAML_SIZE:
                logger.error(f"YAML file too large ({file_size} bytes): {file_path}")
                return

            with open(file_path) as f:
                data = yaml.safe_load(f)

            if not data:
                return

            ontology = self._parse_ontology(data, source_path=file_path)
            if ontology:
                self._register_ontology(ontology)

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
        except OSError as e:
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

        # Parse namespaces (including hierarchical children)
        for ns_name, ns_data in data.get("namespaces", {}).items():
            if isinstance(ns_data, str):
                ns_data = {"description": ns_data}

            # Register the parent namespace
            ontology.namespaces[ns_name] = Namespace(
                name=ns_name,
                description=ns_data.get("description", ""),
                type_hint=ns_data.get("type_hint", "semantic"),
            )

            # Register child namespaces with full paths (e.g., _semantic/decisions)
            children = ns_data.get("children", {})
            for child_name, child_data in children.items():
                if isinstance(child_data, str):
                    child_data = {"description": child_data}
                full_path = f"{ns_name}/{child_name}"
                ontology.namespaces[full_path] = Namespace(
                    name=full_path,
                    description=child_data.get("description", ""),
                    type_hint=child_data.get("type_hint", ns_data.get("type_hint", "semantic")),
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
    org: str = "default",
    project_name: Optional[str] = None,
) -> OntologyRegistry:
    """
    Get a configured OntologyRegistry.

    Resolution order (later overrides earlier):
    1. Bundled ontologies (skills/ontology/fallback/)
    2. User ontologies (${MNEMONIC_ROOT}/{org}/{project}/)
    3. Project ontologies (${MNEMONIC_ROOT}/)

    Args:
        base_path: Path to base ontologies (defaults to bundled fallback)
        user_path: Path to user ontologies
        project_path: Path to project ontologies
        org: Organization name for user-level path
        project_name: Project name for user-level path

    Returns:
        Configured OntologyRegistry
    """
    registry = OntologyRegistry()

    paths = []

    # Base ontologies - bundled fallback
    if base_path:
        paths.append(base_path)
    else:
        plugin_root = Path(__file__).parent.parent

        # 1. Bundled ontologies
        fallback_ontologies = plugin_root / "fallback" / "ontologies"
        if fallback_ontologies.exists():
            paths.append(fallback_ontologies)

        # 2. Legacy plugin ontologies (deprecated)
        if (plugin_root / "ontologies").exists():
            paths.append(plugin_root / "ontologies")

    # User ontologies (with org/project hierarchy)
    if user_path:
        paths.append(user_path)
    else:
        user_base = Path.home() / ".claude" / "mnemonic"
        if project_name:
            paths.append(user_base / org / project_name)
        else:
            paths.append(user_base / org)
        paths.append(user_base)

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
    import sys

    parser = argparse.ArgumentParser(description="Mnemonic Ontology Registry")
    parser.add_argument("--list", action="store_true", help="List all ontologies")
    parser.add_argument("--namespaces", action="store_true", help="List all namespaces")
    parser.add_argument("--types", action="store_true", help="List all entity types")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--validate", metavar="NAMESPACE", help="Validate a namespace")

    args = parser.parse_args()

    registry = get_registry()

    if args.validate:
        valid = registry.validate_namespace(args.validate)
        if args.json:
            print(json.dumps({"namespace": args.validate, "valid": valid}))
        else:
            status = "✓ valid" if valid else "✗ invalid"
            print(f"{args.validate}: {status}")
        sys.exit(0 if valid else 1)

    if args.namespaces:
        namespaces = registry.get_all_namespaces()
        if args.json:
            print(json.dumps(namespaces))
        else:
            print("Available namespaces:")
            for ns in namespaces:
                marker = "(custom)" if registry.is_custom_namespace(ns) else "(base)"
                print(f"  {ns} {marker}")

    elif args.types:
        types = registry.get_all_types()
        if args.json:
            print(json.dumps(types))
        else:
            print("Available entity types:")
            for t in types:
                marker = "(custom)" if registry.is_custom_type(t) else "(base)"
                print(f"  {t} {marker}")

    elif args.list:
        ontologies = registry.list_ontologies()
        if args.json:
            print(json.dumps(ontologies, indent=2))
        else:
            print("Loaded ontologies:")
            for ont in ontologies:
                print(f"  - {ont['id']} v{ont['version']}")
                if ont["namespaces"]:
                    print(f"    Namespaces: {', '.join(ont['namespaces'])}")
                if ont["entity_types"]:
                    print(f"    Entity types: {', '.join(ont['entity_types'])}")

    else:
        # Default: show summary
        ontologies = registry.list_ontologies()
        namespaces = registry.get_all_namespaces()
        types = registry.get_all_types()
        if args.json:
            print(json.dumps({"ontologies": len(ontologies), "namespaces": namespaces, "types": types}, indent=2))
        else:
            print(f"Ontologies: {len(ontologies)}")
            print(f"Namespaces: {len(namespaces)}")
            print(f"Entity types: {len(types)}")
            print("\nUse --namespaces, --types, or --list for details")


if __name__ == "__main__":
    main()
