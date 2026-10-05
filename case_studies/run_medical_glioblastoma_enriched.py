from pathlib import Path
import csv
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rnaseq_nav.navigator import RNASeqNavigator
from rnaseq_nav.batch import BatchConfig, BatchExecutor


CASE_DIR = ROOT / "case_studies" / "medical_glioblastoma"
MANIFEST = CASE_DIR / "published_inclusion_manifest.csv"
RESULTS = CASE_DIR / "results_enriched"

RESULTS.mkdir(parents=True, exist_ok=True)


def load_accessions(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    accessions = [
        row["accession"].strip()
        for row in rows
        if row.get("accession", "").strip()
    ]

    return accessions


def main():
    email = os.environ.get("NCBI_EMAIL")

    if not email:
        raise RuntimeError(
            "NCBI_EMAIL is not set. "
            "Run: export NCBI_EMAIL='your@email.address'"
        )

    accessions = load_accessions(MANIFEST)

    print("=" * 72)
    print("RNASeq-Scout case study: medical / glioblastoma")
    print("=" * 72)
    print(f"Manifest: {MANIFEST}")
    print(f"Accessions: {len(accessions)}")
    print(f"Results: {RESULTS}")
    print()

    config = BatchConfig(
        enrich_biosample=True,
        enrich_study_biosamples=True,

        checkpoint_path=str(
            RESULTS / "batch_checkpoint.json"
        ),

        results_jsonl_path=str(
            RESULTS / "scout_results.jsonl"
        ),

        summary_csv_path=str(
            RESULTS / "scout_summary.csv"
        ),

        max_retries=2,
        retry_backoff_seconds=2.0,
    )

    navigator = RNASeqNavigator(
        email=email
    )

    executor = BatchExecutor(
        navigator=navigator,
        config=config,
    )

    result = executor.run(
        accessions,
        resume=True,
    )

    print()
    print("=" * 72)
    print("BATCH COMPLETE")
    print("=" * 72)
    print(f"Total:       {result.total}")
    print(f"Completed:   {result.completed}")
    print(f"Successful:  {result.successful}")
    print(f"Failed:      {result.failed}")
    print(f"Pending:     {result.pending}")
    print(f"Skipped:     {result.skipped}")
    print()
    print("Output files:")
    print(f"  {config.results_jsonl_path}")
    print(f"  {config.summary_csv_path}")
    print(f"  {config.checkpoint_path}")


if __name__ == "__main__":
    main()
