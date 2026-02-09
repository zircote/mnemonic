#!/usr/bin/env python3
"""
Unit tests for lib/relationships.py — relationship writing and bidirectional linking.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.relationships import (
    add_relationship,
    add_bidirectional_relationship,
    RECIPROCAL_TYPES,
)
from lib.search import REL_RELATES_TO, REL_SUPERSEDES, REL_DERIVED_FROM


class TestAddRelationship:
    """Test add_relationship() function."""

    def test_add_to_file_without_relationships(self, tmp_path):
        """Add relationship to a file that has no relationships section."""
        mem = tmp_path / "test.memory.md"
        mem.write_text('---\nid: aaa-111\ntitle: "Test"\nnamespace: _semantic/decisions\n---\n\n# Test\n\nBody text.\n')

        result = add_relationship(str(mem), REL_RELATES_TO, "bbb-222", label="Related memory")

        assert result is True
        content = mem.read_text()
        assert "relationships:" in content
        assert "  - type: relates_to" in content
        assert "    target: bbb-222" in content
        assert '    label: "Related memory"' in content

    def test_add_to_file_with_existing_relationships(self, tmp_path):
        """Append to existing relationships section."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            "---\nid: aaa-111\ntitle: Test\nrelationships:\n  - type: relates_to\n    target: ccc-333\n---\n\nBody.\n"
        )

        result = add_relationship(str(mem), REL_SUPERSEDES, "ddd-444")

        assert result is True
        content = mem.read_text()
        assert "target: ccc-333" in content
        assert "  - type: supersedes" in content
        assert "    target: ddd-444" in content

    def test_add_to_empty_list_form(self, tmp_path):
        """Replace `relationships: []` with block form."""
        mem = tmp_path / "test.memory.md"
        mem.write_text('---\nid: aaa-111\ntitle: "Test"\nrelationships: []\n---\n\nBody.\n')

        result = add_relationship(str(mem), REL_DERIVED_FROM, "eee-555")

        assert result is True
        content = mem.read_text()
        assert "relationships: []" not in content
        assert "  - type: derived_from" in content
        assert "    target: eee-555" in content

    def test_skip_duplicate(self, tmp_path):
        """Don't add if same type+target already exists."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            "---\nid: aaa-111\ntitle: Test\nrelationships:\n  - type: relates_to\n    target: bbb-222\n---\n\nBody.\n"
        )

        result = add_relationship(str(mem), REL_RELATES_TO, "bbb-222")

        assert result is False

    def test_allow_same_target_different_type(self, tmp_path):
        """Allow same target with a different relationship type."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            "---\nid: aaa-111\ntitle: Test\nrelationships:\n  - type: relates_to\n    target: bbb-222\n---\n\nBody.\n"
        )

        result = add_relationship(str(mem), REL_SUPERSEDES, "bbb-222")

        assert result is True
        content = mem.read_text()
        assert "type: relates_to" in content
        assert "type: supersedes" in content

    def test_nonexistent_file(self):
        """Return False for nonexistent file."""
        result = add_relationship("/nonexistent/path.memory.md", REL_RELATES_TO, "aaa-111")
        assert result is False

    def test_no_frontmatter(self, tmp_path):
        """Return False for file without frontmatter delimiters."""
        mem = tmp_path / "test.memory.md"
        mem.write_text("No frontmatter here.\n")

        result = add_relationship(str(mem), REL_RELATES_TO, "aaa-111")
        assert result is False

    def test_without_label(self, tmp_path):
        """Add relationship without label."""
        mem = tmp_path / "test.memory.md"
        mem.write_text('---\nid: aaa-111\ntitle: "Test"\n---\n\nBody.\n')

        result = add_relationship(str(mem), REL_RELATES_TO, "bbb-222")

        assert result is True
        content = mem.read_text()
        assert "label:" not in content
        assert "    target: bbb-222" in content

    def test_preserves_body_content(self, tmp_path):
        """Body content after frontmatter is preserved."""
        body = "\n# Title\n\nParagraph one.\n\n## Section\n\nMore text.\n"
        mem = tmp_path / "test.memory.md"
        mem.write_text(f'---\nid: aaa-111\ntitle: "Test"\n---{body}')

        add_relationship(str(mem), REL_RELATES_TO, "bbb-222")

        content = mem.read_text()
        assert body in content

    def test_preserves_existing_frontmatter_fields(self, tmp_path):
        """All existing frontmatter fields are preserved."""
        mem = tmp_path / "test.memory.md"
        mem.write_text(
            '---\nid: aaa-111\ntype: semantic\nnamespace: _semantic/decisions\ntitle: "Test"\n'
            "created: 2026-01-01T00:00:00Z\ntags:\n  - auth\n  - jwt\n---\n\nBody.\n"
        )

        add_relationship(str(mem), REL_RELATES_TO, "bbb-222")

        content = mem.read_text()
        assert "id: aaa-111" in content
        assert "type: semantic" in content
        assert "namespace: _semantic/decisions" in content
        assert "created: 2026-01-01T00:00:00Z" in content
        assert "  - auth" in content
        assert "  - jwt" in content


