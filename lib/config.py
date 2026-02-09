#!/usr/bin/env python3
"""
Mnemonic Configuration Module

Reads and writes the mnemonic configuration file at ~/.config/mnemonic/config.json.
This provides a single configurable memory store path instead of hardcoded ~/.claude/mnemonic.

Config Schema:
    {
        "version": "1.0",
        "memory_store_path": "~/.claude/mnemonic"
    }

The config location (~/.config/mnemonic/config.json) is XDG-compliant and fixed.
"""

import json
from pathlib import Path


# Fixed config location (XDG-compliant)
CONFIG_DIR = Path.home() / ".config" / "mnemonic"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default memory store path
DEFAULT_MEMORY_STORE_PATH = "~/.claude/mnemonic"

# Config schema version
CONFIG_VERSION = "1.0"


class MnemonicConfig:
    """Manages mnemonic configuration stored at ~/.config/mnemonic/config.json."""

    def __init__(self, memory_store_path: str = DEFAULT_MEMORY_STORE_PATH, version: str = CONFIG_VERSION):
        self.version = version
        self._memory_store_path = memory_store_path

    @property
    def memory_store_path(self) -> Path:
        """Return the resolved (tilde-expanded) memory store path."""
        return Path(self._memory_store_path).expanduser()

    @property
    def memory_store_path_raw(self) -> str:
        """Return the raw (unexpanded) memory store path as stored in config."""
        return self._memory_store_path

    @classmethod
    def load(cls) -> "MnemonicConfig":
        """Load config from ~/.config/mnemonic/config.json.

        Returns default config if file is missing or invalid.
        """
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                return cls(
                    memory_store_path=data.get("memory_store_path", DEFAULT_MEMORY_STORE_PATH),
                    version=data.get("version", CONFIG_VERSION),
                )
        except (json.JSONDecodeError, OSError, KeyError):
            pass
        return cls()

    def to_dict(self) -> dict:
        """Return config as a dictionary."""
        return {
            "version": self.version,
            "memory_store_path": self._memory_store_path,
        }

    def save(self) -> None:
        """Write config to ~/.config/mnemonic/config.json.

        Creates the config directory if it doesn't exist.
        """
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")


def get_memory_root() -> Path:
    """Return the resolved memory store path from config.

    This is the canonical way to get the memory root path.
    Loads config from disk (with default fallback) and returns
    the tilde-expanded Path.
    """
    return MnemonicConfig.load().memory_store_path
