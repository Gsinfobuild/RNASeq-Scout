from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BatchConfig:
    enrich_biosample: bool = False
    enrich_study_biosamples: bool = False

    checkpoint_path: str = "batch_checkpoint.json"
    results_jsonl_path: str = "batch_results.jsonl"
    summary_csv_path: str = "batch_summary.csv"

    max_retries: int = 2
    retry_backoff_seconds: float = 2.0


@dataclass
class BatchItem:
    accession: str
    database: str
    accession_type: str

    status: str = "pending"
    success: bool = False
    error: Optional[str] = None

    attempts: int = 0
    retryable: bool = False


@dataclass
class BatchResult:
    total: int
    completed: int
    successful: int
    failed: int
    pending: int
    skipped: int
    items: List[BatchItem] = field(default_factory=list)

    @property
    def finished(self) -> bool:
        return self.pending == 0
