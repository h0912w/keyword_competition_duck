"""file_io module for KCPC.

Handles input file parsing and bypass file loading.
"""

from pathlib import Path
from typing import Literal

import pandas as pd

from kcpc.exceptions import FileIOError


def parse_input_file(file_path: str) -> list[tuple[int, str]]:
    """Parse input file and extract keywords from the first column.

    Args:
        file_path: Path to the input file (.txt, .csv, or .xlsx).

    Returns:
        list[tuple[int, str]]: List of (original_index, keyword) tuples.

    Raises:
        FileIOError: If file format is not supported or parsing fails.
        ValidationError: If no valid keywords are found.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileIOError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        return _parse_txt(path)
    elif suffix == ".csv":
        return _parse_csv(path)
    elif suffix in (".xlsx", ".xls"):
        return _parse_excel(path)
    else:
        raise FileIOError(
            f"Unsupported file format: {suffix}. "
            "Supported formats: .txt, .csv, .xlsx"
        )


def _parse_txt(path: Path) -> list[tuple[int, str]]:
    """Parse .txt file (one keyword per line).

    Args:
        path: Path to the .txt file.

    Returns:
        list[tuple[int, str]]: List of (original_index, keyword) tuples.
    """
    keywords = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                keyword = line.strip()
                if keyword:  # Skip empty lines
                    keywords.append((idx, keyword))
    except UnicodeDecodeError:
        # Try with different encoding
        with open(path, "r", encoding="utf-8-sig") as f:
            for idx, line in enumerate(f):
                keyword = line.strip()
                if keyword:
                    keywords.append((idx, keyword))

    return keywords


def _parse_csv(path: Path) -> list[tuple[int, str]]:
    """Parse .csv file (first column).

    Args:
        path: Path to the .csv file.

    Returns:
        list[tuple[int, str]]: List of (original_index, keyword) tuples.
    """
    try:
        df = pd.read_csv(path, header=None)
    except UnicodeDecodeError:
        df = pd.read_csv(path, header=None, encoding="utf-8-sig")

    return _extract_keywords_from_df(df)


def _parse_excel(path: Path) -> list[tuple[int, str]]:
    """Parse .xlsx file (first column).

    Args:
        path: Path to the Excel file.

    Returns:
        list[tuple[int, str]]: List of (original_index, keyword) tuples.
    """
    df = pd.read_excel(path, header=None)
    return _extract_keywords_from_df(df)


def _extract_keywords_from_df(df: pd.DataFrame) -> list[tuple[int, str]]:
    """Extract keywords from the first column of a DataFrame.

    Args:
        df: pandas DataFrame.

    Returns:
        list[tuple[int, str]]: List of (original_index, keyword) tuples.
    """
    keywords = []
    first_column = df.iloc[:, 0]

    for idx, value in enumerate(first_column):
        # Skip NaN, empty strings, and whitespace-only values
        if pd.notna(value) and str(value).strip():
            keywords.append((idx, str(value).strip()))

    return keywords


def load_proxies(file_path: str) -> list[str]:
    """Load proxy list from file.

    Args:
        file_path: Path to the proxies.txt file.

    Returns:
        list[str]: List of proxy URLs. Empty list if file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        return []

    proxies = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            proxy = line.strip()
            if proxy and not proxy.startswith("#"):  # Skip empty and comments
                proxies.append(proxy)

    return proxies


def load_user_agents(file_path: str) -> list[str]:
    """Load User-Agent list from file.

    Args:
        file_path: Path to the user_agents.txt file.

    Returns:
        list[str]: List of User-Agent strings. Empty list if file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        return []

    user_agents = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ua = line.strip()
            if ua and not ua.startswith("#"):  # Skip empty and comments
                user_agents.append(ua)

    return user_agents
