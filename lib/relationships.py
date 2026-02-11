#!/usr/bin/env python3
"""
Mnemonic Relationship Type Registry and Writer

Canonical relationship type definitions from MIF spec Section 8.2.
Provides type registry, inverse mapping, naming conversion helpers,
and functions for writing relationships to memory file frontmatter.
"""

import re
from pathlib import Path
from typing import Optional

from lib.memory_reader import get_memory_metadata

# ---------------------------------------------------------------------------
# Canonical relationship types from MIF spec Section 8.2
# Each entry maps a PascalCase type to its inverse and symmetry flag.
# ---------------------------------------------------------------------------
RELATIONSHIP_TYPES = {
    "RelatesTo": {"inverse": "RelatesTo", "symmetric": True},
    "DerivedFrom": {"inverse": "Derives", "symmetric": False},
    "Supersedes": {"inverse": "SupersededBy", "symmetric": False},
    "ConflictsWith": {"inverse": "ConflictsWith", "symmetric": True},
    "PartOf": {"inverse": "Contains", "symmetric": False},
    "Implements": {"inverse": "ImplementedBy", "symmetric": False},
    "Uses": {"inverse": "UsedBy", "symmetric": False},
    "Created": {"inverse": "CreatedBy", "symmetric": False},
    "MentionedIn": {"inverse": "Mentions", "symmetric": False},
}

# Build the full set of valid types (forward + inverse)
_ALL_VALID_PASCAL: set[str] = set()
for _fwd, _meta in RELATIONSHIP_TYPES.items():
    _ALL_VALID_PASCAL.add(_fwd)
    _ALL_VALID_PASCAL.add(_meta["inverse"])

# Build inverse lookup (includes reverse direction: inverse -> forward)
_INVERSE_MAP: dict[str, str] = {}
for _fwd, _meta in RELATIONSHIP_TYPES.items():
    _INVERSE_MAP[_fwd] = _meta["inverse"]
    _INVERSE_MAP[_meta["inverse"]] = _fwd

# ---------------------------------------------------------------------------
# snake_case backward-compatibility aliases (used in lib/search.py, hooks)
# ---------------------------------------------------------------------------
REL_RELATES_TO = "relates_to"
REL_SUPERSEDES = "supersedes"
REL_DERIVED_FROM = "derived_from"

# Legacy RECIPROCAL_TYPES kept for backward compat (imports in tests, __init__)
# New code should use get_inverse() instead.
RECIPROCAL_TYPES = {
    REL_RELATES_TO: REL_RELATES_TO,
    REL_SUPERSEDES: "superseded_by",
    REL_DERIVED_FROM: "derives",
}

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

# Pre-built maps for fast bidirectional conversion
_SNAKE_TO_PASCAL: dict[str, str] = {}
_PASCAL_TO_SNAKE: dict[str, str] = {}


def _build_conversion_maps() -> None:
    """Build snake_case <-> PascalCase conversion maps for all known types."""
    for pascal_type in _ALL_VALID_PASCAL:
        snake = _pascal_to_snake_impl(pascal_type)
        _SNAKE_TO_PASCAL[snake] = pascal_type
        _PASCAL_TO_SNAKE[pascal_type] = snake


def _pascal_to_snake_impl(name: str) -> str:
    """Convert PascalCase to snake_case (internal, no cache lookup)."""
    result = re.sub(r"([A-Z])", r"_\1", name).lower().lstrip("_")
    return result


# Initialize maps at import time
_build_conversion_maps()


def to_pascal(snake: str) -> str:
    """Convert snake_case relationship type to PascalCase.

    Examples:
        relates_to -> RelatesTo
        superseded_by -> SupersededBy
        derived_from -> DerivedFrom
    """
    # Direct lookup first
    if snake in _SNAKE_TO_PASCAL:
        return _SNAKE_TO_PASCAL[snake]
    # Already PascalCase?
    if snake in _ALL_VALID_PASCAL:
        return snake
    # Fallback: manual conversion
    return "".join(word.capitalize() for word in snake.split("_"))


