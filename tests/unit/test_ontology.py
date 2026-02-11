#!/usr/bin/env python3
"""
Unit tests for ontology library.
"""

import sys
import unittest
from pathlib import Path

# Add skills/ontology/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "ontology" / "lib"))

from entity_resolver import EntityResolver
from ontology_registry import OntologyRegistry
from ontology_validator import OntologyValidator


class TestOntologyValidator(unittest.TestCase):
    """Tests for OntologyValidator."""

    def setUp(self):
        self.validator = OntologyValidator()
        self.base_ontology = Path(__file__).parent.parent.parent / "skills" / "ontology" / "fallback" / "ontologies" / "mif-base.ontology.yaml"
        self.example_ontology = Path(__file__).parent.parent.parent / "skills" / "ontology" / "fallback" / "ontologies" / "examples" / "software-engineering.ontology.yaml"

    def test_validate_base_ontology(self):
        """Base ontology should be valid."""
        if not self.base_ontology.exists():
            self.skipTest("Base ontology not found")
        result = self.validator.validate_file(self.base_ontology)
        self.assertTrue(result.valid, f"Errors: {result.errors}")

    def test_validate_example_ontology(self):
        """Software engineering ontology should be valid."""
        if not self.example_ontology.exists():
            self.skipTest("Example ontology not found")
        result = self.validator.validate_file(self.example_ontology)
        self.assertTrue(result.valid, f"Errors: {result.errors}")

    def test_invalid_id_format(self):
        """IDs must be lowercase with hyphens."""
        data = {
            "ontology": {"id": "InvalidID", "version": "1.0.0"},
            "namespaces": {}
        }
        result = self.validator.validate_data(data)
        self.assertFalse(result.valid)
        self.assertTrue(any("id" in str(e.path).lower() for e in result.errors))

    def test_invalid_base_type(self):
        """Entity types must have valid base type."""
        data = {
            "ontology": {"id": "test", "version": "1.0.0"},
            "entity_types": [
                {"name": "test-entity", "base": "invalid-type"}
            ]
        }
        result = self.validator.validate_data(data)
        self.assertFalse(result.valid)

    def test_undefined_trait_reference(self):
        """Referencing undefined trait should error."""
        data = {
            "ontology": {"id": "test", "version": "1.0.0"},
            "traits": {},
            "entity_types": [
                {"name": "test-entity", "base": "semantic", "traits": ["undefined-trait"]}
            ]
        }
        result = self.validator.validate_data(data)
        self.assertFalse(result.valid)


class TestEntityResolver(unittest.TestCase):
    """Tests for EntityResolver."""

    def setUp(self):
        self.resolver = EntityResolver()

    def test_extract_simple_reference(self):
        """Should extract @[[Name]] references."""
        content = "Using @[[PostgreSQL]] for data storage."
        refs = self.resolver.extract_references(content)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0], ("simple", "PostgreSQL"))

    def test_extract_typed_reference(self):
        """Should extract [[type:id]] references."""
        content = "See [[technology:postgres-123]] for details."
        refs = self.resolver.extract_references(content)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0], ("typed", "technology:postgres-123"))

    def test_extract_multiple_references(self):
        """Should extract multiple references."""
        content = "Using @[[PostgreSQL]] and @[[Redis]] with [[pattern:repository]]."
        refs = self.resolver.extract_references(content)
        self.assertEqual(len(refs), 3)

    def test_no_references(self):
        """Should handle content with no references."""
        content = "Plain text with no entity references."
        refs = self.resolver.extract_references(content)
        self.assertEqual(len(refs), 0)


class TestOntologyRegistry(unittest.TestCase):
    """Tests for OntologyRegistry."""

    def setUp(self):
        self.registry = OntologyRegistry()

    def test_registry_initialization(self):
        """Registry should initialize without error."""
        # Registry may auto-load base namespaces
        namespaces = self.registry.get_all_namespaces()
        self.assertIsInstance(namespaces, list)

    def test_load_ontologies(self):
        """Should load ontologies from path."""
        ontology_dir = Path(__file__).parent.parent.parent / "skills" / "ontology" / "fallback" / "ontologies"
        if not ontology_dir.exists():
            self.skipTest("Ontology directory not found")
        self.registry.load_ontologies([ontology_dir])
        # Base ontology has 9 namespaces
        self.assertGreater(len(self.registry.get_all_namespaces()), 0)


if __name__ == "__main__":
    unittest.main()
