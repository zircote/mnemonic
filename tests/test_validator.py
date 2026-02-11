"""Tests for mnemonic-validate tool."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Add tools directory to path
TOOLS_DIR = Path(__file__).parent.parent / "tools"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "memories"


def run_validator(*args, capture_output=True):
    """Run mnemonic-validate with given arguments."""
    cmd = [sys.executable, str(TOOLS_DIR / "mnemonic-validate"), *args]
    result = subprocess.run(cmd, capture_output=capture_output, text=True)
    return result


class TestValidatorBasics:
    """Basic validator functionality tests."""

    def test_help(self):
        """Test --help flag."""
        result = run_validator("--help")
        assert result.returncode == 0
        assert "Validate mnemonic memory files" in result.stdout

    def test_no_files_found(self):
        """Test with non-existent path."""
        result = run_validator("/nonexistent/path")
        assert "No memory files found" in result.stdout or result.returncode == 0


class TestSchemaValidation:
    """Schema validation tests."""

    def test_valid_semantic_memory(self):
        """Test validation of valid semantic memory."""
        result = run_validator(str(FIXTURES_DIR / "valid-semantic.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["errors"] == 0
        assert result.returncode == 0

    def test_valid_episodic_memory(self):
        """Test validation of valid episodic memory."""
        result = run_validator(str(FIXTURES_DIR / "valid-episodic.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["errors"] == 0
        assert result.returncode == 0

    def test_valid_memory_with_citations(self):
        """Test validation of memory with citations."""
        result = run_validator(str(FIXTURES_DIR / "valid-with-citations.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["errors"] == 0
        assert result.returncode == 0

    def test_missing_required_fields(self):
        """Test detection of missing required fields."""
        result = run_validator(str(FIXTURES_DIR / "invalid-missing-required.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["errors"] > 0
        assert result.returncode == 1

        # Check specific errors
        errors = output["results"][0]["errors"]
        error_fields = [e["field"] for e in errors]
        assert "type" in error_fields or "created" in error_fields

    def test_invalid_uuid_format(self):
        """Test detection of invalid UUID format."""
        result = run_validator(str(FIXTURES_DIR / "invalid-bad-uuid.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["errors"] > 0
        assert result.returncode == 1

        # Check for UUID error
        errors = output["results"][0]["errors"]
        uuid_errors = [e for e in errors if e["field"] == "id"]
        assert len(uuid_errors) > 0
        assert "UUID" in uuid_errors[0]["message"]

    def test_invalid_type_value(self):
        """Test detection of invalid type enum value."""
        result = run_validator(str(FIXTURES_DIR / "invalid-bad-type.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["errors"] > 0
        assert result.returncode == 1

        # Check for type error
        errors = output["results"][0]["errors"]
        type_errors = [e for e in errors if e["field"] == "type"]
        assert len(type_errors) > 0


class TestWarnings:
    """Warning detection tests."""

    def test_bad_tag_format_warning(self):
        """Test detection of improperly formatted tags."""
        result = run_validator(str(FIXTURES_DIR / "warning-bad-tags.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["warnings"] > 0
        # Should still pass (warnings don't fail)
        assert result.returncode == 0


class TestOutputFormats:
    """Output format tests."""

    def test_markdown_output(self):
        """Test markdown output format."""
        result = run_validator(str(FIXTURES_DIR / "valid-semantic.memory.md"), "--format", "markdown")
        assert "# Mnemonic Validation Report" in result.stdout
        assert "## Summary" in result.stdout
        assert result.returncode == 0

    def test_json_output(self):
        """Test JSON output format."""
        result = run_validator(str(FIXTURES_DIR / "valid-semantic.memory.md"), "--format", "json")
        output = json.loads(result.stdout)
        assert "summary" in output
        assert "timestamp" in output
        assert result.returncode == 0


class TestCheckTypes:
    """Specific check type tests."""

    def test_schema_only(self):
        """Test --check schema option."""
        result = run_validator(str(FIXTURES_DIR / "valid-semantic.memory.md"), "--check", "schema", "--format", "json")
        output = json.loads(result.stdout)
        assert output["summary"]["errors"] == 0
        assert result.returncode == 0

    def test_citations_only(self):
        """Test --check citations option."""
        result = run_validator(
            str(FIXTURES_DIR / "valid-with-citations.memory.md"), "--check", "citations", "--format", "json"
        )
        json.loads(result.stdout)
        assert result.returncode == 0


class TestMultipleFiles:
    """Multiple file validation tests."""

    def test_validate_directory(self):
        """Test validating entire fixtures directory."""
        result = run_validator(str(FIXTURES_DIR), "--format", "json")
        output = json.loads(result.stdout)
        # Should find all fixture files
        assert output["summary"]["total"] >= 5
        # Should have some errors from invalid fixtures
        assert output["summary"]["errors"] > 0

    def test_fast_fail(self):
        """Test --fast-fail stops on first error."""
        result = run_validator(str(FIXTURES_DIR), "--fast-fail", "--format", "json")
        json.loads(result.stdout)
        # Should have processed fewer files due to fast-fail
        # (at least stopped at first error)
        assert result.returncode == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
