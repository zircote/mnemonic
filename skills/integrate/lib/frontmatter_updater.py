#!/usr/bin/env python3
"""
Frontmatter Updater for Mnemonic Integration

Updates YAML frontmatter in markdown files to add required tools.
"""

import re
from typing import List, Optional, Tuple

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedSeq
    HAS_RUAMEL = True
except ImportError:
    HAS_RUAMEL = False

try:
    import yaml as pyyaml
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False

# Build tuple of YAML error types for specific exception handling
_yaml_errors = []
if HAS_RUAMEL:
    from ruamel.yaml import YAMLError as RuamelYAMLError
    _yaml_errors.append(RuamelYAMLError)
if HAS_PYYAML:
    _yaml_errors.append(pyyaml.YAMLError)
YAML_ERRORS = tuple(_yaml_errors) if _yaml_errors else (Exception,)


class FrontmatterUpdater:
    """Updates YAML frontmatter in markdown files."""

    # Tools required for mnemonic operations
    REQUIRED_TOOLS = ["Bash", "Glob", "Grep", "Read", "Write"]

    # Regex to match YAML frontmatter (newline after closing --- is optional)
    FRONTMATTER_PATTERN = re.compile(
        r"^(---\s*\n)(.*?)(---\s*\n?)",
        re.DOTALL,
    )

    def __init__(self):
        if HAS_RUAMEL:
            self.yaml = YAML()
            self.yaml.preserve_quotes = True
            self.yaml.default_flow_style = False
        else:
            self.yaml = None

    def has_frontmatter(self, content: str) -> bool:
        """Check if content has YAML frontmatter.

        Args:
            content: File content

        Returns:
            True if frontmatter exists
        """
        return bool(self.FRONTMATTER_PATTERN.match(content))

    def extract_frontmatter(self, content: str) -> Optional[Tuple[str, str, str]]:
        """Extract frontmatter from content.

        Args:
            content: File content

        Returns:
            Tuple of (before, frontmatter, after) or None
        """
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            return None

        start_marker = match.group(1)
        frontmatter_content = match.group(2)
        end_marker = match.group(3)
        rest = content[match.end():]

        return (start_marker + frontmatter_content + end_marker, frontmatter_content, rest)

    def get_allowed_tools(self, content: str) -> List[str]:
        """Get current allowed-tools from frontmatter.

        Args:
            content: File content

        Returns:
            List of current tools, empty if not found
        """
        extracted = self.extract_frontmatter(content)
        if not extracted:
            return []

        _, fm_content, _ = extracted

        try:
            if HAS_RUAMEL:
                from io import StringIO
                data = self.yaml.load(StringIO(fm_content))
            elif HAS_PYYAML:
                data = pyyaml.safe_load(fm_content)
            else:
                return []

            if data and "allowed-tools" in data:
                return list(data["allowed-tools"])
        except YAML_ERRORS:
            pass

        return []

    def has_tool(self, content: str, tool: str) -> bool:
        """Check if tool is in allowed-tools.

        Args:
            content: File content
            tool: Tool name to check

        Returns:
            True if tool is present
        """
        return tool in self.get_allowed_tools(content)

    def has_all_required_tools(self, content: str) -> bool:
        """Check if all required mnemonic tools are present.

        Args:
            content: File content

        Returns:
            True if all required tools are present
        """
        current = set(self.get_allowed_tools(content))
        required = set(self.REQUIRED_TOOLS)
        return required.issubset(current)

    def get_missing_tools(self, content: str) -> List[str]:
        """Get list of missing required tools.

        Args:
            content: File content

        Returns:
            List of tools that need to be added
        """
        current = set(self.get_allowed_tools(content))
        required = set(self.REQUIRED_TOOLS)
        return sorted(required - current)

    def add_tools(self, content: str, tools: Optional[List[str]] = None) -> str:
        """Add tools to allowed-tools in frontmatter.

        Args:
            content: File content
            tools: Tools to add (defaults to REQUIRED_TOOLS)

        Returns:
            Updated content with tools added
        """
        if tools is None:
            tools = self.REQUIRED_TOOLS

        extracted = self.extract_frontmatter(content)
        if not extracted:
            return content

        full_fm, fm_content, rest = extracted

        try:
            if HAS_RUAMEL:
                from io import StringIO
                data = self.yaml.load(StringIO(fm_content))
            elif HAS_PYYAML:
                data = pyyaml.safe_load(fm_content)
            else:
                # Fallback to regex-based update
                return self._add_tools_regex(content, tools)

            if data is None:
                data = {}

            # Get or create allowed-tools list
            if "allowed-tools" not in data:
                data["allowed-tools"] = []

            current_tools = data["allowed-tools"]

            # Handle case where allowed-tools is a string instead of a list
            if isinstance(current_tools, str):
                current_tools = [current_tools] if current_tools else []
                data["allowed-tools"] = current_tools

            if HAS_RUAMEL and not isinstance(current_tools, CommentedSeq):
                current_tools = CommentedSeq(current_tools)
                data["allowed-tools"] = current_tools

            # Add missing tools
            for tool in tools:
                if tool not in current_tools:
                    current_tools.append(tool)

            # Serialize back
            if HAS_RUAMEL:
                from io import StringIO
                stream = StringIO()
                self.yaml.dump(data, stream)
                new_fm = stream.getvalue()
            else:
                new_fm = pyyaml.dump(data, default_flow_style=False)

            return f"---\n{new_fm}---\n{rest}"

        except YAML_ERRORS:
            # Fallback to regex-based update
            return self._add_tools_regex(content, tools)

    def _add_tools_regex(self, content: str, tools: List[str]) -> str:
        """Fallback regex-based tool addition.

        Args:
            content: File content
            tools: Tools to add

        Returns:
            Updated content
        """
        # Find allowed-tools section
        pattern = r"(allowed-tools:\s*\n)((?:\s+-\s+\w+\n)*)"
        match = re.search(pattern, content)

        if match:
            existing = match.group(2)
            existing_tools = re.findall(r"-\s+(\w+)", existing)

            # Build new list
            all_tools = list(existing_tools)
            for tool in tools:
                if tool not in all_tools:
                    all_tools.append(tool)

            # Format new section
            new_section = match.group(1)
            for tool in all_tools:
                new_section += f"  - {tool}\n"

            return content[:match.start()] + new_section + content[match.end():]

        # No allowed-tools found, try to add after other frontmatter fields
        if self.has_frontmatter(content):
            # Add before closing ---
            insert_text = "allowed-tools:\n"
            for tool in tools:
                insert_text += f"  - {tool}\n"

            return re.sub(
                r"(^---\s*\n.*?)(---\s*\n)",
                rf"\1{insert_text}\2",
                content,
                flags=re.DOTALL,
            )

        return content


