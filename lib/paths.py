#!/usr/bin/env python3
"""
Mnemonic Path Resolution Library

Centralized path resolution for all mnemonic memory operations.
Provides a single source of truth for path construction with support
for migration from legacy path schemes.

Design Goals:
- Single source of truth for all path logic
- Support legacy and new path schemes during migration
- Testable and mockable for unit tests
- Clean abstraction that makes future changes easy

Path Schemes:
- LEGACY: Dual location (user + project) with flat namespace
- V2 (Target): Unified user-level with project hierarchy

Examples:
    # Get memory file path
    resolver = PathResolver()
    path = resolver.get_memory_path(
        namespace="_semantic/decisions",
        scope="project"
    )

    # Get search paths for recall
    paths = resolver.get_search_paths(
        namespace="_semantic/decisions",
        include_project=True
    )
"""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

from lib.config import MnemonicConfig


class PathScheme(Enum):
    """Path scheme versions for migration support."""

    LEGACY = "legacy"  # Current: dual location, flat namespace
    V2 = "v2"  # Target: unified user-level, project hierarchy


class Scope(Enum):
    """Memory scope for organization."""

    USER = "user"  # Cross-project memories
    PROJECT = "project"  # Project-specific memories
    ORG = "org"  # Organization-wide memories (V2 only)


@dataclass
class PathContext:
    """Context information for path resolution."""

    org: str
    project: str
    home_dir: Path
    project_dir: Path
    memory_root: Path
    scheme: PathScheme = PathScheme.LEGACY

    @classmethod
    def detect(cls, scheme: PathScheme = PathScheme.LEGACY) -> "PathContext":
        """Detect context from environment."""
        config = MnemonicConfig.load()
        return cls(
            org=_detect_org(),
            project=_detect_project(),
            home_dir=Path.home(),
            project_dir=Path.cwd(),
            memory_root=config.memory_store_path,
            scheme=scheme,
        )


