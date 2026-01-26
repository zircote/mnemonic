#!/usr/bin/env python3
"""
Fix Malformed Memory Files

Repairs common issues in memory files:
1. Missing frontmatter delimiter (---)
2. Missing required fields (id, type, namespace, title, created)
3. Invalid UUID format in id field

Usage:
    python scripts/fix_malformed_memories.py --dry-run  # Preview changes
    python scripts/fix_malformed_memories.py            # Execute fixes
    python scripts/fix_malformed_memories.py --delete   # Delete unfixable files
"""

import argparse
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


def detect_type_from_namespace(namespace: str) -> str:
    """Infer memory type from namespace."""
    if namespace.startswith("semantic") or namespace in ["decisions", "knowledge", "apis", "context", "learnings", "security"]:
        return "semantic"
    elif namespace.startswith("episodic") or namespace in ["blockers", "incidents", "sessions"]:
        return "episodic"
    elif namespace.startswith("procedural") or namespace in ["patterns", "runbooks", "migrations", "testing"]:
        return "procedural"
    return "semantic"


def detect_namespace_from_path(file_path: Path) -> str:
    """Extract namespace from file path."""
    parts = file_path.parts

    # Look for known namespace patterns
    for i, part in enumerate(parts):
        if part in ["semantic", "episodic", "procedural"]:
            if i + 1 < len(parts) and parts[i + 1] in ["decisions", "knowledge", "entities", "incidents", "sessions", "blockers", "runbooks", "patterns", "migrations"]:
                return f"{part}/{parts[i + 1]}"
            return part
        if part in ["decisions", "learnings", "patterns", "blockers", "apis", "context", "security", "testing"]:
            return part

    return "semantic/knowledge"


