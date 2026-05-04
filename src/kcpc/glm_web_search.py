r"""GLM API Web Search module for KCPC.

Uses GLM API to perform Google search and return result counts.
This is the official web search verification method for QA.

Based on working project at C:\Users\h0912\claude_project\GLM_WEBSEARCH
"""

import json
import os
import re
import time
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import requests
from dotenv import load_dotenv

from kcpc.logging_config import get_logger

logger = get_logger()

# Load environment variables
load_dotenv()

GLM_API_KEY = os.environ.get("GLM_API_KEY")
GLM_BASE_URL = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/anthropic/v1/messages")
GLM_MODEL = os.environ.get("GLM_MODEL", "glm-4.7")

# Search delay settings to prevent blocking
GLM_SEARCH_MIN_DELAY = 2
GLM_SEARCH_MAX_DELAY = 3


@dataclass
class GLMSearchResult:
    """Result from GLM API Google search."""

    keyword: str
    ddg_count: int
    google_result_count: int
    google_estimate: str
    correlation: Literal["high", "medium", "low", "none"]
    notes: str


class RateLimitTracker:
    """Track API request rate to avoid blocking."""

    def __init__(self, rpm_limit: int = 30, min_interval: float = 2.0):
        self.rpm_limit = rpm_limit
        self.min_interval = min_interval
        self.requests = []
        self.request_window = 60
        self.last_request_time = 0

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.request_window]
        while len(self.requests) >= self.rpm_limit:
            time.sleep(1)
            now = time.time()
            self.requests = [t for t in self.requests if now - t < self.request_window]
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        jitter = random.uniform(0.1, 0.3)
        time.sleep(jitter)

    def record_request(self):
        """Record a request was made."""
        self.last_request_time = time.time()
        self.requests.append(self.last_request_time)


class GLMClient:
    """GLM API client using Anthropic-compatible endpoint."""

    _rate_tracker: Optional[RateLimitTracker] = None

    @classmethod
    def get_rate_tracker(cls) -> RateLimitTracker:
        """Get or create rate tracker instance."""
        if cls._rate_tracker is None:
            cls._rate_tracker = RateLimitTracker(rpm_limit=30, min_interval=2.0)
        return cls._rate_tracker

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "glm-4.7",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url or GLM_BASE_URL
        self.model = model
        self.timeout = timeout

        self.session = requests.Session()
        # IMPORTANT: Use Authorization: Bearer header, not x-api-key
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        })
        self.rate_tracker = self.get_rate_tracker()

    def search(self, query: str, max_retries: int = 3) -> dict:
        """Search using GLM API with inference prompt.

        Uses a simple inference prompt asking GLM to estimate how many
        web pages mention the keyword. This is the proven working method.
        """
        self.rate_tracker.wait_if_needed()

        # Simple inference prompt - NO web_search tool
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": f"If you had to guess, approximately how many web pages mention '{query}'? Just give me a number between 0 and 10000000000."
                }
            ],
            "max_tokens": 30,
            "temperature": 0.5
        }

        last_error = None
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                logger.info(f"Sending GLM request (attempt {attempt + 1}) to {self.base_url}")

                response = self.session.post(
                    self.base_url,
                    json=payload,
                    timeout=self.timeout
                )

                logger.info(f"GLM response status: {response.status_code}")

                if response.status_code == 429:
                    delay = base_delay * (2 ** attempt)
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        continue
                    else:
                        raise ConnectionError("Rate limit exceeded. Please try again later.")

                response.raise_for_status()
                result = response.json()

                # Convert Anthropic format to standard format
                normalized = self._normalize_anthropic_response(result)
                logger.info(f"GLM response content: {normalized.get('choices', [{}])[0].get('message', {}).get('content', '')}")

                self.rate_tracker.record_request()
                return normalized

            except requests.exceptions.Timeout:
                last_error = TimeoutError(f"Request timed out after {self.timeout} seconds")
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    raise last_error

            except requests.exceptions.HTTPError as e:
                logger.error(f"GLM HTTP Error: {e.response.status_code}")
                try:
                    error_data = e.response.json()
                    logger.error(f"Error details: {error_data}")
                except:
                    pass

                if e.response.status_code == 401:
                    raise ConnectionError("Invalid API key.")
                elif e.response.status_code == 429:
                    delay = base_delay * (2 ** attempt)
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        continue
                    else:
                        raise ConnectionError("Rate limit exceeded. Please try again later.")
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    raise ConnectionError(f"GLM API request failed: {e}")

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    raise ConnectionError(f"GLM API request failed: {e}")

        raise last_error or ConnectionError("Failed to complete request after maximum retries")

    def _normalize_anthropic_response(self, result: dict) -> dict:
        """Convert Anthropic v1 messages format to standard choices format."""
        content = ""
        if "content" in result:
            if isinstance(result["content"], list):
                for item in result["content"]:
                    if item.get("type") == "text":
                        content += item.get("text", "")
            else:
                content = str(result["content"])

        return {
            "choices": [
                {
                    "message": {
                        "content": content
                    }
                }
            ]
        }

    def close(self):
        """Close the session."""
        try:
            self.session.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def extract_count_from_response(content: str) -> int:
    """Extract count from GLM response with multiple strategies.

    Google search results can range from 0 to trillions for common words.
    Increased max limit to 1 trillion to handle very common words.
    """
    content = str(content).strip()

    strategies = [
        # Try exact integer first
        lambda c: int(c) if c.isdigit() else _raise_value_error(),
        # Try comma-separated number
        lambda c: int(c.replace(',', '')) if re.match(r'^[\d,]+$', c) else _raise_value_error(),
        # Try to find number in text
        lambda c: int(re.search(r'\b([\d,]+)\b', c).group(1).replace(',', '')) if re.search(r'\b([\d,]+)\b', c) else _raise_value_error(),
    ]

    for strategy in strategies:
        try:
            count = strategy(content)
            # Increased max limit from 10B to 1T (1,000,000,000,000)
            # Common words like "the", "and", "not" can have 500B+ results
            if 0 <= count <= 1_000_000_000_000:  # Sanity check
                return count
            else:
                logger.warning(f"Extracted count {count} exceeds max limit, capping at 1T")
                return 1_000_000_000_000
        except (ValueError, AttributeError):
            continue

    # Default fallback if no number found
    logger.warning(f"Could not extract valid count from: {content}, using default")
    return 0


