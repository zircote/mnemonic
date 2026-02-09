#!/usr/bin/env python3
"""
Unit tests for lib/search.py memory search functions.

Tests search, detection, and extraction functions with mocked subprocess.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from lib.search import (
    search_memories,
    find_related_memories,
    find_memories_for_context,
    detect_file_context,
    detect_namespace_for_file,
    extract_keywords_from_path,
    extract_topic,
)


class TestSearchMemories:
    """Test search_memories() function."""

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_search_memories_success(self, mock_run, mock_roots, tmp_path):
        """Test successful memory search."""
        mnemonic_dir = tmp_path / "mnemonic"
        mnemonic_dir.mkdir()

        mock_roots.return_value = [mnemonic_dir]
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.memory.md\nfile2.memory.md\nfile3.memory.md\n"
        mock_run.return_value = mock_result

        results = search_memories("python testing", max_results=3)

        assert len(results) == 3
        assert results[0] == str(mnemonic_dir / "file1.memory.md")
        assert results[1] == str(mnemonic_dir / "file2.memory.md")
        assert results[2] == str(mnemonic_dir / "file3.memory.md")

        # Verify subprocess call
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["rg", "-i", "-l", "python testing", "--glob", "*.memory.md"]

    @patch("lib.search.get_all_memory_roots_with_legacy")
    def test_search_memories_empty_topic(self, mock_roots):
        """Test search with empty topic returns empty list."""
        results = search_memories("", max_results=3)
        assert results == []

    @patch("lib.search.get_all_memory_roots_with_legacy")
    def test_search_memories_no_roots(self, mock_roots):
        """Test search with no memory roots returns empty list."""
        mock_roots.return_value = []
        results = search_memories("test", max_results=3)
        assert results == []

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_search_memories_nonexistent_root(self, mock_run, mock_roots):
        """Test search skips nonexistent memory roots."""
        mock_roots.return_value = [Path("/nonexistent/path")]
        results = search_memories("test", max_results=3)
        assert results == []
        mock_run.assert_not_called()

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_search_memories_no_matches(self, mock_run, mock_roots):
        """Test search with no matching files."""
        mock_roots.return_value = [Path("/home/user/.local/share/mnemonic")]
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        results = search_memories("nonexistent topic", max_results=3)
        assert results == []

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_search_memories_respects_max_results(self, mock_run, mock_roots, tmp_path):
        """Test max_results parameter limits output."""
        mnemonic_dir = tmp_path / "mnemonic"
        mnemonic_dir.mkdir()

        mock_roots.return_value = [mnemonic_dir]
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "file1.memory.md\nfile2.memory.md\nfile3.memory.md\nfile4.memory.md\n"
        mock_run.return_value = mock_result

        results = search_memories("test", max_results=2)
        assert len(results) == 2

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_search_memories_subprocess_exception(self, mock_run, mock_roots):
        """Test search handles subprocess exceptions gracefully."""
        mock_roots.return_value = [Path("/home/user/.local/share/mnemonic")]
        mock_run.side_effect = subprocess.TimeoutExpired("rg", 2)

        results = search_memories("test", max_results=3)
        assert results == []

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_search_memories_multiple_roots(self, mock_run, mock_roots, tmp_path):
        """Test search across multiple memory roots."""
        mnemonic_dir1 = tmp_path / "mnemonic1"
        mnemonic_dir2 = tmp_path / "mnemonic2"
        mnemonic_dir1.mkdir()
        mnemonic_dir2.mkdir()

        mock_roots.return_value = [mnemonic_dir1, mnemonic_dir2]
        mock_result1 = MagicMock()
        mock_result1.returncode = 0
        mock_result1.stdout = "file1.memory.md\n"
        mock_result2 = MagicMock()
        mock_result2.returncode = 0
        mock_result2.stdout = "file2.memory.md\n"
        mock_run.side_effect = [mock_result1, mock_result2]

        results = search_memories("test", max_results=5)
        assert len(results) == 2
        assert results[0] == str(mnemonic_dir1 / "file1.memory.md")
        assert results[1] == str(mnemonic_dir2 / "file2.memory.md")


class TestFindRelatedMemories:
    """Test find_related_memories() function."""

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_find_related_memories_success(self, mock_run, mock_roots, tmp_path):
        """Test successful related memory search."""
        mnemonic_dir = tmp_path / "mnemonic"
        mnemonic_dir.mkdir()

        mock_roots.return_value = [mnemonic_dir]
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "related1.memory.md\nrelated2.memory.md\n"
        mock_run.return_value = mock_result

        results = find_related_memories("authentication", max_results=3)

        assert len(results) == 2
        assert results[0] == str(mnemonic_dir / "related1.memory.md")

        # Verify subprocess call uses --max-count=1
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "--max-count" in call_args[0][0]
        assert "1" in call_args[0][0]

    @patch("lib.search.get_all_memory_roots_with_legacy")
    def test_find_related_memories_empty_context(self, mock_roots):
        """Test find_related with empty context returns empty list."""
        results = find_related_memories("", max_results=3)
        assert results == []

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_find_related_memories_timeout(self, mock_run, mock_roots):
        """Test find_related handles timeout gracefully."""
        mock_roots.return_value = [Path("/home/user/.local/share/mnemonic")]
        mock_run.side_effect = subprocess.TimeoutExpired("rg", 2)

        results = find_related_memories("test", max_results=3)
        assert results == []


class TestFindMemoriesForContext:
    """Test find_memories_for_context() function."""

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_find_memories_for_context_success(self, mock_run, mock_roots, tmp_path):
        """Test successful context-based search."""
        mnemonic_dir = tmp_path / "mnemonic"
        mnemonic_dir.mkdir()

        mock_roots.return_value = [mnemonic_dir]

        # First namespace returns a result, second returns nothing
        mock_result1 = MagicMock()
        mock_result1.returncode = 0
        mock_result1.stdout = str(mnemonic_dir / "_semantic/decisions/file1.memory.md") + "\n"

        mock_result2 = MagicMock()
        mock_result2.returncode = 1
        mock_result2.stdout = ""

        mock_run.side_effect = [mock_result1, mock_result2]

        context = {"namespaces": ["_semantic/decisions", "_procedural/patterns"]}
        results = find_memories_for_context(context)

        assert len(results) == 1
        assert results[0] == str(mnemonic_dir / "_semantic/decisions/file1.memory.md")

        # Verify subprocess was called for both namespaces
        assert mock_run.call_count == 2

    @patch("lib.search.get_all_memory_roots_with_legacy")
    def test_find_memories_for_context_no_roots(self, mock_roots):
        """Test with no existing memory roots."""
        mock_roots.return_value = []
        context = {"namespaces": ["_semantic/decisions"]}
        results = find_memories_for_context(context)
        assert results == []

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_find_memories_for_context_multiple_namespaces(self, mock_run, mock_roots, tmp_path):
        """Test search across multiple namespaces."""
        mnemonic_dir = tmp_path / "mnemonic"
        mnemonic_dir.mkdir()

        mock_roots.return_value = [mnemonic_dir]
        mock_result1 = MagicMock()
        mock_result1.returncode = 0
        mock_result1.stdout = str(mnemonic_dir / "file1.memory.md") + "\n"
        mock_result2 = MagicMock()
        mock_result2.returncode = 0
        mock_result2.stdout = str(mnemonic_dir / "file2.memory.md") + "\n"
        mock_run.side_effect = [mock_result1, mock_result2]

        context = {"namespaces": ["_semantic/decisions", "_procedural/patterns"]}
        results = find_memories_for_context(context)

        assert len(results) == 2

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_find_memories_for_context_max_limit(self, mock_run, mock_roots, tmp_path):
        """Test max 5 results limit."""
        mnemonic_dir = tmp_path / "mnemonic"
        mnemonic_dir.mkdir()

        mock_roots.return_value = [mnemonic_dir]
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "\n".join([f"file{i}.memory.md" for i in range(10)]) + "\n"
        mock_run.return_value = mock_result

        context = {"namespaces": ["_semantic/decisions"]}
        results = find_memories_for_context(context)

        assert len(results) == 5

    @patch("lib.search.get_all_memory_roots_with_legacy")
    @patch("lib.search.subprocess.run")
    def test_find_memories_for_context_exception_handling(self, mock_run, mock_roots):
        """Test exception handling during search."""
        mock_roots.return_value = [Path("/home/user/.local/share/mnemonic")]
        mock_run.side_effect = Exception("Search failed")

        context = {"namespaces": ["_semantic/decisions"]}
        results = find_memories_for_context(context)

        assert results == []


class TestDetectFileContext:
    """Test detect_file_context() function."""

    def test_detect_file_context_match(self):
        """Test successful context detection."""
        file_patterns = [
            {
                "patterns": ["auth", "login", "session"],
                "namespaces": ["_semantic/knowledge", "_semantic/decisions"],
                "context": "authentication",
            },
            {
                "patterns": ["api", "endpoint"],
                "namespaces": ["_semantic/knowledge"],
                "context": "API design",
            },
        ]

        result = detect_file_context("/project/src/auth_handler.py", file_patterns)

        assert result is not None
        assert result["context_description"] == "authentication"
        assert result["namespaces"] == ["_semantic/knowledge", "_semantic/decisions"]

    def test_detect_file_context_case_insensitive(self):
        """Test case-insensitive matching."""
        file_patterns = [
            {
                "patterns": ["auth"],
                "namespaces": ["_semantic/knowledge"],
                "context": "authentication",
            }
        ]

        result = detect_file_context("/project/src/AUTH_handler.py", file_patterns)
        assert result is not None
        assert result["context_description"] == "authentication"

    def test_detect_file_context_no_match(self):
        """Test no pattern match."""
        file_patterns = [
            {
                "patterns": ["auth", "login"],
                "namespaces": ["_semantic/knowledge"],
                "context": "authentication",
            }
        ]

        result = detect_file_context("/project/src/database.py", file_patterns)
        assert result is None

    def test_detect_file_context_multiple_patterns(self):
        """Test matching with multiple patterns in config."""
        file_patterns = [
            {
                "patterns": ["db", "database", "model"],
                "namespaces": ["_semantic/decisions"],
                "context": "database",
            }
        ]

        result1 = detect_file_context("/project/db_schema.py", file_patterns)
        result2 = detect_file_context("/project/models.py", file_patterns)

        assert result1 is not None
        assert result2 is not None
        assert result1["context_description"] == "database"
        assert result2["context_description"] == "database"

    def test_detect_file_context_first_match_wins(self):
        """Test that first matching pattern is returned."""
        file_patterns = [
            {
                "patterns": ["test"],
                "namespaces": ["_procedural/patterns"],
                "context": "testing",
            },
            {
                "patterns": ["test"],
                "namespaces": ["_semantic/decisions"],
                "context": "other",
            },
        ]

        result = detect_file_context("/project/test_utils.py", file_patterns)
        assert result is not None
        assert result["context_description"] == "testing"


class TestDetectNamespaceForFile:
    """Test detect_namespace_for_file() function."""

    def test_detect_namespace_for_file_match(self):
        """Test successful namespace detection."""
        file_patterns = [
            {
                "patterns": ["auth", "login"],
                "namespaces": ["_semantic/knowledge", "_semantic/decisions"],
                "context": "authentication",
            }
        ]

        result = detect_namespace_for_file("/project/auth_handler.py", file_patterns)
        assert result == "_semantic/knowledge"

    def test_detect_namespace_for_file_no_match(self):
        """Test no namespace match."""
        file_patterns = [
            {
                "patterns": ["auth"],
                "namespaces": ["_semantic/knowledge"],
                "context": "authentication",
            }
        ]

        result = detect_namespace_for_file("/project/database.py", file_patterns)
        assert result == ""

    def test_detect_namespace_for_file_empty_namespaces(self):
        """Test pattern with empty namespaces list."""
        file_patterns = [
            {
                "patterns": ["auth"],
                "namespaces": [],
                "context": "authentication",
            }
        ]

        result = detect_namespace_for_file("/project/auth.py", file_patterns)
        assert result == ""

    def test_detect_namespace_for_file_case_insensitive(self):
        """Test case-insensitive matching."""
        file_patterns = [
            {
                "patterns": ["deploy"],
                "namespaces": ["_procedural/runbooks"],
                "context": "deployment",
            }
        ]

        result = detect_namespace_for_file("/project/DEPLOY_script.sh", file_patterns)
        assert result == "_procedural/runbooks"


class TestExtractKeywordsFromPath:
    """Test extract_keywords_from_path() function."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        result = extract_keywords_from_path("/project/auth_handler.py")
        assert result == "auth handler"

    def test_extract_keywords_multiple_delimiters(self):
        """Test extraction with multiple delimiters."""
        result = extract_keywords_from_path("/project/user-auth_service.ts")
        assert result == "user auth service"

    def test_extract_keywords_filters_short_tokens(self):
        """Test that short tokens (<=2 chars) are filtered."""
        result = extract_keywords_from_path("/project/api_v2_handler.py")
        assert result == "api handler"
        assert "v2" not in result

    def test_extract_keywords_max_four(self):
        """Test max 4 keywords limit."""
        result = extract_keywords_from_path("/project/very_long_complex_file_name_here.py")
        words = result.split()
        assert len(words) <= 4

    def test_extract_keywords_lowercase(self):
        """Test lowercase conversion."""
        result = extract_keywords_from_path("/project/AuthHandler.py")
        assert result == "authhandler"

    def test_extract_keywords_no_valid_tokens(self):
        """Test path with no valid tokens."""
        result = extract_keywords_from_path("/a/b/c.py")
        assert result == ""

    def test_extract_keywords_complex_path(self):
        """Test complex real-world path."""
        result = extract_keywords_from_path("/project/src/services/authentication-service.ts")
        assert "authentication" in result
        assert "service" in result


