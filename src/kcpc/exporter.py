"""exporter module for KCPC.

Handles Excel/CSV export with multiple sheets.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from kcpc.checkpoint_db import KeywordMeasurement, Status
from kcpc.config import get_config
from kcpc.exceptions import ExportError
from kcpc.logging_config import get_logger

logger = get_logger()


def export_results(
    measurements: list[KeywordMeasurement],
    output_path: str | None = None,
    format: Literal["xlsx", "csv"] | None = None,
) -> None:
    """Export measurement results to Excel or CSV.

    Args:
        measurements: List of keyword measurements to export.
        output_path: Path to output file. If None, uses config default.
        format: Output format ("xlsx" or "csv"). If None, uses config default.

    Raises:
        ExportError: If export fails.
    """
    config = get_config()

    if output_path is None:
        output_path = config.output_file_path

    if format is None:
        format = config.output_format

    output_file = Path(output_path)

    try:
        if format == "xlsx":
            _export_excel(measurements, output_file)
        else:
            _export_csv(measurements, output_file)

        logger.info(f"Results exported to: {output_file}")

    except Exception as e:
        raise ExportError(f"Export failed: {e}") from e


def _export_excel(
    measurements: list[KeywordMeasurement],
    output_path: Path,
) -> None:
    """Export to Excel with multiple sheets.

    Args:
        measurements: List of keyword measurements.
        output_path: Path to output Excel file.
    """
    # Create Results sheet data
    results_data = []
    for m in measurements:
        results_data.append({
            "Original_Index": m.original_index,
            "Keyword": m.keyword,
            "Normalized_Key": m.keyword_hash[:16] + "...",  # Show prefix of hash
            "Top10_Title_Match_Count": m.top10_title_match_count,
            "Status": m.status.value,
            "Error_Message": m.error_message or "",
            "Updated_At": m.updated_at or "",
        })

    df_results = pd.DataFrame(results_data)

    # Create Run_Summary data
    total_rows = len(measurements)
    done_count = sum(1 for m in measurements if m.status == Status.DONE)
    failed_count = sum(1 for m in measurements if m.status == Status.FAILED)
    duplicate_count = sum(1 for m in measurements if m.status == Status.SKIPPED_DUPLICATE)
    pending_count = sum(1 for m in measurements if m.status == Status.PENDING)

    summary_data = {
        "Item": [
            "Total_Input_Rows",
            "Done_Count",
            "Failed_Count",
            "Duplicate_Count",
            "Pending_Count",
            "Exported_At",
        ],
        "Value": [
            total_rows,
            done_count,
            failed_count,
            duplicate_count,
            pending_count,
            datetime.now().isoformat(),
        ],
    }

    df_summary = pd.DataFrame(summary_data)

    # Create Failed_Items data
    failed_items = [
        {
            "Original_Index": m.original_index,
            "Keyword": m.keyword,
            "Error_Message": m.error_message or "Unknown error",
        }
        for m in measurements
        if m.status == Status.FAILED
    ]

    df_failed = pd.DataFrame(failed_items) if failed_items else pd.DataFrame()

    # Write Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_results.to_excel(writer, sheet_name="Results", index=False)
        df_summary.to_excel(writer, sheet_name="Run_Summary", index=False)

        if not df_failed.empty:
            df_failed.to_excel(writer, sheet_name="Failed_Items", index=False)


def _export_csv(
    measurements: list[KeywordMeasurement],
    output_path: Path,
) -> None:
    """Export to CSV (Results sheet only).

    Args:
        measurements: List of keyword measurements.
        output_path: Path to output CSV file.
    """
    results_data = []
    for m in measurements:
        results_data.append({
            "Original_Index": m.original_index,
            "Keyword": m.keyword,
            "Normalized_Key": m.keyword_hash[:16] + "...",
            "Top10_Title_Match_Count": m.top10_title_match_count,
            "Status": m.status.value,
            "Error_Message": m.error_message or "",
            "Updated_At": m.updated_at or "",
        })

    df = pd.DataFrame(results_data)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
