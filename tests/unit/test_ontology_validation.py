#!/usr/bin/env python3
"""
Unit tests for lib/ontology.py validate_memory_against_ontology().
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.ontology import validate_memory_against_ontology


class TestValidateMemoryAgainstOntology:
    """Test validate_memory_against_ontology()."""

    def _make_ontology(self):
        """Create a minimal ontology data dict for testing."""
        return {
            "namespaces": {
                "_semantic": {
                    "description": "Facts and knowledge",
                    "children": {
                        "decisions": {"type_hint": "semantic"},
                        "knowledge": {"type_hint": "semantic"},
                        "entities": {"type_hint": "semantic"},
                    },
                },
                "_episodic": {
                    "description": "Events and experiences",
                    "children": {
                        "incidents": {"type_hint": "episodic"},
                        "sessions": {"type_hint": "episodic"},
                        "blockers": {"type_hint": "episodic"},
                    },
                },
                "_procedural": {
                    "description": "Processes and steps",
                    "children": {
                        "runbooks": {"type_hint": "procedural"},
                        "patterns": {"type_hint": "procedural"},
                        "migrations": {"type_hint": "procedural"},
                    },
                },
            }
        }

    def test_valid_namespace_and_type(self):
        """Valid namespace + matching type produces no errors."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_semantic/decisions", "semantic", ontology)
        assert errors == []

    def test_valid_procedural(self):
        """Procedural namespace + procedural type is valid."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_procedural/patterns", "procedural", ontology)
        assert errors == []

    def test_valid_episodic(self):
        """Episodic namespace + episodic type is valid."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_episodic/incidents", "episodic", ontology)
        assert errors == []

    def test_type_mismatch(self):
        """Type doesn't match namespace prefix -> error."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_semantic/decisions", "procedural", ontology)
        assert len(errors) == 1
        assert "does not match namespace" in errors[0]

    def test_unknown_namespace(self):
        """Completely unknown namespace -> error."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_unknown/foo", "semantic", ontology)
        assert len(errors) >= 1
        assert "Unknown namespace" in errors[0]

    def test_top_level_namespace_accepted(self):
        """Top-level namespace like '_semantic' is accepted."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_semantic", "semantic", ontology)
        assert errors == []

    def test_empty_ontology_skips_validation(self):
        """Empty ontology data skips validation (no errors)."""
        errors = validate_memory_against_ontology("_semantic/decisions", "semantic", {})
        assert errors == []

    def test_none_ontology_skips_validation(self):
        """None-ish ontology data skips validation."""
        errors = validate_memory_against_ontology("_semantic/decisions", "semantic", {})
        assert errors == []

    def test_both_errors_at_once(self):
        """Unknown namespace AND type mismatch -> multiple errors possible."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_unknown/bar", "episodic", ontology)
        assert len(errors) >= 1

    def test_empty_namespace(self):
        """Empty namespace with valid type -> no type mismatch error."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("", "semantic", ontology)
        # Empty namespace won't trigger type mismatch (no prefix to check)
        type_errors = [e for e in errors if "does not match" in e]
        assert len(type_errors) == 0

    def test_empty_type(self):
        """Empty type with valid namespace -> no type mismatch error."""
        ontology = self._make_ontology()
        errors = validate_memory_against_ontology("_semantic/decisions", "", ontology)
        type_errors = [e for e in errors if "does not match" in e]
        assert len(type_errors) == 0
