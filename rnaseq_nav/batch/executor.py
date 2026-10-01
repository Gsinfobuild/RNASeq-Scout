import csv
import json
import re
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from rnaseq_nav.accession import detect_accession
from rnaseq_nav.navigator import RNASeqNavigator

from .checkpoint import BatchCheckpoint
from .models import BatchConfig, BatchItem, BatchResult


class BatchExecutor:

    RETRYABLE_PATTERNS = (
        "429",
        "500 internal server error",
        "502 bad gateway",
        "503 service unavailable",
        "504 gateway timeout",
        "bad gateway",
        "gateway timeout",
        "service unavailable",
        "connection reset",
        "connection aborted",
        "connection error",
        "connection refused",
        "temporary failure",
        "temporarily unavailable",
        "timeout",
        "timed out",
        "remote disconnected",
        "server disconnected",
    )

    def __init__(
        self,
        navigator: RNASeqNavigator,
        config: BatchConfig | None = None,
    ):
        self.navigator = navigator
        self.config = config or BatchConfig()

        self.checkpoint = BatchCheckpoint(
            self.config.checkpoint_path
        )

    @staticmethod
    def normalize_accessions(
        accessions: Iterable[str],
    ) -> List[str]:
        seen = set()
        normalized = []

        for accession in accessions:
            accession = str(accession).strip().upper()

            if not accession:
                continue

            if accession in seen:
                continue

            seen.add(accession)
            normalized.append(accession)

        return normalized

    @staticmethod
    def _make_item(accession: str) -> BatchItem:
        detected = detect_accession(accession)

        return BatchItem(
            accession=accession,
            database=str(
                detected.get("database", "Unknown")
            ),
            accession_type=str(
                detected.get("type", "Unknown")
            ),
        )

    @classmethod
    def _is_retryable_error(cls, error: Any) -> bool:
        if error is None:
            return False

        message = str(error).lower()

        return any(
            pattern in message
            for pattern in cls.RETRYABLE_PATTERNS
        )

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None:
            return None

        if is_dataclass(value):
            return {
                key: BatchExecutor._json_safe(val)
                for key, val in asdict(value).items()
            }

        if isinstance(value, dict):
            return {
                str(key): BatchExecutor._json_safe(val)
                for key, val in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                BatchExecutor._json_safe(item)
                for item in value
            ]

        if isinstance(value, (str, int, float, bool)):
            return value

        return str(value)

    @staticmethod
    def _result_summary(result: Any) -> Dict[str, Any]:
        if result is None:
            return {
                "accession": "",
                "success": False,
                "error": "No inspection result returned.",
            }

        modality = getattr(result, "modality_insight", None)
        suitability = getattr(result, "suitability_insight", None)
        readiness = getattr(result, "reanalysis_readiness", None)
        analysis_plan = getattr(result, "analysis_plan", None)

        return {
            "accession": getattr(result, "accession", ""),
            "success": bool(getattr(result, "success", False)),
            "error": getattr(result, "error", None),

            "modality": getattr(
                modality, "modality", ""
            ) if modality else "",

            "library_strategy": getattr(
                modality, "library_strategy", ""
            ) if modality else "",

            "suitability": getattr(
                suitability, "overall", ""
            ) if suitability else "",

            "reanalysis_readiness": getattr(
                readiness, "verdict", ""
            ) if readiness else "",

            "analysis_goal": getattr(
                analysis_plan, "workflow", ""
            ) if analysis_plan else "",
        }

    def _checkpoint_items(
        self,
        items: List[BatchItem],
    ) -> None:
        self.checkpoint.save(
            items=[
                self._json_safe(item)
                for item in items
            ],
            config={
                "enrich_biosample":
                    self.config.enrich_biosample,
                "enrich_study_biosamples":
                    self.config.enrich_study_biosamples,
                "checkpoint_path":
                    self.config.checkpoint_path,
                "results_jsonl_path":
                    self.config.results_jsonl_path,
                "summary_csv_path":
                    self.config.summary_csv_path,
                "max_retries":
                    self.config.max_retries,
                "retry_backoff_seconds":
                    self.config.retry_backoff_seconds,
            },
        )

    def _write_jsonl(
        self,
        result: Any,
    ) -> None:
        path = Path(
            self.config.results_jsonl_path
        )
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    self._json_safe(result),
                    ensure_ascii=False,
                )
                + "\n"
            )

    def _write_summary(
        self,
        items: List[BatchItem],
        summaries: Dict[str, Dict[str, Any]],
    ) -> None:
        path = Path(
            self.config.summary_csv_path
        )
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fields = [
            "accession",
            "success",
            "error",
            "modality",
            "library_strategy",
            "suitability",
            "reanalysis_readiness",
            "analysis_goal",
            "attempts",
            "retryable",
            "status",
        ]

        with path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
            )
            writer.writeheader()

            for item in items:
                row = dict(
                    summaries.get(
                        item.accession,
                        {},
                    )
                )

                row.update(
                    {
                        "accession":
                            item.accession,
                        "attempts":
                            item.attempts,
                        "retryable":
                            item.retryable,
                        "status":
                            item.status,
                    }
                )

                writer.writerow(
                    {
                        field: row.get(
                            field,
                            "",
                        )
                        for field in fields
                    }
                )

    def _load_or_create_items(
        self,
        accessions: List[str],
        resume: bool,
    ) -> List[BatchItem]:

        if resume and self.checkpoint.exists():
            payload = self.checkpoint.load()

            saved_items = payload.get(
                "items",
                [],
            )

            saved_by_accession = {
                item["accession"]: item
                for item in saved_items
                if item.get("accession")
            }

            items = []

            for accession in accessions:
                if accession in saved_by_accession:
                    saved = saved_by_accession[
                        accession
                    ]

                    item = BatchItem(
                        accession=accession,
                        database=saved.get(
                            "database",
                            "Unknown",
                        ),
                        accession_type=saved.get(
                            "accession_type",
                            "Unknown",
                        ),
                        status=saved.get(
                            "status",
                            "pending",
                        ),
                        success=bool(
                            saved.get(
                                "success",
                                False,
                            )
                        ),
                        error=saved.get(
                            "error"
                        ),
                        attempts=int(
                            saved.get(
                                "attempts",
                                0,
                            )
                        ),
                        retryable=bool(
                            saved.get(
                                "retryable",
                                False,
                            )
                        ),
                    )

                    items.append(item)

                else:
                    items.append(
                        self._make_item(accession)
                    )

            return items

        return [
            self._make_item(accession)
            for accession in accessions
        ]

    def _should_skip(
        self,
        item: BatchItem,
        resume: bool,
    ) -> bool:

        if not resume:
            return False

        if item.status == "completed" and item.success:
            return True

        if (
            item.status == "failed"
            and not item.retryable
        ):
            return True

        return False

    def _run_one(
        self,
        item: BatchItem,
    ) -> Any:

        while True:
            item.attempts += 1
            item.status = "running"
            item.error = None

            self._checkpoint_items(
                self._current_items
            )

            try:
                result = self.navigator.inspect(
                    item.accession,
                    enrich_biosample=
                        self.config.enrich_biosample,
                    enrich_study_biosamples=
                        self.config.enrich_study_biosamples,
                )

            except Exception as exc:
                result = None
                error = str(exc)

            else:
                error = getattr(
                    result,
                    "error",
                    None,
                )

            success = bool(
                result is not None
                and getattr(
                    result,
                    "success",
                    False,
                )
            )

            if success:
                item.success = True
                item.status = "completed"
                item.error = None
                item.retryable = False
                return result

            item.success = False
            item.error = (
                error
                or "Unknown inspection failure."
            )
            item.retryable = (
                self._is_retryable_error(
                    item.error
                )
            )

            if (
                not item.retryable
                or item.attempts >
                    self.config.max_retries
            ):
                item.status = (
                    "retry_exhausted"
                    if item.retryable
                    else "failed"
                )

                return result

            delay = (
                self.config.retry_backoff_seconds
                * (2 ** (item.attempts - 1))
            )

            time.sleep(delay)

    def run(
        self,
        accessions: Iterable[str],
        resume: bool = True,
    ) -> BatchResult:

        normalized = self.normalize_accessions(
            accessions
        )

        items = self._load_or_create_items(
            normalized,
            resume=resume,
        )

        self._current_items = items

        summaries: Dict[str, Dict[str, Any]] = {}
        skipped = 0

        for item in items:

            if self._should_skip(
                item,
                resume=resume,
            ):
                skipped += 1
                continue

            result = self._run_one(item)

            if result is not None:
                summaries[item.accession] = (
                    self._result_summary(result)
                )
                self._write_jsonl(result)

            self._checkpoint_items(items)

            self._write_summary(
                items,
                summaries,
            )

        completed = sum(
            item.status
            in {
                "completed",
                "failed",
                "retry_exhausted",
            }
            for item in items
        )

        successful = sum(
            item.success
            for item in items
        )

        failed = sum(
            item.status
            in {
                "failed",
                "retry_exhausted",
            }
            for item in items
        )

        pending = sum(
            item.status == "pending"
            for item in items
        )

        return BatchResult(
            total=len(items),
            completed=completed,
            successful=successful,
            failed=failed,
            pending=pending,
            skipped=skipped,
            items=items,
        )
