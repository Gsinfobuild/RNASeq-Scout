from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DATABASE_PATH = Path("data/usage.sqlite3")


def classify_accession(accession: str) -> str:
    """Classify a public sequencing accession."""
    normalized = accession.strip().upper()

    if re.fullmatch(r"(SRR|ERR|DRR)\d+", normalized):
        return "run"
    if re.fullmatch(r"(SRX|ERX|DRX)\d+", normalized):
        return "experiment"
    if re.fullmatch(r"(SRP|ERP|DRP|SRA)\d+", normalized):
        return "study"
    if re.fullmatch(r"PRJ(NA|EB|DB)\d+", normalized):
        return "project"
    if re.fullmatch(r"(SRS|ERS|DRS|SAMN|SAMEA)\d+", normalized):
        return "sample"

    return "other"


class UsageTracker:
    """Record inspection outcomes in Turso or a local SQLite database."""

    def __init__(
        self,
        database_path: str | Path = DEFAULT_DATABASE_PATH,
        *,
        turso_database_url: str | None = None,
        turso_auth_token: str | None = None,
        supabase_client: Any | None = None,
        use_supabase: bool | None = None,
    ) -> None:
        # Keep legacy constructor arguments accepted for compatibility.
        # Usage tracking now uses Turso or SQLite, not Supabase.
        del supabase_client
        if use_supabase:
            raise ValueError(
                "Supabase usage tracking is no longer supported. "
                "Configure TURSO_DATABASE_URL and TURSO_AUTH_TOKEN."
            )

        self.database_path = Path(database_path)
        self.turso_database_url = (
            turso_database_url
            or os.getenv("TURSO_DATABASE_URL", "")
        ).strip()
        self.turso_auth_token = (
            turso_auth_token
            or os.getenv("TURSO_AUTH_TOKEN", "")
        ).strip()

        custom_path = self.database_path != DEFAULT_DATABASE_PATH
        self.using_turso = bool(
            self.turso_database_url
            and self.turso_auth_token
            and not custom_path
        )
        self.backend_label = "Turso cloud" if self.using_turso else "Local SQLite"

        if not custom_path and bool(self.turso_database_url) != bool(
            self.turso_auth_token
        ):
            raise ValueError(
                "Configure both TURSO_DATABASE_URL and TURSO_AUTH_TOKEN, "
                "or leave both unset to use local SQLite."
            )

        self._initialize_database()

    def _connect(self):
        if self.using_turso:
            import turso_serverless

            return turso_serverless.connect(
                self.turso_database_url,
                auth_token=self.turso_auth_token,
            )

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS accession_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checked_at TEXT NOT NULL,
                    accession TEXT NOT NULL,
                    accession_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'single'
                )
                """
            )

            # Migrate existing local databases without deleting their records.
            if not self.using_turso:
                columns = {
                    row["name"]
                    for row in connection.execute(
                        "PRAGMA table_info(accession_checks)"
                    ).fetchall()
                }
                if "source" not in columns:
                    connection.execute(
                        "ALTER TABLE accession_checks "
                        "ADD COLUMN source TEXT NOT NULL DEFAULT 'single'"
                    )

            connection.commit()
        finally:
            connection.close()

    def record_result(
        self,
        accession: str,
        success: bool,
        source: str = "single",
    ) -> None:
        """Record one terminal inspection outcome, successful or failed."""
        normalized = str(accession).strip().upper()
        if not normalized:
            raise ValueError("Accession cannot be empty.")

        normalized_source = str(source).strip().lower() or "single"
        timestamp = datetime.now(timezone.utc).isoformat()
        connection = self._connect()

        try:
            connection.execute(
                """
                INSERT INTO accession_checks
                    (checked_at, accession, accession_type, status, source)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    normalized,
                    classify_accession(normalized),
                    "success" if success else "failure",
                    normalized_source,
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def record_success(self, accession: str, source: str = "single") -> None:
        """Record a successful inspection."""
        self.record_result(accession, True, source)

    def record_failure(self, accession: str, source: str = "single") -> None:
        """Record a failed inspection."""
        self.record_result(accession, False, source)

    def _count(self, sql: str) -> int:
        connection = self._connect()
        try:
            row = connection.execute(sql).fetchone()
            return int(row[0])
        finally:
            connection.close()

    def total_checks(self) -> int:
        """Return successful inspections, preserving the legacy API."""
        return self._count(
            "SELECT COUNT(*) FROM accession_checks WHERE status = 'success'"
        )

    def unique_accessions(self) -> int:
        """Count distinct accessions with successful inspections."""
        return self._count(
            """
            SELECT COUNT(DISTINCT accession)
            FROM accession_checks
            WHERE status = 'success'
            """
        )

    def detailed_summary(self) -> dict[str, int]:
        """Return counters for the visible application usage display."""
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_inspections,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)
                        AS successful_inspections,
                    SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END)
                        AS failed_inspections,
                    COUNT(DISTINCT accession) AS unique_accessions
                FROM accession_checks
                """
            ).fetchone()

            return {
                "total_inspections": int(row[0] or 0),
                "successful_inspections": int(row[1] or 0),
                "failed_inspections": int(row[2] or 0),
                "unique_accessions": int(row[3] or 0),
            }
        finally:
            connection.close()

    def summary(self) -> dict[str, int]:
        """Return the original summary shape for backward compatibility."""
        return {
            "total_checks": self.total_checks(),
            "unique_accessions": self.unique_accessions(),
        }