class TestAddBidirectionalRelationship:
    """Test add_bidirectional_relationship() function."""

    def test_bidirectional_relates_to(self, tmp_path):
        """relates_to creates symmetric links."""
        source = tmp_path / "source.memory.md"
        target = tmp_path / "target.memory.md"
        source.write_text('---\nid: aaa-111\ntitle: "Source"\n---\n\nBody.\n')
        target.write_text('---\nid: bbb-222\ntitle: "Target"\n---\n\nBody.\n')

        fwd, rev = add_bidirectional_relationship(str(source), str(target), REL_RELATES_TO, label="Related")

        assert fwd is True
        assert rev is True

        source_content = source.read_text()
        target_content = target.read_text()

        assert "target: bbb-222" in source_content
        assert "type: relates_to" in source_content
        assert "target: aaa-111" in target_content
        assert "type: relates_to" in target_content

    def test_bidirectional_supersedes(self, tmp_path):
        """supersedes creates relates_to back-link."""
        source = tmp_path / "source.memory.md"
        target = tmp_path / "target.memory.md"
        source.write_text('---\nid: aaa-111\ntitle: "Source"\n---\n\nBody.\n')
        target.write_text('---\nid: bbb-222\ntitle: "Target"\n---\n\nBody.\n')

        fwd, rev = add_bidirectional_relationship(str(source), str(target), REL_SUPERSEDES, label="Newer version")

        assert fwd is True
        assert rev is True

        source_content = source.read_text()
        target_content = target.read_text()

        # Forward: supersedes
        assert "type: supersedes" in source_content
        assert "target: bbb-222" in source_content

        # Reverse: relates_to (reciprocal)
        assert "type: relates_to" in target_content
        assert "target: aaa-111" in target_content
        assert "Back-link:" in target_content

    def test_bidirectional_derived_from(self, tmp_path):
        """derived_from creates relates_to back-link."""
        source = tmp_path / "source.memory.md"
        target = tmp_path / "target.memory.md"
        source.write_text('---\nid: aaa-111\ntitle: "Source"\n---\n\nBody.\n')
        target.write_text('---\nid: bbb-222\ntitle: "Target"\n---\n\nBody.\n')

        fwd, rev = add_bidirectional_relationship(str(source), str(target), REL_DERIVED_FROM)

        assert fwd is True
        assert rev is True

        source_content = source.read_text()
        target_content = target.read_text()

        assert "type: derived_from" in source_content
        assert "type: relates_to" in target_content

    def test_nonexistent_source(self, tmp_path):
        """Return (False, False) when source doesn't exist."""
        target = tmp_path / "target.memory.md"
        target.write_text('---\nid: bbb-222\ntitle: "Target"\n---\n\nBody.\n')

        fwd, rev = add_bidirectional_relationship("/nonexistent.memory.md", str(target), REL_RELATES_TO)

        assert fwd is False
        assert rev is False

    def test_missing_id(self, tmp_path):
        """Return (False, False) when a file has no id."""
        source = tmp_path / "source.memory.md"
        target = tmp_path / "target.memory.md"
        source.write_text('---\ntitle: "No ID"\n---\n\nBody.\n')
        target.write_text('---\nid: bbb-222\ntitle: "Target"\n---\n\nBody.\n')

        fwd, rev = add_bidirectional_relationship(str(source), str(target), REL_RELATES_TO)

        assert fwd is False
        assert rev is False

    def test_no_reverse_label_without_forward_label(self, tmp_path):
        """No reverse label when forward has no label."""
        source = tmp_path / "source.memory.md"
        target = tmp_path / "target.memory.md"
        source.write_text('---\nid: aaa-111\ntitle: "Source"\n---\n\nBody.\n')
        target.write_text('---\nid: bbb-222\ntitle: "Target"\n---\n\nBody.\n')

        add_bidirectional_relationship(str(source), str(target), REL_RELATES_TO)

        target_content = target.read_text()
        assert "label:" not in target_content


class TestReciprocalTypes:
    """Test RECIPROCAL_TYPES mapping."""

    def test_relates_to_is_symmetric(self):
        assert RECIPROCAL_TYPES[REL_RELATES_TO] == REL_RELATES_TO

    def test_supersedes_reciprocal(self):
        assert RECIPROCAL_TYPES[REL_SUPERSEDES] == REL_RELATES_TO

    def test_derived_from_reciprocal(self):
        assert RECIPROCAL_TYPES[REL_DERIVED_FROM] == REL_RELATES_TO

    def test_all_types_have_reciprocals(self):
        for rel_type in [REL_RELATES_TO, REL_SUPERSEDES, REL_DERIVED_FROM]:
            assert rel_type in RECIPROCAL_TYPES
