#!/usr/bin/env python3
"""
Entity Resolver for Mnemonic

Resolves entity references across memories and maintains an entity index.
Supports @[[entity]] and [[type:id]] reference syntax.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import logging
import re
import subprocess

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """An entity discovered or defined in memories."""

    id: str
    name: str
    entity_type: str
    memory_path: Path
    ontology_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def canonical_ref(self) -> str:
        """Get canonical reference string."""
        return f"[[{self.entity_type}:{self.id}]]"

    @property
    def simple_ref(self) -> str:
        """Get simple reference string."""
        return f"@[[{self.name}]]"


@dataclass
class EntityLink:
    """A link between two entities."""

    from_entity_id: str
    to_entity_id: str
    relationship: str
    memory_path: Path
    bidirectional: bool = False

    def __hash__(self):
        return hash((self.from_entity_id, self.to_entity_id, self.relationship))


@dataclass
class EntityIndexStats:
    """Statistics about the entity index."""

    total_entities: int = 0
    total_links: int = 0
    entities_by_type: Dict[str, int] = field(default_factory=dict)
    memories_indexed: int = 0


class EntityResolver:
    """
    Resolves and manages entities across memories.

    Features:
    - Parse entity references from memory content
    - Maintain in-memory index of entities
    - Search entities using ripgrep
    - Track relationships between entities
    """

    # Regex patterns for entity references
    SIMPLE_REF_PATTERN = re.compile(r"@\[\[([^\]]+)\]\]")  # @[[Entity Name]]
    TYPED_REF_PATTERN = re.compile(r"\[\[([a-z-]+):([^\]]+)\]\]")  # [[type:id]]

    def __init__(self, registry: Optional[Any] = None):
        """
        Initialize EntityResolver.

        Args:
            registry: Optional OntologyRegistry for type validation
        """
        self.registry = registry
        self._entities: Dict[str, Entity] = {}  # id -> Entity
        self._name_index: Dict[str, str] = {}  # lowercase name -> id
        self._type_index: Dict[str, Set[str]] = {}  # type -> set of ids
        self._links: List[EntityLink] = []
        self._indexed_memories: Set[Path] = set()

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the index."""
        self._entities[entity.id] = entity
        self._name_index[entity.name.lower()] = entity.id

        if entity.entity_type not in self._type_index:
            self._type_index[entity.entity_type] = set()
        self._type_index[entity.entity_type].add(entity.id)

        logger.debug(f"Added entity: {entity.name} ({entity.entity_type})")

    def add_link(self, link: EntityLink) -> None:
        """Add a link between entities."""
        self._links.append(link)
        logger.debug(
            f"Added link: {link.from_entity_id} --{link.relationship}--> {link.to_entity_id}"
        )

    def resolve_reference(self, ref: str) -> Optional[Entity]:
        """
        Resolve an entity reference to an Entity.

        Args:
            ref: Reference string like "@[[PostgreSQL]]" or "[[technology:postgres-id]]"

        Returns:
            Entity if found, None otherwise
        """
        # Try simple reference first
        simple_match = self.SIMPLE_REF_PATTERN.match(ref)
        if simple_match:
            name = simple_match.group(1)
            return self.find_by_name(name)

        # Try typed reference
        typed_match = self.TYPED_REF_PATTERN.match(ref)
        if typed_match:
            entity_type = typed_match.group(1)
            entity_id = typed_match.group(2)
            return self.find_by_id(entity_id)

        # Try as plain name
        return self.find_by_name(ref)

    def find_by_id(self, entity_id: str) -> Optional[Entity]:
        """Find entity by ID."""
        return self._entities.get(entity_id)

    def find_by_name(self, name: str) -> Optional[Entity]:
        """Find entity by name (case-insensitive)."""
        entity_id = self._name_index.get(name.lower())
        return self._entities.get(entity_id) if entity_id else None

    def find_by_type(self, entity_type: str) -> List[Entity]:
        """Find all entities of a given type."""
        ids = self._type_index.get(entity_type, set())
        return [self._entities[id] for id in ids if id in self._entities]

    def get_relationships(self, entity_id: str) -> List[EntityLink]:
        """Get all relationships for an entity."""
        return [
            link
            for link in self._links
            if link.from_entity_id == entity_id or link.to_entity_id == entity_id
        ]

    def get_outgoing_relationships(
        self, entity_id: str, relationship: Optional[str] = None
    ) -> List[EntityLink]:
        """Get outgoing relationships from an entity."""
        links = [link for link in self._links if link.from_entity_id == entity_id]
        if relationship:
            links = [link for link in links if link.relationship == relationship]
        return links

    def get_incoming_relationships(
        self, entity_id: str, relationship: Optional[str] = None
    ) -> List[EntityLink]:
        """Get incoming relationships to an entity."""
        links = [link for link in self._links if link.to_entity_id == entity_id]
        if relationship:
            links = [link for link in links if link.relationship == relationship]
        return links

    def index_memory(self, memory_path: Path) -> List[Entity]:
        """
        Index entities from a memory file.

        Parses frontmatter for entity definitions and body for references.

        Args:
            memory_path: Path to the memory file

        Returns:
            List of entities found in the memory
        """
        if yaml is None:
            logger.warning("PyYAML not installed, cannot index memories")
            return []

        if memory_path in self._indexed_memories:
            return []

        try:
            content = memory_path.read_text()
        except FileNotFoundError:
            # File disappeared between discovery and read (TOCTOU race)
            logger.debug(f"File removed during indexing: {memory_path}")
            self._indexed_memories.add(memory_path)  # Mark to avoid retry
            return []
        except PermissionError as e:
            logger.warning(f"Permission denied reading {memory_path}: {e}")
            self._indexed_memories.add(memory_path)
            return []
        except OSError as e:
            logger.error(f"Failed to read {memory_path}: {e}")
            return []

        entities = []

        # Parse frontmatter
        frontmatter, body = self._parse_frontmatter(content)

        # Handle YAML parse errors (frontmatter contains _parse_error marker)
        if frontmatter and "_parse_error" in frontmatter:
            logger.warning(f"Skipping entity extraction for {memory_path}: corrupt frontmatter")
            self._indexed_memories.add(memory_path)
            return []

        # Check for entity definition in frontmatter
        if frontmatter and "ontology" in frontmatter:
            ont_data = frontmatter["ontology"]
            entity_id = ont_data.get("entity_id")
            entity_type = ont_data.get("entity_type")

            if entity_id and entity_type:
                entity = Entity(
                    id=entity_id,
                    name=frontmatter.get("title", entity_id),
                    entity_type=entity_type,
                    memory_path=memory_path,
                    ontology_id=ont_data.get("id"),
                    metadata=frontmatter.get("entity", {}),
                )
                self.add_entity(entity)
                entities.append(entity)

        # Parse entity links from frontmatter
        if frontmatter:
            entity_links = frontmatter.get("entity_links", [])
            for link_data in entity_links:
                if isinstance(link_data, dict):
                    link = EntityLink(
                        from_entity_id=frontmatter.get("id", ""),
                        to_entity_id=link_data.get("id", ""),
                        relationship=link_data.get("type", "relates-to"),
                        memory_path=memory_path,
                    )
                    self.add_link(link)

        # Extract entity references from body
        refs = self.extract_references(body)
        for ref_type, ref_value in refs:
            existing = self.resolve_reference(ref_value)
            if existing and frontmatter and frontmatter.get("id"):
                # Create implicit link
                link = EntityLink(
                    from_entity_id=frontmatter["id"],
                    to_entity_id=existing.id,
                    relationship="references",
                    memory_path=memory_path,
                )
                self.add_link(link)

        self._indexed_memories.add(memory_path)
        return entities

    def extract_references(self, content: str) -> List[Tuple[str, str]]:
        """
        Extract entity references from content.

        Returns:
            List of (ref_type, ref_value) tuples
            ref_type is "simple" or "typed"
        """
        refs = []

        # Find simple references @[[Name]]
        for match in self.SIMPLE_REF_PATTERN.finditer(content):
            refs.append(("simple", match.group(1)))

        # Find typed references [[type:id]]
        for match in self.TYPED_REF_PATTERN.finditer(content):
            refs.append(("typed", f"{match.group(1)}:{match.group(2)}"))

        return refs

    def search_entities(
        self,
        query: str,
        mnemonic_dirs: Optional[List[Path]] = None,
    ) -> List[Entity]:
        """
        Search for entities using ripgrep.

        Args:
            query: Search query
            mnemonic_dirs: Directories to search

        Returns:
            List of matching entities
        """
        if not mnemonic_dirs:
            mnemonic_dirs = [
                Path.home() / ".claude" / "mnemonic",
                Path.cwd() / ".claude" / "mnemonic",
            ]

        # Security: Validate query length and character safety
        MAX_QUERY_LENGTH = 256
        if len(query) > MAX_QUERY_LENGTH:
            logger.warning(f"Search query too long ({len(query)} chars, max {MAX_QUERY_LENGTH})")
            return []
        # Allow: alphanumeric, underscore, dash, dot, space, colon, slash, quotes, brackets
        # Block: shell metacharacters (;$`|&<>), excessive whitespace
        if not re.match(r'^[a-zA-Z0-9_\-./: "\'@\[\]]+$', query) or re.search(r'\s{3,}', query):
            logger.warning(f"Invalid search query contains unsafe characters: {query}")
            return []

        entities = []

        for mnemonic_dir in mnemonic_dirs:
            if not mnemonic_dir.exists():
                continue

            try:
                # Resolve directory path for use in subprocess
                resolved_dir = mnemonic_dir.resolve()

                # Use fixed-string matching (-F) for safer search
                result = subprocess.run(
                    [
                        "rg",
                        "-i",
                        "-l",
                        "-F",  # Fixed strings - no regex interpretation
                        query,
                        "--glob",
                        "*.memory.md",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(resolved_dir),
                    timeout=5,
                )

                if result.returncode == 0 and result.stdout.strip():
                    for file_path in result.stdout.strip().split("\n"):
                        full_path = resolved_dir / file_path
                        found = self.index_memory(full_path)
                        entities.extend(found)

            except FileNotFoundError:
                logger.warning("ripgrep not found, falling back to manual search")
            except subprocess.TimeoutExpired:
                logger.warning("Search timed out")
            except (subprocess.SubprocessError, OSError) as e:
                logger.error(f"Search failed: {e}")

        return entities

    # Resource limits for build_index to prevent memory exhaustion
    MAX_INDEX_FILES = 10000
    MAX_INDEX_SIZE = 100 * 1024 * 1024  # 100MB total

    def build_index(self, mnemonic_dirs: Optional[List[Path]] = None) -> EntityIndexStats:
        """
        Build complete entity index from memory files.

        Args:
            mnemonic_dirs: Directories to scan

        Returns:
            Index statistics
        """
        if not mnemonic_dirs:
            mnemonic_dirs = [
                Path.home() / ".claude" / "mnemonic",
                Path.cwd() / ".claude" / "mnemonic",
            ]

        files_processed = 0
        total_size = 0

        for mnemonic_dir in mnemonic_dirs:
            if not mnemonic_dir.exists():
                continue

            for memory_path in mnemonic_dir.rglob("*.memory.md"):
                # Check file count limit
                files_processed += 1
                if files_processed > self.MAX_INDEX_FILES:
                    logger.warning(f"Hit file limit ({self.MAX_INDEX_FILES}), stopping index build")
                    return self.get_stats()

                # Check total size limit
                try:
                    file_size = memory_path.stat().st_size
                    total_size += file_size
                    if total_size > self.MAX_INDEX_SIZE:
                        logger.warning(f"Hit size limit ({self.MAX_INDEX_SIZE} bytes), stopping index build")
                        return self.get_stats()
                except OSError:
                    continue  # Skip files we can't stat

                self.index_memory(memory_path)

        return self.get_stats()

    def get_stats(self) -> EntityIndexStats:
        """Get index statistics."""
        stats = EntityIndexStats(
            total_entities=len(self._entities),
            total_links=len(self._links),
            memories_indexed=len(self._indexed_memories),
        )

        for entity_type, ids in self._type_index.items():
            stats.entities_by_type[entity_type] = len(ids)

        return stats

    def clear(self) -> None:
        """Clear the entity index."""
        self._entities.clear()
        self._name_index.clear()
        self._type_index.clear()
        self._links.clear()
        self._indexed_memories.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export index as dictionary."""
        return {
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "memory_path": str(e.memory_path),
                    "ontology_id": e.ontology_id,
                }
                for e in self._entities.values()
            ],
            "links": [
                {
                    "from": link.from_entity_id,
                    "to": link.to_entity_id,
                    "relationship": link.relationship,
                }
                for link in self._links
            ],
            "stats": {
                "total_entities": len(self._entities),
                "total_links": len(self._links),
                "memories_indexed": len(self._indexed_memories),
            },
        }

    def _parse_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """Parse YAML frontmatter from content."""
        if yaml is None:
            return None, content

        if not content.startswith("---"):
            return None, content

        try:
            # Find end of frontmatter
            end_match = re.search(r"\n---\s*\n", content[3:])
            if not end_match:
                return None, content

            frontmatter_end = end_match.start() + 3
            frontmatter_str = content[3:frontmatter_end]
            body = content[frontmatter_end + end_match.end() - end_match.start():]

            frontmatter = yaml.safe_load(frontmatter_str)
            return frontmatter, body

        except yaml.YAMLError as e:
            # Log as error (not warning) since this indicates corrupt data
            logger.error(f"Corrupt YAML frontmatter, skipping entity extraction: {e}")
            # Return special marker dict to distinguish from "no frontmatter"
            return {"_parse_error": str(e)}, content


def main():
    """CLI interface for entity resolver."""
    import argparse

    parser = argparse.ArgumentParser(description="Mnemonic Entity Resolver")
    parser.add_argument("--build-index", action="store_true", help="Build entity index")
    parser.add_argument("--search", type=str, help="Search for entities")
    parser.add_argument("--resolve", type=str, help="Resolve entity reference")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    resolver = EntityResolver()

    if args.build_index:
        stats = resolver.build_index()
        if args.json:
            print(json.dumps(resolver.to_dict(), indent=2))
        else:
            print(f"Indexed {stats.memories_indexed} memories")
            print(f"Found {stats.total_entities} entities")
            print(f"Found {stats.total_links} links")
            if stats.entities_by_type:
                print("\nEntities by type:")
                for t, count in stats.entities_by_type.items():
                    print(f"  {t}: {count}")

    elif args.search:
        resolver.build_index()
        entities = resolver.search_entities(args.search)
        if args.json:
            print(json.dumps([{"id": e.id, "name": e.name, "type": e.entity_type} for e in entities], indent=2))
        else:
            for e in entities:
                print(f"  {e.name} ({e.entity_type}): {e.memory_path}")

    elif args.resolve:
        resolver.build_index()
        entity = resolver.resolve_reference(args.resolve)
        if entity:
            if args.json:
                print(json.dumps({"id": entity.id, "name": entity.name, "type": entity.entity_type}))
            else:
                print(f"Resolved: {entity.name} ({entity.entity_type})")
                print(f"  Path: {entity.memory_path}")
        else:
            print(f"Not found: {args.resolve}")
            exit(1)


if __name__ == "__main__":
    main()