class PathResolver:
    """
    Central path resolver for all mnemonic operations.

    This class encapsulates all path construction logic, enabling:
    - Easy testing via dependency injection
    - Migration between path schemes
    - Consistent path resolution across all components
    """

    def __init__(self, context: Optional[PathContext] = None):
        """
        Initialize resolver with context.

        Args:
            context: Path context. If None, will auto-detect.
        """
        self.context = context or PathContext.detect()

    def get_memory_dir(
        self,
        namespace: str,
        scope: Scope = Scope.PROJECT,
    ) -> Path:
        """
        Get directory for storing memories.

        Args:
            namespace: Hierarchical namespace (e.g., "_semantic/decisions")
            scope: Memory scope (user, project, or org)

        Returns:
            Path to memory directory

        Examples:
            # LEGACY scheme, project scope
            get_memory_dir("_semantic/decisions", Scope.PROJECT)
            # => ./.claude/mnemonic/semantic/decisions

            # V2 scheme, project scope
            get_memory_dir("_semantic/decisions", Scope.PROJECT)
            # => {memory_root}/{org}/{project}/semantic/decisions

            # V2 scheme, org scope
            get_memory_dir("_semantic/decisions", Scope.ORG)
            # => {memory_root}/{org}/semantic/decisions
        """
        if self.context.scheme == PathScheme.LEGACY:
            return self._get_legacy_memory_dir(namespace, scope)
        else:
            return self._get_v2_memory_dir(namespace, scope)

    def get_memory_path(
        self,
        namespace: str,
        filename: str,
        scope: Scope = Scope.PROJECT,
    ) -> Path:
        """
        Get full path to a memory file.

        Args:
            namespace: Hierarchical namespace
            filename: Memory filename (should end with .memory.md)
            scope: Memory scope

        Returns:
            Full path to memory file
        """
        directory = self.get_memory_dir(namespace, scope)
        return directory / filename

    def get_search_paths(
        self,
        namespace: Optional[str] = None,
        include_user: bool = True,
        include_project: bool = True,
        include_org: bool = False,
    ) -> List[Path]:
        """
        Get ordered list of paths to search for memories.

        Search order priority:
        1. Project-specific memories
        2. Organization-wide memories (V2 only)
        3. User cross-project memories

        Args:
            namespace: Optional namespace filter
            include_user: Include user-scope paths
            include_project: Include project-scope paths
            include_org: Include org-scope paths (V2 only)

        Returns:
            List of paths to search, in priority order
        """
        if self.context.scheme == PathScheme.LEGACY:
            return self._get_legacy_search_paths(namespace, include_user, include_project)
        else:
            return self._get_v2_search_paths(namespace, include_user, include_project, include_org)

    def get_blackboard_dir(
        self,
        scope: Scope = Scope.PROJECT,
    ) -> Path:
        """
        Get blackboard directory for session coordination.

        Args:
            scope: Blackboard scope (project or org)

        Returns:
            Path to blackboard directory
        """
        if self.context.scheme == PathScheme.LEGACY:
            if scope == Scope.PROJECT:
                return self.context.project_dir / ".claude" / "mnemonic" / ".blackboard"
            else:
                return self.context.memory_root / ".blackboard"
        else:
            if scope == Scope.PROJECT:
                base = self.context.memory_root / self.context.org / self.context.project
                return base / ".blackboard"
            else:
                return self.context.memory_root / self.context.org / ".blackboard"

    def get_ontology_paths(self) -> List[Path]:
        """
        Get ordered list of ontology file paths to check.

        Returns:
            List of ontology paths in precedence order:
            1. Project-level ontology
            2. User-level ontology
            3. MIF base ontology
        """
        paths = []

        # Project ontology
        if self.context.scheme == PathScheme.LEGACY:
            paths.append(self.context.project_dir / ".claude" / "mnemonic" / "ontology.yaml")
        else:
            paths.append(self.context.memory_root / self.context.org / self.context.project / "ontology.yaml")

        # User/org ontology
        if self.context.scheme == PathScheme.LEGACY:
            paths.append(self.context.memory_root / "ontology.yaml")
        else:
            paths.append(self.context.memory_root / self.context.org / "ontology.yaml")

        return paths

    def get_all_memory_roots(self) -> List[Path]:
        """
        Get all root directories that may contain memories.

        Useful for operations like:
        - Garbage collection across all memories
        - Health checks
        - Migration scripts

        Returns:
            List of all memory root directories
        """
        if self.context.scheme == PathScheme.LEGACY:
            roots = []
            user_base = self.context.memory_root

            # User org directory
            org_path = user_base / self.context.org
            if org_path.exists():
                roots.append(org_path)

            # Default directory
            default_path = user_base / "default"
            if default_path.exists():
                roots.append(default_path)

            # Project directory
            project_path = self.context.project_dir / ".claude" / "mnemonic"
            if project_path.exists():
                roots.append(project_path)

            return roots
        else:
            # V2: Everything is under memory_root
            base = self.context.memory_root / self.context.org
            return [base] if base.exists() else []

    # Legacy scheme implementations

    def _get_legacy_memory_dir(self, namespace: str, scope: Scope) -> Path:
        """Get memory directory using legacy path scheme."""
        if scope == Scope.PROJECT:
            return self.context.project_dir / ".claude" / "mnemonic" / namespace
        else:
            return self.context.memory_root / self.context.org / namespace

    def _get_legacy_search_paths(
        self,
        namespace: Optional[str],
        include_user: bool,
        include_project: bool,
    ) -> List[Path]:
        """Get search paths using legacy scheme."""
        paths = []

        if include_project:
            project_base = self.context.project_dir / ".claude" / "mnemonic"
            if namespace:
                paths.append(project_base / namespace)
            else:
                paths.append(project_base)

        if include_user:
            user_base = self.context.memory_root

            # Org-specific memories
            org_base = user_base / self.context.org
            if namespace:
                paths.append(org_base / namespace)
            else:
                paths.append(org_base)

            # Default fallback
            default_base = user_base / "default"
            if namespace:
                paths.append(default_base / namespace)
            else:
                paths.append(default_base)

        return [p for p in paths if p.exists()]

    # V2 scheme implementations

    def _get_v2_memory_dir(self, namespace: str, scope: Scope) -> Path:
        """Get memory directory using V2 path scheme."""
        base = self.context.memory_root / self.context.org

        if scope == Scope.PROJECT:
            return base / self.context.project / namespace
        elif scope == Scope.ORG:
            return base / namespace
        else:  # USER scope - store in "shared" or under project
            return base / self.context.project / namespace

    def _get_v2_search_paths(
        self,
        namespace: Optional[str],
        include_user: bool,
        include_project: bool,
        include_org: bool,
    ) -> List[Path]:
        """Get search paths using V2 scheme."""
        paths = []
        base = self.context.memory_root / self.context.org

        # Project-specific (highest priority)
        if include_project:
            project_base = base / self.context.project
            if namespace:
                paths.append(project_base / namespace)
            else:
                paths.append(project_base)

        # Org-wide
        if include_org:
            if namespace:
                paths.append(base / namespace)
            else:
                paths.append(base)

        # Default fallback (for backward compatibility)
        if include_user:
            default_base = self.context.memory_root / "default"
            if namespace:
                paths.append(default_base / namespace)
            else:
                paths.append(default_base)

        return [p for p in paths if p.exists()]


