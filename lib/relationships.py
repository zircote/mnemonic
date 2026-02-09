#!/usr/bin/env python3
"""
Mnemonic Relationship Writer

Functions for writing and managing relationships in memory file frontmatter.
Provides both one-directional and bidirectional linking between memories.
"""

import re
from pathlib import Path
from typing import Optional

from lib.memory_reader import get_memory_metadata
from lib.search import REL_RELATES_TO, REL_SUPERSEDES, REL_DERIVED_FROM

# Reciprocal relationship types for bidirectional linking.
# When A -[supersedes]-> B, B gets a relates_to back-link to A.
# When A -[derived_from]-> B, B gets a relates_to back-link to A.
# relates_to is symmetric.
RECIPROCAL_TYPES = {
    REL_RELATES_TO: REL_RELATES_TO,
    REL_SUPERSEDES: REL_RELATES_TO,
    REL_DERIVED_FROM: REL_RELATES_TO,
}


def add_relationship(
    memory_path: str,
    rel_type: str,
    target_id: str,
    label: Optional[str] = None,
) -> bool:
    """Add a relationship to a memory file's YAML frontmatter.

    Appends a new relationship entry to the frontmatter. If a relationships
    section doesn't exist, one is created. Duplicate relationships (same
    type + target) are skipped.

    Args:
        memory_path: Absolute path to the .memory.md file.
        rel_type: Relationship type (relates_to, supersedes, derived_from).
        target_id: UUID of the target memory.
        label: Optional human-readable description.

    Returns:
        True if the relationship was added, False if it already exists
        or the file couldn't be modified.
    """
    p = Path(memory_path)
    if not p.exists():
        return False

    try:
        content = p.read_text(encoding="utf-8")
    except Exception:
        return False

    # Split into frontmatter and body
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False

    frontmatter = parts[1]
    body = parts[2]

    # Check for duplicate: same type + target already exists
    existing = re.findall(
        r"-\s*type:\s*(\S+)\s*\n\s*target:\s*(\S+)",
        frontmatter,
    )
    for existing_type, existing_target in existing:
        if existing_type == rel_type and existing_target == target_id:
            return False

    # Build the new relationship entry
    rel_entry = f"  - type: {rel_type}\n    target: {target_id}"
    if label:
        rel_entry += f'\n    label: "{label}"'

    # Check if relationships section exists
    rel_section_match = re.search(
        r"^relationships:\s*(\[\])?",
        frontmatter,
        re.MULTILINE,
    )

    if rel_section_match:
        # Section exists — append after it
        if rel_section_match.group(1):
            # Empty list form: `relationships: []` — replace with block form
            frontmatter = frontmatter.replace(
                rel_section_match.group(0),
                f"relationships:\n{rel_entry}",
            )
        else:
            # Block form already — find the end of existing entries and append
            insert_pos = rel_section_match.end()
            # Find existing relationship entries after the key
            remaining = frontmatter[insert_pos:]
            # Find where the relationship block ends (next top-level key or end)
            block_end = re.search(r"\n\S", remaining)
            if block_end:
                insert_pos += block_end.start()
            else:
                insert_pos = len(frontmatter)
            frontmatter = frontmatter[:insert_pos] + f"\n{rel_entry}" + frontmatter[insert_pos:]
    else:
        # No relationships section — add before closing ---
        frontmatter = frontmatter.rstrip("\n") + f"\nrelationships:\n{rel_entry}\n"

    # Reassemble and write
    new_content = f"---{frontmatter}---{body}"
    try:
        p.write_text(new_content, encoding="utf-8")
        return True
    except Exception:
        return False


def add_bidirectional_relationship(
    source_path: str,
    target_path: str,
    rel_type: str,
    label: Optional[str] = None,
) -> tuple[bool, bool]:
    """Add a relationship in both directions between two memory files.

    Creates A→B with the given rel_type and B→A with the reciprocal type.

    Args:
        source_path: Path to the source memory file (A).
        target_path: Path to the target memory file (B).
        rel_type: Relationship type for A→B.
        label: Optional label for the forward relationship.

    Returns:
        Tuple of (forward_added, reverse_added) booleans.
    """
    source_meta = get_memory_metadata(source_path)
    target_meta = get_memory_metadata(target_path)

    if not source_meta or not target_meta:
        return (False, False)

    source_id = source_meta.get("id")
    target_id = target_meta.get("id")

    if not source_id or not target_id:
        return (False, False)

    # Forward: source → target
    forward = add_relationship(source_path, rel_type, target_id, label=label)

    # Reverse: target → source with reciprocal type
    reciprocal = RECIPROCAL_TYPES.get(rel_type, REL_RELATES_TO)
    reverse_label = None
    if label:
        reverse_label = f"Back-link: {label}"
    reverse = add_relationship(target_path, reciprocal, source_id, label=reverse_label)

    return (forward, reverse)
