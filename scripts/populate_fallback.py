#!/usr/bin/env python3
"""
Populate Fallback Ontologies

Copies ontology files from MIF submodule to the fallback directory.
Used for offline installations where git submodule is not available.

Usage:
    python scripts/populate_fallback.py
    python scripts/populate_fallback.py --check  # Verify fallback is populated
"""

import argparse
import shutil
import sys
from pathlib import Path


def get_paths():
    """Get source and destination paths."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    mif_path = project_root / "mif"
    fallback_path = project_root / "skills" / "ontology" / "fallback"

    return mif_path, fallback_path


def populate_fallback(mif_path: Path, fallback_path: Path) -> bool:
    """Copy ontology files from MIF to fallback."""
    if not mif_path.exists():
        print(f"Error: MIF submodule not found at {mif_path}")
        print("Run: git submodule update --init")
        return False

    # Create fallback directories
    fallback_ontologies = fallback_path / "ontologies"
    fallback_schema = fallback_path / "schema" / "ontology"

    fallback_ontologies.mkdir(parents=True, exist_ok=True)
    fallback_schema.mkdir(parents=True, exist_ok=True)

    copied = 0

    # Copy ontology files
    mif_ontologies = mif_path / "ontologies"
    if mif_ontologies.exists():
        for src_file in mif_ontologies.glob("*.ontology.yaml"):
            dst_file = fallback_ontologies / src_file.name
            shutil.copy2(src_file, dst_file)
            print(f"Copied: {src_file.name}")
            copied += 1

        # Copy examples
        examples_src = mif_ontologies / "examples"
        examples_dst = fallback_ontologies / "examples"
        if examples_src.exists():
            examples_dst.mkdir(exist_ok=True)
            for src_file in examples_src.glob("*.yaml"):
                dst_file = examples_dst / src_file.name
                shutil.copy2(src_file, dst_file)
                print(f"Copied: examples/{src_file.name}")
                copied += 1

    # Copy schema files
    mif_schema = mif_path / "schema" / "ontology"
    if mif_schema.exists():
        for src_file in mif_schema.glob("*"):
            if src_file.is_file():
                dst_file = fallback_schema / src_file.name
                shutil.copy2(src_file, dst_file)
                print(f"Copied: schema/{src_file.name}")
                copied += 1

    print(f"\nPopulated fallback with {copied} files")
    return True


def check_fallback(fallback_path: Path) -> bool:
    """Check if fallback is properly populated."""
    required_files = [
        fallback_path / "ontologies" / "mif-base.ontology.yaml",
        fallback_path / "schema" / "ontology" / "ontology.schema.json",
    ]

    missing = []
    for req in required_files:
        if not req.exists():
            missing.append(req)

    if missing:
        print("Missing fallback files:")
        for m in missing:
            print(f"  - {m}")
        return False

    print("Fallback is properly populated")
    return True


def main():
    parser = argparse.ArgumentParser(description="Populate fallback ontologies")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if fallback is populated",
    )

    args = parser.parse_args()
    mif_path, fallback_path = get_paths()

    if args.check:
        success = check_fallback(fallback_path)
    else:
        success = populate_fallback(mif_path, fallback_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
