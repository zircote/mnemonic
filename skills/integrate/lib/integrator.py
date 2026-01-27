#!/usr/bin/env python3
"""
Mnemonic Integrator - Main Orchestration Logic

Orchestrates the integration of mnemonic protocol into plugin components.
This is the single source of truth for integration operations.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    from .frontmatter_updater import FrontmatterUpdater
    from .marker_parser import MarkerParser
    from .template_validator import TemplateValidator, ValidationResult
except ImportError:
    from frontmatter_updater import FrontmatterUpdater
    from marker_parser import MarkerParser
    from template_validator import TemplateValidator, ValidationResult


@dataclass
class IntegrationResult:
    """Result of integrating a single file."""

    file_path: Path
    success: bool
    action: str  # "inserted", "updated", "migrated", "removed", "skipped"
    message: str
    had_legacy: bool = False
    markers_added: bool = False
    tools_added: List[str] = field(default_factory=list)


@dataclass
class IntegrationReport:
    """Complete report of integration operation."""

    plugin_root: Path
    template_path: Path
    mode: str  # "integrate", "remove", "migrate", "verify"
    results: List[IntegrationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def all_successful(self) -> bool:
        return self.failure_count == 0 and len(self.errors) == 0


class Integrator:
    """Main orchestrator for mnemonic protocol integration."""

    # Component types that can be integrated
    COMPONENT_TYPES = ["commands", "skills", "agents"]

    # File extensions to process
    VALID_EXTENSIONS = {".md", ".markdown"}

    def __init__(self, plugin_root: Path, template_path: Optional[Path] = None):
        """Initialize integrator.

        Args:
            plugin_root: Root directory of the plugin
            template_path: Path to protocol template (auto-detected if None)
        """
        self.plugin_root = Path(plugin_root).resolve()
        self.template_path = template_path or self._find_template()

        self.marker_parser = MarkerParser()
        self.template_validator = TemplateValidator()
        self.frontmatter_updater = FrontmatterUpdater()

        self._template_content: Optional[str] = None

    def _find_template(self) -> Path:
        """Find the mnemonic protocol template.

        Returns:
            Path to template file

        Raises:
            FileNotFoundError: If template cannot be found
        """
        # Check standard locations
        candidates = [
            self.plugin_root / "templates" / "mnemonic-protocol.md",
            self.plugin_root / ".claude-plugin" / "templates" / "mnemonic-protocol.md",
            self.plugin_root / "mnemonic-protocol.md",
        ]

        # Also check CLAUDE_PLUGIN_ROOT if set
        plugin_root_env = os.environ.get("CLAUDE_PLUGIN_ROOT")
        if plugin_root_env:
            plugin_root_path = Path(plugin_root_env).resolve()
            candidates.insert(0, plugin_root_path / "templates" / "mnemonic-protocol.md")

        for candidate in candidates:
            if candidate.exists():
                resolved = candidate.resolve()
                # Validate template is within expected directories (no path traversal)
                allowed_roots = [self.plugin_root]
                if plugin_root_env:
                    allowed_roots.append(Path(plugin_root_env).resolve())

                is_valid = any(
                    self._is_path_within(resolved, root) for root in allowed_roots
                )
                if not is_valid:
                    continue  # Skip templates outside allowed roots
                return resolved

        raise FileNotFoundError(
            f"Mnemonic protocol template not found. Searched: {[str(c) for c in candidates]}"
        )

    def _is_path_within(self, path: Path, root: Path) -> bool:
        """Check if path is within root directory.

        Args:
            path: Path to check (should be resolved)
            root: Root directory to check against

        Returns:
            True if path is within root
        """
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _load_template(self) -> str:
        """Load and cache template content.

        Returns:
            Template content

        Raises:
            ValueError: If template is invalid
        """
        if self._template_content is not None:
            return self._template_content

        result = self.template_validator.validate_template(self.template_path)
        if not result.valid:
            raise ValueError(f"Invalid template: {'; '.join(result.errors)}")

        self._template_content = self.template_path.read_text()
        return self._template_content

    def _get_manifest(self) -> Optional[Dict]:
        """Load plugin manifest if it exists.

        Returns:
            Manifest dict or None
        """
        manifest_path = self.plugin_root / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            return None

        try:
            return json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            return None

    def discover_components(self) -> Dict[str, List[Path]]:
        """Discover all integrable components in the plugin.

        Returns:
            Dict mapping component type to list of file paths
        """
        components: Dict[str, List[Path]] = {t: [] for t in self.COMPONENT_TYPES}

        # Try manifest first
        manifest = self._get_manifest()
        if manifest:
            for comp_type in self.COMPONENT_TYPES:
                if comp_type in manifest:
                    for rel_path in manifest[comp_type]:
                        full_path = self.plugin_root / ".claude-plugin" / rel_path
                        if full_path.exists() and full_path.suffix in self.VALID_EXTENSIONS:
                            components[comp_type].append(full_path)

        # Also scan directories for any missed files
        for comp_type in self.COMPONENT_TYPES:
            comp_dir = self.plugin_root / ".claude-plugin" / comp_type
            if comp_dir.exists():
                for file_path in comp_dir.rglob("*.md"):
                    if file_path not in components[comp_type]:
                        # Skip symlinks or files that resolve outside plugin root
                        if file_path.is_symlink():
                            try:
                                file_path.resolve().relative_to(self.plugin_root)
                            except ValueError:
                                continue  # Symlink points outside, skip
                        components[comp_type].append(file_path)

        return components

    def _validate_path(self, file_path: Path) -> Optional[str]:
        """Validate that a file path is safe to operate on.

        Args:
            file_path: Path to validate

        Returns:
            Error message if invalid, None if valid
        """
        # Resolve to absolute path
        resolved = file_path.resolve()

        # Check for directory traversal (path should be within plugin root)
        try:
            resolved.relative_to(self.plugin_root)
        except ValueError:
            return f"Path {resolved} is outside plugin root {self.plugin_root}"

        # Check for symlink attacks
        if file_path.is_symlink():
            target = file_path.resolve()
            try:
                target.relative_to(self.plugin_root)
            except ValueError:
                return f"Symlink {file_path} points outside plugin root"

        return None

    def integrate_file(
        self,
        file_path: Path,
        dry_run: bool = False,
        force: bool = False,
    ) -> IntegrationResult:
        """Integrate mnemonic protocol into a single file.

        Args:
            file_path: Path to file to integrate
            dry_run: If True, don't write changes
            force: If True, overwrite existing markers

        Returns:
            IntegrationResult with details of operation
        """
        file_path = Path(file_path).resolve()

        # Validate path security
        path_error = self._validate_path(file_path)
        if path_error:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"Security error: {path_error}",
            )

        if not file_path.exists():
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"File not found: {file_path}",
            )

        try:
            content = file_path.read_text()
            template = self._load_template()
        except Exception as e:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=str(e),
            )

        # Check current state
        has_markers = self.marker_parser.has_markers(content)
        has_legacy = self.marker_parser.has_legacy_pattern(content)

        # Determine action
        if has_markers and not force:
            # Update existing markers
            try:
                # Extract just the content between markers from template
                template_inner = self.marker_parser.extract_between(template)
                if template_inner is None:
                    template_inner = template

                new_content = self.marker_parser.replace_between(content, f"\n{template_inner}\n")
                action = "updated"
            except ValueError as e:
                return IntegrationResult(
                    file_path=file_path,
                    success=False,
                    action="skipped",
                    message=str(e),
                )
        elif has_legacy:
            # Migrate legacy section
            new_content = self.marker_parser.migrate_legacy(content, template)
            action = "migrated"
        else:
            # Fresh insert after frontmatter
            new_content = self.marker_parser.insert_after_frontmatter(content, template)
            action = "inserted"

        # Add required tools to frontmatter
        tools_added = []
        if self.frontmatter_updater.has_frontmatter(new_content):
            missing = self.frontmatter_updater.get_missing_tools(new_content)
            if missing:
                new_content = self.frontmatter_updater.add_tools(new_content, missing)
                tools_added = missing

        # Write if not dry run
        if not dry_run:
            file_path.write_text(new_content)

        return IntegrationResult(
            file_path=file_path,
            success=True,
            action=action,
            message=f"Successfully {action} mnemonic protocol",
            had_legacy=has_legacy,
            markers_added=(action == "inserted"),
            tools_added=tools_added,
        )

    def remove_from_file(self, file_path: Path, dry_run: bool = False) -> IntegrationResult:
        """Remove mnemonic protocol from a file.

        Args:
            file_path: Path to file
            dry_run: If True, don't write changes

        Returns:
            IntegrationResult with details
        """
        file_path = Path(file_path).resolve()

        # Validate path security
        path_error = self._validate_path(file_path)
        if path_error:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"Security error: {path_error}",
            )

        if not file_path.exists():
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"File not found: {file_path}",
            )

        try:
            content = file_path.read_text()
        except Exception as e:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=str(e),
            )

        if not self.marker_parser.has_markers(content):
            return IntegrationResult(
                file_path=file_path,
                success=True,
                action="skipped",
                message="No markers found to remove",
            )

        new_content = self.marker_parser.remove_markers(content)

        if not dry_run:
            file_path.write_text(new_content)

        return IntegrationResult(
            file_path=file_path,
            success=True,
            action="removed",
            message="Successfully removed mnemonic protocol",
        )

    def verify_file(self, file_path: Path) -> IntegrationResult:
        """Verify that a file has correct mnemonic integration.

        Args:
            file_path: Path to file

        Returns:
            IntegrationResult with verification status
        """
        file_path = Path(file_path).resolve()

        # Validate path security
        path_error = self._validate_path(file_path)
        if path_error:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"Security error: {path_error}",
            )

        if not file_path.exists():
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"File not found: {file_path}",
            )

        try:
            content = file_path.read_text()
            template = self._load_template()
        except Exception as e:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=str(e),
            )

        # Check markers
        if not self.marker_parser.has_markers(content):
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message="Missing mnemonic protocol markers",
            )

        # Validate markers
        valid, error = self.marker_parser.has_valid_markers(content)
        if not valid:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"Invalid markers: {error}",
            )

        # Verify content matches template
        matches = self.template_validator.verify_insertion(content, template)
        if not matches:
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message="Content between markers does not match template",
            )

        # Check required tools
        if not self.frontmatter_updater.has_all_required_tools(content):
            missing = self.frontmatter_updater.get_missing_tools(content)
            return IntegrationResult(
                file_path=file_path,
                success=False,
                action="skipped",
                message=f"Missing required tools: {', '.join(missing)}",
            )

        return IntegrationResult(
            file_path=file_path,
            success=True,
            action="verified",
            message="Integration verified successfully",
        )

    def run(
        self,
        mode: str = "integrate",
        component_types: Optional[List[str]] = None,
        files: Optional[List[Path]] = None,
        dry_run: bool = False,
        force: bool = False,
        git_commit: bool = False,
        rollback_on_failure: bool = True,
    ) -> IntegrationReport:
        """Run integration operation.

        Args:
            mode: Operation mode ("integrate", "remove", "migrate", "verify")
            component_types: Types to process (None = all)
            files: Specific files to process (None = discover)
            dry_run: If True, don't write changes
            force: If True, overwrite existing content
            git_commit: If True, commit changes to git
            rollback_on_failure: If True, restore files on any failure

        Returns:
            IntegrationReport with complete results
        """
        report = IntegrationReport(
            plugin_root=self.plugin_root,
            template_path=self.template_path,
            mode=mode,
        )

        # Validate template first
        try:
            self._load_template()
        except Exception as e:
            report.errors.append(f"Template error: {e}")
            return report

        # Get files to process
        if files:
            target_files = [Path(f).resolve() for f in files]
        else:
            components = self.discover_components()
            if component_types:
                components = {k: v for k, v in components.items() if k in component_types}
            target_files = [f for files in components.values() for f in files]

        if not target_files:
            report.warnings.append("No files found to process")
            return report

        # Track original file contents for rollback (using temp files for crash safety)
        backup_dir: Optional[Path] = None
        backups: Dict[Path, Path] = {}  # Maps original path to backup path
        if rollback_on_failure and not dry_run and mode != "verify":
            backup_dir = Path(tempfile.mkdtemp(prefix="mnemonic_backup_"))
            for file_path in target_files:
                if file_path.exists():
                    try:
                        backup_file = backup_dir / f"{file_path.name}.{id(file_path)}.bak"
                        backup_file.write_text(file_path.read_text())
                        backups[file_path] = backup_file
                    except Exception:
                        pass  # If we can't backup, we can't rollback

        # Process each file
        for file_path in target_files:
            if mode == "integrate":
                result = self.integrate_file(file_path, dry_run=dry_run, force=force)
            elif mode == "remove":
                result = self.remove_from_file(file_path, dry_run=dry_run)
            elif mode == "verify":
                result = self.verify_file(file_path)
            elif mode == "migrate":
                # Migrate is just integrate with legacy awareness
                result = self.integrate_file(file_path, dry_run=dry_run, force=False)
            else:
                report.errors.append(f"Unknown mode: {mode}")
                return report

            report.results.append(result)

            # Check for failure and rollback if enabled
            if not result.success and rollback_on_failure and not dry_run:
                self._rollback(backups, report, backup_dir)
                return report

        # Write manifest for tracking (integrate/migrate modes only)
        if mode in ("integrate", "migrate") and not dry_run and report.all_successful:
            try:
                self._write_manifest(report)
            except Exception as e:
                report.warnings.append(f"Failed to write manifest: {e}")

        # Git commit if requested
        if git_commit and not dry_run and report.all_successful:
            self._git_commit(report)

        # Clean up backup directory on success
        if backup_dir and backup_dir.exists():
            import shutil
            try:
                shutil.rmtree(backup_dir)
            except Exception:
                pass  # Best effort cleanup

        return report

    def _rollback(
        self,
        backups: Dict[Path, Path],
        report: IntegrationReport,
        backup_dir: Optional[Path] = None,
    ) -> None:
        """Rollback changes by restoring file backups from temp files.

        Args:
            backups: Dict mapping file paths to their backup temp file paths
            report: Integration report to add warnings to
            backup_dir: Temp directory containing backups (will be cleaned up)
        """
        import shutil

        rolled_back = 0
        for file_path, backup_path in backups.items():
            try:
                if backup_path.exists():
                    file_path.write_text(backup_path.read_text())
                    rolled_back += 1
            except Exception as e:
                report.errors.append(f"Rollback failed for {file_path}: {e}")

        if rolled_back > 0:
            report.warnings.append(f"Rolled back {rolled_back} file(s) due to failure")

        # Clean up temp backup directory
        if backup_dir and backup_dir.exists():
            try:
                shutil.rmtree(backup_dir)
            except Exception:
                pass  # Best effort cleanup

    def _git_commit(self, report: IntegrationReport) -> None:
        """Commit integration changes to git.

        Args:
            report: Integration report to use for commit message
        """
        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.plugin_root,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                report.warnings.append("Not a git repository, skipping commit")
                return

            # Stage changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.plugin_root,
                check=True,
            )

            # Build commit message
            actions = {}
            for r in report.results:
                actions[r.action] = actions.get(r.action, 0) + 1

            action_summary = ", ".join(f"{v} {k}" for k, v in actions.items())
            message = f"chore(mnemonic): {report.mode} integration ({action_summary})"

            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.plugin_root,
                check=True,
            )

        except subprocess.CalledProcessError as e:
            report.warnings.append(f"Git commit failed: {e}")

    def _write_manifest(self, report: IntegrationReport) -> None:
        """Write integration manifest for tracking.

        Creates .mnemonic-integration-manifest.json in the plugin root.

        Args:
            report: Integration report with results
        """
        from datetime import datetime, timezone

        manifest_path = self.plugin_root / ".mnemonic-integration-manifest.json"

        # Build manifest data
        manifest = {
            "version": "1.0.0",
            "integrated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "template_path": str(self.template_path.relative_to(self.plugin_root))
            if self.template_path.is_relative_to(self.plugin_root)
            else str(self.template_path),
            "files": [
                {
                    "path": str(r.file_path.relative_to(self.plugin_root))
                    if r.file_path.is_relative_to(self.plugin_root)
                    else str(r.file_path),
                    "action": r.action,
                    "success": r.success,
                }
                for r in report.results
                if r.success
            ],
            "tools_required": FrontmatterUpdater.REQUIRED_TOOLS,
        }

        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def main():
    """CLI for mnemonic integrator."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Mnemonic Protocol Integrator")
    parser.add_argument(
        "plugin_root",
        nargs="?",
        default=".",
        help="Plugin root directory",
    )
    parser.add_argument(
        "--mode",
        choices=["integrate", "remove", "migrate", "verify"],
        default="integrate",
        help="Operation mode",
    )
    parser.add_argument(
        "--template",
        help="Path to template file",
    )
    parser.add_argument(
        "--type",
        dest="types",
        action="append",
        choices=["commands", "skills", "agents"],
        help="Component types to process",
    )
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        help="Specific files to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing content",
    )
    parser.add_argument(
        "--git-commit",
        action="store_true",
        help="Commit changes to git",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    try:
        template_path = Path(args.template) if args.template else None
        integrator = Integrator(
            plugin_root=Path(args.plugin_root),
            template_path=template_path,
        )

        files = [Path(f) for f in args.files] if args.files else None

        report = integrator.run(
            mode=args.mode,
            component_types=args.types,
            files=files,
            dry_run=args.dry_run,
            force=args.force,
            git_commit=args.git_commit,
        )

        if args.json:
            output = {
                "plugin_root": str(report.plugin_root),
                "template_path": str(report.template_path),
                "mode": report.mode,
                "success": report.all_successful,
                "results": [
                    {
                        "file": str(r.file_path),
                        "success": r.success,
                        "action": r.action,
                        "message": r.message,
                    }
                    for r in report.results
                ],
                "errors": report.errors,
                "warnings": report.warnings,
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Mnemonic Integration Report")
            print(f"{'=' * 40}")
            print(f"Plugin: {report.plugin_root}")
            print(f"Mode: {report.mode}")
            print(f"Results: {report.success_count} success, {report.failure_count} failed")
            print()

            for r in report.results:
                status = "[OK]" if r.success else "[FAIL]"
                print(f"  {status} {r.file_path.name}: {r.action} - {r.message}")
                if r.tools_added:
                    print(f"       Added tools: {', '.join(r.tools_added)}")

            if report.errors:
                print("\nErrors:")
                for e in report.errors:
                    print(f"  - {e}")

            if report.warnings:
                print("\nWarnings:")
                for w in report.warnings:
                    print(f"  - {w}")

        sys.exit(0 if report.all_successful else 1)

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
