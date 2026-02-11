"""Unit tests for frontmatter_updater.py."""

import sys
from pathlib import Path

import pytest

# Add the skills/integrate/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "integrate" / "lib"))

from frontmatter_updater import FrontmatterUpdater


@pytest.fixture
def updater():
    """Create a FrontmatterUpdater instance."""
    return FrontmatterUpdater()


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent / "fixtures" / "integrate"


class TestHasFrontmatter:
    """Tests for has_frontmatter method."""

    def test_has_frontmatter_true(self, updater):
        content = """---
title: Test
---

# Content"""
        assert updater.has_frontmatter(content) is True

    def test_has_frontmatter_false(self, updater):
        content = "# No Frontmatter\n\nJust content"
        assert updater.has_frontmatter(content) is False

    def test_frontmatter_not_at_start(self, updater):
        content = """Some content

---
title: Test
---"""
        assert updater.has_frontmatter(content) is False


class TestExtractFrontmatter:
    """Tests for extract_frontmatter method."""

    def test_extract_simple(self, updater):
        content = """---
title: Test
allowed-tools:
  - Bash
---

# Content"""
        result = updater.extract_frontmatter(content)
        assert result is not None
        full, inner, rest = result
        assert "---" in full
        assert "title: Test" in inner
        assert "# Content" in rest

    def test_extract_no_frontmatter(self, updater):
        content = "# No frontmatter"
        assert updater.extract_frontmatter(content) is None


class TestGetAllowedTools:
    """Tests for get_allowed_tools method."""

    def test_get_tools(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Read
  - Write
---

# Content"""
        tools = updater.get_allowed_tools(content)
        assert "Bash" in tools
        assert "Read" in tools
        assert "Write" in tools

    def test_get_tools_no_frontmatter(self, updater):
        content = "# No frontmatter"
        assert updater.get_allowed_tools(content) == []

    def test_get_tools_no_allowed_tools_key(self, updater):
        content = """---
title: Test
---

# Content"""
        assert updater.get_allowed_tools(content) == []


class TestHasTool:
    """Tests for has_tool method."""

    def test_has_tool_true(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Read
---"""
        assert updater.has_tool(content, "Bash") is True
        assert updater.has_tool(content, "Read") is True

    def test_has_tool_false(self, updater):
        content = """---
allowed-tools:
  - Bash
---"""
        assert updater.has_tool(content, "Write") is False


class TestHasAllRequiredTools:
    """Tests for has_all_required_tools method."""

    def test_has_all_tools(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
---"""
        assert updater.has_all_required_tools(content) is True

    def test_missing_some_tools(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Read
---"""
        assert updater.has_all_required_tools(content) is False

    def test_has_extra_tools_ok(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
  - Task
  - WebSearch
---"""
        assert updater.has_all_required_tools(content) is True


class TestGetMissingTools:
    """Tests for get_missing_tools method."""

    def test_get_missing(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Read
---"""
        missing = updater.get_missing_tools(content)
        assert "Glob" in missing
        assert "Grep" in missing
        assert "Write" in missing
        assert "Bash" not in missing
        assert "Read" not in missing

    def test_no_missing(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
---"""
        assert updater.get_missing_tools(content) == []


class TestAddTools:
    """Tests for add_tools method."""

    def test_add_missing_tools(self, updater):
        content = """---
allowed-tools:
  - Bash
---

# Content"""
        result = updater.add_tools(content, ["Read", "Write"])
        tools = updater.get_allowed_tools(result)
        assert "Bash" in tools
        assert "Read" in tools
        assert "Write" in tools

    def test_add_tools_no_duplicates(self, updater):
        content = """---
allowed-tools:
  - Bash
  - Read
---"""
        result = updater.add_tools(content, ["Bash", "Write"])
        tools = updater.get_allowed_tools(result)
        # Should have Bash only once
        assert tools.count("Bash") == 1
        assert "Write" in tools

    def test_add_tools_creates_section(self, updater):
        content = """---
title: Test
---

# Content"""
        result = updater.add_tools(content, ["Bash", "Read"])
        tools = updater.get_allowed_tools(result)
        assert "Bash" in tools
        assert "Read" in tools

    def test_add_tools_no_frontmatter_unchanged(self, updater):
        content = "# No frontmatter"
        result = updater.add_tools(content, ["Bash"])
        # Without frontmatter, nothing changes
        assert result == content

    def test_add_default_tools(self, updater):
        content = """---
allowed-tools:
  - Task
---

# Content"""
        result = updater.add_tools(content)  # No tools specified = defaults
        tools = updater.get_allowed_tools(result)
        assert "Bash" in tools
        assert "Glob" in tools
        assert "Grep" in tools
        assert "Read" in tools
        assert "Write" in tools
        assert "Task" in tools  # Original preserved


class TestWithFixtures:
    """Tests using fixture files."""

    def test_sample_no_markers_tools(self, updater, fixtures_dir):
        content = (fixtures_dir / "sample_no_markers.md").read_text()
        tools = updater.get_allowed_tools(content)
        assert "Bash" in tools
        assert "Read" in tools

    def test_sample_with_markers_all_tools(self, updater, fixtures_dir):
        content = (fixtures_dir / "sample_with_markers.md").read_text()
        assert updater.has_all_required_tools(content) is True

    def test_sample_legacy_missing_tools(self, updater, fixtures_dir):
        content = (fixtures_dir / "sample_legacy.md").read_text()
        missing = updater.get_missing_tools(content)
        assert len(missing) > 0  # Has some missing

    def test_sample_no_frontmatter(self, updater, fixtures_dir):
        content = (fixtures_dir / "sample_no_frontmatter.md").read_text()
        assert updater.has_frontmatter(content) is False
        assert updater.get_allowed_tools(content) == []


class TestRegexFallback:
    """Tests for regex-based tool addition (when YAML libraries unavailable)."""

    def test_regex_add_to_existing(self, updater):
        # Test the regex fallback directly
        content = """---
allowed-tools:
  - Bash
  - Read
---

# Content"""
        result = updater._add_tools_regex(content, ["Write", "Glob"])
        assert "Write" in result
        assert "Glob" in result
        assert "Bash" in result

    def test_regex_create_section(self, updater):
        content = """---
title: Test
---

# Content"""
        result = updater._add_tools_regex(content, ["Bash"])
        assert "allowed-tools:" in result
        assert "Bash" in result