def is_valid_uuid(value: str) -> bool:
    """Check if string is valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def extract_frontmatter(content: str) -> tuple:
    """Extract frontmatter and body from content."""
    if not content.startswith("---"):
        return None, content

    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, content


def parse_yaml_frontmatter(frontmatter: str) -> dict:
    """Simple YAML frontmatter parser."""
    result = {}
    current_key = None
    current_list = None

    for line in frontmatter.split("\n"):
        if not line.strip():
            continue

        # Check for list item
        if line.startswith("  - "):
            if current_list is not None:
                current_list.append(line[4:].strip().strip('"').strip("'"))
            continue

        # Check for key: value
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if value:
                result[key] = value
            else:
                # Might be a list
                result[key] = []
                current_list = result[key]
            current_key = key

    return result


def generate_frontmatter(data: dict) -> str:
    """Generate YAML frontmatter from dict."""
    lines = ["---"]

    # Order fields properly
    field_order = ["id", "type", "namespace", "title", "created", "modified", "confidence", "tags"]

    for field in field_order:
        if field in data:
            value = data[field]
            if isinstance(value, list):
                lines.append(f"{field}:")
                for item in value:
                    lines.append(f"  - {item}")
            elif " " in str(value) or ":" in str(value):
                lines.append(f'{field}: "{value}"')
            else:
                lines.append(f"{field}: {value}")

    # Add any remaining fields
    for key, value in data.items():
        if key not in field_order:
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            elif " " in str(value) or ":" in str(value):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")

    lines.append("---")
    return "\n".join(lines)


def fix_memory_file(file_path: Path, dry_run: bool = True) -> dict:
    """Fix a malformed memory file. Returns dict with fix details."""
    result = {
        "path": str(file_path),
        "fixes": [],
        "errors": [],
        "fixed": False,
        "content": None,
    }

    try:
        content = file_path.read_text()
    except Exception as e:
        result["errors"].append(f"Cannot read file: {e}")
        return result

    # Check for frontmatter
    frontmatter, body = extract_frontmatter(content)

    if frontmatter is None:
        # Try to find frontmatter without proper start
        if "---" in content:
            # Find first --- and assume it ends frontmatter
            parts = content.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1].strip()
                body = parts[2] if len(parts) > 2 else ""
                result["fixes"].append("Added missing frontmatter start delimiter")
        else:
            # No frontmatter at all - create minimal one
            frontmatter = ""
            body = content
            result["fixes"].append("Created new frontmatter")

    # Parse frontmatter
    data = parse_yaml_frontmatter(frontmatter) if frontmatter else {}

    # Detect namespace from path
    namespace = detect_namespace_from_path(file_path)

    # Fix missing id
    if "id" not in data or not data["id"]:
        # Try to extract from filename
        filename = file_path.stem
        uuid_match = re.search(r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", filename)
        if uuid_match:
            data["id"] = uuid_match.group(1)
            result["fixes"].append(f"Extracted id from filename: {data['id']}")
        else:
            data["id"] = str(uuid.uuid4())
            result["fixes"].append(f"Generated new id: {data['id']}")
    elif not is_valid_uuid(data["id"]):
        old_id = data["id"]
        data["id"] = str(uuid.uuid4())
        result["fixes"].append(f"Replaced invalid id '{old_id}' with: {data['id']}")

    # Fix missing type
    if "type" not in data or not data["type"]:
        data["type"] = detect_type_from_namespace(namespace)
        result["fixes"].append(f"Added type: {data['type']}")

    # Fix missing namespace
    if "namespace" not in data or not data["namespace"]:
        data["namespace"] = namespace
        result["fixes"].append(f"Added namespace: {namespace}")

    # Fix missing title
    if "title" not in data or not data["title"]:
        # Try to extract from filename or first heading
        filename = file_path.stem
        # Remove UUID prefix if present
        title = re.sub(r"^[a-f0-9-]{36}-", "", filename)
        title = title.replace("-", " ").replace("_", " ").title()
        data["title"] = title
        result["fixes"].append(f"Generated title: {title}")

    # Fix missing created
    if "created" not in data or not data["created"]:
        # Use file modification time
        mtime = file_path.stat().st_mtime
        created = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        data["created"] = created
        result["fixes"].append(f"Added created from file mtime: {created}")

    # Add default confidence if missing
    if "confidence" not in data:
        data["confidence"] = "0.9"
        result["fixes"].append("Added default confidence: 0.9")

    if result["fixes"]:
        # Generate new content
        new_frontmatter = generate_frontmatter(data)
        new_content = f"{new_frontmatter}\n\n{body.strip()}\n"
        result["content"] = new_content
        result["fixed"] = True

        if not dry_run:
            try:
                file_path.write_text(new_content)
            except Exception as e:
                result["errors"].append(f"Cannot write file: {e}")
                result["fixed"] = False

    return result


def find_memory_files(base_paths: list) -> list:
    """Find all memory files in given paths."""
    files = []
    for base_path in base_paths:
        if base_path.exists():
            files.extend(base_path.rglob("*.memory.md"))
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Fix malformed memory files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete files that cannot be fixed",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Specific path to scan",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show details for each file",
    )

    args = parser.parse_args()

    # Paths to scan
    if args.path:
        paths = [args.path]
    else:
        paths = [
            Path.home() / ".claude" / "mnemonic",
            Path.cwd() / ".claude" / "mnemonic",
        ]

    print("Scanning for malformed memory files...")
    files = find_memory_files(paths)
    print(f"Found {len(files)} memory files\n")

    fixed_count = 0
    error_count = 0

    for file_path in files:
        result = fix_memory_file(file_path, dry_run=args.dry_run)

        if result["fixes"]:
            fixed_count += 1
            print(f"{'[DRY RUN] ' if args.dry_run else ''}Fixed: {file_path.name}")
            if args.verbose:
                for fix in result["fixes"]:
                    print(f"  - {fix}")

        if result["errors"]:
            error_count += 1
            print(f"Error: {file_path.name}")
            for err in result["errors"]:
                print(f"  ! {err}")

    print(f"\n{'=' * 50}")
    print(f"Total files scanned: {len(files)}")
    print(f"Files fixed: {fixed_count}")
    print(f"Files with errors: {error_count}")

    if args.dry_run and fixed_count > 0:
        print("\n(Dry run - no changes made)")
        print("Run without --dry-run to apply fixes")


if __name__ == "__main__":
    main()
