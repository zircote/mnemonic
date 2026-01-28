#!/usr/bin/env python3
"""
Template Validator for Mnemonic Integration

Validates and verifies mnemonic protocol templates.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:
    from .marker_parser import MarkerParser
except ImportError:
    from marker_parser import MarkerParser


@dataclass
class ValidationResult:
    """Result of template validation."""

    valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self) -> bool:
        return self.valid


class TemplateValidator:
    """Validator for mnemonic protocol templates."""

    # Characters/patterns that could indicate executable code
    EXECUTABLE_PATTERNS = [
        ("$(", "Shell command substitution"),
        ("eval ", "Eval statement"),
        ("subprocess", "Subprocess usage"),
    ]

    def __init__(self):
        self.marker_parser = MarkerParser()

    def validate_template(self, template_path: Path) -> ValidationResult:
        """Validate template file structure and content.

        Args:
            template_path: Path to template file

        Returns:
            ValidationResult with validity status and any issues
        """
        errors = []
        warnings = []

        # Check file exists
        if not template_path.exists():
            return ValidationResult(
                valid=False,
                errors=[f"Template not found: {template_path}"],
                warnings=[],
            )

        try:
            content = template_path.read_text()
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Cannot read template: {e}"],
                warnings=[],
            )

        # Check for markers
        if not self.marker_parser.has_markers(content):
            errors.append("Template missing sentinel markers")

        # Validate markers are properly paired
        valid, error = self.marker_parser.has_valid_markers(content)
        if not valid:
            errors.append(f"Invalid markers: {error}")

        # Check template is not empty
        extracted = self.marker_parser.extract_between(content)
        if extracted is not None and not extracted.strip():
            errors.append("Template content between markers is empty")

        # Check for suspicious executable patterns (outside code blocks)
        content_outside_blocks = self._remove_code_blocks(content)
        for pattern, description in self.EXECUTABLE_PATTERNS:
            if pattern in content_outside_blocks:
                warnings.append(f"Possible executable code detected: {description}. Pattern: '{pattern}'")

        # Check template is reasonably sized
        if len(content) > 10000:
            warnings.append("Template is unusually large (>10KB)")

        if len(content) < 50:
            warnings.append("Template is unusually small (<50 bytes)")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def verify_insertion(self, file_content: str, template_content: str) -> bool:
        """Verify that inserted content matches template exactly.

        Args:
            file_content: Content of file after insertion
            template_content: Expected template content

        Returns:
            True if insertion matches template
        """
        # Extract what was inserted
        extracted = self.marker_parser.extract_between(file_content)
        if extracted is None:
            return False

        # Extract expected content from template
        expected = self.marker_parser.extract_between(template_content)
        if expected is None:
            # Template might not have markers (just the inner content)
            expected = template_content

        # Normalize whitespace for comparison
        extracted_normalized = extracted.strip()
        expected_normalized = expected.strip()

        return extracted_normalized == expected_normalized

    def get_template_content(self, template_path: Path) -> Optional[str]:
        """Read and return template content.

        Args:
            template_path: Path to template file

        Returns:
            Template content or None if invalid
        """
        result = self.validate_template(template_path)
        if not result.valid:
            return None

        return template_path.read_text()

    def _remove_code_blocks(self, content: str) -> str:
        """Remove markdown code blocks for executable pattern detection.

        Args:
            content: Markdown content

        Returns:
            Content with code blocks removed
        """
        import re

        # Remove fenced code blocks
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        # Remove inline code
        content = re.sub(r"`[^`]+`", "", content)
        return content


def main():
    """CLI for template validation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Mnemonic Template Validator")
    parser.add_argument("template", help="Path to template file")
    parser.add_argument("--verify-against", help="Verify template against file content")

    args = parser.parse_args()

    validator = TemplateValidator()
    template_path = Path(args.template)

    result = validator.validate_template(template_path)

    print(f"Valid: {result.valid}")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if args.verify_against:
        try:
            file_content = Path(args.verify_against).read_text()
            template_content = template_path.read_text()
            matches = validator.verify_insertion(file_content, template_content)
            print(f"\nInsertion matches template: {matches}")
        except Exception as e:
            print(f"\nVerification failed: {e}")
            sys.exit(1)

    sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
