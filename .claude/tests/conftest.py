#!/usr/bin/env python3
"""
Pytest configuration and fixtures for mnemonic tests.

Provides isolated test environments that don't touch real memory files.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest


# ============================================================================
# Isolated Environment Fixtures
# ============================================================================


@pytest.fixture
def isolated_mnemonic_env(tmp_path, monkeypatch):
    """
    Create a completely isolated mnemonic environment for testing.

    This fixture:
    - Creates temp directories for user and project mnemonic
    - Patches HOME to redirect ~/.claude/mnemonic
    - Copies Claude CLI auth config so API calls work
    - Sets up proper directory structure
    - Cleans up automatically after test

    Usage:
        def test_something(isolated_mnemonic_env):
            env = isolated_mnemonic_env
            # env['user_mnemonic'] - path to isolated user mnemonic
            # env['project_mnemonic'] - path to isolated project mnemonic
            # env['home'] - path to fake home directory
    """
    # Create isolated directories
    fake_home = tmp_path / "home"
    fake_project = tmp_path / "project"

    user_mnemonic = fake_home / ".claude" / "mnemonic"
    project_mnemonic = fake_project / ".claude" / "mnemonic"

    # Create namespace structure
    namespaces = [
        "apis",
        "blockers",
        "context",
        "decisions",
        "learnings",
        "patterns",
        "security",
        "testing",
        "episodic",
    ]

    for ns in namespaces:
        (user_mnemonic / "testorg" / ns / "user").mkdir(parents=True)
        (user_mnemonic / "testorg" / ns / "project").mkdir(parents=True)
        (project_mnemonic / ns / "project").mkdir(parents=True)

    # Create blackboard directories
    (user_mnemonic / ".blackboard").mkdir(parents=True)
    (project_mnemonic / ".blackboard").mkdir(parents=True)

    # Copy Claude CLI auth config from real home to preserve authentication
    real_home = Path.home()
    real_claude = real_home / ".claude"
    fake_claude = fake_home / ".claude"

    # Copy essential auth files (not mnemonic directories)
    auth_files = [".credentials.json", "settings.json", "settings.local.json"]
    for auth_file in auth_files:
        src = real_claude / auth_file
        if src.exists():
            dst = fake_claude / auth_file
            shutil.copy2(src, dst)

    # Copy .claude.json if it exists at home level
    if (real_home / ".claude.json").exists():
        shutil.copy2(real_home / ".claude.json", fake_home / ".claude.json")

    # Patch HOME environment variable
    monkeypatch.setenv("HOME", str(fake_home))

    # Change to fake project directory
    original_cwd = os.getcwd()
    os.chdir(fake_project)

    yield {
        "home": fake_home,
        "user_mnemonic": user_mnemonic,
        "project_mnemonic": project_mnemonic,
        "project_root": fake_project,
        "org": "testorg",
    }

    # Cleanup: restore original directory
    os.chdir(original_cwd)


@pytest.fixture
def memory_factory(isolated_mnemonic_env):
    """
    Factory fixture for creating test memory files.

    Usage:
        def test_search(memory_factory):
            mem = memory_factory.create(
                namespace="decisions",
                title="Use Redis for caching",
                content="We decided to use Redis...",
                tags=["caching", "redis"]
            )
            # mem is Path to created file
    """
    env = isolated_mnemonic_env

    class MemoryFactory:
        def __init__(self):
            self.created_files = []

        def create(
            self,
            namespace: str = "context",
            title: str = "Test Memory",
            content: str = "Test content",
            memory_type: str = "semantic",
            tags: list = None,
            level: str = "user",  # "user" or "project"
            org: str = None,
        ) -> Path:
            """Create a test memory file and return its path."""
            memory_id = str(uuid4())
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            slug = self._slugify(title)

            org = org or env["org"]
            tags = tags or []

            # Determine path based on level
            if level == "user":
                base = env["user_mnemonic"] / org / namespace / "user"
            else:
                base = env["project_mnemonic"] / namespace / "project"

            base.mkdir(parents=True, exist_ok=True)

            filename = f"{slug}.memory.md"
            filepath = base / filename

            # Create memory content
            memory_content = f"""---
