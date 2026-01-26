"""Pytest configuration for mnemonic tests."""

import sys
from pathlib import Path

# Add project root to Python path for lib imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
