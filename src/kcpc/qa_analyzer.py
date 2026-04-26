"""qa_analyzer module for KCPC.

Statistical analysis and DDG parameter optimization for QA.
"""

import time
from dataclasses import dataclass
from typing import Literal

from kcpc.config import get_config
from kcpc.logging_config import get_logger
from kcpc.measurer import measure_keyword

logger = get_logger()


@dataclass
class ParameterTestResult:
    """Result from DDG parameter A-B test."""

    parameter_name: str
    value_a: any
    value_b: any
    count_a: int
    count_b: int
    difference: int
    recommendation: Literal["A", "B", "NEUTRAL"]


def ab_test_timelimit(keyword: str, timelimit_a: str, timelimit_b: str) -> ParameterTestResult:
    """A-B test timelimit parameter.

    Args:
        keyword: Test keyword.
        timelimit_a: First timelimit value (d/w/m/y).
        timelimit_b: Second timelimit value.

    Returns:
        ParameterTestResult: Test result.
    """
    from duckduckgo_search import DDGS

    ddgs = DDGS()

    try:
        # Test timelimit A
        results_a = list(ddgs.text(keyword, timelimit=timelimit_a, max_results=10))
        count_a = sum(1 for r in results_a if keyword.lower() in r.get("title", "").lower())

        time.sleep(2)

        # Test timelimit B
        results_b = list(ddgs.text(keyword, timelimit=timelimit_b, max_results=10))
        count_b = sum(1 for r in results_b if keyword.lower() in r.get("title", "").lower())

        difference = abs(count_a - count_b)

        # Recommendation based on result count
        if count_a > count_b:
            recommendation = "A"
        elif count_b > count_a:
            recommendation = "B"
        else:
            recommendation = "NEUTRAL"

        logger.info(f"Timelimit A-B test for '{keyword}': {timelimit_a}={count_a}, {timelimit_b}={count_b}, "
                    f"difference={difference}, recommendation={recommendation}")

        return ParameterTestResult(
            parameter_name="timelimit",
            value_a=timelimit_a,
            value_b=timelimit_b,
            count_a=count_a,
            count_b=count_b,
            difference=difference,
            recommendation=recommendation
        )

    except Exception as e:
        logger.error(f"Timelimit A-B test error for '{keyword}': {e}")
        return ParameterTestResult(
            parameter_name="timelimit",
            value_a=timelimit_a,
            value_b=timelimit_b,
            count_a=-1,
            count_b=-1,
            difference=-1,
            recommendation="NEUTRAL"
        )


