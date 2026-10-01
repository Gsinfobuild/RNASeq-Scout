"""Sequential, resumable batch executor for RNA-Seq Scout."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from rnaseq_nav.accession import detect_accession
from rnaseq_nav.navigator import RNASeqNavigator
from rnaseq_nav.batch.checkpoint import BatchCheckpoint
from rnaseq_nav.batch.models import (
    BatchConfig,
    BatchItem,
    BatchResult,
)


class BatchExecutor:
    """
    Execute multiple accession inspections through the
    existing RNASeqNavigator pipeline.

    The batch layer deliberately does not implement accession
    routing, metadata retrieval, interpretation, or assessment.
    It delegates those responsibilities to RNASeqNavigator.
    """

    def __init__(
        self,
        navigator: RNASeqNavigator,
        config: BatchConfig | None = None,
    ):
        self.navigator = navigator
        self.config = config or BatchConfig()

    @staticmethod
    def normalize_accessions(
        accessions: Iterable[str],
    ) -> list[str]:
        """Normalize and deduplicate accession identifiers."""

        normalized = []
        seen = set()

        for value in accessions:
            if value is None:
                continue

            accession = str(value).strip().upper()

            if not accession:
                continue

            if accession in seen:
                continue

            seen.add(accession)
            normalized.append(accession)

        return normalized

    @staticmethod
    def _make_item(accession: str) -> BatchItem:
        info = detect_accession(accession)

        return BatchItem(
            accession=info["accession"],
            database=info["database"],
            accession_type=info["type"],
        )

    @staticmethod
    def _result_summary(result) -> dict:
        """
        Extract a compact, stable summary from InspectionResult.

        The complete result remains available in JSONL; this summary
        is intended for CSV-scale inspection.
        """

        row = {
            "accession": getattr(result, "accession", ""),
            "success": getattr(result, "success", False),
            "error": getattr(result, "error", None),
        }

        modality = getattr(result, "modality_insight", None)
        suitability = getattr(result, "suitability_insight", None)
        readiness = getattr(result, "reanalysis_readiness", None)
        plan = getattr(result, "analysis_plan", None)

        row["modality"] = getattr(
            modality,
            "modality",
            "",
        )

        row["library_strategy"] = getattr(
            modality,
            "library_strategy",
            "",
        )

        row["suitability"] = getattr(
            suitability,
            "overall",
            "",
        )

        row["reanalysis_readiness"] = getattr(
            readiness,
            "overall",
            "",
        )

        row["analysis_goal"] = getattr(
            plan,
            "analysis_goal",
            "",
        )

        return row

    @staticmethod
    def _json_safe(value):
        """Convert Scout objects into JSON-safe structures."""

        if value is None:
            return None

        if hasattr(value, "to_dict"):
            try:
                return value.to_dict()
            except Exception:
                pass

        if hasattr(value, "__dataclass_fields__"):
            return {
                key: BatchExecutor._json_safe(
                    getattr(value, key)
                )
                for key in value.__dataclass_fields__
            }

        if isinstance(value, dict):
            return {
                str(key): BatchExecutor._json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                BatchExecutor._json_safe(item)
                for item in value
            ]

        if isinstance(value, (str, int, float, bool)):
            return value

        return str(value)

    def _write_result_jsonl(self, result) -> None:
        path = Path(self.config.results_jsonl_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = self._json_safe(result)

        with path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    default=str,
                )
            )
            handle.write("\n")

    def _write_summary_csv(
        self,
        summaries: list[dict],
    ) -> None:
        path = Path(self.config.summary_csv_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not summaries:
            return

        fieldnames = [
            "accession",
            "success",
            "error",
            "modality",
            "library_strategy",
            "suitability",
            "reanalysis_readiness",
            "analysis_goal",
        ]

        with path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for summary in summaries:
                writer.writerow({
                    field: summary.get(field, "")
                    for field in fieldnames
                })

    def _save_checkpoint(
        self,
        items: list[BatchItem],
    ) -> None:
        checkpoint = BatchCheckpoint(
            self.config.checkpoint_path
        )

        checkpoint.save({
            "config": asdict(self.config),
            "items": [
                asdict(item)
                for item in items
            ],
        })

    def _load_or_create_items(
        self,
        accessions: list[str],
        resume: bool,
    ) -> list[BatchItem]:

        checkpoint = BatchCheckpoint(
            self.config.checkpoint_path
        )

        if resume and checkpoint.exists():
            payload = checkpoint.load()

            saved_items = payload.get(
                "items",
                [],
            )

            if saved_items:
                return [
                    BatchItem(**item)
                    for item in saved_items
                ]

        return [
            self._make_item(accession)
            for accession in accessions
        ]

    def run(
        self,
        accessions: Iterable[str],
        resume: bool = True,
    ) -> BatchResult:
        """
        Execute the batch sequentially.

        Each accession is sent directly through
        RNASeqNavigator.inspect().
        """

        normalized = self.normalize_accessions(
            accessions
        )

        items = self._load_or_create_items(
            normalized,
            resume=resume,
        )

        summaries = []

        for item in items:

            if item.status == "completed":
                item.status = "completed"
                continue

            item.status = "running"
            item.error = None

            self._save_checkpoint(items)

            try:
                result = self.navigator.inspect(
                    item.accession,
                    enrich_biosample=(
                        self.config.enrich_biosample
                    ),
                    enrich_study_biosamples=(
                        self.config.enrich_study_biosamples
                    ),
                )

                item.success = bool(
                    getattr(
                        result,
                        "success",
                        False,
                    )
                )

                item.error = getattr(
                    result,
                    "error",
                    None,
                )

                item.status = "completed"

                summary = self._result_summary(
                    result
                )

                summaries.append(summary)

                self._write_result_jsonl(
                    result
                )

            except Exception as exc:
                item.success = False
                item.error = str(exc)
                item.status = "completed"

            self._save_checkpoint(items)

        self._write_summary_csv(
            summaries
        )

        successful = sum(
            1
            for item in items
            if item.status == "completed"
            and item.success is True
        )

        failed = sum(
            1
            for item in items
            if item.status == "completed"
            and item.success is False
        )

        pending = sum(
            1
            for item in items
            if item.status != "completed"
        )

        return BatchResult(
            total=len(items),
            completed=successful + failed,
            successful=successful,
            failed=failed,
            pending=pending,
            skipped=0,
            items=items,
        )
