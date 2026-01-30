#!/usr/bin/env python3
"""
Cleanup Memory Paths Script

Fixes the messed up directory structure in ${MNEMONIC_ROOT}:
1. Removes double-nested paths (semantic/semantic/decisions → semantic/decisions)
2. Cleans up stray root-level directories that should be under an org
3. Removes empty files and directories
4. Properly structures org/project/namespace hierarchy

Usage:
    python scripts/cleanup_memory_paths.py --dry-run  # Preview changes
    python scripts/cleanup_memory_paths.py --commit   # Execute and commit
"""

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

# Valid org directories (everything else at root should be removed or moved)
VALID_ROOT_ITEMS = {
    ".git",
    ".gitignore",
    ".blackboard",
    ".obsidian",
    # Known orgs
    "zircote",
    "default",
    "HMH-ProdOps",
}

# Valid cognitive namespaces
VALID_NAMESPACES = {
    "semantic",
    "episodic",
    "procedural",
}

# Valid sub-namespaces
VALID_SUB_NAMESPACES = {
    "semantic": {"decisions", "knowledge", "entities"},
    "episodic": {"incidents", "sessions", "blockers"},
    "procedural": {"runbooks", "patterns", "migrations"},
}


def find_double_nested_paths(base_path: Path) -> List[Tuple[Path, Path]]:
    """Find paths with double nesting like semantic/semantic/decisions."""
    moves = []

    for ns in VALID_NAMESPACES:
        # Look for patterns like semantic/semantic/ or episodic/episodic/
        double_path = base_path / ns / ns
        if double_path.exists():
            for item in double_path.iterdir():
                if item.is_dir():
                    correct_path = base_path / ns / item.name
                    moves.append((item, correct_path))

    # Also check procedural/procedural/patterns -> procedural/patterns
    for org in base_path.iterdir():
        if org.name in VALID_ROOT_ITEMS and org.name not in {"zircote", "default", "HMH-ProdOps"}:
            continue
        if not org.is_dir():
            continue

        for ns in VALID_NAMESPACES:
            double_path = org / ns / ns
            if double_path.exists():
                for item in double_path.iterdir():
                    if item.is_dir():
                        correct_path = org / ns / item.name
                        moves.append((item, correct_path))

            # Check for procedural/procedural/patterns pattern
            triple_path = org / "procedural" / "procedural" / "patterns"
            if triple_path.exists():
                correct_path = org / "procedural" / "patterns"
                moves.append((triple_path, correct_path))

    return moves


def find_stray_root_items(base_path: Path) -> List[Path]:
    """Find items at root that shouldn't be there."""
    strays = []

    for item in base_path.iterdir():
        if item.name.startswith("."):
            continue
        if item.name in VALID_ROOT_ITEMS:
            continue
        # Check if it's an old namespace at root
        if item.name in {"apis", "blockers", "context", "decisions", "learnings",
                         "patterns", "security", "testing", "episodic", "bridge",
                         "semantic", "procedural", "_test_debug"}:
            strays.append(item)
        # Check for stray files
        if item.is_file():
            strays.append(item)

    return strays


def merge_directories(src: Path, dst: Path, dry_run: bool = True) -> int:
    """Merge source directory into destination."""
    if not src.exists():
        return 0

    count = 0

    for item in src.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(src)
            dest_file = dst / rel_path

            if dry_run:
                print(f"  Would move: {item.name} → {dest_file}")
            else:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                if dest_file.exists():
                    print(f"  Skipping (exists): {dest_file}")
                else:
                    shutil.move(str(item), str(dest_file))
                    print(f"  Moved: {item.name}")
            count += 1

    return count


def cleanup_empty_dirs(base_path: Path):
    """Remove empty directories recursively."""
    for dirpath, _, _ in os.walk(str(base_path), topdown=False):
        path = Path(dirpath)
        if path.name.startswith("."):
            continue
        try:
            if not any(path.iterdir()):
                path.rmdir()
                print(f"  Removed empty: {path}")
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Cleanup mnemonic memory paths")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    parser.add_argument("--commit", action="store_true", help="Execute and commit")
    parser.add_argument("--path", type=Path, default=Path.home() / ".claude" / "mnemonic")

    args = parser.parse_args()
    base_path = args.path
    dry_run = args.dry_run or not args.commit

    if not base_path.exists():
        print(f"Path does not exist: {base_path}")
        return

    print(f"Cleaning up: {base_path}\n")

    # Step 1: Fix double-nested paths
    print("Step 1: Fixing double-nested paths...")
    double_nested = find_double_nested_paths(base_path)
    for src, dst in double_nested:
        if dry_run:
            print(f"  Would merge: {src} → {dst}")
        else:
            count = merge_directories(src, dst, dry_run=False)
            if count > 0:
                # Remove empty source
                try:
                    shutil.rmtree(str(src))
                except Exception as e:
                    print(f"  Error removing {src}: {e}")

    # Step 2: Handle stray root items
    print("\nStep 2: Handling stray root items...")
    strays = find_stray_root_items(base_path)
    for stray in strays:
        if stray.is_file():
            if dry_run:
                print(f"  Would remove file: {stray.name}")
            else:
                stray.unlink()
                print(f"  Removed file: {stray.name}")
        elif stray.is_dir():
            # Check if it has memory files that should be migrated
            memory_files = list(stray.rglob("*.memory.md"))
            if memory_files:
                print(f"  Found {len(memory_files)} memories in stray dir: {stray.name}")
                if not dry_run:
                    # Move to default org
                    default_dir = base_path / "default"
                    merge_directories(stray, default_dir, dry_run=False)

            if dry_run:
                print(f"  Would remove dir: {stray.name}")
            else:
                try:
                    shutil.rmtree(str(stray))
                    print(f"  Removed dir: {stray.name}")
                except Exception as e:
                    print(f"  Error removing {stray}: {e}")

    # Step 3: Clean up empty directories
    if not dry_run:
        print("\nStep 3: Cleaning up empty directories...")
        cleanup_empty_dirs(base_path)

    # Step 4: Show final structure
    print("\nFinal structure:")
    for item in sorted(base_path.iterdir()):
        if item.name.startswith(".") and item.name != ".blackboard":
            continue
        if item.is_dir():
            count = len(list(item.rglob("*.memory.md")))
            print(f"  {item.name}/  ({count} memories)")

    if dry_run:
        print("\n(Dry run - no changes made)")
        print("Run with --commit to execute changes")
    elif args.commit:
        # Git commit
        os.chdir(base_path)
        subprocess.run(["git", "add", "-A"], check=True)
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if result.stdout.strip():
            subprocess.run([
                "git", "commit", "-m",
                "chore: cleanup memory directory structure\n\n"
                "- Fixed double-nested paths (semantic/semantic → semantic)\n"
                "- Removed stray root-level directories\n"
                "- Cleaned up empty directories"
            ], check=True)
            print("\nCreated git commit")
        else:
            print("\nNo changes to commit")


if __name__ == "__main__":
    main()
