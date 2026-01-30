"""Link validation and repair for memory files."""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .memory_file import UUID_PATTERN, MemoryFile
from .report import Report


class LinkIndex:
    """Index of all memory files by UUID and slug for fast lookup."""

    def __init__(self) -> None:
        self._by_uuid: Dict[str, Path] = {}
        self._by_slug: Dict[str, Path] = {}
        self._all_paths: Set[Path] = set()
        self.collisions: List[Tuple[str, Path, Path]] = []  # (key, existing, new)

    def build(self, roots: List[Path]) -> None:
        """Scan all memory roots and build UUID/slug indexes."""
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*.memory.md"):
                self._all_paths.add(path)
                mem = MemoryFile(path)
                uid = mem.uuid
                if uid:
                    if uid in self._by_uuid:
                        self.collisions.append(("uuid:" + uid, self._by_uuid[uid], path))
                    self._by_uuid[uid] = path
                slug = mem.slug
                if slug:
                    if slug in self._by_slug:
                        self.collisions.append(("slug:" + slug, self._by_slug[slug], path))
                    self._by_slug[slug] = path

    def resolve(self, ref: str) -> Optional[Path]:
        """Resolve a reference (UUID or slug) to a file path."""
        ref_clean = ref.strip().replace("urn:mif:", "")
        if UUID_PATTERN.match(ref_clean):
            return self._by_uuid.get(ref_clean)
        return self._by_slug.get(ref_clean)

    def find_references_to(self, target_path: Path) -> List[Tuple[Path, str]]:
        """Find all memories that reference the target (by UUID or slug)."""
        target_mem = MemoryFile(target_path)
        target_uuid = target_mem.uuid or ""
        target_slug = target_mem.slug

        refs: List[Tuple[Path, str]] = []
        for path in self._all_paths:
            if path == target_path:
                continue
            mem = MemoryFile(path)
            for link in mem.find_wiki_links():
                if link == target_uuid or link == target_slug:
                    refs.append((path, link))
            for rel_target in mem.find_relationship_targets():
                if rel_target == target_uuid or rel_target == target_slug:
                    refs.append((path, rel_target))
        return refs

    @property
    def all_paths(self) -> Set[Path]:
        return self._all_paths

    def has_uuid(self, uid: str) -> bool:
        return uid in self._by_uuid

    def has_slug(self, slug: str) -> bool:
        return slug in self._by_slug


def validate_links(roots: List[Path], report: Report, fix: bool = False) -> LinkIndex:
    """Validate all wiki-links and frontmatter relationships.

    Returns the built LinkIndex for reuse by other operations.
    """
    index = LinkIndex()
    index.build(roots)

    # Report any UUID/slug collisions
    for key, existing, duplicate in index.collisions:
        report.warning(
            "collisions",
            f"Duplicate {key}: {existing.name} and {duplicate.name}",
            file_path=duplicate,
        )

    for path in sorted(index.all_paths):
        mem = MemoryFile(path)

        # Check wiki-links in body
        for link in mem.find_wiki_links():
            resolved = index.resolve(link)
            if resolved is None:
                if fix:
                    # Remove broken wiki-link, replace with plain text
                    mem.replace_in_body(f"[[{link}]]", link)
                    report.error(
                        "links",
                        f"Broken wiki-link [[{link}]] removed",
                        file_path=path,
                        fixed=True,
                    )
                else:
                    report.error(
                        "links",
                        f"Broken wiki-link: [[{link}]]",
                        file_path=path,
                    )

        # Check frontmatter relationship targets
        for target_id in mem.find_relationship_targets():
            # Skip wiki-links already checked above
            if target_id in mem.find_wiki_links():
                continue
            resolved = index.resolve(target_id)
            if resolved is None:
                report.error(
                    "relationships",
                    f"Relationship target not found: {target_id}",
                    file_path=path,
                )

        if fix and mem._dirty:
            mem.save()

    return index


def find_orphans(index: LinkIndex) -> List[Path]:
    """Find memory files with no incoming references."""
    referenced: Set[Path] = set()

    for path in index.all_paths:
        mem = MemoryFile(path)
        for link in mem.find_wiki_links():
            resolved = index.resolve(link)
            if resolved:
                referenced.add(resolved)
        for target_id in mem.find_relationship_targets():
            resolved = index.resolve(target_id)
            if resolved:
                referenced.add(resolved)

    return sorted(index.all_paths - referenced)