class TestExtractTopic:
    """Test extract_topic() function."""

    def test_extract_topic_basic(self):
        """Test basic topic extraction."""
        result = extract_topic("explain python testing best practices")
        assert "explain" in result
        assert "python" in result
        assert "testing" in result
        assert "best" in result
        assert "practices" in result

    def test_extract_topic_filters_stopwords(self):
        """Test stopword filtering."""
        result = extract_topic("what is the best way to use authentication")
        words = result.split()
        assert "what" not in words
        assert "the" not in words
        assert "use" not in words
        assert "best" in words
        assert "authentication" in words

    def test_extract_topic_max_five_keywords(self):
        """Test max 5 keywords limit."""
        result = extract_topic("one two three four five six seven eight nine ten")
        words = result.split()
        assert len(words) <= 5

    def test_extract_topic_removes_punctuation(self):
        """Test punctuation removal."""
        result = extract_topic("hello, world! testing: python?")
        assert "hello" in result
        assert "world" in result
        assert "testing" in result
        assert "python" in result
        assert "," not in result

    def test_extract_topic_lowercase(self):
        """Test lowercase conversion."""
        result = extract_topic("Python Testing Best Practices")
        words = result.split()
        for word in words:
            assert word.islower()

    def test_extract_topic_filters_short_words(self):
        """Test short word filtering (<=2 chars)."""
        result = extract_topic("go on to use it as we did")
        assert "go" not in result
        assert "on" not in result
        assert "to" not in result
        assert "it" not in result
        assert "as" not in result
        assert "we" not in result

    def test_extract_topic_empty_after_filtering(self):
        """Test prompt with only stopwords."""
        result = extract_topic("the a an is are was were")
        assert result == ""

    def test_extract_topic_memory_specific_stopwords(self):
        """Test filtering of memory-specific stopwords."""
        result = extract_topic("remember what we did before last time")
        assert "remember" not in result
        assert "what" not in result
        assert "before" not in result
        assert "last" not in result
        assert "time" not in result

    def test_extract_topic_real_world_example(self):
        """Test real-world prompt example."""
        result = extract_topic("How do we configure authentication with JWT tokens?")
        assert "configure" in result
        assert "authentication" in result
        assert "jwt" in result
        assert "tokens" in result
        assert "how" not in result
        assert "do" not in result
        assert "we" not in result
        assert "with" not in result
