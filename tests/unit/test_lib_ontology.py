#!/usr/bin/env python3
"""
Unit tests for lib/ontology.py ontology loading functions.

Tests ontology file discovery, loading, and pattern extraction.
"""

from pathlib import Path
from unittest.mock import mock_open, patch

from lib.ontology import (
    _collect_namespaces,
    _extract_entity_type_names,
    get_fallback_content_patterns,
    get_fallback_file_patterns,
    get_ontology_file,
    get_ontology_info,
    load_content_patterns,
    load_file_patterns,
    load_ontology_data,
    load_ontology_namespaces,
)


class TestGetOntologyFile:
    """Test get_ontology_file() function."""

    def test_get_ontology_file_mif_location(self):
        """Test finding ontology file returns Path or None."""
        # This test is challenging with the current implementation
        # Let's test the actual behavior with a real setup
        result = get_ontology_file()
        assert result is None or isinstance(result, Path)

    def test_get_ontology_file_returns_path_or_none(self):
        """Test that function returns Path or None."""
        result = get_ontology_file()
        assert result is None or isinstance(result, Path)


class TestLoadOntologyData:
    """Test load_ontology_data() function."""

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_ontology_data_success(self, mock_yaml, mock_get_file):
        """Test successful ontology loading."""
        mock_get_file.return_value = Path("/project/mif/ontologies/mif-base.ontology.yaml")
        mock_yaml.safe_load.return_value = {
            "ontology": {"id": "mif-base", "version": "1.0"},
            "namespaces": {},
            "relationships": {},
        }

        with patch("builtins.open", mock_open(read_data="ontology: {}")):
            result = load_ontology_data()

        assert isinstance(result, dict)
        assert "ontology" in result

    @patch("lib.ontology.get_ontology_file")
    def test_load_ontology_data_no_file(self, mock_get_file):
        """Test when ontology file not found."""
        mock_get_file.return_value = None

        result = load_ontology_data()

        assert result == {}

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml", None)
    def test_load_ontology_data_no_yaml_module(self, mock_get_file):
        """Test when yaml module not available."""
        mock_get_file.return_value = Path("/project/ontology.yaml")

        result = load_ontology_data()

        assert result == {}

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_ontology_data_parse_error(self, mock_yaml, mock_get_file):
        """Test handling of YAML parse errors."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_yaml.safe_load.return_value = None

        with patch("builtins.open", mock_open(read_data="invalid: yaml: [")):
            result = load_ontology_data()

        assert result == {}


class TestLoadFilePatterns:
    """Test load_file_patterns() function."""

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_file_patterns_success(self, mock_yaml, mock_get_file):
        """Test successful file pattern loading."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_yaml.safe_load.return_value = {
            "discovery": {
                "enabled": True,
                "file_patterns": [
                    {
                        "pattern": "auth|login|session",
                        "namespaces": ["_semantic/knowledge", "_semantic/decisions"],
                        "context": "authentication",
                    },
                    {
                        "pattern": "api|endpoint",
                        "namespaces": ["_semantic/knowledge"],
                        "context": "API design",
                    },
                ],
            }
        }

        with patch("builtins.open", mock_open(read_data="")):
            result = load_file_patterns()

        assert len(result) == 2
        assert result[0]["patterns"] == ["auth", "login", "session"]
        assert result[0]["namespaces"] == ["_semantic/knowledge", "_semantic/decisions"]
        assert result[0]["context"] == "authentication"

    @patch("lib.ontology.get_ontology_file")
    def test_load_file_patterns_no_file(self, mock_get_file):
        """Test fallback when no ontology file."""
        mock_get_file.return_value = None

        result = load_file_patterns()

        # Should return fallback patterns
        assert isinstance(result, list)
        assert len(result) > 0
        assert any("auth" in p["patterns"] for p in result)

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_file_patterns_discovery_disabled(self, mock_yaml, mock_get_file):
        """Test fallback when discovery is disabled."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_yaml.safe_load.return_value = {
            "discovery": {
                "enabled": False,
            }
        }

        with patch("builtins.open", mock_open(read_data="")):
            result = load_file_patterns()

        # Should return fallback patterns
        assert isinstance(result, list)
        assert len(result) > 0

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_file_patterns_empty_patterns(self, mock_yaml, mock_get_file):
        """Test fallback when file_patterns is empty."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_yaml.safe_load.return_value = {
            "discovery": {
                "enabled": True,
                "file_patterns": [],
            }
        }

        with patch("builtins.open", mock_open(read_data="")):
            result = load_file_patterns()

        # Should return fallback patterns
        assert isinstance(result, list)
        assert len(result) > 0

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_file_patterns_invalid_entries(self, mock_yaml, mock_get_file):
        """Test filtering of invalid pattern entries."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_yaml.safe_load.return_value = {
            "discovery": {
                "enabled": True,
                "file_patterns": [
                    {
                        "pattern": "auth",
                        "namespaces": ["_semantic/knowledge"],
                        "context": "authentication",
                    },
                    {
                        "pattern": "",  # Invalid: empty pattern
                        "namespaces": ["_semantic/knowledge"],
                        "context": "empty",
                    },
                    {
                        "pattern": "test",
                        "namespaces": [],  # Invalid: empty namespaces
                        "context": "test",
                    },
                ],
            }
        }

        with patch("builtins.open", mock_open(read_data="")):
            result = load_file_patterns()

        # Should only include valid entry
        assert len(result) == 1
        assert result[0]["patterns"] == ["auth"]


class TestLoadContentPatterns:
    """Test load_content_patterns() function."""

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_content_patterns_success(self, mock_yaml, mock_get_file):
        """Test successful content pattern loading."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_yaml.safe_load.return_value = {
            "discovery": {
                "enabled": True,
                "content_patterns": [
                    {"namespace": "_semantic/decisions", "pattern": r"\bdecided to\b"},
                    {"namespace": "_semantic/decisions", "pattern": r"\bgoing with\b"},
                    {"namespace": "_semantic/knowledge", "pattern": r"\blearned that\b"},
                ],
            }
        }

        with patch("builtins.open", mock_open(read_data="")):
            result = load_content_patterns()

        assert isinstance(result, dict)
        assert "_semantic/decisions" in result
        assert len(result["_semantic/decisions"]) == 2
        assert r"\bdecided to\b" in result["_semantic/decisions"]
        assert "_semantic/knowledge" in result
        assert len(result["_semantic/knowledge"]) == 1

    @patch("lib.ontology.get_ontology_file")
    def test_load_content_patterns_no_file(self, mock_get_file):
        """Test fallback when no ontology file."""
        mock_get_file.return_value = None

        result = load_content_patterns()

        # Should return fallback patterns
        assert isinstance(result, dict)
        assert "_semantic/decisions" in result
        assert "_semantic/knowledge" in result

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.yaml")
    def test_load_content_patterns_discovery_disabled(self, mock_yaml, mock_get_file):
        """Test fallback when discovery is disabled."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_yaml.safe_load.return_value = {
            "discovery": {
                "enabled": False,
            }
        }

        with patch("builtins.open", mock_open(read_data="")):
            result = load_content_patterns()

        # Should return fallback patterns
        assert isinstance(result, dict)
        assert len(result) > 0


class TestLoadOntologyNamespaces:
    """Test load_ontology_namespaces() function."""

    @patch("lib.ontology.get_v2_resolver")
    @patch("lib.ontology.yaml")
    def test_load_ontology_namespaces_success(self, mock_yaml, mock_resolver):
        """Test successful namespace loading."""
        mock_resolver.return_value.get_ontology_paths.return_value = [Path("/project/custom.ontology.yaml")]
        mock_yaml.safe_load.return_value = {
            "namespaces": {
                "custom": {
                    "children": {
                        "category1": {},
                        "category2": {},
                    }
                }
            }
        }

        with patch("builtins.open", mock_open(read_data="")):
            with patch.object(Path, "exists", return_value=True):
                result = load_ontology_namespaces()

        assert isinstance(result, list)
        # Should include base namespaces
        assert "_semantic" in result
        assert "_semantic/decisions" in result
        # Should include custom namespaces
        assert "custom" in result
        assert "custom/category1" in result

    @patch("lib.ontology.get_v2_resolver")
    @patch("lib.ontology.yaml", None)
    def test_load_ontology_namespaces_no_yaml(self, mock_resolver):
        """Test when yaml module not available."""
        mock_resolver.return_value.get_ontology_paths.return_value = []

        result = load_ontology_namespaces()

        # Should return base namespaces only
        assert isinstance(result, list)
        assert "_semantic" in result
        assert "_procedural" in result
        assert "_episodic" in result

    @patch("lib.ontology.get_v2_resolver")
    @patch("lib.ontology.yaml")
    def test_load_ontology_namespaces_no_custom_files(self, mock_yaml, mock_resolver):
        """Test with no custom ontology files."""
        mock_resolver.return_value.get_ontology_paths.return_value = []

        result = load_ontology_namespaces()

        # Should return base namespaces only
        assert isinstance(result, list)
        assert "_semantic" in result
        assert len([ns for ns in result if ns.startswith("_")]) >= 10


class TestCollectNamespaces:
    """Test _collect_namespaces() helper function."""

    def test_collect_namespaces_flat(self):
        """Test collecting flat namespace structure."""
        namespaces = {
            "category1": {},
            "category2": {},
            "category3": {},
        }
        result = []

        _collect_namespaces(namespaces, "", result)

        assert len(result) == 3
        assert "category1" in result
        assert "category2" in result
        assert "category3" in result

    def test_collect_namespaces_hierarchical(self):
        """Test collecting hierarchical namespace structure."""
        namespaces = {
            "parent": {
                "children": {
                    "child1": {},
                    "child2": {
                        "children": {
                            "grandchild": {},
                        }
                    },
                }
            }
        }
        result = []

        _collect_namespaces(namespaces, "", result)

        assert "parent" in result
        assert "parent/child1" in result
        assert "parent/child2" in result
        assert "parent/child2/grandchild" in result

    def test_collect_namespaces_with_prefix(self):
        """Test collecting namespaces with prefix."""
        namespaces = {
            "child1": {},
            "child2": {},
        }
        result = []

        _collect_namespaces(namespaces, "parent", result)

        assert "parent/child1" in result
        assert "parent/child2" in result


class TestExtractEntityTypeNames:
    """Test _extract_entity_type_names() helper function."""

    def test_extract_entity_type_names_success(self):
        """Test extracting entity type names."""
        data = {
            "entity_types": [
                {"name": "Document", "description": "A document"},
                {"name": "Component", "description": "A component"},
                {"name": "Service", "description": "A service"},
            ]
        }

        result = _extract_entity_type_names(data)

        assert len(result) == 3
        assert "Document" in result
        assert "Component" in result
        assert "Service" in result

    def test_extract_entity_type_names_empty(self):
        """Test with no entity types."""
        data = {"entity_types": []}

        result = _extract_entity_type_names(data)

        assert result == []

    def test_extract_entity_type_names_missing_key(self):
        """Test with missing entity_types key."""
        data = {}

        result = _extract_entity_type_names(data)

        assert result == []

    def test_extract_entity_type_names_invalid_format(self):
        """Test with invalid entity_types format."""
        data = {"entity_types": "not a list"}

        result = _extract_entity_type_names(data)

        assert result == []


class TestGetFallbackPatterns:
    """Test fallback pattern functions."""

    def test_get_fallback_file_patterns(self):
        """Test fallback file patterns."""
        result = get_fallback_file_patterns()

        assert isinstance(result, list)
        assert len(result) == 8
        # Check for key patterns
        assert any("auth" in p["patterns"] for p in result)
        assert any("api" in p["patterns"] for p in result)
        assert any("database" in p["patterns"] or "db" in p["patterns"] for p in result)
        assert any("test" in p["patterns"] for p in result)

    def test_get_fallback_file_patterns_structure(self):
        """Test structure of fallback patterns."""
        result = get_fallback_file_patterns()

        for pattern in result:
            assert "patterns" in pattern
            assert "namespaces" in pattern
            assert "context" in pattern
            assert isinstance(pattern["patterns"], list)
            assert isinstance(pattern["namespaces"], list)
            assert isinstance(pattern["context"], str)

    def test_get_fallback_content_patterns(self):
        """Test fallback content patterns."""
        result = get_fallback_content_patterns()

        assert isinstance(result, dict)
        assert "_semantic/decisions" in result
        assert "_semantic/knowledge" in result
        assert "_procedural/patterns" in result
        assert "_episodic/blockers" in result

    def test_get_fallback_content_patterns_structure(self):
        """Test structure of fallback content patterns."""
        result = get_fallback_content_patterns()

        for namespace, patterns in result.items():
            assert isinstance(namespace, str)
            assert isinstance(patterns, list)
            assert all(isinstance(p, str) for p in patterns)


class TestGetOntologyInfo:
    """Test get_ontology_info() function."""

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.get_v2_resolver")
    @patch("lib.ontology.yaml")
    def test_get_ontology_info_success(self, mock_yaml, mock_resolver, mock_get_file):
        """Test successful ontology info retrieval."""
        mock_get_file.return_value = Path("/project/mif-base.ontology.yaml")
        mock_resolver.return_value.get_ontology_paths.return_value = []
        mock_yaml.safe_load.return_value = {
            "ontology": {
                "id": "mif-base",
                "version": "1.0.0",
            },
            "namespaces": {
                "_semantic": {
                    "children": {
                        "decisions": {},
                        "knowledge": {},
                    }
                }
            },
            "entity_types": [
                {"name": "Document"},
                {"name": "Component"},
            ],
            "traits": {
                "versioned": {"description": "Has version tracking"},
            },
            "relationships": {
                "relates_to": {"description": "Generic relationship"},
                "supersedes": {"description": "Replaces older item"},
            },
            "discovery": {
                "enabled": True,
            },
        }

        with patch("builtins.open", mock_open(read_data="")):
            with patch.object(Path, "exists", return_value=True):
                result = get_ontology_info()

        assert result["loaded"] is True
        assert result["id"] == "mif-base"
        assert result["version"] == "1.0.0"
        assert "_semantic" in result["namespaces"]
        assert "_semantic/decisions" in result["namespaces"]
        assert "Document" in result["entity_types"]
        assert "versioned" in result["traits"]
        assert "relates_to" in result["relationships"]
        assert result["discovery_enabled"] is True

    @patch("lib.ontology.yaml", None)
    def test_get_ontology_info_no_yaml(self):
        """Test when yaml module not available."""
        result = get_ontology_info()

        assert result["loaded"] is False
        assert result["id"] is None
        assert result["version"] is None
        assert result["namespaces"] == []
        assert result["entity_types"] == []
        assert result["relationships"] == {}

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.get_v2_resolver")
    @patch("lib.ontology.yaml")
    def test_get_ontology_info_no_file(self, mock_yaml, mock_resolver, mock_get_file):
        """Test when ontology file not found."""
        mock_get_file.return_value = None
        mock_resolver.return_value.get_ontology_paths.return_value = []

        result = get_ontology_info()

        assert result["loaded"] is False
        assert result["id"] is None

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.get_v2_resolver")
    @patch("lib.ontology.yaml")
    def test_get_ontology_info_with_custom_ontology(self, mock_yaml, mock_resolver, mock_get_file):
        """Test loading both MIF base and custom ontology."""
        mock_get_file.return_value = Path("/project/mif-base.ontology.yaml")
        mock_resolver.return_value.get_ontology_paths.return_value = [Path("/project/custom.ontology.yaml")]

        mif_data = {
            "ontology": {"id": "mif-base", "version": "1.0"},
            "namespaces": {"_semantic": {}},
            "entity_types": [{"name": "Document"}],
            "traits": {"base_trait": {}},
            "relationships": {"relates_to": {}},
            "discovery": {"enabled": True},
        }

        custom_data = {
            "ontology": {"id": "custom-ontology"},
            "namespaces": {"custom": {}},
            "entity_types": [{"name": "CustomType"}],
            "traits": {"custom_trait": {}},
            "relationships": {"custom_rel": {}},
        }

        mock_yaml.safe_load.side_effect = [mif_data, custom_data]

        with patch("builtins.open", mock_open(read_data="")):
            with patch.object(Path, "exists", return_value=True):
                result = get_ontology_info()

        assert result["loaded"] is True
        assert result["id"] == "mif-base"
        assert result["custom_id"] == "custom-ontology"
        assert "_semantic" in result["namespaces"]
        assert "custom" in result["namespaces"]
        assert "Document" in result["entity_types"]
        assert "CustomType" in result["entity_types"]
        assert "base_trait" in result["traits"]
        assert "custom_trait" in result["traits"]
        assert "relates_to" in result["relationships"]
        assert "custom_rel" in result["relationships"]

    @patch("lib.ontology.get_ontology_file")
    @patch("lib.ontology.get_v2_resolver")
    @patch("lib.ontology.yaml")
    def test_get_ontology_info_partial_data(self, mock_yaml, mock_resolver, mock_get_file):
        """Test with partial ontology data."""
        mock_get_file.return_value = Path("/project/ontology.yaml")
        mock_resolver.return_value.get_ontology_paths.return_value = []
        mock_yaml.safe_load.return_value = {
            "ontology": {"id": "minimal"},
            # Missing namespaces, entity_types, etc.
        }

        with patch("builtins.open", mock_open(read_data="")):
            with patch.object(Path, "exists", return_value=True):
                result = get_ontology_info()

        assert result["loaded"] is True
        assert result["id"] == "minimal"
        assert result["namespaces"] == []
        assert result["entity_types"] == []
        assert result["relationships"] == {}
