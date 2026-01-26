"""
Mnemonic Library Package

Core utilities and shared libraries for the mnemonic memory system.
"""

# Make paths module easily importable
from .paths import (
    PathResolver,
    PathContext,
    PathScheme,
    Scope,
    get_default_resolver,
    get_memory_dir,
    get_search_paths,
    get_blackboard_dir,
)

__all__ = [
    # Core classes
    "PathResolver",
    "PathContext",
    "PathScheme",
    "Scope",
    # Convenience functions
    "get_default_resolver",
    "get_memory_dir",
    "get_search_paths",
    "get_blackboard_dir",
]

__version__ = "1.0.0"
