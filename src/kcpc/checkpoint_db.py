"""checkpoint_db module for KCPC.

Manages SQLite checkpoint database for resume capability.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from kcpc.config import get_config
from kcpc.exceptions import DatabaseError


class Status(str, Enum):
    """Keyword measurement status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


@dataclass
class KeywordMeasurement:
    """Represents a keyword measurement record."""

    id: int | None
    original_index: int
    keyword: str
    keyword_hash: str
    status: Status
    top10_title_match_count: int
    error_message: str | None
    updated_at: str | None


class CheckpointDB:
    """Manages SQLite checkpoint database."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize checkpoint database.

        Args:
            db_path: Path to the database file. If None, uses config default.
        """
        if db_path is None:
            config = get_config()
            db_path = config.db_file_path

        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Connect to the database and create schema if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        if self.conn is None:
            raise DatabaseError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyword_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_index INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                keyword_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                top10_title_match_count INTEGER DEFAULT -1,
                error_message TEXT DEFAULT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(keyword_hash)
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON keyword_measurements(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_original_idx
            ON keyword_measurements(original_index)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_keyword_hash
            ON keyword_measurements(keyword_hash)
        """)

        self.conn.commit()

    def insert_keyword(self, keyword: KeywordMeasurement) -> int:
        """Insert a new keyword measurement record.

        Args:
            keyword: Keyword measurement to insert.

        Returns:
            int: The ID of the inserted record.

        Raises:
            DatabaseError: If insertion fails.
        """
        if self.conn is None:
            raise DatabaseError("Database connection not established")

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO keyword_measurements
                (original_index, keyword, keyword_hash, status,
                 top10_title_match_count, error_message, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                keyword.original_index,
                keyword.keyword,
                keyword.keyword_hash,
                keyword.status.value,
                keyword.top10_title_match_count,
                keyword.error_message,
                keyword.updated_at or datetime.now().isoformat(),
            ))

            self.conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError as e:
            raise DatabaseError(f"Duplicate keyword hash: {keyword.keyword_hash}") from e

    def update_status(
        self,
        keyword_hash: str,
        status: Status,
        top10_title_match_count: int = -1,
        error_message: str | None = None,
    ) -> bool:
        """Update the status of a keyword measurement.

        Args:
            keyword_hash: Hash of the keyword to update.
            status: New status.
            top10_title_match_count: Measurement count (for DONE status).
            error_message: Error message (for FAILED status).

        Returns:
            bool: True if update was successful, False if keyword not found.
        """
        if self.conn is None:
            raise DatabaseError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE keyword_measurements
            SET status = ?, top10_title_match_count = ?,
                error_message = ?, updated_at = ?
            WHERE keyword_hash = ?
        """, (
            status.value,
            top10_title_match_count,
            error_message,
            datetime.now().isoformat(),
            keyword_hash,
        ))

        self.conn.commit()
        return cursor.rowcount > 0

    def get_by_hash(self, keyword_hash: str) -> KeywordMeasurement | None:
        """Get a keyword measurement by hash.

        Args:
            keyword_hash: Hash of the keyword.

        Returns:
            KeywordMeasurement | None: The measurement record, or None if not found.
        """
        if self.conn is None:
            raise DatabaseError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, original_index, keyword, keyword_hash, status,
                   top10_title_match_count, error_message, updated_at
            FROM keyword_measurements
            WHERE keyword_hash = ?
        """, (keyword_hash,))

        row = cursor.fetchone()

        if row is None:
            return None

        return KeywordMeasurement(
            id=row["id"],
            original_index=row["original_index"],
            keyword=row["keyword"],
            keyword_hash=row["keyword_hash"],
            status=Status(row["status"]),
            top10_title_match_count=row["top10_title_match_count"],
            error_message=row["error_message"],
            updated_at=row["updated_at"],
        )

    def get_pending(self) -> list[KeywordMeasurement]:
        """Get all pending keyword measurements.

        Returns:
            list[KeywordMeasurement]: List of pending measurements.
        """
        if self.conn is None:
            raise DatabaseError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, original_index, keyword, keyword_hash, status,
                   top10_title_match_count, error_message, updated_at
            FROM keyword_measurements
            WHERE status IN ('PENDING', 'RUNNING')
            ORDER BY original_index
        """)

        results = []
        for row in cursor.fetchall():
            results.append(KeywordMeasurement(
                id=row["id"],
                original_index=row["original_index"],
                keyword=row["keyword"],
                keyword_hash=row["keyword_hash"],
                status=Status(row["status"]),
                top10_title_match_count=row["top10_title_match_count"],
                error_message=row["error_message"],
                updated_at=row["updated_at"],
            ))

        return results

    def get_all(self) -> list[KeywordMeasurement]:
        """Get all keyword measurements.

        Returns:
            list[KeywordMeasurement]: List of all measurements.
        """
        if self.conn is None:
            raise DatabaseError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, original_index, keyword, keyword_hash, status,
                   top10_title_match_count, error_message, updated_at
            FROM keyword_measurements
            ORDER BY original_index
        """)

        results = []
        for row in cursor.fetchall():
            results.append(KeywordMeasurement(
                id=row["id"],
                original_index=row["original_index"],
                keyword=row["keyword"],
                keyword_hash=row["keyword_hash"],
                status=Status(row["status"]),
                top10_title_match_count=row["top10_title_match_count"],
                error_message=row["error_message"],
                updated_at=row["updated_at"],
            ))

        return results

    def reset_running_to_pending(self) -> int:
        """Reset all RUNNING status to PENDING (for recovery).

        Returns:
            int: Number of records updated.
        """
        if self.conn is None:
            raise DatabaseError("Database connection not established")

        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE keyword_measurements
            SET status = 'PENDING'
            WHERE status = 'RUNNING'
        """)

        self.conn.commit()
        return cursor.rowcount

    def __enter__(self) -> "CheckpointDB":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.close()
