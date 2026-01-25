#!/usr/bin/env python3
"""
CLI integration tests with isolated environments.

Tests Claude CLI behavior without touching real memory files.

NOTE: These tests require Claude CLI to be available and make API calls.
Mark with @pytest.mark.slow to skip in quick runs.
"""

import time

import pytest


@pytest.fixture
def require_claude_cli(claude_cli):
    """Skip test if Claude CLI not available."""
    if not claude_cli.is_available():
        pytest.skip("Claude CLI not available")


@pytest.mark.slow
@pytest.mark.integration
class TestCaptureViaCLI:
    """Test memory capture via Claude CLI."""

    def test_capture_decision(
        self,
        require_claude_cli,
        claude_cli,
        memory_searcher,
        isolated_mnemonic_env,
    ):
        """Decision statement creates memory in decisions namespace."""
        unique_id = f"test-{int(time.time())}"

        claude_cli.run(
            f"I've decided we should use Redis-{unique_id} for caching. "
            "Just acknowledge briefly."
        )

        # Wait for file system
        time.sleep(2)

        # Search for the memory
        results = memory_searcher.search(unique_id)
        assert len(results) > 0, f"No memory found for {unique_id}"

    def test_capture_learning(
        self,
        require_claude_cli,
        claude_cli,
        memory_searcher,
    ):
        """Learning statement creates memory in learnings namespace."""
        unique_id = f"test-{int(time.time())}"

        claude_cli.run(
            f"I learned that the API-{unique_id} has a rate limit of 100/min. "
            "Just acknowledge."
        )

        time.sleep(2)

        results = memory_searcher.search(unique_id)
        assert len(results) > 0

    def test_capture_is_silent(
        self,
        require_claude_cli,
        claude_cli,
    ):
        """Capture happens without announcement in response."""
        response = claude_cli.run(
            "Decision: use PostgreSQL for the database. Acknowledge briefly."
        )

        # Response should NOT mention capturing
        response_lower = response.lower()
        assert "capturing" not in response_lower
        assert "saving to memory" not in response_lower
        assert "mnemonic" not in response_lower
        assert "i'll remember" not in response_lower


@pytest.mark.slow
@pytest.mark.integration
class TestRecallViaCLI:
    """Test memory recall via Claude CLI."""

    def test_recall_existing_memory(
        self,
        require_claude_cli,
        memory_factory,
        claude_cli,
    ):
        """Claude references existing memory when relevant."""
        unique_id = f"test-{int(time.time())}"

        # Create a memory first
        memory_factory.create(
            namespace="decisions",
            title=f"Use Express-{unique_id} for API",
            content=f"We decided to use Express.js framework ({unique_id}).",
        )

        # Ask about the topic
        response = claude_cli.run(
            f"What framework should I use for the API? "
            f"Check for any decisions about Express-{unique_id}."
        )

        # Response should reference Express or the ID
        assert "express" in response.lower() or unique_id in response.lower()


@pytest.mark.slow
@pytest.mark.integration
class TestFullWorkflow:
    """Test complete capture and recall workflow."""

    def test_capture_then_recall(
        self,
        require_claude_cli,
        claude_cli,
        memory_searcher,
    ):
        """Memory captured in one call is findable in another."""
        unique_id = f"workflow-{int(time.time())}"

        # First call: make a decision
        claude_cli.run(
            f"Decision: use JWT-{unique_id} for authentication. Acknowledge."
        )

        time.sleep(2)

        # Verify memory exists
        results = memory_searcher.search(unique_id)
        assert len(results) > 0, "Memory should be created"

        # Second call: ask about authentication
        response = claude_cli.run(
            f"How should we handle authentication? "
            f"Check for any decisions about JWT-{unique_id}."
        )

        # Should reference the decision
        assert "jwt" in response.lower() or unique_id in response.lower()