def _raise_value_error():
    """Helper to raise ValueError in lambda."""
    raise ValueError("No match")


def estimate_from_count(count: int) -> Literal["high", "medium", "low", "none"]:
    """Convert result count to volume estimate."""
    if count == 0:
        return "none"
    elif count < 100:
        return "low"
    elif count < 100000:
        return "medium"
    else:
        return "high"


def calculate_correlation(ddg_count: int, google_estimate: str) -> Literal["high", "medium", "low", "none"]:
    """Calculate correlation between DDG count and Google estimate."""
    # Map DDG count to volume level
    if ddg_count == 0:
        ddg_level = 0  # none
    elif ddg_count <= 3:
        ddg_level = 1  # low
    elif ddg_count <= 6:
        ddg_level = 2  # medium
    else:
        ddg_level = 3  # high

    # Map Google estimate to level
    google_levels = {"none": 0, "low": 1, "medium": 2, "high": 3}
    google_level = google_levels.get(google_estimate, 2)

    # Calculate correlation based on level difference
    diff = abs(ddg_level - google_level)

    if diff == 0:
        return "high"
    elif diff == 1:
        return "medium"
    else:
        return "low"


def search_google_via_glm(keyword: str) -> dict:
    """Search Google using GLM API inference.

    This function uses GLM API with a simple inference prompt to estimate
    how many web pages mention the keyword. This is the proven working method
    from the GLM_WEBSEARCH project.

    Args:
        keyword: The search keyword.

    Returns:
        dict: Contains google_result_count (int), google_estimate (str),
              and raw_response (str).
    """
    if not GLM_API_KEY:
        raise ValueError("GLM_API_KEY not set in environment")

    try:
        with GLMClient(
            api_key=GLM_API_KEY,
            base_url=GLM_BASE_URL,
            model=GLM_MODEL,
            timeout=30
        ) as client:
            result = client.search(keyword)

            if not result:
                raise ValueError("Empty response from GLM API")

            if "choices" not in result:
                raise ValueError(f"Invalid GLM API response format: missing 'choices' field")

            if not result["choices"]:
                raise ValueError("GLM API returned no choices")

            choice = result["choices"][0]

            if "message" not in choice:
                raise ValueError("Invalid GLM API response format: missing 'message' field")

            message = choice["message"]

            if "content" not in message:
                raise ValueError("Invalid GLM API response format: missing 'content' field")

            content = str(message["content"]).strip()

            if not content:
                raise ValueError("Empty content in GLM API response")

            logger.info(f"GLM raw response: {content}")

            count = extract_count_from_response(content)
            logger.info(f"Extracted count: {count}")

            return {
                "google_result_count": count,
                "google_estimate": estimate_from_count(count),
                "raw_response": content.strip(),
                "success": True
            }

    except ValueError as e:
        logger.error(f"GLM API value error: {e}")
        return {
            "google_result_count": 0,
            "google_estimate": "none",
            "raw_response": f"Value Error: {str(e)}",
            "success": False
        }
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"GLM API connection error: {e}")
        return {
            "google_result_count": 0,
            "google_estimate": "none",
            "raw_response": f"Connection Error: {str(e)}",
            "success": False
        }
    except Exception as e:
        logger.error(f"GLM API unexpected error: {e}")
        return {
            "google_result_count": 0,
            "google_estimate": "none",
            "raw_response": f"Unexpected Error: {str(e)}",
            "success": False
        }


