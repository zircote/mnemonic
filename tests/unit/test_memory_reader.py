#!/usr/bin/env python3
"""
Unit tests for lib/memory_reader.py memory file reader.

Tests memory file parsing and summary extraction.
"""


from lib.memory_reader import get_memory_summary


class TestGetMemorySummary:
    """Test get_memory_summary() function."""

    def test_get_memory_summary_success(self, tmp_path):
        """Test successful memory file reading."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Authentication Decision
namespace: _semantic/decisions
tags: [auth, jwt, security]
---

We decided to use JWT tokens for authentication because they are stateless
and scale well across distributed systems.
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "Authentication Decision"
        assert "JWT tokens for authentication" in result["summary"]
        assert "stateless" in result["summary"]

    def test_get_memory_summary_no_frontmatter(self, tmp_path):
        """Test memory file without frontmatter."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """This is a memory file without frontmatter.

It should still parse correctly.
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "test.memory"  # Falls back to stem (includes .memory)
        # Note: current implementation only extracts summary after frontmatter
        # Files without frontmatter will have empty summary
        assert result["summary"] == ""

    def test_get_memory_summary_title_with_quotes(self, tmp_path):
        """Test title extraction with quotes."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: "Authentication Decision"
namespace: _semantic/decisions
---

Content here.
"""
        )

        result = get_memory_summary(str(memory_file))
        assert result["title"] == "Authentication Decision"

    def test_get_memory_summary_title_without_quotes(self, tmp_path):
        """Test title extraction without quotes."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Authentication Decision
namespace: _semantic/decisions
---

Content here.
"""
        )

        result = get_memory_summary(str(memory_file))
        assert result["title"] == "Authentication Decision"

    def test_get_memory_summary_max_length(self, tmp_path):
        """Test summary length truncation."""
        memory_file = tmp_path / "test.memory.md"
        long_text = "A" * 500
        memory_file.write_text(
            f"""---
title: Long Memory
---

{long_text}
"""
        )

        result = get_memory_summary(str(memory_file), max_summary=100)

        assert len(result["summary"]) <= 100
        assert result["summary"].endswith("...")

    def test_get_memory_summary_nonexistent_file(self, tmp_path):
        """Test handling of nonexistent file."""
        result = get_memory_summary(str(tmp_path / "nonexistent.memory.md"))

        assert result["title"] == "nonexistent.memory"
        assert result["summary"] == ""

    def test_get_memory_summary_empty_file(self, tmp_path):
        """Test handling of empty file."""
        memory_file = tmp_path / "empty.memory.md"
        memory_file.write_text("")

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "empty.memory"
        assert result["summary"] == ""

    def test_get_memory_summary_only_frontmatter(self, tmp_path):
        """Test file with only frontmatter, no content."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Only Frontmatter
namespace: _semantic/decisions
---
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "Only Frontmatter"
        assert result["summary"] == ""

    def test_get_memory_summary_skips_headings(self, tmp_path):
        """Test that headings are skipped for summary."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Test Memory
---

# Main Heading

## Sub Heading

This is the actual content that should be used as summary.
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["summary"] == "This is the actual content that should be used as summary."
        assert "Main Heading" not in result["summary"]

    def test_get_memory_summary_incomplete_frontmatter(self, tmp_path):
        """Test file with incomplete frontmatter."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Incomplete

This should be treated as content.
"""
        )

        result = get_memory_summary(str(memory_file))

        # Should handle gracefully
        assert result["title"] in ["Incomplete", "test"]
        assert isinstance(result["summary"], str)

    def test_get_memory_summary_malformed_yaml(self, tmp_path):
        """Test file with malformed YAML frontmatter."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: [[[invalid yaml
namespace: test
---

Content here.
"""
        )

        result = get_memory_summary(str(memory_file))

        # Should extract title even if malformed
        assert "[[[invalid yaml" in result["title"] or result["title"] == "test.memory"
        assert "Content here" in result["summary"] or result["summary"] == ""

    def test_get_memory_summary_unicode_content(self, tmp_path):
        """Test file with unicode content."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Unicode Test
---

Testing with unicode: 你好世界 🎉 Ñoño
""",
            encoding="utf-8",
        )

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "Unicode Test"
        assert "你好世界" in result["summary"] or "unicode" in result["summary"]

    def test_get_memory_summary_binary_content_handling(self, tmp_path):
        """Test handling of files with binary content."""
        memory_file = tmp_path / "test.memory.md"
        # Write binary content
        memory_file.write_bytes(b"\x00\x01\x02\xff" + b"---\ntitle: Test\n---\nContent")

        # Should not crash, uses error='replace' for decoding
        result = get_memory_summary(str(memory_file))

        assert isinstance(result, dict)
        assert "title" in result
        assert "summary" in result

    def test_get_memory_summary_multiple_frontmatter_blocks(self, tmp_path):
        """Test file with multiple --- blocks."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: First Block
---

Summary content here.

---
This is not frontmatter.
---
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "First Block"
        assert "Summary content here" in result["summary"]

    def test_get_memory_summary_whitespace_handling(self, tmp_path):
        """Test handling of whitespace in title and summary."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title:   Whitespace   Title
---

    Summary with leading spaces.
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "Whitespace   Title"  # Strips outer whitespace
        assert result["summary"] == "Summary with leading spaces."

    def test_get_memory_summary_first_paragraph_priority(self, tmp_path):
        """Test that first non-heading paragraph is used."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Test
---

First paragraph here.

Second paragraph here.

Third paragraph here.
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["summary"] == "First paragraph here."
        assert "Second" not in result["summary"]

    def test_get_memory_summary_custom_max_summary(self, tmp_path):
        """Test custom max_summary parameter."""
        memory_file = tmp_path / "test.memory.md"
        memory_file.write_text(
            """---
title: Test
---

This is a very long summary that should be truncated at the specified length.
"""
        )

        result = get_memory_summary(str(memory_file), max_summary=30)

        assert len(result["summary"]) <= 30
        assert result["summary"].endswith("...")

    def test_get_memory_summary_exception_handling(self, tmp_path):
        """Test general exception handling."""
        # Test with a path that will cause an exception during read
        # Use a directory path instead of file path
        dir_path = tmp_path / "directory"
        dir_path.mkdir()

        result = get_memory_summary(str(dir_path))

        assert isinstance(result, dict)
        assert "title" in result
        assert "summary" in result

    def test_get_memory_summary_real_world_example(self, tmp_path):
        """Test with real-world memory file structure."""
        memory_file = tmp_path / "jwt-auth-decision.memory.md"
        memory_file.write_text(
            """---
title: JWT Authentication Implementation
namespace: _semantic/decisions
tags: [authentication, jwt, security, api]
created_at: 2024-01-15T10:30:00Z
---

We decided to implement JWT-based authentication for the REST API instead of
session-based authentication. This decision was driven by the need for stateless
authentication that can scale horizontally across multiple API servers.

## Key Factors

- Stateless authentication enables better horizontal scaling
- JWT tokens can be validated without database lookups
- Tokens can carry user claims and permissions

## Trade-offs

- Token revocation requires additional infrastructure (blacklist/short TTL)
- Larger payload size compared to session IDs
"""
        )

        result = get_memory_summary(str(memory_file))

        assert result["title"] == "JWT Authentication Implementation"
        assert "JWT-based authentication" in result["summary"]
        # Summary is truncated at max_summary=300 (default), so may not include "stateless"
        # Should stop at first paragraph, not include headings
        assert "Key Factors" not in result["summary"]
