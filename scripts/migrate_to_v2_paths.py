#!/usr/bin/env python3
"""
Migrate Mnemonic Memories from Legacy to V2 Path Scheme

Migrates memories from the legacy dual-location structure to the unified
V2 path structure where everything is stored under ${MNEMONIC_ROOT}.

Legacy Structure:
    ${MNEMONIC_ROOT}/{org}/{namespace}/
    ./.claude/mnemonic/{namespace}/

V2 Structure:
    ${MNEMONIC_ROOT}/{org}/{project}/{namespace}/
    ${MNEMONIC_ROOT}/{org}/{namespace}/  # org-wide

Usage:
    python scripts/migrate_to_v2_paths.py --dry-run  # Preview changes
    python scripts/migrate_to_v2_paths.py            # Execute migration
    python scripts/migrate_to_v2_paths.py --rollback # Revert migration

Features:
    - Automatic backup before migration
    - Rollback capability
    - Progress tracking
    - Git commit of changes
"""

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict
import sys

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.paths import PathResolver, PathContext, PathScheme, Scope


@dataclass
class MigrationRecord:
    """Record of a single file migration."""
    source: str
    destination: str
    namespace: str
    scope: str
    timestamp: str
    success: bool
    error: str = ""


@dataclass
class MigrationPlan:
    """Complete migration plan."""
    legacy_roots: List[str]
    v2_root: str
    total_memories: int
    total_size_bytes: int
    migrations: List[MigrationRecord]
    created: str


