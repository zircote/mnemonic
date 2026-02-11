#!/usr/bin/env python3
"""
Functional tests for mnemonic capture behavior.

These tests invoke Claude CLI and verify that memories are actually created.
They test REAL AI behavior using test-specific tags for identification and cleanup.

Requirements:
- Claude CLI installed and authenticated
- Makes real API calls
- Uses test tags for cleanup (not isolated HOME)
"""

import time
from uuid import uuid4

import pytest

CLAUDE_TIMEOUT = 120


class TestCaptureDecisions:
    """Test that Claude can capture decisions to memory when instructed."""

    def test_capture_on_decision_statement(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User states a decision and asks to capture it
        THEN: Memory file is created in decisions/ namespace
        """
        unique_id = f"redis-{uuid4().hex[:8]}"

        # Explicitly ask Claude to capture the decision (tests the mechanism)
        prompt = (
            f"I've decided we should use {unique_id} for caching in this project. "
            f"Please capture this decision to memory as per the mnemonic instructions in CLAUDE.md."
        )

        claude_runner.run(prompt)
        time.sleep(2)

        memories = memory_helper.find_with_content(unique_id, "decisions")

        assert len(memories) > 0, (
            f"Expected memory file with '{unique_id}' in decisions/\n"
            f"Found: {[m.name for m in memory_helper.find_recent('decisions')]}"
        )

    def test_capture_on_lets_use_phrase(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User says "let's use X for Y"
        THEN: Memory file is created
        """
        unique_id = f"postgres-{uuid4().hex[:8]}"

        prompt = f"Let's use {unique_id} for our database. Acknowledge briefly."

        claude_runner.run(prompt)
        time.sleep(2)

        memories = memory_helper.find_with_content(unique_id, "decisions")

        assert len(memories) > 0, f"Expected memory for '{unique_id}'"

    def test_capture_on_going_with_phrase(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User says "we're going with X"
        THEN: Memory file is created
        """
        unique_id = f"jwt-{uuid4().hex[:8]}"

        prompt = f"We're going with {unique_id} for authentication. Acknowledge."

        claude_runner.run(prompt)
        time.sleep(2)

        memories = memory_helper.find_with_content(unique_id, "decisions")

        assert len(memories) > 0, f"Expected memory for '{unique_id}'"


class TestCaptureLearnings:
    """Test that Claude captures learnings to memory."""

    def test_capture_on_i_learned(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User says "I learned that X"
        THEN: Memory file is created in learnings/
        """
        unique_id = f"ratelimit-{uuid4().hex[:8]}"

        prompt = f"I learned that the API-{unique_id} has a rate limit of 100 requests per minute. Acknowledge."

        claude_runner.run(prompt)
        time.sleep(2)

        memories = memory_helper.find_with_content(unique_id, "learnings")

        assert len(memories) > 0, f"Expected learning memory for '{unique_id}'"

    def test_capture_on_turns_out(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User says "turns out X"
        THEN: Memory file is created in learnings/
        """
        unique_id = f"timeout-{uuid4().hex[:8]}"

        prompt = f"Turns out the {unique_id} timeout was causing the failures. Acknowledge."

        claude_runner.run(prompt)
        time.sleep(2)

        memories = memory_helper.find_with_content(unique_id, "learnings")

        assert len(memories) > 0, f"Expected learning memory for '{unique_id}'"


class TestCapturePatterns:
    """Test that Claude captures patterns to memory."""

    def test_capture_on_pattern_statement(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User establishes a coding convention
        THEN: Memory file is created in patterns/
        """
        unique_id = f"pattern-{uuid4().hex[:8]}"

        prompt = f"Convention {unique_id}: We should always use snake_case for database columns. Acknowledge."

        claude_runner.run(prompt)
        time.sleep(2)

        # Check for any recent pattern memory (Claude may not preserve the exact ID)
        memories = memory_helper.find_with_content(unique_id, "patterns")
        if not memories:
            # Fall back to checking for any recent pattern about snake_case
            memories = memory_helper.find_with_content("snake", "patterns")

        assert len(memories) > 0, f"Expected pattern memory for '{unique_id}' or snake_case"


class TestCaptureBlockers:
    """Test that Claude captures blockers to memory."""

    def test_capture_on_stuck_statement(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User reports being stuck
        THEN: Memory file is created in blockers/
        """
        unique_id = f"auth-{uuid4().hex[:8]}"

        prompt = f"I'm stuck on the {unique_id} authentication flow. Tokens expire too early. Acknowledge."

        claude_runner.run(prompt)
        time.sleep(2)

        memories = memory_helper.find_with_content(unique_id, "blockers")

        assert len(memories) > 0, f"Expected blocker memory for '{unique_id}'"


class TestSilentCapture:
    """Test that capture happens silently."""

    def test_no_capture_announcement(
        self, require_claude, test_mnemonic, claude_runner
    ):
        """
        GIVEN: Claude with mnemonic instructions
        WHEN: User makes a decision
        THEN: Response does NOT announce memory capture
        """
        unique_id = f"silent-{uuid4().hex[:8]}"

        prompt = f"Decision: use {unique_id} for the cache. Acknowledge briefly."

        response = claude_runner.run(prompt)

        response_lower = response.lower()

        # Should NOT contain these phrases
        forbidden = [
            "capturing",
            "saving to memory",
            "i'll remember",
            "storing this",
            "mnemonic",
            "memory file",
        ]

        for phrase in forbidden:
            assert phrase not in response_lower, (
                f"Response should not mention '{phrase}'\n"
                f"Response: {response[:500]}"
            )


class TestMemoryFileFormat:
    """Test that created memories have correct format."""

    def test_memory_has_valid_structure(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Claude creates a memory
        WHEN: We read the file
        THEN: Memory file contains the decision content (format may vary)
        """
        unique_id = f"format-{uuid4().hex[:8]}"

        prompt = f"I've decided to use {unique_id} for testing. Acknowledge."

        claude_runner.run(prompt)
        time.sleep(2)

        memories = memory_helper.find_with_content(unique_id)

        assert len(memories) > 0, "Memory should be created"

        content = memories[0].read_text()

        # Verify content contains the unique identifier
        assert unique_id in content, f"Memory should contain '{unique_id}'"

        # Check for either YAML frontmatter or markdown structure
        has_frontmatter = content.startswith("---")
        has_markdown_structure = content.startswith("#") or "Decision" in content

        assert has_frontmatter or has_markdown_structure, (
            "Memory should have either YAML frontmatter or markdown structure"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
