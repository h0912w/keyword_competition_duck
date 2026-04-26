"""title_validator module for KCPC.

Validates title field matching for search results.
"""

from typing import Literal


def validate_title_match(
    results: list[dict] | None,
    keyword: str,
) -> int:
    """Count how many search results have the keyword in their title.

    Performs case-insensitive substring matching.

    Args:
        results: List of search result dictionaries from DDG.
        keyword: The keyword to search for in titles.

    Returns:
        int: Number of results (0-10) with keyword in title.
            Returns -1 if results structure is invalid.
    """
    if results is None:
        return -1

    if not isinstance(results, list):
        return -1

    keyword_lower = keyword.lower()
    match_count = 0

    for result in results[:10]:  # Only check top 10
        if not isinstance(result, dict):
            return -1

        title = result.get("title", "")
        if not isinstance(title, str):
            return -1

        if title and keyword_lower in title.lower():
            match_count += 1

    return match_count


def is_valid_result_structure(results: list[dict] | None) -> bool:
    """Check if search results have valid structure.

    Args:
        results: List of search result dictionaries.

    Returns:
        bool: True if structure is valid, False otherwise.
    """
    if results is None:
        return False

    if not isinstance(results, list):
        return False

    for result in results:
        if not isinstance(result, dict):
            return False

        if "title" not in result:
            return False

    return True
