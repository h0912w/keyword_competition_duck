"""pipeline module for KCPC.

Orchestrates the complete measurement workflow.
"""

from pathlib import Path

from kcpc.checkpoint_db import CheckpointDB, KeywordMeasurement, Status
from kcpc.config import get_config
from kcpc.exceptions import ValidationError
from kcpc.exporter import export_results
from kcpc.file_io import parse_input_file
from kcpc.logging_config import get_logger
from kcpc.measurer import measure_keyword
from kcpc.normalizer import (
    NormalizedKeyword,
    deduplicate_keywords,
    find_duplicate_hashes,
    normalize_keywords,
)
from kcpc.signal_handler import is_shutdown_requested

logger = get_logger()


def run_pipeline(input_file: str, reset: bool = False) -> None:
    """Run the complete KCPC measurement pipeline.

    Args:
        input_file: Path to the input file.
        reset: If True, reset existing database and start fresh.

    Raises:
        ValidationError: If input file is invalid.
        KcpcError: If pipeline execution fails.
    """
    config = get_config()
    logger.info(f"KCPC pipeline started with input: {input_file}")

    # Step 1: Parse input file
    logger.info("Step 1: Parsing input file...")
    keywords = parse_input_file(input_file)

    if not keywords:
        raise ValidationError("No valid keywords found in input file")

    logger.info(f"Loaded {len(keywords)} keywords from input file")

    # Step 2: Normalize keywords
    logger.info("Step 2: Normalizing keywords...")
    normalized_keywords = normalize_keywords(keywords)

    # Find duplicates for logging
    duplicates = find_duplicate_hashes(normalized_keywords)
    if duplicates:
        dup_count = sum(len(v) for v in duplicates.values())
        logger.info(f"Found {len(duplicates)} duplicate keyword groups ({dup_count} total duplicates)")

    # Step 3: Initialize/restore checkpoint database
    logger.info("Step 3: Initializing checkpoint database...")

    if reset:
        # Delete existing database
        db_path = Path(config.db_file_path)
        if db_path.exists():
            db_path.unlink()
            logger.info("Existing database deleted for reset")

    with CheckpointDB() as db:
        # Reset any RUNNING status to PENDING
        reset_count = db.reset_running_to_pending()
        if reset_count > 0:
            logger.info(f"Reset {reset_count} RUNNING keywords to PENDING")

        # Insert new keywords
        _insert_new_keywords(db, normalized_keywords)

        # Step 4-7: Process keywords
        logger.info("Step 4-7: Processing keywords...")
        _process_keywords(db)

        # Step 8: Export results
        logger.info("Step 8: Exporting results...")
        measurements = db.get_all()
        export_results(measurements)

    logger.info("Pipeline completed successfully")


def _insert_new_keywords(
    db: CheckpointDB,
    normalized_keywords: list[NormalizedKeyword],
) -> None:
    """Insert new keywords into the database.

    Args:
        db: Checkpoint database instance.
        normalized_keywords: List of normalized keywords.
    """
    inserted_count = 0
    skipped_count = 0

    for nk in normalized_keywords:
        existing = db.get_by_hash(nk.keyword_hash)

        if existing is None:
            measurement = KeywordMeasurement(
                id=None,
                original_index=nk.original_index,
                keyword=nk.keyword,
                keyword_hash=nk.keyword_hash,
                status=Status.PENDING,
                top10_title_match_count=-1,
                error_message=None,
                updated_at=None,
            )
            db.insert_keyword(measurement)
            inserted_count += 1
        else:
            skipped_count += 1

    logger.info(f"Inserted {inserted_count} new keywords, skipped {skipped_count} existing")


def _process_keywords(db: CheckpointDB) -> None:
    """Process all pending keywords.

    Args:
        db: Checkpoint database instance.
    """
    while True:
        # Check for shutdown
        if is_shutdown_requested():
            logger.info("Shutdown requested, stopping pipeline...")
            break

        # Get next pending keyword
        pending = db.get_pending()

        if not pending:
            break

        for keyword_measurement in pending:
            # Check shutdown before each keyword
            if is_shutdown_requested():
                break

            _process_single_keyword(db, keyword_measurement)


def _process_single_keyword(
    db: CheckpointDB,
    keyword_measurement: KeywordMeasurement,
) -> None:
    """Process a single keyword measurement.

    Args:
        db: Checkpoint database instance.
        keyword_measurement: The keyword measurement to process.
    """
    keyword = keyword_measurement.keyword
    keyword_hash = keyword_measurement.keyword_hash

    # Update status to RUNNING
    db.update_status(keyword_hash, Status.RUNNING)

    logger.info(f"Processing: {keyword}")

    try:
        # Measure keyword
        result = measure_keyword(keyword)

        if result is None:
            # Measurement failed
            db.update_status(
                keyword_hash,
                Status.FAILED,
                top10_title_match_count=-1,
                error_message="Measurement failed after retries",
            )
            logger.error(f"Failed: {keyword}")
        else:
            # Measurement succeeded
            db.update_status(
                keyword_hash,
                Status.DONE,
                top10_title_match_count=result,
            )
            logger.info(f"Done: {keyword} -> {result}")

    except Exception as e:
        # Unexpected error
        db.update_status(
            keyword_hash,
            Status.FAILED,
            top10_title_match_count=-1,
            error_message=str(e),
        )
        logger.error(f"Error processing '{keyword}': {e}")
