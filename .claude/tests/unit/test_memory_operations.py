#!/usr/bin/env python3
"""
Unit tests for memory operations using isolated environments.

All tests use fixtures that create temporary directories,
ensuring no pollution of actual memory files.
"""

import pytest


class TestMemoryCreation:
    """Test memory file creation."""

    def test_create_memory_in_decisions(self, memory_factory, isolated_mnemonic_env):
        """Memory created in decisions namespace."""
        mem = memory_factory.create(
            namespace="decisions",
            title="Use PostgreSQL for database",
            content="We decided to use PostgreSQL because...",
        )

        assert mem.exists()
        assert "/decisions/" in str(mem)
        assert mem.suffix == ".md"

        content = mem.read_text()
        assert "id:" in content
        assert "Use PostgreSQL" in content

    def test_create_memory_in_learnings(self, memory_factory):
        """Memory created in learnings namespace."""
        mem = memory_factory.create(
            namespace="learnings",
            title="API rate limit is 100/min",
            content="Discovered that the external API has a rate limit.",
        )

        assert mem.exists()
        assert "/learnings/" in str(mem)

    def test_create_memory_with_tags(self, memory_factory):
        """Memory includes specified tags."""
        mem = memory_factory.create(
            namespace="patterns",
            title="Use snake_case for DB columns",
            tags=["database", "naming", "conventions"],
        )

        content = mem.read_text()
        assert "database" in content
        assert "naming" in content

    def test_create_project_level_memory(self, memory_factory, isolated_mnemonic_env):
        """Memory created at project level goes to ./.claude/mnemonic."""
        mem = memory_factory.create(
            namespace="context",
            title="Project-specific context",
            level="project",
        )

        assert mem.exists()
        assert str(isolated_mnemonic_env["project_mnemonic"]) in str(mem)

    def test_create_user_level_memory(self, memory_factory, isolated_mnemonic_env):
        """Memory created at user level goes to ${MNEMONIC_ROOT}."""
        mem = memory_factory.create(
            namespace="decisions",
            title="User-level decision",
            level="user",
        )

        assert mem.exists()
        assert str(isolated_mnemonic_env["user_mnemonic"]) in str(mem)

    def test_slug_generation(self, memory_factory):
        """Title is converted to valid slug."""
        mem = memory_factory.create(
            title="Use JWT for Authentication!!",
        )

        # Filename should have slugified title
        assert "use-jwt-for-authentication" in mem.name.lower()
        assert "!!" not in mem.name

    def test_slug_truncation(self, memory_factory):
        """Very long titles are truncated in slug."""
        long_title = "A" * 200
        mem = memory_factory.create(title=long_title)

        # Slug should be max 50 chars
        slug_part = mem.name.replace(".memory.md", "")
        assert len(slug_part) <= 50

    def test_no_uuid_in_filename(self, memory_factory):
        """Memory filename uses slug-only format (no UUID prefix)."""
        import re

        mem = memory_factory.create(title="Test")
        uuid_pattern = r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}-"
        assert not re.search(uuid_pattern, mem.name)
        assert mem.name == "test.memory.md"


class TestMemorySearch:
    """Test memory search functionality."""

    def test_search_finds_memory(self, memory_factory, memory_searcher):
        """Search finds memory by content."""
        memory_factory.create(
            namespace="decisions",
            title="Use Redis",
            content="We will use Redis for caching.",
        )

        results = memory_searcher.search("Redis")
        assert len(results) == 1

    def test_search_finds_multiple(self, memory_factory, memory_searcher):
        """Search finds all matching memories."""
        memory_factory.create(title="Auth with JWT", content="Use JWT tokens")
        memory_factory.create(title="JWT Refresh", content="Refresh JWT every hour")

        results = memory_searcher.search("JWT")
        assert len(results) == 2

    def test_search_no_results(self, memory_factory, memory_searcher):
        """Search returns empty list when no matches."""
        memory_factory.create(title="Unrelated", content="Nothing about databases")

        results = memory_searcher.search("PostgreSQL")
        assert len(results) == 0

    def test_search_case_insensitive(self, memory_factory, memory_searcher):
        """Search is case insensitive by default."""
        memory_factory.create(title="JWT Auth", content="Use JWT tokens")

        results = memory_searcher.search("jwt")
        assert len(results) == 1

        results = memory_searcher.search("JWT")
        assert len(results) == 1

    def test_search_by_namespace(self, memory_factory, memory_searcher):
        """Search can filter by namespace."""
        memory_factory.create(namespace="decisions", title="Decision JWT")
        memory_factory.create(namespace="learnings", title="Learning JWT")

        results = memory_searcher.search("JWT", namespace="decisions")
        assert len(results) == 1
        assert "/decisions/" in str(results[0])

    def test_search_both_levels(self, memory_factory, memory_searcher):
        """Search finds memories at both user and project level."""
        memory_factory.create(title="User Auth", level="user")
        memory_factory.create(title="Project Auth", level="project")

        results = memory_searcher.search("Auth")
        assert len(results) == 2