def main():
    """CLI for frontmatter updates."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Mnemonic Frontmatter Updater")
    parser.add_argument("file", help="File to update")
    parser.add_argument("--check", action="store_true", help="Check if tools are present")
    parser.add_argument("--add", action="store_true", help="Add missing tools")
    parser.add_argument("--list", action="store_true", help="List current tools")

    args = parser.parse_args()

    try:
        with open(args.file) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        print("Suggestion: Check the file path or ensure the file exists.", file=sys.stderr)
        sys.exit(1)

    updater = FrontmatterUpdater()

    if args.list:
        tools = updater.get_allowed_tools(content)
        print("Current allowed-tools:")
        for tool in tools:
            print(f"  - {tool}")
        missing = updater.get_missing_tools(content)
        if missing:
            print("\nMissing required tools:")
            for tool in missing:
                print(f"  - {tool}")

    elif args.check:
        if updater.has_all_required_tools(content):
            print("All required tools present")
            sys.exit(0)
        else:
            missing = updater.get_missing_tools(content)
            print(f"Missing tools: {', '.join(missing)}")
            sys.exit(1)

    elif args.add:
        if updater.has_all_required_tools(content):
            print("All tools already present")
        else:
            updated = updater.add_tools(content)
            with open(args.file, "w") as f:
                f.write(updated)
            print(f"Added tools to {args.file}")


if __name__ == "__main__":
    main()
