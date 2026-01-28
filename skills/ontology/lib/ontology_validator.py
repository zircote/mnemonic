#!/usr/bin/env python3
"""
Ontology Validator for Mnemonic

Validates ontology definition files against the meta-schema.
Checks entity type definitions, trait compatibility, and relationships.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json
import logging
import re

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A validation issue (error or warning)."""

    level: str  # "error" | "warning"
    path: str  # JSON path to the issue (e.g., "entity_types.component.schema")
    message: str
    value: Any = None

    def __str__(self):
        return f"[{self.level.upper()}] {self.path}: {self.message}"


@dataclass
class OntologyValidationResult:
    """Result of ontology validation."""

    valid: bool
    file_path: Optional[Path] = None
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    def add_error(self, path: str, message: str, value: Any = None):
        """Add an error."""
        self.errors.append(ValidationIssue("error", path, message, value))
        self.valid = False

    def add_warning(self, path: str, message: str, value: Any = None):
        """Add a warning."""
        self.warnings.append(ValidationIssue("warning", path, message, value))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "valid": self.valid,
            "file_path": str(self.file_path) if self.file_path else None,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                {"path": e.path, "message": e.message, "value": e.value}
                for e in self.errors
            ],
            "warnings": [
                {"path": w.path, "message": w.message, "value": w.value}
                for w in self.warnings
            ],
        }

    def __str__(self):
        lines = []
        if self.file_path:
            lines.append(f"Validating: {self.file_path}")

        if self.valid:
            lines.append("Status: VALID")
        else:
            lines.append("Status: INVALID")

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  - {e}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)