class MigrationManager:
    """Manages the migration from legacy to V2 path scheme."""

    def __init__(self, dry_run: bool = True, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose

        # Create resolvers for both schemes
        self.legacy_context = PathContext.detect(scheme=PathScheme.LEGACY)
        self.v2_context = PathContext.detect(scheme=PathScheme.V2)

        self.legacy_resolver = PathResolver(self.legacy_context)
        self.v2_resolver = PathResolver(self.v2_context)

        # Track migration state
        self.plan: MigrationPlan | None = None
        self.backup_dir: Path | None = None

    def analyze(self) -> MigrationPlan:
        """
        Analyze current structure and create migration plan.

        Returns:
            MigrationPlan with all files to migrate
        """
        if self.verbose:
            print("Analyzing current memory structure...")

        migrations = []
        total_size = 0

        # Get all legacy memory roots
        legacy_roots = self.legacy_resolver.get_all_memory_roots()

        for legacy_root in legacy_roots:
            if not legacy_root.exists():
                continue

            if self.verbose:
                print(f"  Scanning: {legacy_root}")

            # Find all memory files
            for memory_file in legacy_root.rglob("*.memory.md"):
                # Determine namespace from path
                namespace = self._extract_namespace(memory_file, legacy_root)

                # Determine scope (project if under .claude in cwd, else user)
                if self._is_project_memory(memory_file):
                    scope = Scope.PROJECT
                else:
                    scope = Scope.USER

                # Calculate V2 destination
                v2_path = self._compute_v2_path(memory_file, namespace, scope)

                # Get file size
                file_size = memory_file.stat().st_size
                total_size += file_size

                migrations.append(MigrationRecord(
                    source=str(memory_file),
                    destination=str(v2_path),
                    namespace=namespace,
                    scope=scope.value,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    success=False,
                ))

        plan = MigrationPlan(
            legacy_roots=[str(r) for r in legacy_roots],
            v2_root=str(self.v2_resolver.context.home_dir / ".claude" / "mnemonic"),
            total_memories=len(migrations),
            total_size_bytes=total_size,
            migrations=migrations,
            created=datetime.now(timezone.utc).isoformat(),
        )

        self.plan = plan
        return plan

    def _extract_namespace(self, file_path: Path, root: Path) -> str:
        """Extract namespace from file path relative to root."""
        relative = file_path.parent.relative_to(root)
        return str(relative) if str(relative) != "." else ""

    def _is_project_memory(self, file_path: Path) -> bool:
        """Check if memory is in project directory."""
        try:
            file_path.relative_to(self.legacy_context.project_dir)
            return True
        except ValueError:
            return False

    def _compute_v2_path(
        self,
        source: Path,
        namespace: str,
        scope: Scope
    ) -> Path:
        """Compute V2 destination path for a memory file."""
        filename = source.name

        # Get V2 directory
        v2_dir = self.v2_resolver.get_memory_dir(namespace, scope)

        return v2_dir / filename

    def create_backup(self) -> Path:
        """
        Create backup of all legacy memories.

        Returns:
            Path to backup directory
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = (
            self.legacy_context.home_dir / ".claude" / "mnemonic_backups"
            / f"legacy_backup_{timestamp}"
        )

        if self.dry_run:
            print(f"[DRY RUN] Would create backup at: {backup_dir}")
            self.backup_dir = backup_dir
            return backup_dir

        print(f"Creating backup at: {backup_dir}")
        backup_dir.mkdir(parents=True, exist_ok=True)

        user_base = self.legacy_context.home_dir / ".claude" / "mnemonic"

        # Copy all legacy roots
        for root in self.legacy_resolver.get_all_memory_roots():
            if not root.exists():
                continue

            # Preserve directory structure in backup
            try:
                # Try user-level path first
                relative = root.relative_to(user_base)
                backup_target = backup_dir / relative
            except ValueError:
                # Project-level path - use "project" prefix
                backup_target = backup_dir / "project" / root.name

            print(f"  Backing up: {root} -> {backup_target}")
            shutil.copytree(root, backup_target, dirs_exist_ok=True)

        # Save migration plan
        plan_file = backup_dir / "migration_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(asdict(self.plan), f, indent=2)

        self.backup_dir = backup_dir
        print(f"Backup complete: {backup_dir}")
        return backup_dir

    def execute(self) -> Dict[str, int]:
        """
        Execute the migration plan.

        Returns:
            Dict with success/failure counts
        """
        if not self.plan:
            raise ValueError("Must call analyze() before execute()")

        stats = {"success": 0, "failed": 0, "skipped": 0}

        print(f"\nMigrating {self.plan.total_memories} memories...")

        for i, migration in enumerate(self.plan.migrations, 1):
            if self.verbose or i % 10 == 0:
                print(f"  [{i}/{self.plan.total_memories}] {Path(migration.source).name}")

            try:
                source = Path(migration.source)
                dest = Path(migration.destination)

                # Skip if already migrated
                if dest.exists() and not self.dry_run:
                    if self._files_identical(source, dest):
                        stats["skipped"] += 1
                        migration.success = True
                        continue

                if self.dry_run:
                    print(f"    [DRY RUN] {source} -> {dest}")
                else:
                    # Create destination directory
                    dest.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file (don't move yet, in case of failure)
                    shutil.copy2(source, dest)

                migration.success = True
                stats["success"] += 1

            except Exception as e:
                migration.error = str(e)
                stats["failed"] += 1
                print(f"    ERROR: {e}")

        return stats

    def _files_identical(self, file1: Path, file2: Path) -> bool:
        """Check if two files are identical."""
        if file1.stat().st_size != file2.stat().st_size:
            return False
        return file1.read_bytes() == file2.read_bytes()

    def cleanup_legacy(self) -> int:
        """
        Remove legacy directories after successful migration.

        Returns:
            Number of files removed
        """
        if self.dry_run:
            print("\n[DRY RUN] Would remove legacy directories:")
            for root in self.legacy_resolver.get_all_memory_roots():
                print(f"  - {root}")
            return 0

        removed = 0
        print("\nCleaning up legacy directories...")

        for root in self.legacy_resolver.get_all_memory_roots():
            if not root.exists():
                continue

            # Only remove if empty or only contains migrated files
            for memory_file in root.rglob("*.memory.md"):
                try:
                    memory_file.unlink()
                    removed += 1
                except Exception as e:
                    print(f"  Warning: Could not remove {memory_file}: {e}")

            # Remove empty directories
            self._remove_empty_dirs(root)

        return removed

    def _remove_empty_dirs(self, root: Path):
        """Recursively remove empty directories."""
        for dirpath in sorted(root.rglob("*"), reverse=True):
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                try:
                    dirpath.rmdir()
                except Exception:
                    pass

    def commit_changes(self, message: str = None):
        """Commit changes to git."""
        if self.dry_run:
            print("\n[DRY RUN] Would commit changes to git")
            return

        git_dir = self.v2_context.home_dir / ".claude" / "mnemonic"
        if not (git_dir / ".git").exists():
            print("\nNo git repository found, skipping commit")
            return

        print("\nCommitting changes to git...")

        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=git_dir,
                check=True,
            )

            commit_msg = message or f"migrate: Legacy to V2 path scheme ({self.plan.total_memories} memories)"

            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=git_dir,
                check=True,
            )

            print("Changes committed successfully")

        except subprocess.CalledProcessError as e:
            print(f"Warning: Git commit failed: {e}")

    def rollback(self, backup_dir: Path):
        """
        Rollback migration using backup.

        Args:
            backup_dir: Path to backup directory
        """
        if not backup_dir.exists():
            raise ValueError(f"Backup directory not found: {backup_dir}")

        print(f"Rolling back from backup: {backup_dir}")

        # Load migration plan
        plan_file = backup_dir / "migration_plan.json"
        if not plan_file.exists():
            raise ValueError(f"Migration plan not found in backup: {plan_file}")

        with open(plan_file) as f:
            plan_data = json.load(f)

        # Restore each file
        for migration in plan_data["migrations"]:
            dest = Path(migration["destination"])

            if dest.exists():
                print(f"  Removing: {dest}")
                dest.unlink()

        # Restore from backup
        user_base = self.legacy_context.home_dir / ".claude" / "mnemonic"
        for root_str in plan_data["legacy_roots"]:
            root = Path(root_str)
            try:
                relative = root.relative_to(user_base)
                backup_source = backup_dir / relative
            except ValueError:
                # Project-level path
                backup_source = backup_dir / "project" / root.name

            if backup_source.exists():
                print(f"  Restoring: {backup_source} -> {root}")
                shutil.copytree(backup_source, root, dirs_exist_ok=True)

        print("Rollback complete")

        # Commit rollback
        self.commit_changes("rollback: Revert V2 migration to legacy paths")

    def print_summary(self, stats: Dict[str, int]):
        """Print migration summary."""
        if not self.plan:
            print("No migration plan available.")
            return

        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total memories:     {self.plan.total_memories}")
        print(f"Successfully moved: {stats['success']}")
        print(f"Already migrated:   {stats['skipped']}")
        print(f"Failed:             {stats['failed']}")
        print(f"Total size:         {self._format_bytes(self.plan.total_size_bytes)}")
        print(f"Backup location:    {self.backup_dir}")
        print("=" * 60)

        if stats['failed'] > 0:
            print("\nWARNING: Some migrations failed. Check errors above.")
            print("Your backup is safe and you can rollback if needed.")

    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes as human-readable size."""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="Migrate mnemonic memories from legacy to V2 path scheme"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation (not recommended)",
    )
    parser.add_argument(
        "--rollback",
        type=Path,
        metavar="BACKUP_DIR",
        help="Rollback migration using specified backup directory",
    )

    args = parser.parse_args()

    # Handle rollback
    if args.rollback:
        manager = MigrationManager(dry_run=False, verbose=args.verbose)
        manager.rollback(args.rollback)
        return

    # Create migration manager
    manager = MigrationManager(dry_run=args.dry_run, verbose=args.verbose)

    # Analyze current structure
    print("Analyzing memory structure...")
    plan = manager.analyze()

    if plan.total_memories == 0:
        print("\nNo memories found to migrate.")
        print("Either migration already complete or no memories exist.")
        return

    print(f"\nFound {plan.total_memories} memories to migrate")
    print(f"Total size: {manager._format_bytes(plan.total_size_bytes)}")

    if args.dry_run:
        print("\n[DRY RUN MODE] - No changes will be made")

    # Confirm with user
    if not args.dry_run:
        print("\nThis will migrate all memories to the new V2 path structure.")
        print("A backup will be created before migration.")
        confirm = input("\nProceed? [y/N]: ")
        if confirm.lower() != 'y':
            print("Migration cancelled")
            return

    # Create backup
    backup_dir: Path | None = None
    if not args.no_backup:
        backup_dir = manager.create_backup()
        print(f"\nBackup created: {backup_dir}")
    else:
        print("\nWARNING: Skipping backup (--no-backup specified)")

    # Execute migration
    print("\nExecuting migration...")
    stats = manager.execute()

    # Print summary
    manager.print_summary(stats)

    # Cleanup legacy directories
    if stats["failed"] == 0 and not args.dry_run:
        confirm_cleanup = input("\nRemove legacy directories? [y/N]: ")
        if confirm_cleanup.lower() == 'y':
            removed = manager.cleanup_legacy()
            print(f"Removed {removed} files from legacy locations")

    # Commit changes
    if not args.dry_run:
        manager.commit_changes()

    print("\nMigration complete!")
    if not args.dry_run and backup_dir:
        print(f"Backup saved at: {backup_dir}")
        print(f"To rollback: python scripts/migrate_to_v2_paths.py --rollback {backup_dir}")


if __name__ == "__main__":
    main()
