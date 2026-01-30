"""MIF schema and ontological relationship validation."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .memory_file import MemoryFile
from .report import Report

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# Valid MIF relationship types
VALID_RELATIONSHIP_TYPES = {
    "RelatesTo",
    "DerivedFrom",
    "Supersedes",
    "ConflictsWith",
    "PartOf",
    "Implements",
    "Uses",
    "Created",
    "MentionedIn",
}

# Valid provenance source types
VALID_SOURCE_TYPES = {
    "user_explicit",
    "user_implicit",
    "agent_inferred",
    "external_import",
    "system_generated",
}


def validate_memories(roots: List[Path], report: Report) -> int:
    """Validate memory frontmatter completeness against MIF schema.

    Returns number of memories with errors.
    """
    error_count = 0

    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.memory.md")):
            mem = MemoryFile(path)
            errors = mem.validate_frontmatter()

            for err in errors:
                report.error("frontmatter", err, file_path=path)
                error_count += 1

            # Additional checks beyond basic required fields

            # Check namespace matches directory structure
            ns = mem.namespace
            if ns:
                expected_parts = ns.replace("_", "").split("/")
                path_parts = [p for p in path.parent.parts if p not in (".", "..")]
                # Namespace should appear in path
                ns_found = any(part in path_parts for part in expected_parts)
                if not ns_found:
                    report.warning(
                        "frontmatter",
                        f"Namespace '{ns}' doesn't match directory path",
                        file_path=path,
                    )

            # Check provenance source_type
            source_type = mem.get_nested("provenance", "source_type")
            if source_type and str(source_type) not in VALID_SOURCE_TYPES:
                report.warning(
                    "frontmatter",
                    f"Unknown provenance source_type: {source_type}",
                    file_path=path,
                )

            # Check confidence range
            confidence = mem.get_nested("provenance", "confidence")
            if confidence is not None:
                try:
                    conf_val = float(confidence)
                    if not 0.0 <= conf_val <= 1.0:
                        report.error(
                            "frontmatter",
                            f"Confidence {conf_val} out of range [0.0, 1.0]",
                            file_path=path,
                        )
                except (ValueError, TypeError):
                    report.error(
                        "frontmatter",
                        f"Invalid confidence value: {confidence}",
                        file_path=path,
                    )

    return error_count


def validate_relationships(
    roots: List[Path],
    report: Report,
    ontology_data: Optional[Dict[str, Any]] = None,
) -> int:
    """Validate ontological relationship types and targets.

    Args:
        roots: Memory root directories
        report: Report to accumulate findings
        ontology_data: Loaded ontology YAML data (optional, for custom relationships)

    Returns:
        Number of relationship errors found.
    """
    # Build set of valid relationship types (built-in + ontology custom)
    valid_types = set(VALID_RELATIONSHIP_TYPES)
    if ontology_data and "relationships" in ontology_data:
        for rel_name in ontology_data["relationships"]:
            valid_types.add(rel_name)
            # Also add PascalCase variant
            valid_types.add(rel_name.replace("_", " ").title().replace(" ", ""))

    error_count = 0

    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.memory.md")):
            mem = MemoryFile(path)
            rels = mem.get("relationships")
            if not isinstance(rels, list):
                continue

            for rel in rels:
                if not isinstance(rel, dict):
                    report.error(
                        "relationships",
                        "Relationship entry is not a mapping",
                        file_path=path,
                    )
                    error_count += 1
                    continue

                rel_type = rel.get("relationshipType") or rel.get("type", "")
                if rel_type and str(rel_type) not in valid_types:
                    report.error(
                        "relationships",
                        f"Unknown relationship type: {rel_type}",
                        file_path=path,
                    )
                    error_count += 1

                # Check target exists
                target = rel.get("target")
                if target is None:
                    report.error(
                        "relationships",
                        "Relationship missing target",
                        file_path=path,
                    )
                    error_count += 1

                # Check strength range if present
                strength = rel.get("strength")
                if strength is not None:
                    try:
                        s_val = float(strength)
                        if not 0.0 <= s_val <= 1.0:
                            report.warning(
                                "relationships",
                                f"Relationship strength {s_val} out of range [0.0, 1.0]",
                                file_path=path,
                            )
                    except (ValueError, TypeError):
                        report.warning(
                            "relationships",
                            f"Invalid relationship strength: {strength}",
                            file_path=path,
                        )

    return error_count


def load_ontology(ontology_paths: List[Path]) -> Optional[Dict[str, Any]]:
    """Load the first available ontology file.

    Args:
        ontology_paths: Ordered list of paths to check

    Returns:
        Parsed ontology data or None
    """
    if yaml is None:
        return None
    for ont_path in ontology_paths:
        if ont_path.exists():
            try:
                with open(ont_path) as f:
                    return yaml.safe_load(f)
            except Exception:
                continue
    return None