class TestMemoryFormat:
    """Test memory file format validation."""

    def test_has_valid_frontmatter(self, memory_factory):
        """Memory has valid YAML frontmatter."""
        import yaml

        mem = memory_factory.create(title="Test")
        content = mem.read_text()

        # Extract frontmatter
        parts = content.split("---", 2)
        assert len(parts) >= 3

        frontmatter = yaml.safe_load(parts[1])
        assert "id" in frontmatter
        assert "title" in frontmatter
        assert "type" in frontmatter
        assert "created" in frontmatter

    def test_has_valid_id(self, memory_factory):
        """Memory ID is valid UUID."""
        import re

        import yaml

        mem = memory_factory.create(title="Test")
        content = mem.read_text()

        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        uuid_pattern = r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
        assert re.match(uuid_pattern, frontmatter["id"])

    def test_has_valid_timestamp(self, memory_factory):
        """Memory has valid ISO8601 timestamp."""
        import re

        import yaml

        mem = memory_factory.create(title="Test")
        content = mem.read_text()

        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1])

        # YAML may parse timestamp as datetime, convert to string
        created = str(frontmatter["created"])
        iso_pattern = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
        assert re.search(iso_pattern, created)

    def test_has_body_content(self, memory_factory):
        """Memory has body content after frontmatter."""
        mem = memory_factory.create(
            title="Test",
            content="This is the body content.",
        )
        content = mem.read_text()

        parts = content.split("---", 2)
        body = parts[2]

        assert "This is the body content" in body


class TestBlackboard:
    """Test blackboard operations."""

    def test_write_and_read(self, blackboard_factory):
        """Can write and read blackboard entries."""
        blackboard_factory.write("test-key", "test content")
        result = blackboard_factory.read("test-key")
        assert result == "test content"

    def test_read_nonexistent(self, blackboard_factory):
        """Reading nonexistent key returns None."""
        result = blackboard_factory.read("does-not-exist")
        assert result is None

    def test_list_keys(self, blackboard_factory):
        """Can list all blackboard keys."""
        blackboard_factory.write("key1", "content1")
        blackboard_factory.write("key2", "content2")

        keys = blackboard_factory.list_keys()
        assert "key1" in keys
        assert "key2" in keys

    def test_overwrite_entry(self, blackboard_factory):
        """Can overwrite existing entry."""
        blackboard_factory.write("key", "original")
        blackboard_factory.write("key", "updated")

        result = blackboard_factory.read("key")
        assert result == "updated"


class TestNamespaceRouting:
    """Test that memories go to correct namespaces."""

    @pytest.mark.parametrize(
        "namespace,expected_path",
        [
            ("decisions", "/decisions/"),
            ("learnings", "/learnings/"),
            ("patterns", "/patterns/"),
            ("blockers", "/blockers/"),
            ("context", "/context/"),
            ("apis", "/apis/"),
            ("security", "/security/"),
            ("testing", "/testing/"),
        ],
    )
    def test_namespace_routing(self, memory_factory, namespace, expected_path):
        """Memory is created in correct namespace directory."""
        mem = memory_factory.create(namespace=namespace, title="Test")
        assert expected_path in str(mem)


class TestDeduplication:
    """Test memory deduplication logic."""

    def test_detect_similar_memories(self, memory_factory, memory_searcher):
        """Can detect when similar memory already exists."""
        # Create first memory
        memory_factory.create(
            namespace="decisions",
            title="Use Redis for caching",
            content="We decided to use Redis.",
        )

        # Search before creating duplicate - use single term that exists
        results = memory_searcher.search("Redis")
        assert len(results) >= 1  # Should find existing

    def test_different_memories_not_duplicates(self, memory_factory, memory_searcher):
        """Different topics don't trigger duplicate detection."""
        memory_factory.create(title="Use Redis", content="For caching")
        memory_factory.create(title="Use PostgreSQL", content="For database")

        redis_results = memory_searcher.search("Redis")
        pg_results = memory_searcher.search("PostgreSQL")

        assert len(redis_results) == 1
        assert len(pg_results) == 1
