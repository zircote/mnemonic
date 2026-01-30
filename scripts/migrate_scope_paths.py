#!/usr/bin/env python3
"""
Scope Path Migration Script

Migrates memories from redundant /user/ and /project/ subdirectories
to the parent namespace directory.

Before: ${MNEMONIC_ROOT}/{org}/{namespace}/user/*.memory.md
After:  ${MNEMONIC_ROOT}/{org}/{namespace}/*.memory.md

Before: ./.claude/mnemonic/{namespace}/project/*.memory.md
After:  ./.claude/mnemonic/{namespace}/*.memory.md

Usage:
    python scripts/migrate_scope_paths.py --dry-run  # Preview changes
    python scripts/migrate_scope_paths.py            # Execute migration
"""

import argparse
import shutil
from pathlib import Path


def find_scope_dirs(base_path: Path) -> list:
    """Find all /user/ and /project/ directories."""
    scope_dirs = []
    for scope_name in ["user", "project"]:
        for scope_dir in base_path.rglob(scope_name):
            if scope_dir.is_dir():
                # Check if it contains memory files
                memories = list(scope_dir.glob("*.memory.md"))
                if memories:
                    scope_dirs.append(scope_dir)
    return scope_dirs


def migrate_scope_dir(scope_dir: Path, dry_run: bool = True) -> list:
    """Move all memories from scope dir to parent namespace dir."""
    migrations = []
    parent_dir = scope_dir.parent

    for memory_file in scope_dir.glob("*.memory.md"):
        new_path = parent_dir / memory_file.name

        if dry_run:
            migrations.append((memory_file, new_path))
        else:
            try:
                shutil.move(str(memory_file), str(new_path))
                migrations.append((memory_file, new_path))
            except Exception as e:
                print(f"Error moving {memory_file}: {e}")

    # Remove empty scope directory
    if not dry_run and not any(scope_dir.iterdir()):
        try:
            scope_dir.rmdir()
        except Exception:
            pass

    return migrations


def main():
    parser = argparse.ArgumentParser(
        description="Migrate memories from /user/ and /project/ subdirectories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )

    args = parser.parse_args()

    # Paths to check
    paths = [
        Path.home() / ".claude" / "mnemonic",
        Path.cwd() / ".claude" / "mnemonic",
    ]

    total_migrations = []

    for base_path in paths:
        if not base_path.exists():
            continue

        print(f"Scanning: {base_path}")
        scope_dirs = find_scope_dirs(base_path)

        for scope_dir in scope_dirs:
            migrations = migrate_scope_dir(scope_dir, dry_run=args.dry_run)
            total_migrations.extend(migrations)

            if migrations:
                scope_type = scope_dir.name
                print(f"  {scope_dir.parent.name}/{scope_type}/: {len(migrations)} files")

    if total_migrations:
        print(f"\nTotal: {len(total_migrations)} files migrated")
        if args.dry_run:
            print("\n(Dry run - no changes made)")
            print("Run without --dry-run to execute migration")
    else:
        print("\nNo files to migrate")


if __name__ == "__main__":
    main()
