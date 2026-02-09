#!/usr/bin/env python3
"""
Mnemonic Memory Reader

Shared helper for reading memory file summaries and metadata.
Used by hooks to inject actual memory content instead of bare file paths.
"""

import re
from pathlib import Path
from typing import Optional


def get_memory_summary(path: str, max_summary: int = 300) -> dict:
    """Read a memory file and extract title + summary.

    Args:
        path: Absolute or relative path to a .memory.md file.
        max_summary: Maximum characters for the summary text.

    Returns:
        dict with keys: title (str), summary (str).
        Falls back to filename stem if parsing fails.
    """
    try:
        p = Path(path)
        if not p.exists():
            return {"title": p.stem, "summary": ""}

        content = p.read_bytes()[:1500].decode("utf-8", errors="replace")

        # Extract title from YAML frontmatter
        title = p.stem
        title_match = re.search(r"title:\s*[\"']?([^\"'\n]+)", content)
        if title_match:
            title = title_match.group(1).strip()

        # Extract summary: first non-frontmatter paragraph
        summary = ""
        in_frontmatter = False
        past_frontmatter = False
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    past_frontmatter = True
                    in_frontmatter = False
                continue
            if past_frontmatter and stripped and not stripped.startswith("#"):
                summary = stripped
                break

        if len(summary) > max_summary:
            summary = summary[: max_summary - 3] + "..."

        return {"title": title, "summary": summary}
    except Exception:
        return {"title": Path(path).stem, "summary": ""}


def get_memory_metadata(path: str, max_summary: int = 300) -> Optional[dict]:
    """Read a memory file and extract full metadata including relationships.

    Args:
        path: Absolute or relative path to a .memory.md file.
        max_summary: Maximum characters for the summary text.

    Returns:
        dict with keys: id, title, namespace, tags, relationships, summary, path.
        Returns None if file doesn't exist or can't be read.
    """
    try:
        p = Path(path)
        if not p.exists():
            return None

        # Read first 2000 bytes (enough for frontmatter + first paragraph)
        content = p.read_bytes()[:2000].decode("utf-8", errors="replace")

        # Initialize metadata with defaults
        metadata = {
            "id": None,
            "title": p.stem,
            "namespace": None,
            "tags": [],
            "relationships": [],
            "summary": "",
            "path": str(p.absolute()),
        }

        # Parse frontmatter
        in_frontmatter = False
        past_frontmatter = False
        frontmatter_lines = []
        content_lines = []

        for line in content.split("\n"):
            stripped = line.strip()
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    past_frontmatter = True
                    in_frontmatter = False
                continue

            if in_frontmatter:
                frontmatter_lines.append(line)
            elif past_frontmatter:
                content_lines.append(line)

        # Extract simple key-value fields from frontmatter
        frontmatter_text = "\n".join(frontmatter_lines)

        # Extract id
        id_match = re.search(r"^id:\s*([a-f0-9-]+)", frontmatter_text, re.MULTILINE)
        if id_match:
            metadata["id"] = id_match.group(1).strip()

        # Extract title
        title_match = re.search(r"^title:\s*[\"']?([^\"'\n]+)", frontmatter_text, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Extract namespace
        namespace_match = re.search(r"^namespace:\s*([^\n]+)", frontmatter_text, re.MULTILINE)
        if namespace_match:
            metadata["namespace"] = namespace_match.group(1).strip()

        # Extract tags (simple list parsing)
        tags_match = re.search(r"^tags:\s*\[([^\]]+)\]", frontmatter_text, re.MULTILINE)
        if tags_match:
            tags_str = tags_match.group(1)
            # Parse comma-separated tags, removing quotes
            metadata["tags"] = [tag.strip().strip('"').strip("'") for tag in tags_str.split(",") if tag.strip()]
        else:
            # Try multi-line YAML list format
            tags_section = re.search(r"^tags:\s*\n((?:  - .+\n?)+)", frontmatter_text, re.MULTILINE)
            if tags_section:
                tag_lines = tags_section.group(1).strip().split("\n")
                metadata["tags"] = [
                    line.strip().lstrip("- ").strip('"').strip("'") for line in tag_lines if line.strip()
                ]

        # Extract relationships (simplified YAML list parsing)
        # Format: relationships:\n  - type: X\n    target: Y\n    label: Z
        relationships = []
        rel_section = re.search(
            r"^relationships:\s*\n((?:  - (?:type|target|label):.+\n?)+)",
            frontmatter_text,
            re.MULTILINE,
        )
        if rel_section:
            rel_text = rel_section.group(1)
            # Split by "  - " to get individual relationship blocks
            rel_blocks = re.split(r"\n  - ", "\n" + rel_text)
            for block in rel_blocks:
                if not block.strip():
                    continue
                rel = {}
                type_match = re.search(r"type:\s*([^\n]+)", block)
                target_match = re.search(r"target:\s*([a-f0-9-]+)", block)
                label_match = re.search(r"label:\s*[\"']?([^\"'\n]+)", block)

                if type_match:
                    rel["type"] = type_match.group(1).strip()
                if target_match:
                    rel["target"] = target_match.group(1).strip()
                if label_match:
                    rel["label"] = label_match.group(1).strip()

                if rel.get("type") and rel.get("target"):
                    relationships.append(rel)

        metadata["relationships"] = relationships

        # Extract summary: first non-frontmatter, non-heading paragraph
        for line in content_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                metadata["summary"] = stripped
                break

        if len(metadata["summary"]) > max_summary:
            metadata["summary"] = metadata["summary"][: max_summary - 3] + "..."

        return metadata
    except Exception:
        return None
