"""Unit tests for template_validator.py."""

import sys
import tempfile
from pathlib import Path

import pytest

# Add the skills/integrate/lib to path
lib_path = str(Path(__file__).parent.parent / "skills" / "integrate" / "lib")
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from template_validator import TemplateValidator, ValidationResult


@pytest.fixture
def validator():
    """Create a TemplateValidator instance."""
    return TemplateValidator()


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent / "fixtures" / "integrate"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result_is_truthy(self):
        result = ValidationResult(valid=True, errors=[], warnings=[])
        assert result
        assert bool(result) is True

    def test_invalid_result_is_falsy(self):
        result = ValidationResult(valid=False, errors=["Error"], warnings=[])
        assert not result
        assert bool(result) is False


class TestValidateTemplate:
    """Tests for validate_template method."""

    def test_valid_template(self, validator, fixtures_dir):
        template_path = fixtures_dir / "sample_template.md"
        result = validator.validate_template(template_path)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_nonexistent_template(self, validator):
        result = validator.validate_template(Path("/nonexistent/template.md"))
        assert result.valid is False
        assert any("not found" in e.lower() for e in result.errors)

    def test_template_missing_markers(self, validator, fixtures_dir):
        # sample_no_markers.md has no markers
        result = validator.validate_template(fixtures_dir / "sample_no_markers.md")
        assert result.valid is False
        assert any("marker" in e.lower() for e in result.errors)

    def test_template_with_invalid_markers(self, validator, fixtures_dir):
        result = validator.validate_template(fixtures_dir / "sample_malformed.md")
        assert result.valid is False

    def test_template_size_warning_small(self, validator):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("<!-- BEGIN MNEMONIC PROTOCOL -->\nX\n<!-- END MNEMONIC PROTOCOL -->")
            f.flush()
            result = validator.validate_template(Path(f.name))
            # Should be valid but may have size warning
            assert result.valid is True
            Path(f.name).unlink()


class TestVerifyInsertion:
    """Tests for verify_insertion method."""

    def test_verify_matching_content(self, validator):
        template = """<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Content here
<!-- END MNEMONIC PROTOCOL -->"""

        file_content = """---
title: Test
---

# Header

<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Content here
<!-- END MNEMONIC PROTOCOL -->

# Footer"""

        assert validator.verify_insertion(file_content, template) is True

    def test_verify_mismatched_content(self, validator):
        template = """<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Original content
<!-- END MNEMONIC PROTOCOL -->"""

        file_content = """<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Different content
<!-- END MNEMONIC PROTOCOL -->"""

        assert validator.verify_insertion(file_content, template) is False

    def test_verify_no_markers_in_file(self, validator):
        template = """<!-- BEGIN MNEMONIC PROTOCOL -->
Content
<!-- END MNEMONIC PROTOCOL -->"""

        file_content = "# Just content without markers"
        assert validator.verify_insertion(file_content, template) is False


class TestGetTemplateContent:
    """Tests for get_template_content method."""

    def test_get_valid_template(self, validator, fixtures_dir):
        content = validator.get_template_content(fixtures_dir / "sample_template.md")
        assert content is not None
        assert "BEGIN MNEMONIC" in content

    def test_get_invalid_template_returns_none(self, validator):
        content = validator.get_template_content(Path("/nonexistent.md"))
        assert content is None


class TestRemoveCodeBlocks:
    """Tests for _remove_code_blocks method."""

    def test_remove_fenced_blocks(self, validator):
        content = """Text before

```python
subprocess.run(['ls'])
```

Text after"""
        result = validator._remove_code_blocks(content)
        assert "subprocess" not in result
        assert "Text before" in result
        assert "Text after" in result

    def test_remove_inline_code(self, validator):
        content = "Use `subprocess.run()` to execute"
        result = validator._remove_code_blocks(content)
        assert "subprocess" not in result
        assert "Use" in result


class TestExecutablePatternDetection:
    """Tests for detecting suspicious executable patterns."""

    def test_detect_shell_substitution(self, validator):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("<!-- BEGIN MNEMONIC PROTOCOL -->\n")
            f.write("Run $(dangerous_command) here\n")
            f.write("<!-- END MNEMONIC PROTOCOL -->")
            f.flush()
            result = validator.validate_template(Path(f.name))
            # Should generate warning about executable pattern
            assert any("Shell command" in w for w in result.warnings)
            Path(f.name).unlink()

    def test_code_block_patterns_not_flagged(self, validator):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("<!-- BEGIN MNEMONIC PROTOCOL -->\n")
            f.write("## Memory\n\n")
            f.write("```bash\n$(command)\n```\n")  # In code block
            f.write("<!-- END MNEMONIC PROTOCOL -->")
            f.flush()
            result = validator.validate_template(Path(f.name))
            # Should NOT flag patterns inside code blocks
            assert not any("Shell command" in w for w in result.warnings)
            Path(f.name).unlink()


class TestWithFixtures:
    """Tests using fixture files."""

    def test_sample_template_valid(self, validator, fixtures_dir):
        result = validator.validate_template(fixtures_dir / "sample_template.md")
        assert result.valid is True

    def test_mock_plugin_template(self, validator, fixtures_dir):
        template_path = fixtures_dir / "mock_plugin" / "templates" / "mnemonic-protocol.md"
        result = validator.validate_template(template_path)
        assert result.valid is True
