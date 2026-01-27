"""Unit tests for marker_parser.py."""

import pytest
from pathlib import Path
import sys

# Add the skills/integrate/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "integrate" / "lib"))

from marker_parser import MarkerParser


@pytest.fixture
def parser():
    """Create a MarkerParser instance."""
    return MarkerParser()


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent / "fixtures" / "integrate"


class TestHasMarkers:
    """Tests for has_markers method."""

    def test_has_markers_true(self, parser):
        content = """<!-- BEGIN MNEMONIC PROTOCOL -->
        Content here
        <!-- END MNEMONIC PROTOCOL -->"""
        assert parser.has_markers(content) is True

    def test_has_markers_false_no_markers(self, parser):
        content = "# Just a heading\n\nSome content"
        assert parser.has_markers(content) is False

    def test_has_markers_false_only_begin(self, parser):
        content = "<!-- BEGIN MNEMONIC PROTOCOL -->\nContent"
        assert parser.has_markers(content) is False

    def test_has_markers_false_only_end(self, parser):
        content = "Content\n<!-- END MNEMONIC PROTOCOL -->"
        assert parser.has_markers(content) is False


class TestHasValidMarkers:
    """Tests for has_valid_markers method."""

    def test_valid_markers(self, parser):
        content = """<!-- BEGIN MNEMONIC PROTOCOL -->
        Content
        <!-- END MNEMONIC PROTOCOL -->"""
        valid, error = parser.has_valid_markers(content)
        assert valid is True
        assert error is None

    def test_no_markers_is_valid(self, parser):
        content = "# Just content"
        valid, error = parser.has_valid_markers(content)
        assert valid is True
        assert error is None

    def test_mismatched_begin_count(self, parser):
        content = """<!-- BEGIN MNEMONIC PROTOCOL -->
        <!-- BEGIN MNEMONIC PROTOCOL -->
        Content
        <!-- END MNEMONIC PROTOCOL -->"""
        valid, error = parser.has_valid_markers(content)
        assert valid is False
        assert "Mismatched" in error or "Multiple" in error

    def test_wrong_order(self, parser):
        content = """<!-- END MNEMONIC PROTOCOL -->
        Content
        <!-- BEGIN MNEMONIC PROTOCOL -->"""
        valid, error = parser.has_valid_markers(content)
        assert valid is False
        assert "before" in error.lower()


class TestExtractBetween:
    """Tests for extract_between method."""

    def test_extract_content(self, parser):
        content = """<!-- BEGIN MNEMONIC PROTOCOL -->
Inner content here
<!-- END MNEMONIC PROTOCOL -->"""
        extracted = parser.extract_between(content)
        assert extracted is not None
        assert "Inner content" in extracted

    def test_extract_no_markers(self, parser):
        content = "No markers here"
        assert parser.extract_between(content) is None

    def test_extract_with_surrounding(self, parser):
        content = """# Header

<!-- BEGIN MNEMONIC PROTOCOL -->
Protocol content
<!-- END MNEMONIC PROTOCOL -->

# Footer"""
        extracted = parser.extract_between(content)
        assert extracted is not None
        assert "Protocol content" in extracted


class TestReplaceBetween:
    """Tests for replace_between method."""

    def test_replace_content(self, parser):
        content = """<!-- BEGIN MNEMONIC PROTOCOL -->
Old content
<!-- END MNEMONIC PROTOCOL -->"""
        new = parser.replace_between(content, "\nNew content\n")
        assert "New content" in new
        assert "Old content" not in new
        assert parser.has_markers(new)

    def test_replace_no_markers_raises(self, parser):
        content = "No markers"
        with pytest.raises(ValueError):
            parser.replace_between(content, "New content")


class TestRemoveMarkers:
    """Tests for remove_markers method."""

    def test_remove_markers(self, parser):
        content = """# Header

<!-- BEGIN MNEMONIC PROTOCOL -->
Protocol content
<!-- END MNEMONIC PROTOCOL -->

# Footer"""
        result = parser.remove_markers(content)
        assert "BEGIN MNEMONIC" not in result
        assert "END MNEMONIC" not in result
        assert "Protocol content" not in result
        assert "# Header" in result
        assert "# Footer" in result

    def test_remove_no_markers(self, parser):
        content = "# Just content"
        result = parser.remove_markers(content)
        assert result == content