class OntologyValidator:
    """
    Validates ontology definitions.

    Checks:
    - Required fields are present
    - Field types are correct
    - IDs follow naming conventions
    - Versions follow semver
    - Entity types inherit from valid base types
    - Traits are defined before use
    - Relationships reference valid entity types
    - Discovery patterns are valid regex
    """

    VALID_BASE_TYPES = {"semantic", "episodic", "procedural"}
    VALID_TYPE_HINTS = {"semantic", "episodic", "procedural"}

    ID_PATTERN = re.compile(r"^_?[a-z][a-z0-9-]*$")  # Allow underscore prefix for cognitive triad
    VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+.*$")

    def __init__(self):
        self.result: Optional[OntologyValidationResult] = None

    def validate_file(self, file_path: Path) -> OntologyValidationResult:
        """
        Validate an ontology file.

        Args:
            file_path: Path to the ontology YAML file

        Returns:
            OntologyValidationResult with any errors/warnings
        """
        self.result = OntologyValidationResult(valid=True, file_path=file_path)

        if yaml is None:
            self.result.add_error("", "PyYAML not installed")
            return self.result

        if not file_path.exists():
            self.result.add_error("", f"File not found: {file_path}")
            return self.result

        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.result.add_error("", f"Invalid YAML: {e}")
            return self.result

        if not data:
            self.result.add_error("", "Empty file")
            return self.result

        self._validate_ontology(data)
        return self.result

    def validate_data(self, data: Dict[str, Any]) -> OntologyValidationResult:
        """
        Validate ontology data (already parsed YAML).

        Args:
            data: Parsed ontology data

        Returns:
            OntologyValidationResult with any errors/warnings
        """
        self.result = OntologyValidationResult(valid=True)
        self._validate_ontology(data)
        return self.result

    def _validate_ontology(self, data: Dict[str, Any]) -> None:
        """Validate the full ontology structure."""
        # Check for ontology wrapper
        ont_data = data.get("ontology", data)

        # Required fields
        self._validate_required_field(ont_data, "ontology", "id")

        # Validate ID format
        ont_id = ont_data.get("id")
        if ont_id and not self.ID_PATTERN.match(ont_id):
            self.result.add_error(
                "ontology.id",
                "ID must be lowercase, start with a letter, and contain only letters, numbers, and hyphens",
                ont_id,
            )

        # Validate version format
        version = ont_data.get("version")
        if version and not self.VERSION_PATTERN.match(str(version)):
            self.result.add_warning(
                "ontology.version",
                "Version should follow semantic versioning (e.g., 1.0.0)",
                version,
            )

        # Validate schema_url
        schema_url = ont_data.get("schema_url")
        if schema_url:
            if not schema_url.startswith(("http://", "https://")):
                self.result.add_error(
                    "ontology.schema_url",
                    "schema_url must be a valid HTTP/HTTPS URL",
                    schema_url,
                )

        # Validate namespaces
        self._validate_namespaces(data.get("namespaces", {}))

        # Validate traits first (entity types may reference them)
        defined_traits = self._validate_traits(data.get("traits", {}))

        # Validate entity types
        defined_entity_types = self._validate_entity_types(
            data.get("entity_types", []),
            defined_traits,
        )

        # Validate relationships
        self._validate_relationships(
            data.get("relationships", {}),
            defined_entity_types,
        )

        # Validate discovery config
        self._validate_discovery(
            data.get("discovery", {}),
            defined_entity_types,
        )

    def _validate_required_field(
        self, data: Dict, parent: str, field: str
    ) -> bool:
        """Check that a required field exists."""
        if field not in data:
            self.result.add_error(f"{parent}.{field}", "Required field missing")
            return False
        return True

    def _validate_namespaces(self, namespaces: Dict[str, Any]) -> Set[str]:
        """Validate namespace definitions."""
        defined_namespaces = set()

        for ns_name, ns_data in namespaces.items():
            defined_namespaces.add(ns_name)
            path = f"namespaces.{ns_name}"

            # Validate namespace name format
            if not self.ID_PATTERN.match(ns_name):
                self.result.add_warning(
                    path,
                    "Namespace name should be lowercase with hyphens",
                    ns_name,
                )

            if isinstance(ns_data, dict):
                # Validate type_hint
                type_hint = ns_data.get("type_hint")
                if type_hint and type_hint not in self.VALID_TYPE_HINTS:
                    self.result.add_error(
                        f"{path}.type_hint",
                        f"Invalid type_hint. Must be one of: {self.VALID_TYPE_HINTS}",
                        type_hint,
                    )

                # Validate children (hierarchical namespaces)
                children = ns_data.get("children", {})
                if children:
                    for child_name, child_data in children.items():
                        child_path = f"{path}.children.{child_name}"
                        if not self.ID_PATTERN.match(child_name):
                            self.result.add_warning(
                                child_path,
                                "Child namespace should be lowercase",
                                child_name,
                            )
                        if isinstance(child_data, dict):
                            child_type = child_data.get("type_hint")
                            if child_type:
                                if child_type not in self.VALID_TYPE_HINTS:
                                    self.result.add_error(
                                        f"{child_path}.type_hint",
                                        f"Invalid type_hint: {child_type}",
                                        child_type,
                                    )

        return defined_namespaces

    def _validate_traits(self, traits: Dict[str, Any]) -> Set[str]:
        """Validate trait definitions."""
        defined_traits = set()

        for trait_name, trait_data in traits.items():
            defined_traits.add(trait_name)
            path = f"traits.{trait_name}"

            if not isinstance(trait_data, dict):
                self.result.add_error(path, "Trait must be an object")
                continue

            # Validate fields or requires (trait should have one or the other)
            fields = trait_data.get("fields", {})
            requires = trait_data.get("requires", [])
            if not fields and not requires:
                self.result.add_warning(
                    path, "Trait has no fields or requires defined"
                )

            # Validate requires references
            for req in requires:
                if req not in ["citations", "code_refs", "temporal", "provenance"]:
                    self.result.add_warning(
                        f"{path}.requires",
                        f"Unknown required field: {req}",
                        req,
                    )

        return defined_traits

    def _validate_entity_types(
        self,
        entity_types: Any,
        defined_traits: Set[str],
    ) -> Set[str]:
        """Validate entity type definitions."""
        defined_entity_types = set()

        # Handle both list and dict formats
        if isinstance(entity_types, dict):
            entity_types = [{"name": k, **v} for k, v in entity_types.items()]

        for et_data in entity_types:
            if not isinstance(et_data, dict):
                continue

            name = et_data.get("name")
            if not name:
                self.result.add_error("entity_types", "Entity type missing name")
                continue

            defined_entity_types.add(name)
            path = f"entity_types.{name}"

            # Validate name format
            if not self.ID_PATTERN.match(name):
                self.result.add_warning(
                    f"{path}.name",
                    "Entity type name should be lowercase with hyphens",
                    name,
                )

            # Validate base type
            base = et_data.get("base")
            if not base:
                self.result.add_error(f"{path}.base", "Entity type must have a base type")
            elif base not in self.VALID_BASE_TYPES:
                self.result.add_error(
                    f"{path}.base",
                    f"Invalid base type. Must be one of: {self.VALID_BASE_TYPES}",
                    base,
                )

            # Validate trait references
            traits = et_data.get("traits", [])
            for trait in traits:
                if trait not in defined_traits:
                    self.result.add_error(
                        f"{path}.traits",
                        f"Reference to undefined trait: {trait}",
                        trait,
                    )

            # Validate schema
            schema = et_data.get("schema", {})
            self._validate_entity_schema(schema, path)

        return defined_entity_types

    def _validate_entity_schema(self, schema: Dict[str, Any], path: str) -> None:
        """Validate entity type schema."""
        if not schema:
            return

        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # Check required fields are in properties
        for req_field in required:
            if properties and req_field not in properties:
                self.result.add_warning(
                    f"{path}.schema.required",
                    f"Required field '{req_field}' not in properties",
                    req_field,
                )

        # Validate property definitions
        for prop_name, prop_def in properties.items():
            if not isinstance(prop_def, dict):
                continue

            prop_type = prop_def.get("type")
            if prop_type and prop_type not in [
                "string", "number", "integer", "boolean",
                "array", "object", "null"
            ]:
                self.result.add_warning(
                    f"{path}.schema.properties.{prop_name}.type",
                    f"Unknown property type: {prop_type}",
                    prop_type,
                )

    def _validate_relationships(
        self,
        relationships: Dict[str, Any],
        defined_entity_types: Set[str],
    ) -> None:
        """Validate relationship definitions."""
        for rel_name, rel_data in relationships.items():
            path = f"relationships.{rel_name}"

            if not isinstance(rel_data, dict):
                self.result.add_error(path, "Relationship must be an object")
                continue

            # Validate from_types
            from_types = rel_data.get("from", [])
            for from_type in from_types:
                if from_type not in defined_entity_types:
                    self.result.add_warning(
                        f"{path}.from",
                        f"Reference to undefined entity type: {from_type}",
                        from_type,
                    )

            # Validate to_types
            to_types = rel_data.get("to", [])
            for to_type in to_types:
                if to_type not in defined_entity_types:
                    self.result.add_warning(
                        f"{path}.to",
                        f"Reference to undefined entity type: {to_type}",
                        to_type,
                    )

    def _validate_discovery(
        self,
        discovery: Dict[str, Any],
        defined_entity_types: Set[str],
    ) -> None:
        """Validate discovery configuration."""
        if not discovery:
            return

        path = "discovery"

        # Validate confidence threshold
        threshold = discovery.get("confidence_threshold")
        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                self.result.add_error(
                    f"{path}.confidence_threshold",
                    "confidence_threshold must be a number",
                    threshold,
                )
            elif not 0 <= threshold <= 1:
                self.result.add_error(
                    f"{path}.confidence_threshold",
                    "confidence_threshold must be between 0 and 1",
                    threshold,
                )

        # Validate patterns
        patterns = discovery.get("patterns", [])
        for i, pattern in enumerate(patterns):
            pattern_path = f"{path}.patterns[{i}]"

            if not isinstance(pattern, dict):
                self.result.add_error(pattern_path, "Pattern must be an object")
                continue

            # Check pattern type
            has_content = "content_pattern" in pattern
            has_file = "file_pattern" in pattern
            has_generic = "pattern" in pattern

            if not (has_content or has_file or has_generic):
                self.result.add_error(
                    pattern_path,
                    "Pattern must have 'content_pattern', 'file_pattern', or 'pattern'",
                )

            # Validate regex patterns (content_pattern and pattern only)
            # file_pattern is a glob pattern, not regex
            regex_pattern = (
                pattern.get("content_pattern")
                or pattern.get("pattern")
            )
            if regex_pattern:
                try:
                    re.compile(regex_pattern)
                except re.error as e:
                    self.result.add_error(
                        pattern_path,
                        f"Invalid regex pattern: {e}",
                        regex_pattern,
                    )

            # Validate file_pattern is a reasonable glob
            file_pattern = pattern.get("file_pattern")
            if file_pattern:
                if not isinstance(file_pattern, str):
                    self.result.add_error(
                        pattern_path,
                        "file_pattern must be a string",
                        file_pattern,
                    )

            # Validate suggest_entity
            suggest_entity = pattern.get("suggest_entity")
            if not suggest_entity:
                self.result.add_error(
                    f"{pattern_path}.suggest_entity",
                    "Pattern must specify suggest_entity",
                )
            elif suggest_entity not in defined_entity_types:
                self.result.add_warning(
                    f"{pattern_path}.suggest_entity",
                    f"Reference to undefined entity type: {suggest_entity}",
                    suggest_entity,
                )


def validate_ontology_file(file_path: Path) -> OntologyValidationResult:
    """Convenience function to validate an ontology file."""
    validator = OntologyValidator()
    return validator.validate_file(file_path)


def main():
    """CLI interface for ontology validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Mnemonic Ontology Files")
    parser.add_argument("file", type=Path, help="Ontology YAML file to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = validate_ontology_file(args.file)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result)

    exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
