#!/usr/bin/env python3
"""
Unit tests for lib/paths.py path resolution.

Tests path resolution logic in isolation with mocked context.
"""

import pytest
from pathlib import Path
from lib.paths import (
    PathResolver,
    PathContext,
    PathScheme,
    Scope,
    get_default_resolver,
    get_memory_dir,
    get_search_paths,
    get_blackboard_dir,
)


@pytest.fixture
def legacy_context():
    """Create a legacy scheme context for testing."""
    return PathContext(
        org="testorg",
        project="testproject",
        home_dir=Path("/home/testuser"),
        project_dir=Path("/home/testuser/projects/testproject"),
        memory_root=Path("/home/testuser/.claude/mnemonic"),
        scheme=PathScheme.LEGACY,
    )


@pytest.fixture
def v2_context():
    """Create a V2 scheme context for testing."""
    return PathContext(
        org="testorg",
        project="testproject",
        home_dir=Path("/home/testuser"),
        project_dir=Path("/home/testuser/projects/testproject"),
        memory_root=Path("/home/testuser/.claude/mnemonic"),
        scheme=PathScheme.V2,
    )


class TestLegacyPathScheme:
    """Test legacy path scheme resolution."""

    def test_project_memory_dir(self, legacy_context):
        """Test project-scoped memory directory."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_memory_dir("_semantic/decisions", Scope.PROJECT)
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic/_semantic/decisions")
        assert path == expected

    def test_user_memory_dir(self, legacy_context):
        """Test user-scoped memory directory."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_memory_dir("_semantic/decisions", Scope.USER)
        expected = Path("/home/testuser/.claude/mnemonic/testorg/_semantic/decisions")
        assert path == expected

    def test_memory_path(self, legacy_context):
        """Test full memory file path."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_memory_path("_semantic/decisions", "uuid-test.memory.md", Scope.PROJECT)
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic/_semantic/decisions/uuid-test.memory.md")
        assert path == expected

    def test_blackboard_project(self, legacy_context):
        """Test project blackboard directory."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_blackboard_dir(Scope.PROJECT)
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic/.blackboard")
        assert path == expected

    def test_blackboard_user(self, legacy_context):
        """Test user blackboard directory."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_blackboard_dir(Scope.USER)
        expected = Path("/home/testuser/.claude/mnemonic/.blackboard")
        assert path == expected

    def test_search_paths_all(self, legacy_context, tmp_path, monkeypatch):
        """Test search paths with all scopes."""
        # Create temporary directories
        project_dir = tmp_path / "project" / ".claude" / "mnemonic" / "_semantic"
        user_org_dir = tmp_path / "home" / ".claude" / "mnemonic" / "testorg" / "_semantic"
        user_default_dir = tmp_path / "home" / ".claude" / "mnemonic" / "default" / "_semantic"

        project_dir.mkdir(parents=True)
        user_org_dir.mkdir(parents=True)
        user_default_dir.mkdir(parents=True)

        # Update context with temporary paths
        context = PathContext(
            org="testorg",
            project="testproject",
            home_dir=tmp_path / "home",
            project_dir=tmp_path / "project",
            memory_root=tmp_path / "home" / ".claude" / "mnemonic",
            scheme=PathScheme.LEGACY,
        )

        resolver = PathResolver(context)
        paths = resolver.get_search_paths("_semantic", include_user=True, include_project=True)

        # Should return in priority order: project, org, default
        assert len(paths) == 3
        assert paths[0] == project_dir
        assert paths[1] == user_org_dir
        assert paths[2] == user_default_dir

    def test_search_paths_project_only(self, legacy_context, tmp_path):
        """Test search paths with project scope only."""
        project_dir = tmp_path / "project" / ".claude" / "mnemonic"
        project_dir.mkdir(parents=True)

        context = PathContext(
            org="testorg",
            project="testproject",
            home_dir=tmp_path / "home",
            project_dir=tmp_path / "project",
            memory_root=tmp_path / "home" / ".claude" / "mnemonic",
            scheme=PathScheme.LEGACY,
        )

        resolver = PathResolver(context)
        paths = resolver.get_search_paths(include_user=False, include_project=True)

        assert len(paths) == 1
        assert paths[0] == project_dir

    def test_ontology_paths(self, legacy_context):
        """Test ontology resolution order."""
        resolver = PathResolver(legacy_context)
        paths = resolver.get_ontology_paths()

        assert len(paths) == 2
        assert paths[0] == Path("/home/testuser/projects/testproject/.claude/mnemonic/ontology.yaml")
        assert paths[1] == Path("/home/testuser/.claude/mnemonic/ontology.yaml")


class TestV2PathScheme:
    """Test V2 (unified) path scheme resolution."""

    def test_project_memory_dir(self, v2_context):
        """Test project-scoped memory directory in V2."""
        resolver = PathResolver(v2_context)
        path = resolver.get_memory_dir("_semantic/decisions", Scope.PROJECT)
        expected = Path("/home/testuser/.claude/mnemonic/testorg/testproject/_semantic/decisions")
        assert path == expected

    def test_org_memory_dir(self, v2_context):
        """Test org-scoped memory directory in V2."""
        resolver = PathResolver(v2_context)
        path = resolver.get_memory_dir("_semantic/decisions", Scope.ORG)
        expected = Path("/home/testuser/.claude/mnemonic/testorg/_semantic/decisions")
        assert path == expected

    def test_user_memory_dir(self, v2_context):
        """Test user-scoped memory directory in V2 (stored under project)."""
        resolver = PathResolver(v2_context)
        path = resolver.get_memory_dir("_semantic/decisions", Scope.USER)
        expected = Path("/home/testuser/.claude/mnemonic/testorg/testproject/_semantic/decisions")
        assert path == expected

    def test_blackboard_project(self, v2_context):
        """Test project blackboard directory in V2."""
        resolver = PathResolver(v2_context)
        path = resolver.get_blackboard_dir(Scope.PROJECT)
        expected = Path("/home/testuser/.claude/mnemonic/testorg/testproject/.blackboard")
        assert path == expected

    def test_blackboard_org(self, v2_context):
        """Test org blackboard directory in V2."""
        resolver = PathResolver(v2_context)
        path = resolver.get_blackboard_dir(Scope.ORG)
        expected = Path("/home/testuser/.claude/mnemonic/testorg/.blackboard")
        assert path == expected

    def test_search_paths_all(self, v2_context, tmp_path):
        """Test search paths with all scopes in V2."""
        # Create temporary directories
        project_dir = tmp_path / ".claude" / "mnemonic" / "testorg" / "testproject" / "_semantic"
        org_dir = tmp_path / ".claude" / "mnemonic" / "testorg" / "_semantic"
        default_dir = tmp_path / ".claude" / "mnemonic" / "default" / "_semantic"

        project_dir.mkdir(parents=True)
        org_dir.mkdir(parents=True)
        default_dir.mkdir(parents=True)

        context = PathContext(
            org="testorg",
            project="testproject",
            home_dir=tmp_path,
            project_dir=tmp_path / "projects" / "testproject",
            memory_root=tmp_path / ".claude" / "mnemonic",
            scheme=PathScheme.V2,
        )

        resolver = PathResolver(context)
        paths = resolver.get_search_paths("_semantic", include_user=True, include_project=True, include_org=True)

        # Should return in priority order: project, org, default
        assert len(paths) == 3
        assert paths[0] == project_dir
        assert paths[1] == org_dir
        assert paths[2] == default_dir

    def test_search_paths_org_only(self, v2_context, tmp_path):
        """Test search paths with org scope only in V2."""
        org_dir = tmp_path / ".claude" / "mnemonic" / "testorg" / "_semantic"
        org_dir.mkdir(parents=True)

        context = PathContext(
            org="testorg",
            project="testproject",
            home_dir=tmp_path,
            project_dir=tmp_path / "projects" / "testproject",
            memory_root=tmp_path / ".claude" / "mnemonic",
            scheme=PathScheme.V2,
        )

        resolver = PathResolver(context)
        paths = resolver.get_search_paths("_semantic", include_user=False, include_project=False, include_org=True)

        assert len(paths) == 1
        assert paths[0] == org_dir

    def test_ontology_paths(self, v2_context):
        """Test ontology resolution order in V2."""
        resolver = PathResolver(v2_context)
        paths = resolver.get_ontology_paths()

        assert len(paths) == 2
        assert paths[0] == Path("/home/testuser/.claude/mnemonic/testorg/testproject/ontology.yaml")
        assert paths[1] == Path("/home/testuser/.claude/mnemonic/testorg/ontology.yaml")

    def test_all_memory_roots(self, v2_context, tmp_path):
        """Test getting all memory root directories in V2."""
        org_dir = tmp_path / ".claude" / "mnemonic" / "testorg"
        org_dir.mkdir(parents=True)

        context = PathContext(
            org="testorg",
            project="testproject",
            home_dir=tmp_path,
            project_dir=tmp_path / "projects" / "testproject",
            memory_root=tmp_path / ".claude" / "mnemonic",
            scheme=PathScheme.V2,
        )

        resolver = PathResolver(context)
        roots = resolver.get_all_memory_roots()

        assert len(roots) == 1
        assert roots[0] == org_dir


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    def test_get_memory_dir(self, monkeypatch, legacy_context):
        """Test convenience get_memory_dir function."""

        # Mock the default resolver to use our test context
        def mock_resolver():
            return PathResolver(legacy_context)

        monkeypatch.setattr("lib.paths.get_default_resolver", mock_resolver)

        path = get_memory_dir("_semantic/decisions", "project")
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic/_semantic/decisions")
        assert path == expected

    def test_get_blackboard_dir(self, monkeypatch, legacy_context):
        """Test convenience get_blackboard_dir function."""

        def mock_resolver():
            return PathResolver(legacy_context)

        monkeypatch.setattr("lib.paths.get_default_resolver", mock_resolver)

        path = get_blackboard_dir("project")
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic/.blackboard")
        assert path == expected


class TestNamespaceHierarchy:
    """Test handling of hierarchical namespaces."""

    def test_nested_namespace(self, legacy_context):
        """Test deeply nested namespace paths."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_memory_dir("_semantic/decisions/architecture", Scope.PROJECT)
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic/_semantic/decisions/architecture")
        assert path == expected

    def test_root_namespace(self, legacy_context):
        """Test root-level namespace (_semantic, _episodic, _procedural)."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_memory_dir("_semantic", Scope.USER)
        expected = Path("/home/testuser/.claude/mnemonic/testorg/_semantic")
        assert path == expected


class TestPathContext:
    """Test PathContext creation and detection."""

    def test_manual_context_creation(self):
        """Test manually creating a context."""
        context = PathContext(
            org="myorg",
            project="myproject",
            home_dir=Path("/home/user"),
            project_dir=Path("/home/user/code/myproject"),
            memory_root=Path("/home/user/.claude/mnemonic"),
            scheme=PathScheme.LEGACY,
        )

        assert context.org == "myorg"
        assert context.project == "myproject"
        assert context.scheme == PathScheme.LEGACY

    def test_context_with_v2_scheme(self):
        """Test context with V2 scheme."""
        context = PathContext(
            org="myorg",
            project="myproject",
            home_dir=Path("/home/user"),
            project_dir=Path("/home/user/code/myproject"),
            memory_root=Path("/home/user/.claude/mnemonic"),
            scheme=PathScheme.V2,
        )

        assert context.scheme == PathScheme.V2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_namespace(self, legacy_context):
        """Test handling of empty namespace."""
        resolver = PathResolver(legacy_context)
        path = resolver.get_memory_dir("", Scope.PROJECT)
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic")
        assert path == expected

    def test_default_org(self, legacy_context):
        """Test handling of default organization."""
        context = PathContext(
            org="default",
            project="testproject",
            home_dir=Path("/home/testuser"),
            project_dir=Path("/home/testuser/projects/testproject"),
            memory_root=Path("/home/testuser/.claude/mnemonic"),
            scheme=PathScheme.LEGACY,
        )

        resolver = PathResolver(context)
        path = resolver.get_memory_dir("_semantic", Scope.USER)
        expected = Path("/home/testuser/.claude/mnemonic/default/_semantic")
        assert path == expected

    def test_special_characters_in_namespace(self, legacy_context):
        """Test namespace with special characters."""
        resolver = PathResolver(legacy_context)
        # Path library handles special chars naturally
        path = resolver.get_memory_dir("custom-ns/sub_ns", Scope.PROJECT)
        expected = Path("/home/testuser/projects/testproject/.claude/mnemonic/custom-ns/sub_ns")
        assert path == expected
