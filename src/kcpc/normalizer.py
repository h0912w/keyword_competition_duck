"""normalizer module for KCPC.

Handles keyword normalization and duplicate detection.
"""

import hashlib
from dataclasses import dataclass


def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword by stripping whitespace.

    Args:
        keyword: Raw keyword string.

    Returns:
        str: Normalized keyword with leading/trailing whitespace removed.
    """
    return keyword.strip()


def compute_keyword_hash(keyword: str) -> str:
    """Compute hash for duplicate detection.

    Hash is based on lowercase, stripped keyword for case-insensitive
    duplicate detection while preserving the original keyword.

    Args:
        keyword: The keyword to hash.

    Returns:
        str: SHA256 hash of the normalized lowercase keyword.
    """
    normalized = keyword.lower().strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class NormalizedKeyword:
    """Represents a normalized keyword with metadata."""

    original_index: int
    keyword: str
    normalized: str
    keyword_hash: str


def normalize_keywords(
    keywords: list[tuple[int, str]]
) -> list[NormalizedKeyword]:
    """Normalize a list of keywords and compute hashes.

    Args:
        keywords: List of (original_index, keyword) tuples.

    Returns:
        list[NormalizedKeyword]: List of normalized keywords with metadata.
    """
    normalized_list = []

    for idx, keyword in keywords:
        normalized = normalize_keyword(keyword)
        keyword_hash = compute_keyword_hash(keyword)
        normalized_list.append(
            NormalizedKeyword(
                original_index=idx,
                keyword=keyword,
                normalized=normalized,
                keyword_hash=keyword_hash,
            )
        )

    return normalized_list


def find_duplicate_hashes(
    normalized_keywords: list[NormalizedKeyword]
) -> dict[str, list[NormalizedKeyword]]:
    """Find duplicate keywords by hash.

    Args:
        normalized_keywords: List of normalized keywords.

    Returns:
        dict[str, list[NormalizedKeyword]]: Dictionary mapping hash to
            list of keywords with that hash. Only includes duplicates.
    """
    hash_map: dict[str, list[NormalizedKeyword]] = {}

    for nk in normalized_keywords:
        if nk.keyword_hash not in hash_map:
            hash_map[nk.keyword_hash] = []
        hash_map[nk.keyword_hash].append(nk)

    # Return only duplicates
    return {h: keywords for h, keywords in hash_map.items() if len(keywords) > 1}


def deduplicate_keywords(
    normalized_keywords: list[NormalizedKeyword]
) -> list[NormalizedKeyword]:
    """Remove duplicate keywords, keeping first occurrence.

    Args:
        normalized_keywords: List of normalized keywords.

    Returns:
        list[NormalizedKeyword]: List with duplicates removed.
    """
    seen_hashes = set()
    unique_list = []

    for nk in normalized_keywords:
        if nk.keyword_hash not in seen_hashes:
            seen_hashes.add(nk.keyword_hash)
            unique_list.append(nk)

    return unique_list
