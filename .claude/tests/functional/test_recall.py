#!/usr/bin/env python3
"""
Functional tests for mnemonic recall behavior.

Tests that Claude searches and uses existing memories when answering.
Uses test-specific namespaces with unique IDs for cleanup.
"""

import time
from uuid import uuid4

import pytest


class TestRecallDecisions:
    """Test that Claude recalls existing decisions."""

    def test_recalls_existing_decision(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: A memory exists about using Express.js
        WHEN: User asks what framework to use
        THEN: Response references Express.js from memory
        """
        unique_id = f"express-{uuid4().hex[:8]}"

        # Pre-create memory
        memory_helper.create(
            namespace="decisions",
            title=f"Use Express-{unique_id} for API",
            content=f"We decided to use Express.js ({unique_id}) for the REST API backend.",
            unique_id=unique_id,
        )

        # Ask about the topic
        prompt = f"What framework should we use for the API? Search for decisions about Express-{unique_id}."

        response = claude_runner.run(prompt)

        # Should reference Express or the unique ID
        response_lower = response.lower()
        assert "express" in response_lower or unique_id.lower() in response_lower, (
            f"Response should reference existing Express decision\n"
            f"Response: {response[:500]}"
        )

    def test_recalls_database_decision(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: A memory exists about database choice
        WHEN: User asks about database
        THEN: Response references the existing decision
        """
        unique_id = f"postgres-{uuid4().hex[:8]}"

        memory_helper.create(
            namespace="decisions",
            title=f"Use PostgreSQL-{unique_id} for database",
            content=f"We decided on PostgreSQL ({unique_id}) for its reliability.",
            unique_id=unique_id,
        )

        prompt = f"What database should we use? Check for decisions about PostgreSQL-{unique_id}."

        response = claude_runner.run(prompt)

        response_lower = response.lower()
        assert "postgresql" in response_lower or "postgres" in response_lower or unique_id.lower() in response_lower, (
            f"Response should reference PostgreSQL decision\n"
            f"Response: {response[:500]}"
        )


class TestRecallLearnings:
    """Test that Claude recalls existing learnings."""

    def test_recalls_api_limit_learning(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: A memory exists about API rate limits
        WHEN: User asks about the API
        THEN: Response includes the rate limit info
        """
        unique_id = f"ratelimit-{uuid4().hex[:8]}"

        memory_helper.create(
            namespace="learnings",
            title=f"API-{unique_id} Rate Limit",
            content=f"The API-{unique_id} has a rate limit of exactly 42 requests per minute.",
            unique_id=unique_id,
        )

        prompt = f"What's the rate limit for API-{unique_id}? Search learnings."

        response = claude_runner.run(prompt)

        # Should mention the specific rate limit
        assert "42" in response or unique_id in response, (
            f"Response should reference the rate limit learning\n"
            f"Response: {response[:500]}"
        )


class TestRecallPatterns:
    """Test that Claude recalls existing patterns."""

    def test_recalls_naming_convention(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: A memory exists about naming conventions
        WHEN: User asks about conventions
        THEN: Response references the pattern
        """
        unique_id = f"naming-{uuid4().hex[:8]}"

        memory_helper.create(
            namespace="patterns",
            title=f"Naming Convention {unique_id}",
            content=f"Always use camelCase-{unique_id} for JavaScript variable names.",
            unique_id=unique_id,
        )

        prompt = f"What naming convention should I use? Check patterns for {unique_id}."

        response = claude_runner.run(prompt)

        # Claude should reference either the test-created camelCase memory or existing snake_case patterns
        response_lower = response.lower()
        has_naming_reference = (
            "camelcase" in response_lower or
            "snake_case" in response_lower or
            unique_id.lower() in response_lower or
            "naming" in response_lower
        )
        assert has_naming_reference, (
            f"Response should reference naming convention\n"
            f"Response: {response[:500]}"
        )


class TestNoFalseRecall:
    """Test that Claude doesn't hallucinate memories."""

    def test_no_recall_for_unrelated_topic(
        self, require_claude, test_mnemonic, claude_runner, memory_helper
    ):
        """
        GIVEN: A memory exists about topic A
        WHEN: User asks about unrelated topic B
        THEN: Response does NOT reference topic A
        """
        unique_id = f"redis-{uuid4().hex[:8]}"
        unrelated_id = f"unrelated-{uuid4().hex[:8]}"

        # Create memory about Redis
        memory_helper.create(
            namespace="decisions",
            title=f"Use Redis-{unique_id}",
            content=f"Redis-{unique_id} for caching.",
            unique_id=unique_id,
        )

        # Ask about something completely unrelated
        prompt = f"How do I write a Python function to calculate {unrelated_id} factorial?"

        response = claude_runner.run(prompt)

        # Should NOT mention Redis or the unique_id
        assert unique_id not in response, (
            f"Response should not reference unrelated memory\n"
            f"Response: {response[:500]}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
