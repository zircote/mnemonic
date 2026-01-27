#!/usr/bin/env python3
"""
Marker Parser for Mnemonic Integration

Handles sentinel marker operations for inserting, updating, and removing
mnemonic protocol content in plugin files.
"""

import re
from typing import Optional, Tuple


class MarkerParser:
    """Parser for mnemonic protocol sentinel markers."""

    # Current protocol version
    PROTOCOL_VERSION = "1.0"

    # Markers with optional version
    BEGIN_MARKER = "<!-- BEGIN MNEMONIC PROTOCOL -->"
    END_MARKER = "<!-- END MNEMONIC PROTOCOL -->"

    # Versioned markers for future use
    BEGIN_MARKER_VERSIONED = f"<!-- BEGIN MNEMONIC PROTOCOL v{PROTOCOL_VERSION} -->"
    END_MARKER_VERSIONED = f"<!-- END MNEMONIC PROTOCOL v{PROTOCOL_VERSION} -->"

    # Regex patterns - match both versioned and non-versioned markers
    MARKER_PATTERN = re.compile(
        r"(<!-- BEGIN MNEMONIC PROTOCOL(?: v[\d.]+)? -->)(.*?)(<!-- END MNEMONIC PROTOCOL(?: v[\d.]+)? -->)",
        re.DOTALL,
    )
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

    # Legacy patterns for migration
    LEGACY_MEMORY_PATTERN = re.compile(
        r"^## Memory(?:\s+Operations)?\s*\n"
        r"(?:.*?(?=^## |\Z))",
        re.MULTILINE | re.DOTALL,
    )

    # Regex for finding markers (versioned or not)
    BEGIN_MARKER_RE = re.compile(r"<!-- BEGIN MNEMONIC PROTOCOL(?: v[\d.]+)? -->")
    END_MARKER_RE = re.compile(r"<!-- END MNEMONIC PROTOCOL(?: v[\d.]+)? -->")

    def has_markers(self, content: str) -> bool:
        """Check if content contains sentinel markers.

        Args:
            content: File content to check

        Returns:
            True if both BEGIN and END markers are present
        """
        return bool(
            self.BEGIN_MARKER_RE.search(content) and
            self.END_MARKER_RE.search(content)
        )

    def has_valid_markers(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check if markers are valid (properly paired).

        Args:
            content: File content to check

        Returns:
            Tuple of (is_valid, error_message)
        """
        begin_matches = self.BEGIN_MARKER_RE.findall(content)
        end_matches = self.END_MARKER_RE.findall(content)

        begin_count = len(begin_matches)
        end_count = len(end_matches)

        if begin_count == 0 and end_count == 0:
            return True, None  # No markers is valid

        if begin_count != end_count:
            return False, f"Mismatched markers: {begin_count} BEGIN, {end_count} END"

        if begin_count > 1:
            return False, f"Multiple marker pairs found: {begin_count}"

        # Check order
        begin_match = self.BEGIN_MARKER_RE.search(content)
        end_match = self.END_MARKER_RE.search(content)

        if begin_match and end_match and begin_match.start() > end_match.start():
            return False, "END marker appears before BEGIN marker"

        return True, None

    def extract_between(self, content: str) -> Optional[str]:
        """Extract content between markers.

        Args:
            content: File content

        Returns:
            Content between markers, or None if markers not found
        """
        match = self.MARKER_PATTERN.search(content)
        if match:
            return match.group(2)
        return None

    def replace_between(self, content: str, new_content: str) -> str:
        """Replace content between markers with new content.

        Args:
            content: Original file content
            new_content: New content to insert between markers

        Returns:
            Updated content with replacement

        Raises:
            ValueError: If markers not found
        """
        if not self.has_markers(content):
            raise ValueError("Content does not contain sentinel markers")

        return self.MARKER_PATTERN.sub(
            f"{self.BEGIN_MARKER}{new_content}{self.END_MARKER}",
            content,
        )

    def remove_markers(self, content: str) -> str:
        """Remove markers and content between them.

        Args:
            content: File content

        Returns:
            Content with markers and their content removed
        """
        # Remove the entire marker block including surrounding newlines
        result = self.MARKER_PATTERN.sub("", content)
        # Clean up extra blank lines
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result

    def insert_after_frontmatter(self, content: str, protocol: str) -> str:
        """Insert protocol content after YAML frontmatter.

        Args:
            content: File content with frontmatter
            protocol: Protocol content to insert (should include markers)

        Returns:
            Content with protocol inserted after frontmatter
        """
        match = self.FRONTMATTER_PATTERN.match(content)

        if match:
            frontmatter = match.group(0)
            rest = content[match.end():]
            # Insert with blank line before and after
            return f"{frontmatter}\n{protocol}\n{rest.lstrip()}"
        else:
            # No frontmatter, insert at beginning
            return f"{protocol}\n\n{content}"

    def has_legacy_pattern(self, content: str) -> bool:
        """Check if content has legacy (marker-less) memory section.

        Args:
            content: File content

        Returns:
            True if legacy pattern detected
        """
        # Already has markers - not legacy
        if self.has_markers(content):
            return False

        # Check for legacy section headers (these are definitive)
        if "## Memory Operations" in content or re.search(r"^## Memory\s*$", content, re.MULTILINE):
            return True

        # Check for mnemonic usage patterns OUTSIDE of code blocks
        # Remove code blocks first to avoid false positives
        content_no_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        content_no_code = re.sub(r"`[^`]+`", "", content_no_code)

        # These patterns indicate actual usage, not just documentation
        legacy_usage_patterns = [
            r"rg\s+-[il].*mnemonic",  # rg command searching mnemonic
            r"/mnemonic:capture\s+\w",  # capture command with namespace
            r"~/.claude/mnemonic/\w",  # path with actual content after
        ]

        return any(re.search(pattern, content_no_code) for pattern in legacy_usage_patterns)

    def extract_legacy_section(self, content: str) -> Optional[Tuple[int, int, str]]:
        """Extract legacy memory section for migration.

        Args:
            content: File content

        Returns:
            Tuple of (start_pos, end_pos, section_content) or None
        """
        # Find ## Memory or ## Memory Operations
        patterns = [
            r"^## Memory Operations\s*\n(?:.*?)(?=^## |\Z)",
            r"^## Memory\s*\n(?:.*?)(?=^## |\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                return match.start(), match.end(), match.group(0)

        return None

    def migrate_legacy(self, content: str, protocol: str) -> str:
        """Migrate legacy memory section to marker-wrapped protocol.

        Args:
            content: File content with legacy pattern
            protocol: New protocol content (should include markers)

        Returns:
            Content with legacy section replaced by protocol
        """
        legacy = self.extract_legacy_section(content)

        if legacy:
            start, end, _ = legacy
            return content[:start] + protocol + "\n" + content[end:].lstrip()

        # No legacy section found, just insert after frontmatter
        return self.insert_after_frontmatter(content, protocol)

    def wrap_with_markers(self, content: str) -> str:
        """Wrap content with sentinel markers.

        Args:
            content: Content to wrap

        Returns:
            Content wrapped with BEGIN and END markers
        """
        return f"{self.BEGIN_MARKER}\n{content}\n{self.END_MARKER}"


def main():
    """CLI for testing marker operations."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Mnemonic Marker Parser")
    parser.add_argument("file", help="File to process")
    parser.add_argument("--check", action="store_true", help="Check for markers")
    parser.add_argument("--extract", action="store_true", help="Extract content between markers")
    parser.add_argument("--remove", action="store_true", help="Remove markers and content")
    parser.add_argument("--has-legacy", action="store_true", help="Check for legacy patterns")

    args = parser.parse_args()

    try:
        with open(args.file) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    parser_obj = MarkerParser()

    if args.check:
        has = parser_obj.has_markers(content)
        valid, error = parser_obj.has_valid_markers(content)
        print(f"Has markers: {has}")
        print(f"Valid: {valid}")
        if error:
            print(f"Error: {error}")
        sys.exit(0 if has and valid else 1)

    elif args.extract:
        extracted = parser_obj.extract_between(content)
        if extracted:
            print(extracted)
        else:
            print("No markers found", file=sys.stderr)
            sys.exit(1)

    elif args.remove:
        result = parser_obj.remove_markers(content)
        print(result)

    elif args.has_legacy:
        has = parser_obj.has_legacy_pattern(content)
        print(f"Has legacy pattern: {has}")
        sys.exit(0 if not has else 1)


if __name__ == "__main__":
    main()