def ab_test_max_results(keyword: str, max_a: int, max_b: int) -> ParameterTestResult:
    """A-B test max_results parameter.

    Args:
        keyword: Test keyword.
        max_a: First max_results value.
        max_b: Second max_results value.

    Returns:
        ParameterTestResult: Test result.
    """
    from duckduckgo_search import DDGS

    ddgs = DDGS()

    try:
        # Test max_results A
        results_a = list(ddgs.text(keyword, max_results=max_a))
        count_a = min(max_a, len([r for r in results_a if keyword.lower() in r.get("title", "").lower()]))

        time.sleep(2)

        # Test max_results B
        results_b = list(ddgs.text(keyword, max_results=max_b))
        count_b = min(max_b, len([r for r in results_b if keyword.lower() in r.get("title", "").lower()]))

        difference = abs(count_a - count_b)

        if count_a > count_b:
            recommendation = "A"
        elif count_b > count_a:
            recommendation = "B"
        else:
            recommendation = "NEUTRAL"

        logger.info(f"Max results A-B test for '{keyword}': {max_a}={count_a}, {max_b}={count_b}, "
                    f"difference={difference}, recommendation={recommendation}")

        return ParameterTestResult(
            parameter_name="max_results",
            value_a=max_a,
            value_b=max_b,
            count_a=count_a,
            count_b=count_b,
            difference=difference,
            recommendation=recommendation
        )

    except Exception as e:
        logger.error(f"Max results A-B test error for '{keyword}": {e}")
        return ParameterTestResult(
            parameter_name="max_results",
            value_a=max_a,
            value_b=max_b,
            count_a=-1,
            count_b=-1,
            difference=-1,
            recommendation="NEUTRAL"
        )


def calculate_keyword_type_score(keyword: str) -> Literal["brand", "generic", "longtail"]:
    """Analyze keyword type.

    Args:
        keyword: The keyword to analyze.

    Returns:
        Keyword type: brand, generic, or longtail.
    """
    # Brand indicators (starts with capital)
    if keyword[0].isupper() and len(keyword.split()) <= 2:
        return "brand"

    # Long tail indicators (3+ words)
    word_count = len(keyword.split())
    if word_count >= 3:
        return "longtail"

    # Generic
    return "generic"


def analyze_keyword_type_pattern(keywords: list[str]) -> dict[Literal["brand", "generic", "longtail"], list[int]]:
    """Analyze DDG results by keyword type.

    Args:
        keywords: List of keywords to analyze.

    Returns:
        Dictionary mapping keyword type to list of DDG result counts.
    """
    from duckduckgo_search import DDGS

    ddgs = DDGS()
    type_counts = {"brand": [], "generic": [], "longtail": []}

    for keyword in keywords:
        try:
            keyword_type = calculate_keyword_type_score(keyword)

            results = list(ddgs.text(keyword, max_results=10))
            count = sum(1 for r in results if keyword.lower() in r.get("title", "").lower())

            type_counts[keyword_type].append(count)
            time.sleep(2)

        except Exception as e:
            logger.error(f"Keyword type analysis error for '{keyword}': {e}")

    return type_counts


def calculate_correlation_coefficient(x_values: list[float], y_values: list[float]) -> dict:
    """Calculate Pearson and Spearman correlation coefficients.

    Args:
        x_values: First set of values.
        y_values: Second set of values.

    Returns:
        Dictionary with pearson and spearman coefficients.
    """
    import math

    n = len(x_values)
    if n != len(y_values) or n < 2:
        return {"pearson": 0.0, "spearman": 0.0}

    # Pearson correlation
    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in x_values))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in y_values))

    if denominator_x == 0 or denominator_y == 0:
        pearson = 0.0
    else:
        pearson = numerator / (denominator_x * denominator_y)

    # Spearman correlation (rank-based)
    def get_ranks(values):
        sorted_values = sorted([(v, i) for i, v in enumerate(values)], key=lambda x: x[0])
        ranks = [0] * len(values)
        for rank, (value, original_index) in enumerate(sorted_values):
            ranks[original_index] = rank + 1
        return ranks

    rank_x = get_ranks(x_values)
    rank_y = get_ranks(y_values)

    mean_rank_x = sum(rank_x) / n
    mean_rank_y = sum(rank_y) / n

    numerator_rank = sum((rx - mean_rank_x) * (ry - mean_rank_y) for rx, ry in zip(rank_x, rank_y))
    denominator_rank_x = math.sqrt(sum((rx - mean_rank_x) ** 2 for rx in rank_x))
    denominator_rank_y = math.sqrt(sum((ry - mean_rank_y) ** 2 for ry in rank_y))

    if denominator_rank_x == 0 or denominator_rank_y == 0:
        spearman = 0.0
    else:
        spearman = numerator_rank / (denominator_rank_x * denominator_rank_y)

    logger.info(f"Correlation coefficients: pearson={pearson:.3f}, spearman={spearman:.3f}")

    return {
        "pearson": pearson,
        "spearman": spearman
    }


def calculate_confidence_interval_bootstrap(values: list[int], n_bootstrap: int = 1000, confidence: float = 0.95) -> dict:
    """Calculate confidence interval using bootstrap method.

    Args:
        values: List of measurement values.
        n_bootstrap: Number of bootstrap iterations.
        confidence: Confidence level (default 0.95).

    Returns:
        Dictionary with confidence interval bounds and mean.
    """
    import random

    if not values:
        return {"lower": 0, "upper": 0, "mean": 0}

    n = len(values)
    bootstrap_means = []

    for _ in range(n_bootstrap):
        sample = random.choices(values, k=n)
        bootstrap_means.append(sum(sample) / n)

    bootstrap_means.sort()

    alpha = 1 - confidence
    lower_index = int((alpha / 2) * n_bootstrap)
    upper_index = int((1 - alpha / 2) * n_bootstrap)

    return {
        "lower": bootstrap_means[lower_index],
        "upper": bootstrap_means[upper_index],
        "mean": sum(values) / n
    }
