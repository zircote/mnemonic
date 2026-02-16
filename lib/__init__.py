"""
Mnemonic Library Package

Core utilities and shared libraries for the mnemonic memory system.
"""

# Make paths module easily importable
from .memory_reader import (
    get_memory_metadata,
    get_memory_summary,
)
from .migrate_filenames import (
    is_migration_complete,
    migrate_all,
    migrate_file,
    migration_summary,
)
from .ontology import (
    get_fallback_content_patterns,
    get_fallback_file_patterns,
    get_ontology_file,
    get_ontology_info,
    load_content_patterns,
    load_file_patterns,
    load_ontology_data,
    load_ontology_namespaces,
    validate_memory_against_ontology,
)
from .paths import (
    PathContext,
    PathResolver,
    PathScheme,
    Scope,
    get_all_memory_roots_with_legacy,
    get_blackboard_dir,
    get_default_resolver,
    get_handoff_dir,
    get_memory_dir,
    get_search_paths,
    get_session_blackboard_dir,
    get_v2_resolver,
    migrate_blackboard_to_session_scoped,
)
from .relationships import (
    RECIPROCAL_TYPES,
    REL_DERIVED_FROM,
    REL_RELATES_TO,
    REL_SUPERSEDES,
    RELATIONSHIP_TYPES,
    add_bidirectional_relationship,
    add_relationship,
    get_all_valid_types,
    get_inverse,
    is_symmetric,
    is_valid_type,
    to_pascal,
    to_snake,
)
from .search import (
    SCORE_CONTENT_KEYWORD,
    SCORE_MIN_THRESHOLD,
    SCORE_NAMESPACE_EXACT,
    SCORE_NAMESPACE_TYPE,
    SCORE_TAG_OVERLAP,
    SCORE_TITLE_KEYWORD,
    detect_file_context,
    detect_namespace_for_file,
    extract_keywords_from_path,
    extract_topic,
    find_duplicates,
    find_memories_for_context,
    find_related_memories,
    find_related_memories_scored,
    infer_relationship_type,
    search_memories,
)

__all__ = [
    # Core classes
    "PathResolver",
    "PathContext",
    "PathScheme",
    "Scope",
    # Path convenience functions
    "get_default_resolver",
    "get_memory_dir",
    "get_search_paths",
    "get_blackboard_dir",
    "get_session_blackboard_dir",
    "get_handoff_dir",
    "get_v2_resolver",
    "get_all_memory_roots_with_legacy",
    "migrate_blackboard_to_session_scoped",
    # Ontology functions
    "get_ontology_file",
    "load_ontology_data",
    "load_file_patterns",
    "load_content_patterns",
    "load_ontology_namespaces",
    "get_fallback_file_patterns",
    "get_fallback_content_patterns",
    "get_ontology_info",
    "validate_memory_against_ontology",
    # Search functions
    "search_memories",
    "find_related_memories",
    "find_related_memories_scored",
    "find_memories_for_context",
    "find_duplicates",
    "detect_file_context",
    "detect_namespace_for_file",
    "extract_keywords_from_path",
    "extract_topic",
    "infer_relationship_type",
    # Relationship type constants
    "REL_RELATES_TO",
    "REL_SUPERSEDES",
    "REL_DERIVED_FROM",
    # Scoring weight constants
    "SCORE_NAMESPACE_TYPE",
    "SCORE_NAMESPACE_EXACT",
    "SCORE_TAG_OVERLAP",
    "SCORE_TITLE_KEYWORD",
    "SCORE_CONTENT_KEYWORD",
    "SCORE_MIN_THRESHOLD",
    # Memory reader functions
    "get_memory_summary",
    "get_memory_metadata",
    # Migration functions
    "migrate_all",
    "migrate_file",
    "is_migration_complete",
    "migration_summary",
    # Relationship type registry
    "RELATIONSHIP_TYPES",
    "RECIPROCAL_TYPES",
    # Relationship writer functions
    "add_relationship",
    "add_bidirectional_relationship",
    # Relationship type helpers
    "to_pascal",
    "to_snake",
    "get_inverse",
    "is_valid_type",
    "is_symmetric",
    "get_all_valid_types",
]

__version__ = "1.1.0"