def to_snake(pascal: str) -> str:
    """Convert PascalCase relationship type to snake_case.

    Examples:
        RelatesTo -> relates_to
        SupersededBy -> superseded_by
    """
    # Direct lookup first
    if pascal in _PASCAL_TO_SNAKE:
        return _PASCAL_TO_SNAKE[pascal]
    # Already snake_case?
    if pascal in _SNAKE_TO_PASCAL:
        return pascal
    # Fallback: manual conversion
    return _pascal_to_snake_impl(pascal)


def get_inverse(rel_type: str) -> str:
    """Get the inverse relationship type.

    Accepts both PascalCase and snake_case input.
    Returns the inverse in PascalCase.

    Examples:
        Supersedes -> SupersededBy
        supersedes -> SupersededBy
        SupersededBy -> Supersedes
        DerivedFrom -> Derives
        RelatesTo -> RelatesTo  (symmetric)
    """
    # Normalize to PascalCase
    pascal = to_pascal(rel_type)
    inv = _INVERSE_MAP.get(pascal)
    if inv:
        return inv
    # Unknown type: return RelatesTo as safe default
    return "RelatesTo"


def is_valid_type(rel_type: str) -> bool:
    """Check if a relationship type is valid (MIF-defined).

    Accepts both PascalCase and snake_case forms,
    and recognizes both forward and inverse types.

    Examples:
        is_valid_type("RelatesTo") -> True
        is_valid_type("relates_to") -> True
        is_valid_type("SupersededBy") -> True
        is_valid_type("superseded_by") -> True
        is_valid_type("FooBar") -> False
    """
    if rel_type in _ALL_VALID_PASCAL:
        return True
    if rel_type in _SNAKE_TO_PASCAL:
        return True
    return False


def is_symmetric(rel_type: str) -> bool:
    """Check if a relationship type is symmetric (same inverse as itself)."""
    pascal = to_pascal(rel_type)
    meta = RELATIONSHIP_TYPES.get(pascal)
    if meta:
        return meta["symmetric"]
    # Check inverse types too
    inv_forward = _INVERSE_MAP.get(pascal)
    if inv_forward:
        meta = RELATIONSHIP_TYPES.get(inv_forward)
        if meta:
            return meta["symmetric"]
    return False


def get_all_valid_types() -> set[str]:
    """Return the full set of valid PascalCase relationship types (forward + inverse)."""
    return set(_ALL_VALID_PASCAL)


# ---------------------------------------------------------------------------
# Relationship writer functions
# ---------------------------------------------------------------------------


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
        rel_type: Relationship type (any valid MIF type, snake_case or PascalCase).
        target_id: UUID of the target memory.
        label: Optional human-readable description.

    Returns:
        True if the relationship was added, False if it already exists
        or the file couldn't be modified.
    """
    if not is_valid_type(rel_type):
        return False

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

    # Reassemble and write — ensure newlines around delimiters
    if not frontmatter.endswith("\n"):
        frontmatter += "\n"
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

    Creates A->B with the given rel_type and B->A with the proper inverse type.

    Args:
        source_path: Path to the source memory file (A).
        target_path: Path to the target memory file (B).
        rel_type: Relationship type for A->B (snake_case or PascalCase).
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

    # Forward: source -> target
    forward = add_relationship(source_path, rel_type, target_id, label=label)

    # Reverse: target -> source with proper inverse type
    inverse = get_inverse(rel_type)
    # Convert inverse to match the input convention (snake_case in -> snake_case out)
    # Detect snake_case: first char is lowercase (e.g., "supersedes", "relates_to", "derived_from")
    if rel_type and rel_type[0].islower():
        inverse = to_snake(inverse)
    reverse_label = None
    if label:
        reverse_label = f"Back-link: {label}"
    reverse = add_relationship(target_path, inverse, source_id, label=reverse_label)

    return (forward, reverse)
