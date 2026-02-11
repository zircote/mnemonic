#!/usr/bin/env python3
"""
Migrate memory files from {uuid}-{slug}.memory.md to {slug}.memory.md format.

Handles collisions by merging content when a slug-only target already exists.
UUID is preserved in the frontmatter `id:` field.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# UUID v4 pattern at start of filename
UUID_PREFIX_PATTERN = re.compile(r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-(.+)\.memory\.md$")

# Migration marker filename
MIGRATION_MARKER = ".migration_slug_only_complete"


@dataclass
class MigrationResult:
    original: Path
    target: Path
    action: str  # "renamed", "merged", "skipped"
    merged_with: Optional[Path] = None


def extract_uuid_and_slug(filename: str) -> tuple[Optional[str], str]:
    """Extract UUID prefix and slug from a memory filename.

    Returns (uuid, slug) where uuid is None if no UUID prefix found.
    """
    match = UUID_PREFIX_PATTERN.match(filename)
    if match:
        return match.group(1), match.group(2)
    return None, filename.replace(".memory.md", "")


def should_migrate(file_path: Path) -> bool:
    """Check if a memory file has a UUID prefix that should be removed."""
    uuid, _ = extract_uuid_and_slug(file_path.name)
    return uuid is not None


def _find_frontmatter_end(content: str) -> Optional[int]:
    """Find the character offset of the closing --- delimiter.

    Searches line-by-line starting after the opening --- to avoid
    matching --- within YAML values or body content.
    Returns the character offset of the closing delimiter line, or None.
    """
    if not content.startswith("---"):
        return None

    lines = content.split("\n")
    offset = len(lines[0]) + 1  # skip opening "---\n"

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return offset
        offset += len(lines[i]) + 1

    return None


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and body from memory file content.

    Uses line-by-line delimiter search to handle --- in YAML values.
    Returns (frontmatter_dict, body_text).
    """
    end_offset = _find_frontmatter_end(content)
    if end_offset is None:
        return {}, content

    fm_text = content[4:end_offset].strip()  # skip opening "---\n"
    body = content[end_offset + 3 :].strip()  # skip closing "---"

    # Parse top-level keys only (we only need 'id' for merge provenance)
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()

    return fm, body


def _split_frontmatter_raw(content: str) -> tuple[str, str]:
    """Split content into raw frontmatter block and body, preserving formatting."""
    end_offset = _find_frontmatter_end(content)
    if end_offset is None:
        return "", content

    # Include closing delimiter
    closing_end = content.find("\n", end_offset)
    if closing_end == -1:
        closing_end = end_offset + 3
    else:
        closing_end += 1

    fm_block = content[:closing_end].rstrip("\n")
    body = content[closing_end:].strip()
    return fm_block, body


def merge_memory_contents(existing_content: str, incoming_content: str) -> str:
    """Merge incoming memory content into an existing memory file.

    Strategy:
    - Keep existing frontmatter (preserves original ID, created date)
    - Append incoming body under a merge separator
    - Extract incoming ID for provenance tracking
    """
    existing_fm_text, existing_body = _split_frontmatter_raw(existing_content)
    incoming_fm, incoming_body = parse_frontmatter(incoming_content)

    incoming_id = incoming_fm.get("id", "unknown")

    # Reconstruct: existing frontmatter + existing body + merged section
    # Use horizontal rule (======) instead of --- to avoid frontmatter delimiter conflicts
    merged = existing_fm_text
    merged += "\n\n"
    merged += existing_body
    merged += "\n\n" + "=" * 60 + "\n\n"
    merged += "## Merged Content\n\n"
    merged += incoming_body
    merged += f"\n\n> Merged from memory `{incoming_id}`\n"

    return merged


def migrate_file(file_path: Path, dry_run: bool = False) -> MigrationResult:
    """Migrate a single memory file from UUID-slug to slug-only naming.

    If a slug-only file already exists at the target path, merges content.
    Uses `git mv` when possible to preserve history.
    """
    uuid, slug = extract_uuid_and_slug(file_path.name)

    if uuid is None:
        return MigrationResult(file_path, file_path, "skipped")

    target_path = file_path.parent / f"{slug}.memory.md"

    if target_path.exists():
        # Collision: merge into existing file via atomic write
        if not dry_run:
            incoming_content = file_path.read_text()
            merged = merge_memory_contents(target_path.read_text(), incoming_content)

            # Atomic write: write to temp, then replace
            temp_path = target_path.with_suffix(".memory.md.tmp")
            temp_path.write_text(merged)
            temp_path.replace(target_path)

            file_path.unlink()

        return MigrationResult(file_path, target_path, "merged", target_path)

    # No collision: rename
    if not dry_run:
        # Try git mv first for history preservation
        result = subprocess.run(
            ["git", "mv", str(file_path), str(target_path)],
            capture_output=True,
            cwd=str(file_path.parent),
            timeout=10,
        )
        if result.returncode != 0:
            # Fallback to regular rename
            file_path.rename(target_path)

    return MigrationResult(file_path, target_path, "renamed")


def is_migration_complete(mnemonic_root: Path) -> bool:
    """Check if migration has already been completed."""
    return (mnemonic_root / MIGRATION_MARKER).exists()


def mark_migration_complete(mnemonic_root: Path) -> None:
    """Mark migration as complete so it doesn't re-run."""
    (mnemonic_root / MIGRATION_MARKER).touch()


def migrate_all(mnemonic_root: Path, dry_run: bool = False) -> list[MigrationResult]:
    """Migrate all UUID-prefixed memory files under a directory tree.

    Returns list of results describing what was done.
    Skips if migration marker exists (idempotent).
    """
    if not mnemonic_root.exists():
        return []

    if is_migration_complete(mnemonic_root):
        return []

    results = []

    for memory_file in sorted(mnemonic_root.rglob("*.memory.md")):
        if should_migrate(memory_file):
            result = migrate_file(memory_file, dry_run)
            results.append(result)

    # Mark complete so we don't re-scan on every session
    if not dry_run:
        mark_migration_complete(mnemonic_root)

    return results


def migration_summary(results: list[MigrationResult]) -> dict:
    """Summarize migration results."""
    return {
        "total": len(results),
        "renamed": sum(1 for r in results if r.action == "renamed"),
        "merged": sum(1 for r in results if r.action == "merged"),
        "skipped": sum(1 for r in results if r.action == "skipped"),
    }


if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    mnemonic_root = Path.home() / ".claude" / "mnemonic"

    if dry_run:
        print("DRY RUN - no files will be modified\n")

    if force and not dry_run:
        # Remove marker to force re-run
        marker = mnemonic_root / MIGRATION_MARKER
        if marker.exists():
            marker.unlink()

    results = migrate_all(mnemonic_root, dry_run)
    summary = migration_summary(results)

    for r in results:
        print(f"  {r.action.upper()}: {r.original.name} -> {r.target.name}")
        if r.merged_with:
            print(f"    (merged into existing {r.merged_with.name})")

    print(f"\nTotal: {summary['total']} files")
    print(f"  Renamed: {summary['renamed']}")
    print(f"  Merged: {summary['merged']}")
    print(f"  Skipped: {summary['skipped']}")
