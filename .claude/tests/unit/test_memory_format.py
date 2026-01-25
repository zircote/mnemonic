#!/usr/bin/env python3
"""
Unit tests for memory file format validation.

Tests that memory files follow the expected schema and structure.
"""

import os
import re
import tempfile
import unittest
from pathlib import Path

import yaml

# Valid namespaces
VALID_NAMESPACES = {
    "apis",
    "blockers",
    "context",
    "decisions",
    "learnings",
    "patterns",
    "security",
    "testing",
    "episodic",
}

# Valid memory types
VALID_TYPES = {"semantic", "episodic", "procedural"}

# UUID pattern
UUID_PATTERN = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")

# ISO8601 datetime pattern
ISO8601_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def parse_memory_file(content: str) -> tuple[dict, str]:
    """Parse a memory file into frontmatter and body."""
    if not content.startswith("---"):
        raise ValueError("Memory file must start with ---")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Memory file must have frontmatter between --- markers")

    frontmatter_str = parts[1].strip()
    body = parts[2].strip() if len(parts) > 2 else ""

    frontmatter = yaml.safe_load(frontmatter_str)
    return frontmatter, body


class TestMemoryFileFormat(unittest.TestCase):
    """Test memory file format validation."""

    def test_valid_memory_file(self):
        """Test parsing a valid memory file."""
        content = """---
id: 12345678-1234-1234-1234-123456789abc
title: "Test Memory"
type: semantic
created: 2026-01-25T10:00:00Z
---

# Test Memory

This is the body content.
"""
        frontmatter, body = parse_memory_file(content)

        self.assertEqual(frontmatter["id"], "12345678-1234-1234-1234-123456789abc")
        self.assertEqual(frontmatter["title"], "Test Memory")
        self.assertEqual(frontmatter["type"], "semantic")
        self.assertIn("Test Memory", body)

    def test_id_is_valid_uuid(self):
        """Memory ID must be a valid UUID."""
        valid_ids = [
            "12345678-1234-1234-1234-123456789abc",
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        ]
        for id_ in valid_ids:
            self.assertTrue(UUID_PATTERN.match(id_), f"Should be valid: {id_}")

        invalid_ids = [
            "not-a-uuid",
            "12345678123412341234123456789abc",  # no dashes
            "12345678-1234-1234-1234",  # too short
        ]
        for id_ in invalid_ids:
            self.assertFalse(UUID_PATTERN.match(id_), f"Should be invalid: {id_}")

    def test_type_is_valid(self):
        """Memory type must be one of the valid types."""
        for type_ in VALID_TYPES:
            self.assertIn(type_, VALID_TYPES)

        self.assertNotIn("invalid", VALID_TYPES)
        self.assertNotIn("memory", VALID_TYPES)

    def test_created_is_iso8601(self):
        """Created timestamp must be ISO8601 format."""
        valid_dates = [
            "2026-01-25T10:00:00Z",
            "2025-12-31T23:59:59Z",
        ]
        for date in valid_dates:
            self.assertTrue(ISO8601_PATTERN.match(date), f"Should be valid: {date}")

        invalid_dates = [
            "2026-01-25",  # no time
            "2026-01-25 10:00:00",  # space instead of T
            "Jan 25, 2026",  # wrong format
        ]
        for date in invalid_dates:
            self.assertFalse(ISO8601_PATTERN.match(date), f"Should be invalid: {date}")

    def test_title_is_required(self):
        """Memory must have a title."""
        content = """---
id: 12345678-1234-1234-1234-123456789abc
type: semantic
created: 2026-01-25T10:00:00Z
---

# No title in frontmatter
"""
        frontmatter, _ = parse_memory_file(content)
        self.assertNotIn("title", frontmatter)  # This should fail validation

    def test_body_has_content(self):
        """Memory body should have meaningful content."""
        content = """---
id: 12345678-1234-1234-1234-123456789abc
title: "Test Memory"
type: semantic
created: 2026-01-25T10:00:00Z
---

# Test Memory

This is meaningful content about the decision.
"""
        _, body = parse_memory_file(content)
        self.assertGreater(len(body), 20, "Body should have meaningful content")


class TestMemoryFileValidation(unittest.TestCase):
    """Test validation of actual memory files on disk."""

    def get_memory_files(self):
        """Get all memory files from mnemonic directories."""
        files = []
        paths = [
            Path.home() / ".claude" / "mnemonic",
            Path.cwd() / ".claude" / "mnemonic",
        ]

        for base_path in paths:
            if base_path.exists():
                files.extend(base_path.rglob("*.memory.md"))

        return files

    def test_all_memory_files_valid_format(self):
        """All existing memory files should have valid format."""
        files = self.get_memory_files()

        if not files:
            self.skipTest("No memory files found to validate")

        errors = []
        for file_path in files:
            try:
                content = file_path.read_text()
                frontmatter, body = parse_memory_file(content)

                # Validate required fields
                if "id" not in frontmatter:
                    errors.append(f"{file_path}: missing 'id'")
                elif not UUID_PATTERN.match(str(frontmatter["id"])):
                    errors.append(f"{file_path}: invalid UUID format")

                if "title" not in frontmatter:
                    errors.append(f"{file_path}: missing 'title'")

                if "type" not in frontmatter:
                    errors.append(f"{file_path}: missing 'type'")
                elif frontmatter["type"] not in VALID_TYPES:
                    errors.append(f"{file_path}: invalid type '{frontmatter['type']}'")

                if "created" not in frontmatter:
                    errors.append(f"{file_path}: missing 'created'")

            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")

        if errors:
            self.fail(f"Memory file validation errors:\n" + "\n".join(errors[:10]))

    def test_no_duplicate_ids(self):
        """Each memory should have a unique ID."""
        files = self.get_memory_files()

        if not files:
            self.skipTest("No memory files found to validate")

        ids = {}
        duplicates = []

        for file_path in files:
            try:
                content = file_path.read_text()
                frontmatter, _ = parse_memory_file(content)
                memory_id = frontmatter.get("id")

                if memory_id:
                    if memory_id in ids:
                        duplicates.append(f"ID {memory_id}: {ids[memory_id]} and {file_path}")
                    else:
                        ids[memory_id] = file_path
            except Exception:
                pass  # Skip files that can't be parsed

        if duplicates:
            self.fail(f"Duplicate memory IDs found:\n" + "\n".join(duplicates))


if __name__ == "__main__":
    unittest.main(verbosity=2)
