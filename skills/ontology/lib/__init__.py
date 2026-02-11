"""
Mnemonic Ontology Library

Core library modules for custom ontology support:
- ontology_loader: Load MIF ontologies from multiple sources with caching
- ontology_registry: Load, parse, and manage ontology definitions
- ontology_validator: Validate ontologies against meta-schema
- entity_resolver: Resolve entity references and maintain entity index
"""

from .entity_resolver import Entity, EntityIndexStats, EntityLink, EntityResolver
from .ontology_loader import LoadedOntology, OntologyLoader, get_loader, reset_loader
from .ontology_registry import (
    DiscoveryConfig,
    DiscoveryPattern,
    EntityType,
    Namespace,
    Ontology,
    OntologyRegistry,
    Relationship,
    Trait,
)
from .ontology_validator import OntologyValidationResult, OntologyValidator

__all__ = [
    # Loader
    "OntologyLoader",
    "LoadedOntology",
    "get_loader",
    "reset_loader",
    # Registry
    "OntologyRegistry",
    "Ontology",
    "Namespace",
    "EntityType",
    "Trait",
    "Relationship",
    "DiscoveryConfig",
    "DiscoveryPattern",
    # Validator
    "OntologyValidator",
    "OntologyValidationResult",
    # Resolver
    "EntityResolver",
    "Entity",
    "EntityLink",
    "EntityIndexStats",
]
