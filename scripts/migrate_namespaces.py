#!/usr/bin/env python3
"""
Namespace Migration Script

Migrates existing mnemonic memories from the v1.0 flat namespace model
to the v2.0 cognitive triad hierarchy.

Migration mapping:
- apis → semantic/knowledge
- blockers → episodic/blockers
- context → semantic/knowledge
- decisions → semantic/decisions
- learnings → semantic/knowledge
- patterns → procedural/patterns
- security → semantic/knowledge
- testing → procedural/patterns
- episodic → episodic/sessions

Usage:
    python scripts/migrate_namespaces.py --dry-run  # Preview changes
    python scripts/migrate_namespaces.py            # Execute migration
    python scripts/migrate_namespaces.py --commit   # Execute and commit
"""

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Migration mapping: old namespace → new namespace path
NAMESPACE_MIGRATION = {
    "apis": "_semantic/knowledge",
    "blockers": "_episodic/blockers",
    "context": "_semantic/knowledge",
    "decisions": "_semantic/decisions",
    "learnings": "_semantic/knowledge",
    "patterns": "_procedural/patterns",
    "security": "_semantic/knowledge",
    "testing": "_procedural/patterns",
    "episodic": "_episodic/sessions",
}


def find_memory_files(base_path: Path) -> List[Path]:
    """Find all memory files in the given path."""
    if not base_path.exists():
        return []
    return list(base_path.rglob("*.memory.md"))


def detect_namespace(file_path: Path) -> str:
    """Detect the namespace from file path or content."""
    # Check path for namespace
    for old_ns in NAMESPACE_MIGRATION:
        if f"/{old_ns}/" in str(file_path):
            return old_ns

    # Check frontmatter
    try:
        with open(file_path, "r") as f:
            content = f.read(2000)
        match = re.search(r"namespace:\s*['\"]?(\w+)", content)
        if match:
            return match.group(1)
    except Exception:
        pass

    return ""


def update_frontmatter(content: str, old_ns: str, new_ns: str) -> str:
    """Update namespace in frontmatter."""
    # Replace namespace field
    content = re.sub(
        rf"(namespace:\s*['\"]?){old_ns}(['\"]?)",
        rf"\g<1>{new_ns}\g<2>",
        content,
    )

    # Add migration note if not present
    if "migration:" not in content:
        # Find end of frontmatter
        match = re.search(r"^---\n(.*?)^---", content, re.MULTILINE | re.DOTALL)
        if match:
            frontmatter = match.group(1)
            migration_note = f"migration:\n  from: {old_ns}\n  date: {datetime.now().isoformat()}\n"
            new_frontmatter = frontmatter.rstrip() + "\n" + migration_note
            content = content.replace(frontmatter, new_frontmatter)

    return content


def get_new_path(old_path: Path, old_ns: str, new_ns: str) -> Path:
    """Calculate the new path for a memory file."""
    path_str = str(old_path)

    # Replace namespace in path
    # Handle both /{namespace}/ and /{namespace}/project/ patterns
    new_path_str = path_str.replace(f"/{old_ns}/", f"/{new_ns}/")

    return Path(new_path_str)


def migrate_file(
    file_path: Path,
    old_ns: str,
    new_ns: str,
    dry_run: bool = True,
) -> Tuple[Path, bool]:
    """Migrate a single file to new namespace."""
    new_path = get_new_path(file_path, old_ns, new_ns)

    if dry_run:
        return new_path, True

    try:
        # Read and update content
        with open(file_path, "r") as f:
            content = f.read()

        updated_content = update_frontmatter(content, old_ns, new_ns)

        # Create destination directory
        new_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to new location
        with open(new_path, "w") as f:
            f.write(updated_content)

        # Remove old file
        file_path.unlink()

        # Remove empty directories
        try:
            file_path.parent.rmdir()
        except OSError:
            pass  # Directory not empty

        return new_path, True

    except Exception as e:
        print(f"Error migrating {file_path}: {e}")
        return file_path, False


def migrate_directory(
    base_path: Path,
    dry_run: bool = True,
) -> Dict[str, List[Tuple[Path, Path]]]:
    """Migrate all memories in a directory."""
    migrations = {}

    for file_path in find_memory_files(base_path):
        old_ns = detect_namespace(file_path)

        if old_ns not in NAMESPACE_MIGRATION:
            continue

        new_ns = NAMESPACE_MIGRATION[old_ns]

        if old_ns not in migrations:
            migrations[old_ns] = []

        new_path, success = migrate_file(file_path, old_ns, new_ns, dry_run)

        if success:
            migrations[old_ns].append((file_path, new_path))

    return migrations


def print_migration_summary(migrations: Dict[str, List[Tuple[Path, Path]]]):
    """Print summary of migrations."""
    total = sum(len(files) for files in migrations.values())

    if total == 0:
        print("No files to migrate")
        return

    print(f"\nMigration Summary: {total} files\n")

    for old_ns, files in sorted(migrations.items()):
        new_ns = NAMESPACE_MIGRATION[old_ns]
        print(f"{old_ns} → {new_ns}: {len(files)} files")
        for old_path, new_path in files[:3]:  # Show first 3
            print(f"  {old_path.name}")
        if len(files) > 3:
            print(f"  ... and {len(files) - 3} more")


def create_git_commit(migrations: Dict[str, List[Tuple[Path, Path]]]):
    """Create a git commit for the migration."""
    total = sum(len(files) for files in migrations.values())

    if total == 0:
        return

    # Stage all changes
    subprocess.run(["git", "add", "-A"], check=True)

    # Create commit message
    ns_summary = ", ".join(
        f"{old}→{NAMESPACE_MIGRATION[old]}"
        for old in sorted(migrations.keys())
    )

    message = f"""chore: migrate {total} memories to cognitive triad namespaces

Migrated namespaces: {ns_summary}

This migration moves memories from the v1.0 flat namespace model
to the v2.0 cognitive triad hierarchy (semantic/episodic/procedural).
"""

    subprocess.run(["git", "commit", "-m", message], check=True)
    print("\nCreated git commit for migration")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate mnemonic memories to new namespace hierarchy"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Create git commit after migration",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Path to migrate (default: ${MNEMONIC_ROOT} and ./.claude/mnemonic)",
    )

    args = parser.parse_args()

    # Determine paths to migrate
    if args.path:
        paths = [args.path]
    else:
        paths = [
            Path.home() / ".claude" / "mnemonic",
            Path.cwd() / ".claude" / "mnemonic",
        ]

    dry_run = args.dry_run or not args.commit

    if dry_run and not args.dry_run:
        print("Note: Use --commit to execute migration with git commit")
        print()

    all_migrations = {}

    for path in paths:
        if not path.exists():
            continue

        print(f"Scanning: {path}")
        migrations = migrate_directory(path, dry_run=dry_run)

        for ns, files in migrations.items():
            if ns not in all_migrations:
                all_migrations[ns] = []
            all_migrations[ns].extend(files)

    print_migration_summary(all_migrations)

    if dry_run:
        print("\n(Dry run - no changes made)")
    elif args.commit and all_migrations:
        create_git_commit(all_migrations)


if __name__ == "__main__":
    main()
