#!/usr/bin/env python3
"""Custodian orchestrator for memory maintenance operations.

Usage:
    python3 custodian.py <operation> [options]

Operations:
    audit                   Full health check (default)
    relocate OLD NEW        Move memories and update references
    validate-links          Check wiki-links and relationships
    ensure-bidirectional    Find/fix missing inverse back-references
    decay                   Recalculate decay strength
    summarize               Find compression candidates
    validate-memories       Check MIF frontmatter completeness
    validate-relationships  Verify ontological relationships

Options:
    --dry-run            Preview without changes
    --fix                Auto-repair issues (validate-links, ensure-bidirectional)
    --json               Output as JSON
    --commit             Git commit after changes
"""

import subprocess
import sys
from pathlib import Path
from typing import List

# Allow imports from plugin root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.custodian.lib.decay import update_decay
from skills.custodian.lib.link_checker import ensure_bidirectional, find_orphans, validate_links
from skills.custodian.lib.relocator import relocate
from skills.custodian.lib.report import Report
from skills.custodian.lib.validators import (
    load_ontology,
    validate_memories,
    validate_relationships,
)

try:
    from lib.paths import PathContext, PathResolver, PathScheme, get_all_memory_roots_with_legacy

    _HAS_PATH_LIB = True
except ImportError:
    _HAS_PATH_LIB = False


def _get_memory_roots() -> List[Path]:
    """Get all memory root directories using the canonical path resolver."""
    if _HAS_PATH_LIB:
        return get_all_memory_roots_with_legacy()

    # Fallback when lib.paths not available: use config-based root
    try:
        from lib.config import get_memory_root

        root = get_memory_root()
        return [p for p in root.iterdir() if p.is_dir()] if root.exists() else []
    except ImportError:
        pass

    # Last resort fallback
    home = Path.home()
    xdg_root = home / ".local" / "share" / "mnemonic"
    if xdg_root.exists():
        return [p for p in xdg_root.iterdir() if p.is_dir()]
    return []


def _get_ontology_paths() -> List[Path]:
    """Get ontology file paths in precedence order."""
    if _HAS_PATH_LIB:
        context = PathContext.detect(scheme=PathScheme.V2)  # type: ignore[name-defined]
        resolver = PathResolver(context)  # type: ignore[name-defined]
        return resolver.get_ontology_paths()
    # Fallback: check config-based root
    try:
        from lib.config import get_memory_root

        root = get_memory_root()
        return [root / "ontology.yaml"]
    except ImportError:
        pass
    return [Path.home() / ".local" / "share" / "mnemonic" / "ontology.yaml"]


def _git_commit(message: str) -> bool:
    """Commit changes in the mnemonic directory."""
    try:
        from lib.config import get_memory_root

        mnemonic_root = get_memory_root()
    except ImportError:
        mnemonic_root = Path.home() / ".local" / "share" / "mnemonic"
    if not (mnemonic_root / ".git").exists():
        return False
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(mnemonic_root),
            capture_output=True,
            timeout=10,
        )
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(mnemonic_root),
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def run_audit(dry_run: bool = False, fix: bool = False) -> Report:
    """Run full audit: links, decay, frontmatter, relationships, orphans."""
    report = Report("audit", dry_run=dry_run)
    roots = _get_memory_roots()

    if not roots:
        report.warning("audit", "No memory directories found")
        return report

    # Count total memories
    total = sum(1 for r in roots for _ in r.rglob("*.memory.md"))
    report.info("audit", f"Scanning {total} memories across {len(roots)} roots")

    # 1. Validate frontmatter (fix placeholder UUIDs/dates when --fix)
    validate_memories(roots, report, fix=fix)

    # 2. Validate links
    index = validate_links(roots, report, fix=fix)

    # 3. Validate relationships
    ontology_data = load_ontology(_get_ontology_paths())
    validate_relationships(roots, report, ontology_data)

    # 4. Update decay
    update_decay(roots, report, dry_run=dry_run)

    # 5. Find orphans and link them to related memories when --fix
    orphans = find_orphans(index)
    if fix and orphans:
        from skills.custodian.lib.link_checker import link_orphans

        link_orphans(index, orphans, report)
        # Re-check orphans after linking
        orphans = find_orphans(index)

    for orphan in orphans:
        report.warning("orphans", "No incoming references", file_path=orphan)

    return report


def run_validate_links(fix: bool = False) -> Report:
    """Validate and optionally repair links."""
    report = Report("validate-links", dry_run=not fix)
    roots = _get_memory_roots()
    validate_links(roots, report, fix=fix)
    return report


def run_decay(dry_run: bool = False) -> Report:
    """Recalculate decay strength."""
    report = Report("decay", dry_run=dry_run)
    roots = _get_memory_roots()
    updated = update_decay(roots, report, dry_run=dry_run)
    report.info("decay", f"Updated {updated} memories")
    return report


