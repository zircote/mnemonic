"""
Mnemonic Integration Library.

This module provides tools for integrating mnemonic memory protocol
into Claude Code plugins.
"""

from .frontmatter_updater import FrontmatterUpdater
from .integrator import IntegrationReport, IntegrationResult, Integrator
from .marker_parser import MarkerParser
from .template_validator import TemplateValidator, ValidationResult

__all__ = [
    "Integrator",
    "IntegrationResult",
    "IntegrationReport",
    "MarkerParser",
    "TemplateValidator",
    "ValidationResult",
    "FrontmatterUpdater",
]
