#!/usr/bin/env python3
"""
Integration tests for mnemonic plugin using Claude CLI.

These tests run Claude in non-interactive mode (-p) and verify:
1. Memory files are created when expected
2. Responses reference existing memories
3. Silent operation (no announcements)

IMPORTANT: These tests make actual API calls and create real memory files.
Run with caution and clean up test data afterward.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Test configuration
CLAUDE_CMD = "claude"
TEST_TIMEOUT = 120  # seconds
MEMORY_BASE = Path.home() / ".claude" / "mnemonic"
PROJECT_MEMORY = Path.cwd() / ".claude" / "mnemonic"

# Test marker to identify test-created memories
TEST_MARKER = "MNEMONIC_TEST_"


def run_claude(prompt: str, timeout: int = TEST_TIMEOUT) -> tuple[int, str, str]:
    """Run Claude CLI with a prompt and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [CLAUDE_CMD, "-p", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(Path.cwd()),
    )
    return result.returncode, result.stdout, result.stderr


def get_recent_memories(namespace: str, minutes: int = 5) -> list[Path]:
    """Get memory files created in the last N minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    memories = []

    for base in [MEMORY_BASE, PROJECT_MEMORY]:
        pattern = f"**/{namespace}/**/*.memory.md"
        for path in base.glob(pattern):
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime > cutoff:
                memories.append(path)

    return memories


def create_test_memory(namespace: str, title: str, content: str) -> Path:
    """Create a test memory file for setup."""
    memory_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:40]

    # Find org directory
    org_dirs = list(MEMORY_BASE.glob("*/"))
    org = org_dirs[0].name if org_dirs else "default"

    memory_dir = MEMORY_BASE / org / namespace / "user"
    memory_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{TEST_MARKER}{slug}.memory.md"
    memory_path = memory_dir / filename

    memory_content = f"""---
id: {memory_id}
title: "{title}"
type: semantic
created: {timestamp}
tags:
  - test
---

# {title}

{content}
"""
    memory_path.write_text(memory_content)
    return memory_path


def cleanup_test_memories():
    """Remove all test-created memories."""
    for base in [MEMORY_BASE, PROJECT_MEMORY]:
        for path in base.rglob(f"*{TEST_MARKER}*.memory.md"):
            path.unlink()


class TestCaptureIntegration(unittest.TestCase):
    """Test that Claude captures memories automatically."""

    @classmethod
    def setUpClass(cls):
        """Verify Claude CLI is available."""
        try:
            result = subprocess.run(
                [CLAUDE_CMD, "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise unittest.SkipTest("Claude CLI not available")
        except FileNotFoundError:
            raise unittest.SkipTest("Claude CLI not installed")

    def setUp(self):
        """Record current time for memory detection."""
        self.start_time = datetime.now(timezone.utc)
        time.sleep(1)  # Ensure time separation

    def tearDown(self):
        """Clean up test memories."""
        cleanup_test_memories()

    def test_capture_decision(self):
        """Test that decisions are captured automatically."""
        unique_id = str(uuid4())[:8]
        prompt = f"I've decided we should use Redis-{unique_id} for caching in this project. Just acknowledge briefly."

        returncode, stdout, stderr = run_claude(prompt)

        self.assertEqual(returncode, 0, f"Claude failed: {stderr}")

        # Wait for file system
        time.sleep(2)

        # Check for new memory
        memories = get_recent_memories("decisions", minutes=2)
        matching = [m for m in memories if unique_id in m.read_text()]

        self.assertGreater(
            len(matching),
            0,
            f"No decision memory found for {unique_id}. Recent memories: {memories}",
        )

    def test_capture_learning(self):
        """Test that learnings are captured automatically."""
        unique_id = str(uuid4())[:8]
        prompt = f"I learned that the API-{unique_id} has a rate limit of 100 requests per minute. Just acknowledge."

        returncode, stdout, stderr = run_claude(prompt)

        self.assertEqual(returncode, 0, f"Claude failed: {stderr}")
        time.sleep(2)

        memories = get_recent_memories("learnings", minutes=2)
        matching = [m for m in memories if unique_id in m.read_text()]

        self.assertGreater(len(matching), 0, f"No learning memory found for {unique_id}")

    def test_capture_silent(self):
        """Test that capture happens silently without announcements."""
        unique_id = str(uuid4())[:8]
        prompt = f"Decision: use PostgreSQL-{unique_id} for the database. Acknowledge briefly."

        returncode, stdout, stderr = run_claude(prompt)

        self.assertEqual(returncode, 0, f"Claude failed: {stderr}")

        # Response should NOT mention capturing
        response_lower = stdout.lower()
        self.assertNotIn("capturing", response_lower)
        self.assertNotIn("saving to memory", response_lower)
        self.assertNotIn("mnemonic", response_lower)
        self.assertNotIn("i'll remember", response_lower)


class TestRecallIntegration(unittest.TestCase):
    """Test that Claude recalls existing memories."""

    @classmethod
    def setUpClass(cls):
        """Verify Claude CLI is available."""
        try:
            result = subprocess.run(
                [CLAUDE_CMD, "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise unittest.SkipTest("Claude CLI not available")
        except FileNotFoundError:
            raise unittest.SkipTest("Claude CLI not installed")

    def tearDown(self):
        """Clean up test memories."""
        cleanup_test_memories()

    def test_recall_existing_memory(self):
        """Test that Claude finds and uses existing memories."""
        unique_id = str(uuid4())[:8]

        # Create a test memory first
        memory_path = create_test_memory(
            namespace="decisions",
            title=f"Use Express-{unique_id} for API",
            content=f"We decided to use Express.js framework with ID {unique_id} for building the REST API.",
        )

        try:
            # Ask about the topic
            prompt = (
                f"What framework should I use for the API? Look for any existing decisions about Express-{unique_id}."
            )

            returncode, stdout, stderr = run_claude(prompt)

            self.assertEqual(returncode, 0, f"Claude failed: {stderr}")

            # Response should reference Express or the memory
            response_lower = stdout.lower()
            found = "express" in response_lower or unique_id.lower() in response_lower

            self.assertTrue(
                found,
                f"Response should reference existing Express decision. Response: {stdout[:500]}",
            )

        finally:
            if memory_path.exists():
                memory_path.unlink()


class TestMemorySearch(unittest.TestCase):
    """Test memory search functionality."""

    def test_search_both_paths(self):
        """Test that search includes both user and project memories."""
        # Verify the search command searches both paths
        search_cmd = 'rg -i "test" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" -l'

        result = subprocess.run(
            ["bash", "-c", search_cmd],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Command should work (even if no results)
        self.assertIn(result.returncode, [0, 1], f"Search command failed: {result.stderr}")


if __name__ == "__main__":
    # Run with verbosity
    unittest.main(verbosity=2)