def verify_keywords_with_glm(keywords: list[tuple[str, int]]) -> list[GLMSearchResult]:
    """Verify multiple keywords using GLM API Google search.

    Args:
        keywords: List of (keyword, ddg_count) tuples.

    Returns:
        list[GLMSearchResult]: Verification results.
    """
    results = []

    for i, (keyword, ddg_count) in enumerate(keywords):
        logger.info(f"Searching Google via GLM {i+1}/{len(keywords)}: {keyword}")

        # Random delay between requests
        if i > 0:
            delay = random.uniform(GLM_SEARCH_MIN_DELAY, GLM_SEARCH_MAX_DELAY)
            logger.info(f"Waiting {delay:.1f} seconds...")
            time.sleep(delay)

        # Perform search
        search_result = search_google_via_glm(keyword)

        # Extract data
        google_count = search_result.get("google_result_count", 0)
        google_estimate = search_result.get("google_estimate", "none")

        # Calculate correlation
        correlation = calculate_correlation(ddg_count, google_estimate)

        # Create result
        result = GLMSearchResult(
            keyword=keyword,
            ddg_count=ddg_count,
            google_result_count=google_count,
            google_estimate=google_estimate,
            correlation=correlation,
            notes=search_result.get("raw_response", "")[:200]
        )

        results.append(result)
        logger.info(f"Result: {google_estimate} (count: {google_count}, correlation: {correlation})")

    return results


def save_glm_results(results: list[GLMSearchResult], output_path: str = "./output/qa/glm_websearch_results.json") -> None:
    """Save GLM web search results to JSON file.

    Args:
        results: List of GLMSearchResult objects.
        output_path: Path to save the results.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "timestamp": datetime.now().isoformat(),
        "method": "GLM API Google Search (Inference via Anthropic-compatible endpoint)",
        "model": GLM_MODEL,
        "endpoint": GLM_BASE_URL,
        "results": [
            {
                "keyword": r.keyword,
                "ddg_count": r.ddg_count,
                "google_result_count": r.google_result_count,
                "google_estimate": r.google_estimate,
                "correlation": r.correlation,
                "notes": r.notes
            }
            for r in results
        ]
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"GLM web search results saved to {output_path}")


if __name__ == "__main__":
    # Test GLM Google search
    test_keywords = [
        ("python", 8),
        ("programming", 6),
        ("xyzqwerty123", 1)
    ]

    print("=" * 70)
    print("GLM API Google Search Test")
    print("=" * 70)
    print(f"API Key: {'✓ Set' if GLM_API_KEY else '✗ NOT SET'}")
    print(f"Model: {GLM_MODEL}")
    print(f"Endpoint: {GLM_BASE_URL}")
    print("=" * 70)
    print()

    try:
        results = verify_keywords_with_glm(test_keywords)

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()

        for r in results:
            print(f"Keyword:        {r.keyword}")
            print(f"DDG Count:       {r.ddg_count}")
            print(f"Google Count:    {r.google_result_count:,}")
            print(f"Google Estimate: {r.google_estimate}")
            print(f"Correlation:     {r.correlation}")
            print(f"Notes:           {r.notes}")
            print("-" * 70)

        # Save results
        save_glm_results(results)
        print(f"\nResults saved to: ./output/qa/glm_websearch_results.json")

        # Calculate statistics
        total = len(results)
        high_corr = sum(1 for r in results if r.correlation == "high")
        medium_corr = sum(1 for r in results if r.correlation == "medium")
        low_corr = sum(1 for r in results if r.correlation == "low")

        print("\n" + "=" * 70)
        print("STATISTICS")
        print("=" * 70)
        print(f"Total:        {total}")
        print(f"High:         {high_corr} ({high_corr/total*100:.1f}%)")
        print(f"Medium:       {medium_corr} ({medium_corr/total*100:.1f}%)")
        print(f"Low:          {low_corr} ({low_corr/total*100:.1f}%)")

    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nTo use GLM API Google search:")
        print("1. Get API key from https://open.bigmodel.cn/")
        print("2. Add to .env: GLM_API_KEY=your_key_here")
        print("3. Ensure GLM_BASE_URL=https://api.z.ai/api/anthropic/v1/messages")
