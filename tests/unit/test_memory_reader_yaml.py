#!/usr/bin/env python3
"""
Unit tests for lib/memory_reader.py YAML-based parsing.

Verifies that get_memory_metadata() returns identical results
whether using the YAML parser or the regex fallback.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.memory_reader import _parse_frontmatter, _regex_fallback_parse, get_memory_metadata


class TestParseFrontmatter:
    """Test _parse_frontmatter() YAML parsing with fallback."""

    def test_basic_fields(self):
        text = 'id: abc-12345-def-67890-ghij\ntitle: "Test Memory"\nnamespace: _semantic/decisions\ntype: semantic\n'
        result = _parse_frontmatter(text)
        assert result["id"] == "abc-12345-def-67890-ghij"
        assert result["title"] == "Test Memory"
        assert result["namespace"] == "_semantic/decisions"
        assert result["type"] == "semantic"

    def test_inline_tags(self):
        text = "tags: [auth, jwt, security]\n"
        result = _parse_frontmatter(text)
        assert isinstance(result["tags"], list)
        assert "auth" in result["tags"]
        assert "jwt" in result["tags"]
        assert "security" in result["tags"]

    def test_multiline_tags(self):
        text = "tags:\n  - auth\n  - jwt\n  - security\n"
        result = _parse_frontmatter(text)
        assert isinstance(result["tags"], list)
        assert len(result["tags"]) == 3

    def test_relationships(self):
        text = (
            "relationships:\n"
            "  - type: relates_to\n"
            "    target: aaa-111\n"
            '    label: "Related"\n'
            "  - type: supersedes\n"
            "    target: bbb-222\n"
        )
        result = _parse_frontmatter(text)
        assert isinstance(result["relationships"], list)
        assert len(result["relationships"]) == 2
        assert result["relationships"][0]["type"] == "relates_to"
        assert result["relationships"][0]["target"] == "aaa-111"
        assert result["relationships"][1]["type"] == "supersedes"


class TestRegexFallbackParse:
    """Test _regex_fallback_parse() directly."""

    def test_basic_fields(self):
        text = 'id: abc-12345-def-67890-ghij\ntitle: "Test Memory"\nnamespace: _semantic/decisions\n'
        result = _regex_fallback_parse(text)
        assert result.get("id") == "abc-12345-def-67890-ghij"
        assert result.get("title") == "Test Memory"
        assert result.get("namespace") == "_semantic/decisions"

    def test_inline_tags(self):
        text = "tags: [auth, jwt]\n"
        result = _regex_fallback_parse(text)
        assert "auth" in result.get("tags", [])
        assert "jwt" in result.get("tags", [])

    def test_relationships_regex(self):
        text = "relationships:\n  - type: relates_to\n    target: aaa-111\n"
        result = _regex_fallback_parse(text)
        rels = result.get("relationships", [])
        assert len(rels) == 1
        assert rels[0]["type"] == "relates_to"
        assert rels[0]["target"] == "aaa-111"


class TestGetMemoryMetadataYAML:
    """Test get_memory_metadata() with real files using YAML parsing."""

    def test_basic_metadata(self, tmp_path):
        """Extract basic metadata fields."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            "---\n"
            "id: aaa-111-bbb-222-ccc\n"
            'title: "Test Memory Title"\n'
            "namespace: _semantic/decisions\n"
            "type: semantic\n"
            "tags: [auth, jwt]\n"
            "---\n"
            "\n"
            "# Test Memory Title\n"
            "\n"
            "This is the summary paragraph.\n"
        )

        result = get_memory_metadata(str(mem))

        assert result is not None
        assert result["id"] == "aaa-111-bbb-222-ccc"
        assert result["title"] == "Test Memory Title"
        assert result["namespace"] == "_semantic/decisions"
        assert "auth" in result["tags"]
        assert "jwt" in result["tags"]
        assert result["summary"] == "This is the summary paragraph."

    def test_multiline_tags(self, tmp_path):
        """Extract tags in multi-line YAML list format."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            '---\nid: aaa-111-bbb-222-ccc\ntitle: "Test"\ntags:\n  - alpha\n  - beta\n  - gamma\n---\n\nBody.\n'
        )

        result = get_memory_metadata(str(mem))
        assert result is not None
        assert len(result["tags"]) == 3
        assert "alpha" in result["tags"]
        assert "beta" in result["tags"]
        assert "gamma" in result["tags"]

    def test_relationships_extraction(self, tmp_path):
        """Extract relationships from frontmatter."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            "---\n"
            "id: aaa-111-bbb-222-ccc\n"
            'title: "Test"\n'
            "relationships:\n"
            "  - type: relates_to\n"
            "    target: ddd-444-eee-555-fff\n"
            '    label: "Related decision"\n'
            "  - type: Supersedes\n"
            "    target: ggg-777-hhh-888-iii\n"
            "---\n"
            "\nBody.\n"
        )

        result = get_memory_metadata(str(mem))
        assert result is not None
        assert len(result["relationships"]) == 2
        assert result["relationships"][0]["type"] == "relates_to"
        assert result["relationships"][0]["target"] == "ddd-444-eee-555-fff"
        assert result["relationships"][0]["label"] == "Related decision"
        assert result["relationships"][1]["type"] == "Supersedes"

    def test_nonexistent_file(self):
        """Return None for nonexistent file."""
        result = get_memory_metadata("/nonexistent/path.memory.md")
        assert result is None

    def test_no_frontmatter(self, tmp_path):
        """File without frontmatter returns minimal metadata."""
        mem = tmp_path / "test.memory.md"
        mem.write_text("Just body content, no frontmatter.\n")

        result = get_memory_metadata(str(mem))
        assert result is not None
        assert result["id"] is None
        assert result["title"] == "test.memory"

    def test_nested_yaml_fields(self, tmp_path):
        """Complex YAML with nested fields parses correctly."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            "---\n"
            "id: aaa-111-bbb-222-ccc\n"
            'title: "Nested Test"\n'
            "namespace: _procedural/patterns\n"
            "temporal:\n"
            "  valid_from: 2026-01-01T00:00:00Z\n"
            "  decay:\n"
            "    model: exponential\n"
            "    currentStrength: 0.85\n"
            "provenance:\n"
            "  source_type: conversation\n"
            "  confidence: 0.95\n"
            "---\n"
            "\nBody.\n"
        )

        result = get_memory_metadata(str(mem))
        assert result is not None
        assert result["id"] == "aaa-111-bbb-222-ccc"
        assert result["namespace"] == "_procedural/patterns"

    def test_empty_relationships_list(self, tmp_path):
        """Empty relationships: [] returns empty list."""
        mem = tmp_path / "test.memory.md"
        mem.write_text('---\nid: aaa-111-bbb-222-ccc\ntitle: "Test"\nrelationships: []\n---\n\nBody.\n')

        result = get_memory_metadata(str(mem))
        assert result is not None
        assert result["relationships"] == []
