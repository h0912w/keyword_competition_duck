"""qa_verifier module for KCPC.

QA verification using Google Search API for correlation analysis.
"""

import time
from dataclasses import dataclass
from typing import Literal

import requests

from kcpc.config import get_config
from kcpc.logging_config import get_logger
from kcpc.measurer import measure_keyword

logger = get_logger()


@dataclass
class GoogleSearchResult:
    """Result from Google Custom Search API."""

    search_information: dict
    total_results: int


@dataclass
class CorrelationAnalysis:
    """Analysis comparing DDG and Google results."""

    keyword: str
    ddg_count: int
    google_total_results: int
    correlation: Literal["high", "medium", "low", "none"]


def verify_with_google_api(
    keywords: list[str],
    max_queries: int | None = None,
) -> list[CorrelationAnalysis]:
    """Verify DDG measurements against Google Search API.

    Args:
        keywords: List of keywords to verify.
        max_queries: Maximum number of Google API queries to make.

    Returns:
        list[CorrelationAnalysis]: Correlation analysis for each keyword.
    """
    config = get_config()

    # Check if Google API is enabled
    if not config.qa_use_google_api:
        logger.info("Google API verification disabled (QA_USE_GOOGLE_API=false)")
        return []

    if not config.google_api_key or not config.google_search_engine_id:
        logger.warning("Google API credentials not configured, skipping verification")
        return []

    # Limit queries
    if max_queries is None:
        max_queries = config.qa_max_google_queries

    keywords_to_verify = keywords[:max_queries]
    logger.info(f"Verifying {len(keywords_to_verify)} keywords with Google API...")

    analyses = []

    for keyword in keywords_to_verify:
        try:
            # Get DDG measurement
            ddg_count = measure_keyword(keyword)
            if ddg_count is None:
                logger.warning(f"DDG measurement failed for '{keyword}', skipping")
                continue

            # Get Google measurement
            google_result = _search_google(keyword)
            google_total = _parse_total_results(google_result)

            # Analyze correlation
            correlation = _analyze_correlation(ddg_count, google_total)

            analysis = CorrelationAnalysis(
                keyword=keyword,
                ddg_count=ddg_count,
                google_total_results=google_total,
                correlation=correlation,
            )
            analyses.append(analysis)

            logger.info(
                f"Keyword '{keyword}': DDG={ddg_count}, Google={google_total:,}, "
                f"Correlation={correlation}"
            )

            # Delay between Google API requests
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error verifying '{keyword}': {e}")

    return analyses


def _search_google(keyword: str) -> GoogleSearchResult:
    """Search using Google Custom Search API.

    Args:
        keyword: The keyword to search for.

    Returns:
        GoogleSearchResult: Google search result information.

    Raises:
        Exception: If API request fails.
    """
    config = get_config()

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": config.google_api_key,
        "cx": config.google_search_engine_id,
        "q": keyword,
        "num": 1,  # We only need searchInformation, not actual results
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    return GoogleSearchResult(
        search_information=data.get("searchInformation", {}),
        total_results=int(data.get("searchInformation", {}).get("totalResults", "0").replace(",", "")),
    )


def _parse_total_results(result: GoogleSearchResult) -> int:
    """Parse total results from Google search result.

    Args:
        result: Google search result.

    Returns:
        int: Total number of search results.
    """
    return result.total_results


def _analyze_correlation(ddg_count: int, google_total: int) -> Literal["high", "medium", "low", "none"]:
    """Analyze correlation between DDG and Google results.

    Since DDG counts title matches in top 10 and Google counts total results,
    we analyze correlation based on result magnitude.

    Args:
        ddg_count: DDG measurement (0-10).
        google_total: Google total results.

    Returns:
        Correlation level.
    """
    # Very low competition (Google results < 1000)
    if google_total < 1000:
        if ddg_count == 0:
            return "high"
        elif ddg_count <= 2:
            return "medium"
        else:
            return "low"

    # Low competition (1000 - 10,000)
    elif google_total < 10000:
        if ddg_count == 0:
            return "low"
        elif ddg_count <= 5:
            return "medium"
        else:
            return "high"

    # Medium competition (10,000 - 100,000)
    elif google_total < 100000:
        if ddg_count == 0:
            return "low"
        elif ddg_count <= 7:
            return "high"
        else:
            return "high"

    # High competition (100,000+)
    else:
        if ddg_count >= 8:
            return "high"
        elif ddg_count >= 5:
            return "medium"
        else:
            return "low"


def generate_correlation_summary(analyses: list[CorrelationAnalysis]) -> str:
    """Generate a summary of correlation analysis.

    Args:
        analyses: List of correlation analyses.

    Returns:
        str: Formatted summary string.
    """
    if not analyses:
        return "No correlation analysis performed (Google API not configured or disabled)."

    lines = [
        "\n## DDG vs Google Correlation Analysis",
        "",
        "| Keyword | DDG Count | Google Total | Correlation |",
        "|---------|-----------|--------------|-------------|",
    ]

    high_count = sum(1 for a in analyses if a.correlation == "high")
    medium_count = sum(1 for a in analyses if a.correlation == "medium")
    low_count = sum(1 for a in analyses if a.correlation == "low")
    none_count = sum(1 for a in analyses if a.correlation == "none")

    for analysis in analyses:
        lines.append(
            f"| {analysis.keyword} | {analysis.ddg_count} | {analysis.google_total_results:,} | {analysis.correlation} |"
        )

    lines.extend([
        "",
        f"**Summary:** High: {high_count}, Medium: {medium_count}, Low: {low_count}, None: {none_count}",
        "",
        "> **Note:** Google API returns total results while DDG counts title matches in top 10.",
        "> Correlation is based on result magnitude patterns, not direct numerical comparison.",
    ])

    return "\n".join(lines)
