"""
Mnemonic Ontology Library

Core library modules for custom ontology support:
- ontology_registry: Load, parse, and manage ontology definitions
- ontology_validator: Validate ontologies against meta-schema
- entity_resolver: Resolve entity references and maintain entity index
"""

from .ontology_registry import (
    OntologyRegistry,
    Ontology,
    Namespace,
    EntityType,
    Trait,
    Relationship,
    DiscoveryConfig,
)
from .ontology_validator import OntologyValidator, OntologyValidationResult
from .entity_resolver import EntityResolver, Entity, EntityLink

__all__ = [
    # Registry
    "OntologyRegistry",
    "Ontology",
    "Namespace",
    "EntityType",
    "Trait",
    "Relationship",
    "DiscoveryConfig",
    # Validator
    "OntologyValidator",
    "OntologyValidationResult",
    # Resolver
    "EntityResolver",
    "Entity",
    "EntityLink",
]
