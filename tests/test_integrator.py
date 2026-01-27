"""Unit tests for integrator.py."""

import json
import pytest
import shutil
from pathlib import Path
import sys
import tempfile

# Add the skills/integrate/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "integrate" / "lib"))

from integrator import Integrator, IntegrationResult, IntegrationReport


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path."""
    return Path(__file__).parent / "fixtures" / "integrate"


@pytest.fixture
def mock_plugin_dir(fixtures_dir, tmp_path):
    """Copy mock plugin to temp directory for modification tests."""
    src = fixtures_dir / "mock_plugin"
    dst = tmp_path / "mock_plugin"
    shutil.copytree(src, dst)
    return dst


@pytest.fixture
def integrator(mock_plugin_dir):
    """Create an Integrator instance with mock plugin."""
    return Integrator(plugin_root=mock_plugin_dir)


class TestIntegrationResult:
    """Tests for IntegrationResult dataclass."""

    def test_result_fields(self):
        result = IntegrationResult(
            file_path=Path("/test.md"),
            success=True,
            action="inserted",
            message="Test message",
        )
        assert result.success is True
        assert result.action == "inserted"
        assert result.message == "Test message"

    def test_result_optional_fields(self):
        result = IntegrationResult(
            file_path=Path("/test.md"),
            success=True,
            action="migrated",
            message="Test",
            had_legacy=True,
            markers_added=True,
            tools_added=["Bash", "Read"],
        )
        assert result.had_legacy is True
        assert result.markers_added is True
        assert "Bash" in result.tools_added


class TestIntegrationReport:
    """Tests for IntegrationReport dataclass."""

    def test_report_counts(self):
        report = IntegrationReport(
            plugin_root=Path("/test"),
            template_path=Path("/template.md"),
            mode="integrate",
        )
        report.results = [
            IntegrationResult(Path("/a.md"), True, "inserted", "OK"),
            IntegrationResult(Path("/b.md"), True, "updated", "OK"),
            IntegrationResult(Path("/c.md"), False, "skipped", "Error"),
        ]
        assert report.success_count == 2
        assert report.failure_count == 1
        assert report.all_successful is False

    def test_report_all_successful(self):
        report = IntegrationReport(
            plugin_root=Path("/test"),
            template_path=Path("/template.md"),
            mode="integrate",
        )
        report.results = [
            IntegrationResult(Path("/a.md"), True, "inserted", "OK"),
        ]
        assert report.all_successful is True


class TestFindTemplate:
    """Tests for template discovery."""

    def test_find_template_in_templates_dir(self, mock_plugin_dir):
        integrator = Integrator(plugin_root=mock_plugin_dir)
        assert integrator.template_path.exists()
        assert "mnemonic-protocol" in integrator.template_path.name

    def test_find_template_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Integrator(plugin_root=tmp_path)


class TestDiscoverComponents:
    """Tests for component discovery."""

    def test_discover_from_manifest(self, integrator):
        components = integrator.discover_components()
        assert "commands" in components
        assert "skills" in components
        assert len(components["commands"]) >= 1
        assert len(components["skills"]) >= 1

    def test_discover_finds_correct_files(self, integrator):
        components = integrator.discover_components()
        command_names = [c.name for c in components["commands"]]
        assert "test-cmd.md" in command_names


class TestIntegrateFile:
    """Tests for integrate_file method."""

    def test_integrate_fresh_file(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        original = cmd_file.read_text()
        assert "BEGIN MNEMONIC" not in original

        result = integrator.integrate_file(cmd_file)

        assert result.success is True
        assert result.action == "inserted"
        new_content = cmd_file.read_text()
        assert "BEGIN MNEMONIC" in new_content
        assert "END MNEMONIC" in new_content

    def test_integrate_dry_run(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        original = cmd_file.read_text()

        result = integrator.integrate_file(cmd_file, dry_run=True)

        assert result.success is True
        assert result.action == "inserted"
        # File should be unchanged
        assert cmd_file.read_text() == original

    def test_integrate_updates_existing(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        # First integrate
        integrator.integrate_file(cmd_file)
        # Manually change content
        content = cmd_file.read_text()
        modified = content.replace("mnemonic:search", "modified:search")
        cmd_file.write_text(modified)

        # Re-integrate
        result = integrator.integrate_file(cmd_file)

        assert result.success is True
        assert result.action == "updated"
        # Should have restored original template content
        new_content = cmd_file.read_text()
        assert "mnemonic:search" in new_content

    def test_integrate_nonexistent_file(self, integrator):
        result = integrator.integrate_file(Path("/nonexistent.md"))
        assert result.success is False
        assert result.action == "skipped"

    def test_integrate_adds_tools(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        result = integrator.integrate_file(cmd_file)

        assert result.success is True
        # Should have added missing tools
        assert len(result.tools_added) > 0


class TestRemoveFromFile:
    """Tests for remove_from_file method."""

    def test_remove_markers(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        # First integrate
        integrator.integrate_file(cmd_file)
        assert "BEGIN MNEMONIC" in cmd_file.read_text()

        # Then remove
        result = integrator.remove_from_file(cmd_file)

        assert result.success is True
        assert result.action == "removed"
        assert "BEGIN MNEMONIC" not in cmd_file.read_text()

    def test_remove_no_markers(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        result = integrator.remove_from_file(cmd_file)

        assert result.success is True
        assert result.action == "skipped"

    def test_remove_dry_run(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        integrator.integrate_file(cmd_file)
        original = cmd_file.read_text()

        result = integrator.remove_from_file(cmd_file, dry_run=True)

        assert result.success is True
        assert cmd_file.read_text() == original


class TestVerifyFile:
    """Tests for verify_file method."""

    def test_verify_correct_integration(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        integrator.integrate_file(cmd_file)

        result = integrator.verify_file(cmd_file)

        assert result.success is True
        assert result.action == "verified"

    def test_verify_missing_markers(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        # Don't integrate first

        result = integrator.verify_file(cmd_file)

        assert result.success is False
        assert "marker" in result.message.lower()

    def test_verify_wrong_content(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        integrator.integrate_file(cmd_file)
        # Modify the content
        content = cmd_file.read_text()
        modified = content.replace("mnemonic:search", "wrong:content")
        cmd_file.write_text(modified)

        result = integrator.verify_file(cmd_file)

        assert result.success is False
        assert "match" in result.message.lower()


class TestRun:
    """Tests for run method."""

    def test_run_integrate_all(self, integrator, mock_plugin_dir):
        report = integrator.run(mode="integrate")

        assert report.all_successful is True
        assert report.success_count >= 2  # At least command + skill

    def test_run_integrate_specific_type(self, integrator, mock_plugin_dir):
        report = integrator.run(mode="integrate", component_types=["commands"])

        assert report.success_count >= 1
        for r in report.results:
            assert "commands" in str(r.file_path)

    def test_run_integrate_specific_files(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        report = integrator.run(mode="integrate", files=[cmd_file])

        assert len(report.results) == 1
        assert report.results[0].file_path == cmd_file

    def test_run_verify_mode(self, integrator, mock_plugin_dir):
        # First integrate
        integrator.run(mode="integrate")
        # Then verify
        report = integrator.run(mode="verify")

        assert report.all_successful is True
        assert all(r.action == "verified" for r in report.results)

    def test_run_remove_mode(self, integrator, mock_plugin_dir):
        integrator.run(mode="integrate")
        report = integrator.run(mode="remove")

        assert report.all_successful is True
        # Verify markers are gone
        for r in report.results:
            content = r.file_path.read_text()
            assert "BEGIN MNEMONIC" not in content

    def test_run_dry_run(self, integrator, mock_plugin_dir):
        cmd_file = mock_plugin_dir / ".claude-plugin" / "commands" / "test-cmd.md"
        original = cmd_file.read_text()

        report = integrator.run(mode="integrate", dry_run=True)

        assert report.all_successful is True
        assert cmd_file.read_text() == original  # Unchanged

    def test_run_no_files_warning(self, tmp_path):
        # Create empty plugin structure
        plugin_dir = tmp_path / "empty_plugin"
        plugin_dir.mkdir()
        (plugin_dir / ".claude-plugin").mkdir()
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{}")
        (plugin_dir / "templates").mkdir()
        (plugin_dir / "templates" / "mnemonic-protocol.md").write_text(
            "<!-- BEGIN MNEMONIC PROTOCOL -->\nTest\n<!-- END MNEMONIC PROTOCOL -->"
        )

        integrator = Integrator(plugin_root=plugin_dir)
        report = integrator.run(mode="integrate")

        assert len(report.warnings) > 0
        assert any("no files" in w.lower() for w in report.warnings)


class TestWithRealFixtures:
    """Tests using the actual fixture files."""

    def test_integrate_legacy_file(self, integrator, mock_plugin_dir, fixtures_dir, tmp_path):
        # Copy legacy fixture to mock plugin (must be inside plugin root for security)
        legacy_file = mock_plugin_dir / ".claude-plugin" / "commands" / "legacy.md"
        shutil.copy(fixtures_dir / "sample_legacy.md", legacy_file)

        result = integrator.integrate_file(legacy_file)

        assert result.success is True
        assert result.action == "migrated"
        assert result.had_legacy is True
        content = legacy_file.read_text()
        assert "BEGIN MNEMONIC" in content
        assert "Memory Operations" not in content  # Old section replaced
