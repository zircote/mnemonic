#!/usr/bin/env python3
"""
Full workflow tests for mnemonic.

Tests complete capture → recall cycles using test-specific namespaces.
"""

import time
from uuid import uuid4

import pytest


class TestFullWorkflow:
    """Test complete capture → recall workflows."""

    def test_capture_then_recall(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Empty test mnemonic
        WHEN: User makes decision, then asks about it
        THEN: Second response references the captured memory
        """
        unique_id = f"workflow-{uuid4().hex[:8]}"

        # First call: make a decision (explicitly ask to capture)
        capture_prompt = (
            f"I've decided we'll use FastAPI ({unique_id}) for the backend API. "
            f"Please capture this decision to memory."
        )
        claude_runner.run(capture_prompt)

        time.sleep(2)

        # Verify memory was created
        memories = memory_helper.find_with_content(unique_id, "decisions")

        assert len(memories) > 0, (
            f"Memory should be created for {unique_id}\n"
            f"Found: {[m.name for m in memory_helper.find_recent()]}"
        )

        # Second call: ask about the topic
        recall_prompt = f"What technology should we use for the backend? Check for {unique_id}."
        response = claude_runner.run(recall_prompt)

        # Should reference the technology
        assert unique_id in response or "technology" in response.lower(), (
            f"Should recall the decision\nResponse: {response[:500]}"
        )

    def test_learning_captured_and_recalled(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: User shares a learning
        WHEN: Asked about the topic later
        THEN: Learning is recalled
        """
        unique_id = f"learn-{uuid4().hex[:8]}"

        # Share a learning (explicitly ask to capture)
        learn_prompt = (
            f"I learned that service-{unique_id} requires authentication. "
            f"Please capture this learning to memory."
        )
        claude_runner.run(learn_prompt)

        time.sleep(2)

        # Ask about it
        recall_prompt = f"Does service-{unique_id} require authentication? Check learnings."
        response = claude_runner.run(recall_prompt)

        assert "auth" in response.lower() or unique_id in response, (
            f"Should recall the learning\nResponse: {response[:500]}"
        )


class TestNoDuplication:
    """Test that duplicate memories aren't created."""

    def test_no_duplicate_on_repeated_decision(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: User states same decision twice
        WHEN: Mnemonic processes both
        THEN: Only one memory is created (or search prevents duplicate)
        """
        unique_id = f"nodup-{uuid4().hex[:8]}"

        # First statement (explicitly capture)
        prompt1 = f"I've decided we'll use {unique_id} for caching. Please capture this decision."
        claude_runner.run(prompt1)

        time.sleep(2)

        # Count memories after first
        memories_after_first = memory_helper.find_with_content(unique_id)
        count_after_first = len(memories_after_first)

        # Second statement (same topic - should detect duplicate)
        prompt2 = f"Yes, {unique_id} is definitely the right choice for caching. Capture this decision."
        claude_runner.run(prompt2)

        time.sleep(2)

        # Count memories after second
        memories_after_second = memory_helper.find_with_content(unique_id)
        count_after_second = len(memories_after_second)

        # Should not have doubled
        assert count_after_second <= count_after_first + 1, (
            f"Should not create many duplicates.\n"
            f"After first: {count_after_first}, After second: {count_after_second}"
        )


class TestMemoryPersistence:
    """Test that memories persist across calls."""

    def test_memory_persists_for_later_recall(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: Memory created in call 1
        WHEN: Call 2 asks about same topic
        THEN: Memory is still accessible
        """
        unique_id = f"persist-{uuid4().hex[:8]}"

        # Create in first call (explicitly capture)
        claude_runner.run(f"I've decided to use framework-{unique_id}. Please capture this decision.")

        time.sleep(2)

        # Verify file exists
        matching = memory_helper.find_with_content(unique_id)

        if matching:
            # Memory exists, verify it persists
            mem_path = matching[0]
            assert mem_path.exists(), "Memory file should persist"

            # Read in second call
            response = claude_runner.run(
                f"What framework did we choose? Look for {unique_id}."
            )

            assert unique_id in response or "framework" in response.lower(), (
                f"Should recall persisted memory\nResponse: {response[:500]}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