# Helper functions for context detection


def _detect_org() -> str:
    """
    Detect organization from git remote.

    Extracts organization name from git remote URL.
    Falls back to "default" if detection fails.

    Returns:
        Organization name or "default"
    """
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            url = result.stdout.strip()
            # Handle both SSH and HTTPS URLs
            if ":" in url and "@" in url:
                # SSH format: git@github.com:org/repo.git
                org = url.split(":")[-1].split("/")[0]
            else:
                # HTTPS format: https://github.com/org/repo.git
                parts = url.rstrip(".git").split("/")
                org = parts[-2] if len(parts) >= 2 else "default"
            return org.replace(".git", "")
    except Exception:
        pass
    return "default"


def _detect_project() -> str:
    """
    Detect project name from git or directory.

    Returns:
        Project name
    """
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            url = result.stdout.strip()
            return url.rstrip(".git").split("/")[-1]
    except Exception:
        pass
    return Path.cwd().name


# Convenience functions for backward compatibility


def get_default_resolver() -> PathResolver:
    """Get default path resolver with auto-detected context."""
    return PathResolver()


def get_memory_dir(namespace: str, scope: str = "project") -> Path:
    """
    Convenience function for getting memory directory.

    Args:
        namespace: Hierarchical namespace
        scope: "user", "project", or "org"

    Returns:
        Path to memory directory
    """
    resolver = get_default_resolver()
    scope_enum = Scope.PROJECT if scope == "project" else Scope.USER if scope == "user" else Scope.ORG
    return resolver.get_memory_dir(namespace, scope_enum)


def get_search_paths(
    namespace: Optional[str] = None,
    include_user: bool = True,
    include_project: bool = True,
) -> List[Path]:
    """
    Convenience function for getting search paths.

    Args:
        namespace: Optional namespace filter
        include_user: Include user-scope paths
        include_project: Include project-scope paths

    Returns:
        List of search paths in priority order
    """
    resolver = get_default_resolver()
    return resolver.get_search_paths(namespace, include_user, include_project)


def get_blackboard_dir(scope: str = "project") -> Path:
    """
    Convenience function for getting blackboard directory.

    Args:
        scope: "project" or "org"

    Returns:
        Path to blackboard directory
    """
    resolver = get_default_resolver()
    scope_enum = Scope.PROJECT if scope == "project" else Scope.ORG
    return resolver.get_blackboard_dir(scope_enum)