def run_validate_memories() -> Report:
    """Validate MIF frontmatter completeness."""
    report = Report("validate-memories", dry_run=True)
    roots = _get_memory_roots()
    error_count = validate_memories(roots, report)
    report.info("frontmatter", f"Found {error_count} frontmatter errors")
    return report


def run_validate_relationships() -> Report:
    """Validate ontological relationships."""
    report = Report("validate-relationships", dry_run=True)
    roots = _get_memory_roots()
    ontology_data = load_ontology(_get_ontology_paths())
    error_count = validate_relationships(roots, report, ontology_data)
    report.info("relationships", f"Found {error_count} relationship errors")
    return report


def run_ensure_bidirectional(fix: bool = False) -> Report:
    """Find and optionally fix missing bidirectional back-references."""
    report = Report("ensure-bidirectional", dry_run=not fix)
    roots = _get_memory_roots()
    if not roots:
        report.warning("bidirectional", "No memory directories found")
        return report

    # Build link index first
    index = validate_links(roots, Report("_index_build"), fix=False)

    missing = ensure_bidirectional(index, report, fix=fix)
    report.info("bidirectional", f"Found {missing} missing back-references")
    return report


def run_relocate(old_path: str, new_path: str, dry_run: bool = False) -> Report:
    """Relocate memories from old path to new path."""
    report = Report("relocate", dry_run=dry_run)
    old_root = Path(old_path).expanduser()
    new_root = Path(new_path).expanduser()
    all_roots = _get_memory_roots()
    moved = relocate(old_root, new_root, all_roots, report, dry_run=dry_run)
    report.info("relocate", f"Total relocated: {moved}")
    return report


def run_summarize(dry_run: bool = False) -> Report:
    """Find compression candidates (summarization delegated to compression-worker agent)."""
    report = Report("summarize", dry_run=dry_run)
    roots = _get_memory_roots()

    from .memory_file import MemoryFile

    candidates = 0
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.memory.md")):
            mem = MemoryFile(path)

            # Skip if already has summary
            if mem.get("summary"):
                continue

            # Check line count
            line_count = mem.body.count("\n") + 1
            if line_count < 100:
                continue

            # Check age or low strength
            import os
            import time

            try:
                mtime = os.path.getmtime(path)
                age_days = (time.time() - mtime) / 86400
            except OSError:
                continue

            strength = mem.get_nested("temporal", "decay", "currentStrength")
            if strength is None:
                strength = mem.get_nested("temporal", "decay", "strength")

            is_candidate = False
            if age_days > 30:
                is_candidate = True
            if strength is not None and float(strength) < 0.3:
                is_candidate = True

            if is_candidate:
                candidates += 1
                report.info(
                    "summarize",
                    f"Compression candidate ({line_count} lines, {age_days:.0f}d old)",
                    file_path=path,
                )

    report.info("summarize", f"Found {candidates} compression candidates")
    if candidates > 0:
        report.info(
            "summarize",
            "Use Task tool with mnemonic:compression-worker agent to compress each candidate",
        )

    return report


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    # Parse flags
    dry_run = "--dry-run" in args
    fix = "--fix" in args
    as_json = "--json" in args
    commit = "--commit" in args

    # Remove flags from args
    positional = [a for a in args if not a.startswith("--")]
    operation = positional[0] if positional else "audit"

    # Dispatch
    if operation == "audit":
        report = run_audit(dry_run=dry_run, fix=fix)
    elif operation == "validate-links":
        report = run_validate_links(fix=fix)
    elif operation == "ensure-bidirectional":
        report = run_ensure_bidirectional(fix=fix)
    elif operation == "decay":
        report = run_decay(dry_run=dry_run)
    elif operation == "validate-memories":
        report = run_validate_memories()
    elif operation == "validate-relationships":
        report = run_validate_relationships()
    elif operation == "relocate":
        if len(positional) < 3:
            print("Usage: custodian.py relocate <old-path> <new-path>", file=sys.stderr)
            sys.exit(1)
        report = run_relocate(positional[1], positional[2], dry_run=dry_run)
    elif operation == "summarize":
        report = run_summarize(dry_run=dry_run)
    else:
        print(f"Unknown operation: {operation}", file=sys.stderr)
        print("Valid operations: audit, validate-links, ensure-bidirectional, decay,", file=sys.stderr)
        print("  validate-memories, validate-relationships, relocate, summarize", file=sys.stderr)
        sys.exit(1)

    # Output
    if as_json:
        print(report.render_json())
    else:
        print(report.render_markdown())

    # Commit if requested and changes were made
    if commit and report.fixed_count > 0:
        committed = _git_commit(f"custodian: {operation} ({report.fixed_count} fixes)")
        if committed:
            print(f"\nCommitted {report.fixed_count} fixes to git")

    # Exit with error code if errors found
    sys.exit(1 if report.errors and not fix else 0)


if __name__ == "__main__":
    main()
