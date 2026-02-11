"""End-to-end integration tests for the mnemonic integrate skill."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Add the skills/integrate/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "integrate" / "lib"))


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent / "fixtures" / "integrate"


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def mock_plugin(fixtures_dir, tmp_path):
    """Create a copy of the mock plugin for testing."""
    src = fixtures_dir / "mock_plugin"
    dst = tmp_path / "test_plugin"
    shutil.copytree(src, dst)
    return dst


class TestE2EIntegration:
    """End-to-end integration tests."""

    def test_full_integration_workflow(self, mock_plugin, project_root):
        """Test complete integration workflow: integrate -> verify -> remove."""
        lib_path = project_root / "skills" / "integrate" / "lib"

        # Step 1: Run integration
        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "integrator.py"),
                str(mock_plugin),
                "--mode", "integrate",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Integration failed: {result.stderr}"
        assert "success" in result.stdout.lower() or "inserted" in result.stdout.lower()

        # Step 2: Verify integration
        cmd_file = mock_plugin / ".claude-plugin" / "commands" / "test-cmd.md"
        content = cmd_file.read_text()
        assert "<!-- BEGIN MNEMONIC PROTOCOL -->" in content
        assert "<!-- END MNEMONIC PROTOCOL -->" in content
        assert "/mnemonic:search" in content
        assert "/mnemonic:capture" in content

        # Step 3: Verify frontmatter tools added
        assert "Bash" in content
        assert "Glob" in content
        assert "Grep" in content
        assert "Read" in content
        assert "Write" in content

        # Step 4: Run verification
        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "integrator.py"),
                str(mock_plugin),
                "--mode", "verify",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Verification failed: {result.stderr}"

        # Step 5: Run removal
        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "integrator.py"),
                str(mock_plugin),
                "--mode", "remove",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Removal failed: {result.stderr}"

        # Step 6: Verify markers removed
        content = cmd_file.read_text()
        assert "<!-- BEGIN MNEMONIC PROTOCOL -->" not in content
        assert "<!-- END MNEMONIC PROTOCOL -->" not in content

    def test_dry_run_no_changes(self, mock_plugin, project_root):
        """Test that dry-run doesn't modify files."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        cmd_file = mock_plugin / ".claude-plugin" / "commands" / "test-cmd.md"
        original = cmd_file.read_text()

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "integrator.py"),
                str(mock_plugin),
                "--mode", "integrate",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # File should be unchanged
        assert cmd_file.read_text() == original

    def test_json_output(self, mock_plugin, project_root):
        """Test JSON output format."""
        import json as json_module
        lib_path = project_root / "skills" / "integrate" / "lib"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "integrator.py"),
                str(mock_plugin),
                "--mode", "integrate",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Should be valid JSON
        data = json_module.loads(result.stdout)
        assert "success" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_specific_component_type(self, mock_plugin, project_root):
        """Test integrating only specific component types."""
        lib_path = project_root / "skills" / "integrate" / "lib"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "integrator.py"),
                str(mock_plugin),
                "--mode", "integrate",
                "--type", "commands",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Command should be integrated
        cmd_file = mock_plugin / ".claude-plugin" / "commands" / "test-cmd.md"
        assert "BEGIN MNEMONIC" in cmd_file.read_text()

        # Skill should NOT be integrated
        skill_file = mock_plugin / ".claude-plugin" / "skills" / "test-skill" / "SKILL.md"
        assert "BEGIN MNEMONIC" not in skill_file.read_text()


class TestE2EMarkerParser:
    """End-to-end tests for marker_parser CLI."""

    def test_check_markers(self, fixtures_dir, project_root):
        """Test marker checking via CLI."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        sample = fixtures_dir / "sample_with_markers.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "marker_parser.py"),
                str(sample),
                "--check",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Has markers: True" in result.stdout

    def test_check_no_markers(self, fixtures_dir, project_root):
        """Test marker checking on file without markers."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        sample = fixtures_dir / "sample_no_markers.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "marker_parser.py"),
                str(sample),
                "--check",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1  # No markers
        assert "Has markers: False" in result.stdout

    def test_extract_content(self, fixtures_dir, project_root):
        """Test extracting content between markers."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        sample = fixtures_dir / "sample_with_markers.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "marker_parser.py"),
                str(sample),
                "--extract",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Memory" in result.stdout

    def test_check_legacy(self, fixtures_dir, project_root):
        """Test legacy pattern detection."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        sample = fixtures_dir / "sample_legacy.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "marker_parser.py"),
                str(sample),
                "--has-legacy",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1  # Has legacy
        assert "Has legacy pattern: True" in result.stdout


class TestE2ETemplateValidator:
    """End-to-end tests for template_validator CLI."""

    def test_validate_good_template(self, fixtures_dir, project_root):
        """Test validating a good template."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        template = fixtures_dir / "sample_template.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "template_validator.py"),
                str(template),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Valid: True" in result.stdout

    def test_validate_bad_template(self, fixtures_dir, project_root):
        """Test validating a template without markers."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        template = fixtures_dir / "sample_no_markers.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "template_validator.py"),
                str(template),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Valid: False" in result.stdout


class TestE2EFrontmatterUpdater:
    """End-to-end tests for frontmatter_updater CLI."""

    def test_list_tools(self, fixtures_dir, project_root):
        """Test listing current tools."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        sample = fixtures_dir / "sample_with_markers.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "frontmatter_updater.py"),
                str(sample),
                "--list",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Bash" in result.stdout

    def test_check_tools(self, fixtures_dir, project_root):
        """Test checking for required tools."""
        lib_path = project_root / "skills" / "integrate" / "lib"
        sample = fixtures_dir / "sample_no_markers.md"

        result = subprocess.run(
            [
                sys.executable,
                str(lib_path / "frontmatter_updater.py"),
                str(sample),
                "--check",
            ],
            capture_output=True,
            text=True,
        )
        # Should fail because not all tools present
        assert result.returncode == 1
        assert "Missing" in result.stdout
