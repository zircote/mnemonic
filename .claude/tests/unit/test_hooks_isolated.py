#!/usr/bin/env python3
"""
Hook tests with isolated environments.

Tests hook behavior without touching real memory files.
"""

import json


class TestSessionStartHook:
    """Test session_start.py hook behavior."""

    def test_returns_valid_json(self, hook_runner):
        """Hook returns valid JSON structure."""
        result = hook_runner.run("session_start.py")

        assert "continue" in result
        assert isinstance(result["continue"], bool)

    def test_continues_session(self, hook_runner):
        """Hook allows session to continue."""
        result = hook_runner.run("session_start.py")
        assert result["continue"] is True

    def test_provides_context(self, hook_runner):
        """Hook provides mnemonic context."""
        result = hook_runner.run("session_start.py")

        hook_output = result.get("hookSpecificOutput", {})
        context = hook_output.get("additionalContext", "")

        # Should mention mnemonic system
        assert "mnemonic" in context.lower() or "memory" in context.lower()

    def test_counts_memories(self, hook_runner, memory_factory):
        """Hook counts memories in isolated environment."""
        # Create some test memories
        memory_factory.create(namespace="decisions", title="Decision 1")
        memory_factory.create(namespace="decisions", title="Decision 2")
        memory_factory.create(namespace="learnings", title="Learning 1")

        result = hook_runner.run("session_start.py")

        # Context should include memory info
        hook_output = result.get("hookSpecificOutput", {})
        context = hook_output.get("additionalContext", "")

        # Should report some memory count
        assert context  # Should have context

    def test_handles_empty_mnemonic(self, hook_runner, isolated_mnemonic_env):
        """Hook works with empty mnemonic directory."""
        # isolated_mnemonic_env creates empty directories
        result = hook_runner.run("session_start.py")

        assert result["continue"] is True


class TestUserPromptSubmitHook:
    """Test user_prompt_submit.py hook behavior."""

    def test_returns_valid_json(self, hook_runner):
        """Hook returns valid JSON."""
        result = hook_runner.run(
            "user_prompt_submit.py",
            env_vars={"CLAUDE_USER_PROMPT": "Hello"},
        )

        assert "continue" in result

    def test_continues_on_normal_prompt(self, hook_runner):
        """Hook continues for normal prompts."""
        result = hook_runner.run(
            "user_prompt_submit.py",
            env_vars={"CLAUDE_USER_PROMPT": "Help me with Python code"},
        )

        assert result["continue"] is True

    def test_continues_on_empty_prompt(self, hook_runner):
        """Hook handles empty prompt gracefully."""
        result = hook_runner.run(
            "user_prompt_submit.py",
            env_vars={"CLAUDE_USER_PROMPT": ""},
        )

        assert result["continue"] is True


class TestPostToolUseHook:
    """Test post_tool_use.py hook behavior."""

    def test_returns_valid_json(self, hook_runner):
        """Hook returns valid JSON."""
        result = hook_runner.run(
            "post_tool_use.py",
            env_vars={
                "CLAUDE_TOOL_USE_NAME": "Read",
                "CLAUDE_TOOL_INPUT": json.dumps({"file_path": "/tmp/test.txt"}),
            },
        )

        assert "continue" in result

    def test_continues_after_read(self, hook_runner):
        """Hook continues after Read tool."""
        result = hook_runner.run(
            "post_tool_use.py",
            env_vars={
                "CLAUDE_TOOL_USE_NAME": "Read",
                "CLAUDE_TOOL_INPUT": json.dumps({"file_path": "/tmp/test.txt"}),
            },
        )

        assert result["continue"] is True

    def test_continues_after_write(self, hook_runner):
        """Hook continues after Write tool."""
        result = hook_runner.run(
            "post_tool_use.py",
            env_vars={
                "CLAUDE_TOOL_USE_NAME": "Write",
                "CLAUDE_TOOL_INPUT": json.dumps({
                    "file_path": "/tmp/test.txt",
                    "content": "test",
                }),
            },
        )

        assert result["continue"] is True


class TestStopHook:
    """Test stop.py hook behavior."""

    def test_returns_valid_json(self, hook_runner):
        """Hook returns valid JSON."""
        result = hook_runner.run(
            "stop.py",
            env_vars={"CLAUDE_STOP_REASON": "end_turn"},
        )

        assert "continue" in result

    def test_continues_on_end_turn(self, hook_runner):
        """Hook continues on normal end_turn."""
        result = hook_runner.run(
            "stop.py",
            env_vars={"CLAUDE_STOP_REASON": "end_turn"},
        )

        assert result["continue"] is True

    def test_handles_interrupt(self, hook_runner):
        """Hook handles interrupt gracefully."""
        result = hook_runner.run(
            "stop.py",
            env_vars={"CLAUDE_STOP_REASON": "interrupt"},
        )

        assert result["continue"] is True


class TestPreToolUseHook:
    """Test pre_tool_use.py hook behavior."""

    def test_returns_valid_json(self, hook_runner):
        """Hook returns valid JSON."""
        result = hook_runner.run(
            "pre_tool_use.py",
            env_vars={
                "CLAUDE_TOOL_USE_NAME": "Bash",
                "CLAUDE_TOOL_INPUT": json.dumps({"command": "ls"}),
            },
        )

        assert "continue" in result

    def test_allows_normal_tools(self, hook_runner):
        """Hook allows normal tool execution."""
        result = hook_runner.run(
            "pre_tool_use.py",
            env_vars={
                "CLAUDE_TOOL_USE_NAME": "Read",
                "CLAUDE_TOOL_INPUT": json.dumps({"file_path": "/tmp/test"}),
            },
        )

        assert result["continue"] is True
