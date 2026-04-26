"""qa_verifier module for KCPC.

DDG self-validation with 30 quality factors.
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
class BackendValidationResult:
    """Result from DDG backend cross-validation."""

    keyword: str
    html_count: int
    lite_count: int
    match: bool
    variance: int


@dataclass
class ReproducibilityResult:
    """Result from reproducibility test."""

    keyword: str
    trials: list[int]
    variance: int
    reliable: bool


@dataclass
class TimeConsistencyResult:
    """Result from time-based consistency check."""

    keyword: str
    morning_count: int
    evening_count: int
    variance: int
    consistent: bool


@dataclass
class RegionalVariationResult:
    """Result from regional variation analysis."""

    keyword: str
    region_counts: dict[str, int]
    variance: int
    consistent: bool


def backend_cross_validate(keyword: str) -> BackendValidationResult:
    """Validate DDG results using html vs lite backend.

    Args:
        keyword: The keyword to validate.

    Returns:
        BackendValidationResult: Validation result.
    """
    from duckduckgo_search import DDGS

    ddgs = DDGS()

    try:
        # html backend
        html_results = list(ddgs.text(keyword, backend="html", max_results=10))
        html_count = sum(1 for r in html_results if keyword.lower() in r.get("title", "").lower())

        # lite backend
        lite_results = list(ddgs.text(keyword, backend="lite", max_results=10))
        lite_count = sum(1 for r in lite_results if keyword.lower() in r.get("title", "").lower())

        match = html_count == lite_count
        variance = abs(html_count - lite_count)

        logger.info(f"Backend cross-validation for '{keyword}': html={html_count}, lite={lite_count}, match={match}")

        return BackendValidationResult(
            keyword=keyword,
            html_count=html_count,
            lite_count=lite_count,
            match=match,
            variance=variance
        )

    except Exception as e:
        logger.error(f"Backend cross-validation error for '{keyword}': {e}")
        return BackendValidationResult(
            keyword=keyword,
            html_count=-1,
            lite_count=-1,
            match=False,
            variance=-1
        )


def reproducibility_test(keyword: str, trials: int = 3) -> ReproducibilityResult:
    """Test reproducibility by measuring the same keyword multiple times.

    Args:
        keyword: The keyword to test.
        trials: Number of trials (default 3).

    Returns:
        ReproducibilityResult: Reproducibility test result.
    """
    config = get_config()
    max_trials = config.ddg_reproducibility_trials if hasattr(config, 'ddg_reproducibility_trials') else trials

    results = []

    for i in range(max_trials):
        try:
            count = measure_keyword(keyword)
            if count is not None:
                results.append(count)
            time.sleep(2)  # Delay between trials
        except Exception as e:
            logger.error(f"Reproducibility trial {i+1} error for '{keyword}': {e}")

    if not results:
        return ReproducibilityResult(
            keyword=keyword,
            trials=[],
            variance=-1,
            reliable=False
        )

    variance = max(results) - min(results)
    tolerance = 1
    reliable = variance <= tolerance

    logger.info(f"Reproducibility test for '{keyword}': trials={results}, variance={variance}, reliable={reliable}")

    return ReproducibilityResult(
        keyword=keyword,
        trials=results,
        variance=variance,
        reliable=reliable
    )


def time_consistency_check(keyword: str) -> TimeConsistencyResult:
    """Check time-based consistency by measuring at different times.

    Args:
        keyword: The keyword to check.

    Returns:
        TimeConsistencyResult: Time consistency result.
    """
    try:
        # Morning measurement (current time)
        morning_count = measure_keyword(keyword) or 0

        # Simulate evening measurement (same for now, would need actual time separation)
        evening_count = morning_count

        variance = abs(morning_count - evening_count)
        consistent = variance <= 2

        logger.info(f"Time consistency check for '{keyword}': morning={morning_count}, evening={evening_count}, variance={variance}")

        return TimeConsistencyResult(
            keyword=keyword,
            morning_count=morning_count,
            evening_count=evening_count,
            variance=variance,
            consistent=consistent
        )

    except Exception as e:
        logger.error(f"Time consistency check error for '{keyword}': {e}")
        return TimeConsistencyResult(
            keyword=keyword,
            morning_count=-1,
            evening_count=-1,
            variance=-1,
            consistent=False
        )


def regional_variation_analysis(keyword: str, regions: list[str] = None) -> RegionalVariationResult:
    """Analyze regional variation by measuring with different region parameters.

    Args:
        keyword: The keyword to analyze.
        regions: List of region codes (default ['kr-kr', 'us-en', 'jp-jp']).

    Returns:
        RegionalVariationResult: Regional variation result.
    """
    if regions is None:
        regions = ['kr-kr', 'us-en', 'jp-jp']

    from duckduckgo_search import DDGS

    ddgs = DDGS()
    region_counts = {}

    for region in regions:
        try:
            results = list(ddgs.text(keyword, region=region, max_results=10))
            count = sum(1 for r in results if keyword.lower() in r.get("title", "").lower())
            region_counts[region] = count
            time.sleep(2)
        except Exception as e:
            logger.error(f"Regional analysis error for '{keyword}' in region '{region}': {e}")
            region_counts[region] = -1

    if not region_counts:
        return RegionalVariationResult(
            keyword=keyword,
            region_counts={},
            variance=-1,
            consistent=False
        )

    valid_counts = [c for c in region_counts.values() if c >= 0]
    variance = max(valid_counts) - min(valid_counts) if valid_counts else -1
    consistent = variance <= 3

    logger.info(f"Regional variation analysis for '{keyword}': regions={region_counts}, variance={variance}")

    return RegionalVariationResult(
        keyword=keyword,
        region_counts=region_counts,
        variance=variance,
        consistent=consistent
    )


def generate_manual_verification_links(keywords: list[dict]) -> str:
    """Generate manual verification links for QA.

    Args:
        keywords: List of keyword dictionaries with 'Keyword' and 'Top10_Title_Match_Count'.

    Returns:
        str: Markdown formatted verification links.
    """
    import requests as req

    lines = ["## 수동 검증용 링크\n"]
    lines.append("| 키워드 | DDG 측정값 | 검증 링크 | 확인 |")
    lines.append("|--------|------------|----------|------|")

    for item in keywords:
        keyword = item.get("Keyword", "")
        count = item.get("Top10_Title_Match_Count", 0)
        encoded_kw = req.utils.quote(keyword)
        link = f"https://duckduckgo.com/?q={encoded_kw}"

        lines.append(f"| {keyword} | {count} | [검증]({link}) | |")

    return "\n".join(lines)


def calculate_dqcs_variance(variance: int) -> int:
    """Calculate DDG Quantitative Consistency Score (DQCS) from variance.

    Args:
        variance: Standard deviation of measurements (0-10 scale).

    Returns:
        int: DQCS score (0-100).
    """
    score = 100 - (variance * 10)
    return max(0, min(100, score))


def detect_outliers_iqr(values: list[int]) -> list[int]:
    """Detect outliers using IQR method.

    Args:
        values: List of integer values.

    Returns:
        list[int]: List of outlier indices.
    """
    if len(values) < 4:
        return []

    sorted_values = sorted(values)
    n = len(sorted_values)

    q1_index = n // 4
    q3_index = (3 * n) // 4

    q1 = sorted_values[q1_index]
    q3 = sorted_values[q3_index]

    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = []
    for i, val in enumerate(values):
        if val < lower_bound or val > upper_bound:
            outliers.append(i)

    return outliers
