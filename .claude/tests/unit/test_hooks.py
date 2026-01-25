#!/usr/bin/env python3
"""
Unit tests for mnemonic hooks.

Tests hook scripts by simulating their environment and verifying output.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Get paths
TESTS_DIR = Path(__file__).parent.parent
PROJECT_ROOT = TESTS_DIR.parent.parent
HOOKS_DIR = PROJECT_ROOT / "hooks"


class TestSessionStartHook(unittest.TestCase):
    """Test session_start.py hook."""

    def setUp(self):
        self.hook_path = HOOKS_DIR / "session_start.py"
        self.assertTrue(self.hook_path.exists(), f"Hook not found: {self.hook_path}")

    def run_hook(self, env_vars=None):
        """Run the hook with given environment variables."""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        result = subprocess.run(
            [sys.executable, str(self.hook_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        return result

    def test_hook_returns_valid_json(self):
        """Hook should return valid JSON."""
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, f"Hook failed: {result.stderr}")

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"Invalid JSON output: {result.stdout}")

        # Must have required fields
        self.assertIn("continue", output)

    def test_hook_continues_session(self):
        """Hook should allow session to continue."""
        result = self.run_hook()
        output = json.loads(result.stdout)
        self.assertTrue(output.get("continue"), "Hook should continue session")

    def test_hook_provides_context(self):
        """Hook should provide mnemonic context."""
        result = self.run_hook()
        output = json.loads(result.stdout)

        # Should have additionalContext with mnemonic info
        hook_output = output.get("hookSpecificOutput", {})
        context = hook_output.get("additionalContext", "")

        # Context should mention mnemonic or memory
        self.assertTrue(
            "mnemonic" in context.lower() or "memory" in context.lower(),
            f"Context should mention mnemonic: {context[:200]}",
        )


class TestUserPromptSubmitHook(unittest.TestCase):
    """Test user_prompt_submit.py hook."""

    def setUp(self):
        self.hook_path = HOOKS_DIR / "user_prompt_submit.py"
        self.assertTrue(self.hook_path.exists(), f"Hook not found: {self.hook_path}")

    def run_hook(self, prompt="test prompt"):
        """Run the hook with given prompt."""
        env = os.environ.copy()
        env["CLAUDE_USER_PROMPT"] = prompt

        result = subprocess.run(
            [sys.executable, str(self.hook_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        return result

    def test_hook_returns_valid_json(self):
        """Hook should return valid JSON."""
        result = self.run_hook("Hello, Claude!")
        self.assertEqual(result.returncode, 0, f"Hook failed: {result.stderr}")

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"Invalid JSON output: {result.stdout}")

        self.assertIn("continue", output)

    def test_hook_continues_on_normal_prompt(self):
        """Hook should continue on normal prompts."""
        result = self.run_hook("Help me with Python code")
        output = json.loads(result.stdout)
        self.assertTrue(output.get("continue"))


class TestPostToolUseHook(unittest.TestCase):
    """Test post_tool_use.py hook."""

    def setUp(self):
        self.hook_path = HOOKS_DIR / "post_tool_use.py"
        self.assertTrue(self.hook_path.exists(), f"Hook not found: {self.hook_path}")

    def run_hook(self, tool_name="Read", tool_input=None, tool_output=None):
        """Run the hook with given tool context."""
        env = os.environ.copy()
        env["CLAUDE_TOOL_USE_NAME"] = tool_name
        if tool_input:
            env["CLAUDE_TOOL_INPUT"] = json.dumps(tool_input)
        if tool_output:
            env["CLAUDE_TOOL_RESULT"] = tool_output

        result = subprocess.run(
            [sys.executable, str(self.hook_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        return result

    def test_hook_returns_valid_json(self):
        """Hook should return valid JSON."""
        result = self.run_hook("Read", {"file_path": "/tmp/test.txt"})
        self.assertEqual(result.returncode, 0, f"Hook failed: {result.stderr}")

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"Invalid JSON output: {result.stdout}")

        self.assertIn("continue", output)


class TestStopHook(unittest.TestCase):
    """Test stop.py hook."""

    def setUp(self):
        self.hook_path = HOOKS_DIR / "stop.py"
        self.assertTrue(self.hook_path.exists(), f"Hook not found: {self.hook_path}")

    def run_hook(self, stop_reason="end_turn"):
        """Run the hook with given stop reason."""
        env = os.environ.copy()
        env["CLAUDE_STOP_REASON"] = stop_reason

        result = subprocess.run(
            [sys.executable, str(self.hook_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        return result

    def test_hook_returns_valid_json(self):
        """Hook should return valid JSON."""
        result = self.run_hook("end_turn")
        self.assertEqual(result.returncode, 0, f"Hook failed: {result.stderr}")

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail(f"Invalid JSON output: {result.stdout}")

        self.assertIn("continue", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
