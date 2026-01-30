"""Memory relocation when project or org names change."""

import subprocess
from pathlib import Path
from typing import List, Tuple

from .link_checker import LinkIndex
from .memory_file import MemoryFile
from .report import Report


def relocate(
    old_root: Path,
    new_root: Path,
    all_roots: List[Path],
    report: Report,
    dry_run: bool = False,
) -> int:
    """Relocate memories from old_root to new_root, updating all references.

    Args:
        old_root: Source directory (e.g. ${MNEMONIC_ROOT}/old-org/old-project)
        new_root: Target directory (e.g. ${MNEMONIC_ROOT}/new-org/new-project)
        all_roots: All memory roots (for updating cross-references)
        report: Report to accumulate findings
        dry_run: Preview without changes

    Returns:
        Number of files relocated.
    """
    if not old_root.exists():
        report.error("relocate", f"Source path does not exist: {old_root}")
        return 0

    if old_root == new_root:
        report.warning("relocate", "Source and target are the same path")
        return 0

    # Collect files to move
    files_to_move: List[Tuple[Path, Path]] = []
    for src in sorted(old_root.rglob("*.memory.md")):
        rel = src.relative_to(old_root)
        dst = new_root / rel
        files_to_move.append((src, dst))

    if not files_to_move:
        report.info("relocate", "No memory files found in source path")
        return 0

    report.info("relocate", f"Found {len(files_to_move)} files to relocate")

    # Build link index across ALL roots for reference updating
    index = LinkIndex()
    index.build(all_roots)

    home = Path.home()

    # Phase 1: Update path references in ALL memories
    refs_updated = 0
    for path in sorted(index.all_paths):
        mem = MemoryFile(path)
        changed = False

        # Update absolute path references to relocated files
        for src, dst in files_to_move:
            try:
                old_path_str = str(src.relative_to(home))
                new_path_str = str(dst.relative_to(home))
            except ValueError:
                # Paths not under home - use absolute paths
                old_path_str = str(src)
                new_path_str = str(dst)

            count = mem.replace_in_raw(old_path_str, new_path_str)
            if count > 0:
                changed = True
                refs_updated += count

        # Update org/project path fragments (use path-delimited matching)
        try:
            old_fragment = str(old_root.relative_to(home))
            new_fragment = str(new_root.relative_to(home))
        except ValueError:
            old_fragment = str(old_root)
            new_fragment = str(new_root)

        # Only replace within path-like contexts (preceded by / or start of line)
        import re

        pattern = re.compile(re.escape(old_fragment))
        for match in pattern.finditer(mem._raw):
            pos = match.start()
            # Ensure this looks like a path context (preceded by / or ~ or start)
            if pos == 0 or mem._raw[pos - 1] in "/~":
                count = mem.replace_in_raw(old_fragment, new_fragment)
                if count > 0:
                    changed = True
                    refs_updated += count
                break  # replace_in_raw replaces all occurrences

        if changed and not dry_run:
            mem.save()

    if refs_updated > 0:
        report.info(
            "relocate",
            f"Updated {refs_updated} path references across memory files",
            fixed=not dry_run,
        )

    # Phase 2: Move files
    moved = 0
    for src, dst in files_to_move:
        report.info("relocate", f"Move: {src.name}", file_path=src, fixed=not dry_run)

        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Try git mv for history preservation
            try:
                result = subprocess.run(
                    ["git", "mv", "--", str(src), str(dst)],
                    capture_output=True,
                    cwd=str(src.parent),
                    timeout=10,
                )
                if result.returncode != 0:
                    src.rename(dst)
            except (subprocess.TimeoutExpired, OSError):
                src.rename(dst)

        moved += 1

    # Phase 3: Clean up empty directories
    if not dry_run:
        _cleanup_empty_dirs(old_root)

    report.info("relocate", f"Relocated {moved} files", fixed=not dry_run)
    return moved


def _cleanup_empty_dirs(root: Path) -> None:
    """Remove empty directories under root, bottom-up."""
    if not root.exists():
        return
    for dirpath in sorted(root.rglob("*"), reverse=True):
        try:
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                dirpath.rmdir()
        except OSError:
            pass  # Race condition: directory no longer empty or already removed
    try:
        if root.is_dir() and not any(root.iterdir()):
            root.rmdir()
    except OSError:
        pass
