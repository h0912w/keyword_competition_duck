"""measurer module for KCPC.

Handles DuckDuckGo search requests with bypass options.
"""

import random
import time
from dataclasses import dataclass

from duckduckgo_search import DDGS

from kcpc.config import get_config
from kcpc.exceptions import MeasurementError
from kcpc.file_io import load_proxies, load_user_agents
from kcpc.logging_config import get_logger

logger = get_logger()


@dataclass
class SearchResult:
    """Represents a single search result."""

    title: str
    url: str
    body: str


def measure_keyword(
    keyword: str,
    proxy_index: int = 0,
    ua_index: int = 0,
) -> int | None:
    """Measure keyword by performing DuckDuckGo search.

    Args:
        keyword: The keyword to measure.
        proxy_index: Starting index for proxy rotation.
        ua_index: Starting index for User-Agent rotation.

    Returns:
        int | None: Number of top 10 results with keyword in title (0-10),
            or None if measurement fails after all retries.
    """
    config = get_config()

    # Load bypass options
    proxies = []
    user_agents = []

    if config.ddg_use_proxy:
        proxies = load_proxies(config.ddg_proxy_list)
        if not proxies:
            logger.warning("DDG_USE_PROXY=true but no proxies loaded, using direct connection")

    if config.ddg_rotate_ua:
        user_agents = load_user_agents(config.ddg_ua_list)
        if not user_agents:
            logger.warning("DDG_ROTATE_UA=true but no User-Agents loaded, using default")

    # Try with exponential backoff
    for retry in range(config.ddg_max_retries):
        try:
            return _attempt_search(
                keyword,
                proxies,
                user_agents,
                proxy_index,
                ua_index,
                retry,
            )

        except MeasurementError as e:
            wait_time = 2 ** retry  # Exponential backoff: 2, 4, 8 seconds

            if retry < config.ddg_max_retries - 1:
                logger.warning(
                    f"DDG request failed for '{keyword}' (attempt {retry + 1}/{config.ddg_max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    f"DDG request failed for '{keyword}' after {config.ddg_max_retries} attempts: {e}"
                )

    return None


def _attempt_search(
    keyword: str,
    proxies: list[str],
    user_agents: list[str],
    proxy_index: int,
    ua_index: int,
    retry: int,
) -> int:
    """Attempt a single search request.

    Args:
        keyword: The keyword to search for.
        proxies: List of proxy URLs.
        user_agents: List of User-Agent strings.
        proxy_index: Current proxy index.
        ua_index: Current User-Agent index.
        retry: Current retry attempt number.

    Returns:
        int: Number of top 10 results with keyword in title.

    Raises:
        MeasurementError: If the search request fails.
    """
    config = get_config()

    # Select User-Agent
    if user_agents and config.ddg_rotate_ua:
        ua = user_agents[ua_index % len(user_agents)]
    else:
        ua = config.ddg_user_agent

    # Select proxy
    proxy = None
    if proxies and config.ddg_use_proxy:
        proxy = proxies[proxy_index % len(proxies)]

    # Build DDGS parameters
    ddgs_params: dict = {}

    # Build headers with User-Agent
    headers = {"User-Agent": ua}

    # Apply bypass options
    if proxy:
        ddgs_params["proxy"] = proxy
        logger.debug(f"Using proxy: {proxy}")

    # SSL verification
    verify_ssl = not config.ddg_ignore_ssl
    ddgs_params["verify"] = verify_ssl

    # Timeout
    ddgs_params["timeout"] = config.ddg_timeout

    try:
        # Create DDGS instance with headers
        ddgs = DDGS(headers=headers, **ddgs_params)

        # Perform search (intitle: operator is unreliable in DDG)
        # We rely on 2nd validation to count title matches instead
        query = keyword
        logger.debug(f"Searching for: {query}")

        results = list(ddgs.text(
            query,
            max_results=config.ddg_max_results,
        ))

        # Count title matches
        match_count = _count_title_matches(results, keyword)

        logger.info(f"Measured '{keyword}' -> {match_count} matches")

        # Apply delay before next request (unless disabled)
        if not config.ddg_ignore_delay:
            delay = random.uniform(config.ddg_min_delay, config.ddg_max_delay)
            time.sleep(delay)

        return match_count

    except Exception as e:
        raise MeasurementError(f"Search failed: {e}") from e


def _count_title_matches(results: list[dict], keyword: str) -> int:
    """Count how many results have the keyword in their title.

    Args:
        results: List of search result dictionaries.
        keyword: The keyword to search for in titles.

    Returns:
        int: Number of results with keyword in title (case-insensitive).
    """
    if not results:
        return 0

    keyword_lower = keyword.lower()
    match_count = 0

    for result in results:
        title = result.get("title", "")
        if title and keyword_lower in title.lower():
            match_count += 1

    return match_count
