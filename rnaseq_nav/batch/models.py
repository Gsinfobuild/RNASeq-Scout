"""Data models for RNA-Seq Scout batch execution."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BatchConfig:
    """Configuration for one batch execution."""

    enrich_biosample: bool = False
    enrich_study_biosamples: bool = False
    checkpoint_path: str = "batch_checkpoint.json"
    results_jsonl_path: str = "batch_results.jsonl"
    summary_csv_path: str = "batch_summary.csv"


@dataclass
class BatchItem:
    """Persistent state for one accession in a batch."""

    accession: str
    database: str = "Unknown"
    accession_type: str = "Unknown"
    status: str = "pending"
    success: bool | None = None
    error: str | None = None


@dataclass
class BatchResult:
    """Summary of one completed batch."""

    total: int
    completed: int
    successful: int
    failed: int
    pending: int
    skipped: int
    items: list[BatchItem] = field(default_factory=list)

    @property
    def finished(self) -> bool:
        return self.pending == 0