id: {memory_id}
title: "{title}"
type: {memory_type}
namespace: {namespace}/{"user" if level == "user" else "project"}
created: {timestamp}
modified: {timestamp}
tags: {json.dumps(tags)}
temporal:
  valid_from: {timestamp}
  recorded_at: {timestamp}
provenance:
  source_type: test
  agent: pytest
  confidence: 1.0
---

# {title}

{content}
"""
            filepath.write_text(memory_content)
            self.created_files.append(filepath)

            return filepath

        def create_many(self, specs: list) -> list:
            """Create multiple memories from a list of specs."""
            return [self.create(**spec) for spec in specs]

        def _slugify(self, text: str) -> str:
            """Convert text to slug format."""
            import re

            slug = text.lower()
            slug = re.sub(r"[^a-z0-9]+", "-", slug)
            slug = re.sub(r"-+", "-", slug)
            return slug[:50].strip("-")

    return MemoryFactory()


@pytest.fixture
def blackboard_factory(isolated_mnemonic_env):
    """
    Factory fixture for creating blackboard entries.

    Usage:
        def test_blackboard(blackboard_factory):
            blackboard_factory.write("session-notes", "Working on auth")
            content = blackboard_factory.read("session-notes")
    """
    env = isolated_mnemonic_env

    class BlackboardFactory:
        def __init__(self):
            self.base = env["user_mnemonic"] / ".blackboard"

        def write(self, key: str, content: str, ttl: int = 3600) -> Path:
            """Write a blackboard entry."""
            filepath = self.base / f"{key}.json"
            data = {
                "content": content,
                "created": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl,
            }
            filepath.write_text(json.dumps(data, indent=2))
            return filepath

        def read(self, key: str) -> str | None:
            """Read a blackboard entry."""
            filepath = self.base / f"{key}.json"
            if not filepath.exists():
                return None
            data = json.loads(filepath.read_text())
            return data.get("content")

        def list_keys(self) -> list:
            """List all blackboard keys."""
            return [f.stem for f in self.base.glob("*.json")]

    return BlackboardFactory()


# ============================================================================
# Hook Testing Fixtures
# ============================================================================


@pytest.fixture
def hook_runner(isolated_mnemonic_env):
    """
    Fixture for running hooks with controlled environment.

    Usage:
        def test_hook(hook_runner):
            result = hook_runner.run("session_start.py")
            assert result["continue"] == True
    """
    import subprocess
    import sys

    project_root = Path(__file__).parent.parent.parent
    hooks_dir = project_root / "hooks"
    env = isolated_mnemonic_env

    class HookRunner:
        def run(
            self,
            hook_name: str,
            env_vars: dict = None,
            timeout: int = 30,
        ) -> dict:
            """Run a hook and return parsed JSON output."""
            hook_path = hooks_dir / hook_name

            if not hook_path.exists():
                raise FileNotFoundError(f"Hook not found: {hook_path}")

            # Build environment
            run_env = os.environ.copy()
            run_env["HOME"] = str(env["home"])

            if env_vars:
                run_env.update(env_vars)

            result = subprocess.run(
                [sys.executable, str(hook_path)],
                capture_output=True,
                text=True,
                env=run_env,
                timeout=timeout,
                cwd=str(env["project_root"]),
            )

            if result.returncode != 0:
                raise RuntimeError(f"Hook failed: {result.stderr}")

            return json.loads(result.stdout)

    return HookRunner()


# ============================================================================
# Search Testing Fixtures
# ============================================================================


@pytest.fixture
def memory_searcher(isolated_mnemonic_env):
    """
    Fixture for searching memories in isolated environment.

    Usage:
        def test_search(memory_factory, memory_searcher):
            memory_factory.create(title="JWT Auth", namespace="decisions")
            results = memory_searcher.search("JWT")
            assert len(results) == 1
    """
    import subprocess

    env = isolated_mnemonic_env

    class MemorySearcher:
        def search(
            self,
            query: str,
            namespace: str = None,
            case_insensitive: bool = True,
        ) -> list:
            """Search for memories matching query."""
            # Build rg command
            cmd = ["rg"]
            if case_insensitive:
                cmd.append("-i")
            cmd.extend(["-l", "--glob", "*.memory.md"])
            cmd.append(query)
            cmd.extend(
                [
                    str(env["user_mnemonic"]),
                    str(env["project_mnemonic"]),
                ]
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode == 1:  # No matches
                return []

            files = [Path(f) for f in result.stdout.strip().split("\n") if f]

            # Filter by namespace if specified
            if namespace:
                files = [f for f in files if f"/{namespace}/" in str(f)]

            return files

        def search_content(self, query: str) -> list:
            """Search and return file contents."""
            files = self.search(query)
            return [(f, f.read_text()) for f in files]

    return MemorySearcher()


# ============================================================================
# CLI Testing Fixtures
# ============================================================================


@pytest.fixture
def claude_cli(isolated_mnemonic_env):
    """
    Fixture for running Claude CLI in isolated environment.

    Usage:
        def test_capture(claude_cli):
            result = claude_cli.run("I decided to use PostgreSQL")
            assert "acknowledged" in result.lower()

    Note: Tests using this fixture will be skipped if Claude CLI
    authentication is not available in the isolated environment.
    Claude uses OAuth which cannot be copied to isolated HOME.
    """
    import subprocess

    env = isolated_mnemonic_env

    class ClaudeCLI:
        def __init__(self):
            self._auth_checked = False
            self._auth_available = False

        def _check_auth(self) -> bool:
            """Check if Claude auth works in isolated env."""
            if self._auth_checked:
                return self._auth_available

            run_env = os.environ.copy()
            run_env["HOME"] = str(env["home"])

            try:
                # Simple test to verify auth works
                result = subprocess.run(
                    ["claude", "-p", "Say 'ok' and nothing else"],
                    capture_output=True,
                    text=True,
                    env=run_env,
                    timeout=30,
                    cwd=str(env["project_root"]),
                )
                self._auth_checked = True
                # Check for auth errors in output
                if "Invalid API key" in result.stdout or "login" in result.stdout.lower():
                    self._auth_available = False
                else:
                    self._auth_available = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self._auth_checked = True
                self._auth_available = False

            return self._auth_available

        def run(
            self,
            prompt: str,
            timeout: int = 120,
        ) -> str:
            """Run Claude CLI with prompt and return response."""
            if not self._check_auth():
                pytest.skip("Claude CLI auth not available in isolated environment")

            run_env = os.environ.copy()
            run_env["HOME"] = str(env["home"])

            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                env=run_env,
                timeout=timeout,
                cwd=str(env["project_root"]),
            )

            if result.returncode != 0:
                # Include both stdout and stderr in error message
                error_msg = f"Claude CLI failed (exit code {result.returncode})"
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nSTDOUT: {result.stdout}"
                raise RuntimeError(error_msg)

            return result.stdout

        def is_available(self) -> bool:
            """Check if Claude CLI is installed."""
            try:
                subprocess.run(
                    ["claude", "--version"],
                    capture_output=True,
                    timeout=10,
                )
                return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return False

        def is_auth_available(self) -> bool:
            """Check if Claude auth works in isolated environment."""
            return self._check_auth()

    return ClaudeCLI()


# ============================================================================
# Markers for test categorization
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external deps)")
    config.addinivalue_line("markers", "integration: Integration tests (may use CLI)")
    config.addinivalue_line("markers", "slow: Slow tests (API calls, etc)")
