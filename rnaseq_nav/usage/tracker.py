from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DATABASE_PATH = Path("data/usage.sqlite3")


def classify_accession(accession: str) -> str:
    """
    Classify an accession into the semantic category used by
    RNASeq Scout's usage tracker.

    Returns:
        run
        experiment
        study
        project
        sample
        other
    """
    normalized = accession.strip().upper()

    if re.fullmatch(r"(SRR|ERR)\d+", normalized):
        return "run"

    if re.fullmatch(r"(SRX|ERX)\d+", normalized):
        return "experiment"

    if re.fullmatch(r"(SRP|ERP|SRA)\d+", normalized):
        return "study"

    if re.fullmatch(r"PRJ(NA|EB|DB)\d+", normalized):
        return "project"

    if re.fullmatch(r"(SRS|ERS|SAMN|SAMEA)\d+", normalized):
        return "sample"

    return "other"


class UsageTracker:
    """
    Persistent usage tracker for RNASeq Scout.

    Backend selection:

    - Default application usage uses Supabase when
      SUPABASE_URL and SUPABASE_KEY are available.
    - Supplying a custom database_path forces SQLite.
      This keeps tests isolated even when Supabase credentials
      exist in the environment.
    - use_supabase can explicitly override automatic selection.
    """

    def __init__(
        self,
        database_path: str | Path = DEFAULT_DATABASE_PATH,
        *,
        supabase_client: Any | None = None,
        use_supabase: bool | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self._supabase = supabase_client

        supabase_url = os.getenv("SUPABASE_URL", "").strip()
        supabase_key = os.getenv("SUPABASE_KEY", "").strip()

        custom_database_path = (
            self.database_path != DEFAULT_DATABASE_PATH
        )

        if use_supabase is None:
            use_supabase = (
                self._supabase is not None
                or (
                    not custom_database_path
                    and bool(supabase_url)
                    and bool(supabase_key)
                )
            )

        self._using_supabase = bool(use_supabase)

        if self._using_supabase and self._supabase is None:
            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Supabase backend requested, but "
                    "SUPABASE_URL and SUPABASE_KEY are not configured."
                )

            from supabase import create_client

            self._supabase = create_client(
                supabase_url,
                supabase_key,
            )

        if not self._using_supabase:
            self._initialize_sqlite()

    @property
    def using_supabase(self) -> bool:
        """Return True when the tracker uses Supabase."""
        return self._using_supabase

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize_sqlite(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS accession_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checked_at TEXT NOT NULL,
                    accession TEXT NOT NULL,
                    accession_type TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def record_success(self, accession: str) -> None:
        """
        Record one successful accession inspection.

        Repeated checks count as multiple total checks but
        only contribute once to the unique-accession count.
        """
        normalized = accession.strip().upper()

        if not normalized:
            raise ValueError(
                "Accession cannot be empty."
            )

        accession_type = classify_accession(
            normalized
        )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        if self.using_supabase:
            self._record_supabase(
                accession=normalized,
                accession_type=accession_type,
                timestamp=timestamp,
            )
        else:
            self._record_sqlite(
                accession=normalized,
                accession_type=accession_type,
                timestamp=timestamp,
            )

    def _record_supabase(
        self,
        *,
        accession: str,
        accession_type: str,
        timestamp: str,
    ) -> None:
        """
        Record usage through the protected Supabase RPC function.
        """
        if self._supabase is None:
            raise RuntimeError(
                "Supabase client is not initialized."
            )

        self._supabase.rpc(
            "record_accession_check",
            {
                "p_accession": accession,
                "p_accession_type": accession_type,
            },
        ).execute()

    def _usage_summary_supabase(self) -> dict[str, int]:
        """
        Retrieve the aggregate usage summary through the
        protected Supabase RPC function.
        """
        if self._supabase is None:
            raise RuntimeError(
                "Supabase client is not initialized."
            )

        response = self._supabase.rpc(
            "get_usage_summary",
            {},
        ).execute()

        data = response.data

        if isinstance(data, dict):
            return {
                "total_checks": int(
                    data.get("total_checks", 0)
                ),
                "unique_accessions": int(
                    data.get("unique_accessions", 0)
                ),
            }

        raise RuntimeError(
            "Supabase returned an invalid usage summary."
        )

    def _record_sqlite(
        self,
        *,
        accession: str,
        accession_type: str,
        timestamp: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO accession_checks (
                    checked_at,
                    accession,
                    accession_type,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    timestamp,
                    accession,
                    accession_type,
                    "success",
                ),
            )

            connection.commit()

    def total_checks(self) -> int:
        """
        Return the total number of successful accession checks.
        """
        if self.using_supabase:
            return self._usage_summary_supabase()[
                "total_checks"
            ]

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM accession_checks
                WHERE status = 'success'
                """
            ).fetchone()

        return int(row["total"])

    def unique_accessions(self) -> int:
        """
        Return the number of distinct successfully checked accessions.
        """
        if self.using_supabase:
            return self._usage_summary_supabase()[
                "unique_accessions"
            ]

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(DISTINCT accession) AS total
                FROM accession_checks
                WHERE status = 'success'
                """
            ).fetchone()

        return int(row["total"])

    def summary(self) -> dict[str, int]:
        """
        Return total and unique usage counts.
        """
        if self.using_supabase:
            return self._usage_summary_supabase()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_checks,
                    COUNT(DISTINCT accession) AS unique_accessions
                FROM accession_checks
                WHERE status = 'success'
                """
            ).fetchone()

        return {
            "total_checks": int(
                row["total_checks"]
            ),
            "unique_accessions": int(
                row["unique_accessions"]
            ),
        }
