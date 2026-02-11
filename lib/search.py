#!/usr/bin/env python3
"""
Mnemonic Memory Search Library

Centralized memory search logic for all mnemonic hooks.
Consolidates duplicated search functions from:
- hooks/pre_tool_use.py (find_memories_for_context, detect_file_context, extract_keywords_from_path)
- hooks/post_tool_use.py (find_related_memories, detect_namespace_for_file)
- hooks/user_prompt_submit.py (search_memories, extract_topic)
"""

import re
import subprocess
from pathlib import Path
from typing import Optional

from lib.memory_reader import get_memory_metadata
from lib.paths import get_all_memory_roots_with_legacy

# Scoring weights for find_related_memories_scored
SCORE_NAMESPACE_TYPE = 30  # Same top-level cognitive type (e.g., both _semantic/*)
SCORE_NAMESPACE_EXACT = 20  # Exact sub-namespace match
SCORE_TAG_OVERLAP = 20  # Per shared tag
SCORE_TITLE_KEYWORD = 15  # Per shared title keyword
SCORE_CONTENT_KEYWORD = 5  # Per matching content keyword
SCORE_MIN_THRESHOLD = 15  # Minimum score to include in results

# Common stopwords for keyword extraction
STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "we",
        "i",
        "you",
        "it",
        "do",
        "did",
        "does",
        "have",
        "has",
        "had",
        "what",
        "how",
        "why",
        "when",
        "about",
        "this",
        "that",
        "there",
        "here",
        "with",
        "for",
        "to",
        "from",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "of",
        "as",
        "by",
    }
)