class TestInsertAfterFrontmatter:
    """Tests for insert_after_frontmatter method."""

    def test_insert_after_frontmatter(self, parser):
        content = """---
title: Test
---

# Content"""
        protocol = "<!-- BEGIN MNEMONIC PROTOCOL -->\nProtocol\n<!-- END MNEMONIC PROTOCOL -->"
        result = parser.insert_after_frontmatter(content, protocol)
        assert "---" in result
        assert "# Content" in result
        # Protocol should be between frontmatter and content
        fm_end = result.find("---\n", 4)
        protocol_pos = result.find("BEGIN MNEMONIC")
        content_pos = result.find("# Content")
        assert fm_end < protocol_pos < content_pos

    def test_insert_no_frontmatter(self, parser):
        content = "# Content\n\nParagraph"
        protocol = "<!-- BEGIN MNEMONIC PROTOCOL -->\nProtocol\n<!-- END MNEMONIC PROTOCOL -->"
        result = parser.insert_after_frontmatter(content, protocol)
        assert result.startswith("<!-- BEGIN")
        assert "# Content" in result


class TestLegacyPatterns:
    """Tests for legacy pattern detection and migration."""

    def test_has_legacy_pattern_true(self, parser):
        content = """# Command

## Memory Operations

rg -i "search" ~/.claude/mnemonic/

## Procedure"""
        assert parser.has_legacy_pattern(content) is True

    def test_has_legacy_pattern_false(self, parser):
        content = """# Command

## Procedure

Do stuff"""
        assert parser.has_legacy_pattern(content) is False

    def test_has_legacy_false_if_markers_exist(self, parser):
        content = """<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

rg -i search
<!-- END MNEMONIC PROTOCOL -->"""
        # Should return False because markers exist
        assert parser.has_legacy_pattern(content) is False

    def test_extract_legacy_section(self, parser):
        content = """# Command

## Memory Operations

Some content here
More content

## Procedure

Do stuff"""
        result = parser.extract_legacy_section(content)
        assert result is not None
        start, end, section = result
        assert "Memory Operations" in section
        assert "Some content" in section

    def test_migrate_legacy(self, parser):
        content = """# Command

## Memory Operations

Old memory content

## Procedure

Do stuff"""
        protocol = "<!-- BEGIN MNEMONIC PROTOCOL -->\n## Memory\n\nNew content\n<!-- END MNEMONIC PROTOCOL -->"
        result = parser.migrate_legacy(content, protocol)
        assert "BEGIN MNEMONIC" in result
        assert "END MNEMONIC" in result
        assert "## Procedure" in result
        assert "Memory Operations" not in result or "BEGIN" in result


class TestWrapWithMarkers:
    """Tests for wrap_with_markers method."""

    def test_wrap_content(self, parser):
        content = "## Memory\n\nSearch first"
        result = parser.wrap_with_markers(content)
        assert result.startswith("<!-- BEGIN MNEMONIC PROTOCOL -->")
        assert result.endswith("<!-- END MNEMONIC PROTOCOL -->")
        assert "## Memory" in result


class TestWithFixtures:
    """Tests using fixture files."""

    def test_sample_no_markers(self, parser, fixtures_dir):
        content = (fixtures_dir / "sample_no_markers.md").read_text()
        assert parser.has_markers(content) is False
        assert parser.has_legacy_pattern(content) is False

    def test_sample_with_markers(self, parser, fixtures_dir):
        content = (fixtures_dir / "sample_with_markers.md").read_text()
        assert parser.has_markers(content) is True
        valid, _ = parser.has_valid_markers(content)
        assert valid is True

    def test_sample_legacy(self, parser, fixtures_dir):
        content = (fixtures_dir / "sample_legacy.md").read_text()
        assert parser.has_markers(content) is False
        assert parser.has_legacy_pattern(content) is True

    def test_sample_malformed(self, parser, fixtures_dir):
        content = (fixtures_dir / "sample_malformed.md").read_text()
        assert parser.has_markers(content) is True
        valid, error = parser.has_valid_markers(content)
        assert valid is False
        assert error is not None
