#!/usr/bin/env python3
"""
Functional test configuration for mnemonic.

Runs tests in the actual mnemonic project directory to ensure
CLAUDE.md is properly loaded. Uses unique test IDs for cleanup.
"""

import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest


# Project root is the mnemonic directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def get_mnemonic_paths():
    """Get mnemonic paths."""
    home = Path.home()
    return {
        "user_mnemonic": home / ".claude" / "mnemonic",
        "project_mnemonic": PROJECT_ROOT / ".claude" / "mnemonic",
    }


@pytest.fixture(scope="session")
def test_session_id():
    """Unique ID for this test session, used to identify and cleanup test memories."""
    return f"functest-{uuid4().hex[:8]}"


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_memories(test_session_id):
    """
    Cleanup any memories created during this test session.
    Runs after all tests complete.
    """
    yield

    # Cleanup: remove memories with test session ID
    paths = get_mnemonic_paths()
    for mnemonic_path in [paths["user_mnemonic"], paths["project_mnemonic"]]:
        if not mnemonic_path.exists():
            continue
        for memory_file in mnemonic_path.rglob("*.memory.md"):
            try:
                content = memory_file.read_text()
                if test_session_id in content:
                    memory_file.unlink()
            except (OSError, IOError):
                pass


@pytest.fixture
def claude_runner(test_session_id):
    """
    Run Claude CLI in the project directory.
    Uses --allowed-tools to permit memory creation.
    """
    class ClaudeRunner:
        def run(self, prompt: str, timeout: int = 120) -> str:
            """Run Claude and return response."""
            result = subprocess.run(
                [
                    "claude",
                    "--plugin-dir", str(PROJECT_ROOT),
                    "--allowed-tools", "Bash(cat:*) Bash(uuidgen:*) Bash(date:*) Bash(rg:*) Bash(mkdir:*) Write Skill",
                    "-p", prompt
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(PROJECT_ROOT),
            )

            if result.returncode != 0:
                if "Invalid API key" in result.stdout or "login" in result.stdout.lower():
                    pytest.skip("Claude CLI not authenticated")
                raise RuntimeError(
                    f"Claude CLI failed (exit {result.returncode}): "
                    f"{result.stderr or result.stdout}"
                )

            # Debug: print response
            print(f"\n[DEBUG] Claude response:\n{result.stdout[:1000]}\n")

            return result.stdout

    return ClaudeRunner()


@pytest.fixture
def memory_helper(test_session_id):
    """
    Helper for creating and finding test memories.
    All test memories include the session ID for cleanup.
    """
    paths = get_mnemonic_paths()
    user_mnemonic = paths["user_mnemonic"]

    # Determine the org from existing directories
    orgs = [d.name for d in user_mnemonic.iterdir() if d.is_dir() and not d.name.startswith(".")]
    default_org = orgs[0] if orgs else "zircote"

    class MemoryHelper:
        def create(
            self,
            namespace: str,
            title: str,
            content: str,
            unique_id: str = None,
            org: str = None,
        ) -> Path:
            """Create a test memory file with session ID for cleanup."""
            memory_id = str(uuid4())
            unique_id = unique_id or memory_id[:8]
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            slug = title.lower().replace(" ", "-")[:40]

            org = org or default_org
            # Scope is implicit from base path - no /user/ suffix needed
            memory_dir = user_mnemonic / org / namespace
            memory_dir.mkdir(parents=True, exist_ok=True)

            filepath = memory_dir / f"{memory_id}-{slug}.memory.md"

            # Include session ID in content for cleanup
            memory_content = f"""---
id: {memory_id}
title: "{title}"
type: semantic
namespace: {namespace}
created: {timestamp}
confidence: 0.9
tags: [test, {unique_id}, {test_session_id}]
---

# {title}

{content}

Test ID: {unique_id}
Session: {test_session_id}
"""
            filepath.write_text(memory_content)
            return filepath

        def find_recent(self, namespace: str = None, minutes: int = 5) -> list[Path]:
            """Find recently created memories."""
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            memories = []

            for mnemonic_path in [user_mnemonic, paths["project_mnemonic"]]:
                if not mnemonic_path.exists():
                    continue

                pattern = f"**/{namespace}/**/*.memory.md" if namespace else "**/*.memory.md"
                for path in mnemonic_path.glob(pattern):
                    try:
                        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                        if mtime > cutoff:
                            memories.append(path)
                    except (OSError, IOError):
                        continue

            return memories

        def find_with_content(self, text: str, namespace: str = None) -> list[Path]:
            """Find memories containing specific text."""
            memories = []

            for mnemonic_path in [user_mnemonic, paths["project_mnemonic"]]:
                if not mnemonic_path.exists():
                    continue

                pattern = f"**/{namespace}/**/*.memory.md" if namespace else "**/*.memory.md"
                for path in mnemonic_path.glob(pattern):
                    try:
                        if text in path.read_text():
                            memories.append(path)
                    except (OSError, IOError):
                        continue

            return memories

    return MemoryHelper()


@pytest.fixture
def test_mnemonic(test_session_id, memory_helper):
    """Provide test context."""
    return {
        "session_id": test_session_id,
        "project_root": PROJECT_ROOT,
    }


@pytest.fixture
def require_claude():
    """Skip if Claude CLI not available."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=10
        )
        if result.returncode != 0:
            pytest.skip("Claude CLI not available")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("Claude CLI not installed")