def search_memories(topic: str, max_results: int = 3) -> list[str]:
    """Search mnemonic for memories matching topic.

    Args:
        topic: Search keywords.
        max_results: Maximum number of results to return.

    Returns:
        List of absolute paths to matching memory files.
    """
    if not topic:
        return []

    memory_roots = get_all_memory_roots_with_legacy()
    if not memory_roots:
        return []

    results = []
    for mnemonic_dir in memory_roots:
        if not mnemonic_dir.exists():
            continue
        try:
            result = subprocess.run(
                ["rg", "-i", "-l", topic, "--glob", "*.memory.md"],
                capture_output=True,
                text=True,
                cwd=str(mnemonic_dir),
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                for rel_path in result.stdout.strip().split("\n"):
                    results.append(str(mnemonic_dir / rel_path))
                    if len(results) >= max_results:
                        break
        except Exception:
            pass
        if len(results) >= max_results:
            break
    return results[:max_results]


def find_related_memories(context: str, max_results: int = 3) -> list[str]:
    """Find existing memories that might be related to current work.

    Args:
        context: Context string to search for (e.g., file stem keywords).
        max_results: Maximum number of results to return.

    Returns:
        List of absolute paths to matching memory files.
    """
    if not context:
        return []

    memory_roots = get_all_memory_roots_with_legacy()
    results = []
    for mnemonic_dir in memory_roots:
        if not mnemonic_dir.exists():
            continue
        try:
            result = subprocess.run(
                ["rg", "-i", "-l", context, "--glob", "*.memory.md", "--max-count", "1"],
                capture_output=True,
                text=True,
                cwd=str(mnemonic_dir),
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                for rel_path in result.stdout.strip().split("\n"):
                    results.append(str(mnemonic_dir / rel_path))
                    if len(results) >= max_results:
                        break
        except Exception:
            pass
        if len(results) >= max_results:
            break
    return results[:max_results]


def find_memories_for_context(context: dict) -> list[str]:
    """Find relevant memory files using fast ripgrep search.

    Args:
        context: Dict with 'namespaces' key containing list of namespace strings.

    Returns:
        List of absolute paths to matching memory files (max 5).
    """
    memory_files = []

    memory_roots = get_all_memory_roots_with_legacy()
    existing_paths = [str(p) for p in memory_roots if p.exists()]
    if not existing_paths:
        return []

    for namespace in context["namespaces"]:
        try:
            cmd = ["rg", "-l", f"namespace:.*{namespace}", "--glob", "*.memory.md", "--max-count", "1"] + existing_paths

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and line.endswith(".memory.md"):
                        memory_files.append(line)
                        if len(memory_files) >= 5:
                            break
        except Exception:
            continue

        if len(memory_files) >= 5:
            break

    return memory_files[:5]


def detect_file_context(file_path: str, file_patterns: list) -> Optional[dict]:
    """Detect which context a file belongs to based on path patterns.

    Args:
        file_path: Path to the file being edited.
        file_patterns: List of pattern dicts from ontology (with keys: patterns, namespaces, context).

    Returns:
        Dict with context_description and namespaces, or None if no match.
    """
    path_lower = file_path.lower()

    for config in file_patterns:
        for pattern in config["patterns"]:
            if pattern in path_lower:
                return {"context_description": config["context"], "namespaces": config["namespaces"]}

    return None


def detect_namespace_for_file(file_path: str, file_patterns: list) -> str:
    """Detect suggested namespace based on file path.

    Args:
        file_path: Path to the file being edited.
        file_patterns: List of pattern dicts from ontology.

    Returns:
        First matching namespace string, or empty string if no match.
    """
    path_lower = file_path.lower()

    for config in file_patterns:
        for pattern in config["patterns"]:
            if pattern in path_lower:
                return config["namespaces"][0] if config["namespaces"] else ""
    return ""


def extract_keywords_from_path(file_path: str) -> str:
    """Extract searchable keywords from a file path.

    Args:
        file_path: Path to extract keywords from.

    Returns:
        Space-separated keywords string (max 4 keywords).
    """
    stem = Path(file_path).stem
    tokens = re.split(r"[-_./]", stem.lower())
    keywords = [t for t in tokens if len(t) > 2]
    return " ".join(keywords[:4]) if keywords else ""


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text, removing stopwords and short words.

    Args:
        text: Text to extract keywords from.

    Returns:
        List of keywords (lowercase, no stopwords, length > 2).
    """
    words = re.sub(r"[^\w\s]", "", text.lower()).split()
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def extract_topic(prompt: str) -> str:
    """Extract topic keywords from a user prompt for search.

    Args:
        prompt: User prompt text.

    Returns:
        Space-separated keywords string (max 5 keywords).
    """
    words = re.sub(r"[^\w\s]", "", prompt.lower()).split()
    # Extend base stopwords with memory-specific terms
    stopwords = STOPWORDS | {
        "remember",
        "recall",
        "before",
        "earlier",
        "previously",
        "last",
        "time",
        "let",
        "lets",
        "use",
        "using",
        "go",
        "going",
        "will",
        "should",
        "can",
    }
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return " ".join(keywords[:5]) if keywords else ""


def find_related_memories_scored(
    title: str,
    tags: Optional[list[str]] = None,
    namespace: Optional[str] = None,
    content_keywords: Optional[list[str]] = None,
    max_results: int = 5,
) -> list[dict]:
    """Find related memories using multi-signal scoring.

    Scoring:
    - Namespace match: +30 (same top-level cognitive type)
    - Sub-namespace match: +20 (same sub-namespace)
    - Tag overlap: +20 per shared tag
    - Title keyword match: +15 per shared keyword (after stopword removal)
    - Content match: +5 per matching content keyword (via rg)

    Args:
        title: Memory title to find related memories for.
        tags: List of tags to match against.
        namespace: Namespace to match against (e.g., "_semantic/decisions").
        content_keywords: Additional content keywords to search for.
        max_results: Maximum number of results to return.

    Returns:
        List of dicts: [{"id", "title", "path", "namespace", "tags", "score", "match_reasons"}]
        Sorted by score descending, filtered to score >= 15.
    """
    memory_roots = get_all_memory_roots_with_legacy()
    if not memory_roots:
        return []

    # Extract keywords from title (remove stopwords)
    title_keywords = _extract_keywords(title)

    # Build search query to find candidate files
    # Combine title keywords, tags, and content keywords
    search_terms = set(title_keywords)
    if tags:
        search_terms.update(tag.lower() for tag in tags)
    if content_keywords:
        search_terms.update(kw.lower() for kw in content_keywords)

    if not search_terms:
        return []

    # Use rg to find candidate files (limit to 20 for performance)
    candidates = set()
    for mnemonic_dir in memory_roots:
        if not mnemonic_dir.exists():
            continue

        # Search for any of the terms (OR query)
        search_pattern = "|".join(re.escape(term) for term in list(search_terms)[:10])
        try:
            result = subprocess.run(
                ["rg", "-i", "-l", search_pattern, "--glob", "*.memory.md"],
                capture_output=True,
                text=True,
                cwd=str(mnemonic_dir),
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                for rel_path in result.stdout.strip().split("\n")[:20]:
                    if rel_path:
                        candidates.add(str(mnemonic_dir / rel_path))
        except Exception:
            continue

    if not candidates:
        return []

    # Score each candidate
    scored_results = []
    for candidate_path in candidates:
        metadata = get_memory_metadata(candidate_path)
        if not metadata:
            continue

        score = 0
        match_reasons = []

        # Namespace scoring
        if namespace and metadata.get("namespace"):
            candidate_ns = metadata["namespace"]
            # Same top-level namespace (e.g., both _semantic/*)
            if candidate_ns.split("/")[0] == namespace.split("/")[0]:
                score += SCORE_NAMESPACE_TYPE
                match_reasons.append(f"Same type: {namespace.split('/')[0]}")

                # Same sub-namespace (exact match)
                if candidate_ns == namespace:
                    score += SCORE_NAMESPACE_EXACT
                    match_reasons.append(f"Same namespace: {namespace}")

        # Tag overlap scoring
        if tags and metadata.get("tags"):
            candidate_tags = {t.lower() for t in metadata["tags"]}
            query_tags = {t.lower() for t in tags}
            shared_tags = candidate_tags & query_tags
            if shared_tags:
                tag_score = len(shared_tags) * SCORE_TAG_OVERLAP
                score += tag_score
                match_reasons.append(f"Shared tags: {', '.join(shared_tags)}")

        # Title keyword match scoring
        if title_keywords and metadata.get("title"):
            candidate_keywords = _extract_keywords(metadata["title"])

            shared_keywords = set(title_keywords) & set(candidate_keywords)
            if shared_keywords:
                keyword_score = len(shared_keywords) * SCORE_TITLE_KEYWORD
                score += keyword_score
                match_reasons.append(f"Title keywords: {', '.join(shared_keywords)}")

        # Content keyword match scoring
        if content_keywords:
            # Check if any content keywords appear in summary
            summary = metadata.get("summary", "").lower()
            matched_content_kw = [kw for kw in content_keywords if kw.lower() in summary]
            if matched_content_kw:
                content_score = len(matched_content_kw) * SCORE_CONTENT_KEYWORD
                score += content_score
                match_reasons.append(f"Content: {', '.join(matched_content_kw)}")

        # Filter out low-scoring results (noise threshold)
        if score >= SCORE_MIN_THRESHOLD:
            scored_results.append(
                {
                    "id": metadata.get("id"),
                    "title": metadata.get("title"),
                    "path": metadata.get("path"),
                    "namespace": metadata.get("namespace"),
                    "tags": metadata.get("tags", []),
                    "score": score,
                    "match_reasons": match_reasons,
                }
            )

    # Sort by score descending and return top N
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:max_results]


def find_duplicates(
    title: str,
    namespace: Optional[str] = None,
    threshold: float = 0.5,
    max_results: int = 5,
) -> list[dict]:
    """Find existing memories that may be duplicates of a proposed new memory.

    Uses Jaccard similarity on title keywords to detect near-duplicates.
    Intended to be called at capture time to prevent duplicate creation.

    Args:
        title: Proposed title for the new memory.
        namespace: Optional namespace to narrow search scope.
        threshold: Minimum Jaccard similarity to consider a duplicate (0.0-1.0).
        max_results: Maximum number of results to return.

    Returns:
        List of dicts: [{"path", "title", "id", "namespace", "similarity"}]
        Sorted by similarity descending.
    """
    title_keywords = set(_extract_keywords(title))
    if not title_keywords:
        return []

    memory_roots = get_all_memory_roots_with_legacy()
    if not memory_roots:
        return []

    # Build search pattern from title keywords
    search_pattern = "|".join(re.escape(kw) for kw in list(title_keywords)[:8])

    # Find candidate files via rg
    candidates = set()
    for mnemonic_dir in memory_roots:
        if not mnemonic_dir.exists():
            continue
        try:
            result = subprocess.run(
                ["rg", "-i", "-l", search_pattern, "--glob", "*.memory.md"],
                capture_output=True,
                text=True,
                cwd=str(mnemonic_dir),
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                for rel_path in result.stdout.strip().split("\n")[:30]:
                    if rel_path:
                        candidates.add(str(mnemonic_dir / rel_path))
        except Exception:
            continue

    if not candidates:
        return []

    # Score each candidate by Jaccard similarity
    results = []
    for candidate_path in candidates:
        metadata = get_memory_metadata(candidate_path)
        if not metadata:
            continue

        # Filter by namespace if specified
        if namespace and metadata.get("namespace"):
            candidate_ns = metadata["namespace"]
            # Must share at least the top-level cognitive type
            if candidate_ns.split("/")[0] != namespace.split("/")[0]:
                continue

        candidate_keywords = set(_extract_keywords(metadata.get("title", "")))
        if not candidate_keywords:
            continue

        # Jaccard similarity: |intersection| / |union|
        intersection = title_keywords & candidate_keywords
        union = title_keywords | candidate_keywords
        similarity = len(intersection) / len(union) if union else 0.0

        if similarity >= threshold:
            results.append(
                {
                    "path": candidate_path,
                    "title": metadata.get("title", ""),
                    "id": metadata.get("id", ""),
                    "namespace": metadata.get("namespace", ""),
                    "similarity": round(similarity, 3),
                }
            )

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:max_results]


def infer_relationship_type(
    source_title: str,
    source_namespace: str,
    source_tags: list[str],
    target_metadata: dict,
) -> str:
    """Infer relationship type between a new memory and an existing one.

    Decision logic (conservative — RelatesTo is the safe default):
    - Supersedes: Same namespace + very high title keyword overlap (>70%)
    - ConflictsWith: Same namespace + high overlap (>50%) but not superseding
    - Implements: Procedural source referencing semantic target
    - DerivedFrom: Different namespace + moderate title overlap (>30%)
    - RelatesTo: Default for thematic connections

    Args:
        source_title: Title of the new memory being created
        source_namespace: Namespace of the new memory
        source_tags: Tags of the new memory
        target_metadata: Metadata dict of the candidate memory (from get_memory_metadata)

    Returns:
        PascalCase relationship type string (e.g. "Supersedes", "RelatesTo")
    """
    # Extract keywords from source title
    source_keywords = set(_extract_keywords(source_title))

    # Extract keywords from target title
    target_title = target_metadata.get("title", "")
    target_keywords = set(_extract_keywords(target_title))

    # Calculate keyword overlap ratio
    if not source_keywords or not target_keywords:
        overlap_ratio = 0.0
    else:
        shared_keywords = source_keywords & target_keywords
        min_keyword_count = min(len(source_keywords), len(target_keywords))
        overlap_ratio = len(shared_keywords) / min_keyword_count if min_keyword_count > 0 else 0.0

    # Compare namespaces
    target_namespace = target_metadata.get("namespace", "")
    same_namespace = source_namespace == target_namespace
    source_top = source_namespace.split("/")[0] if source_namespace else ""
    target_top = target_namespace.split("/")[0] if target_namespace else ""

    # Apply decision tree (most specific first)
    if same_namespace and overlap_ratio > 0.7:
        return "Supersedes"
    elif same_namespace and overlap_ratio >= 0.5:
        return "ConflictsWith"
    elif source_top == "_procedural" and target_top == "_semantic" and overlap_ratio > 0.3:
        return "Implements"
    elif not same_namespace and overlap_ratio > 0.3:
        return "DerivedFrom"
    else:
        return "RelatesTo"
