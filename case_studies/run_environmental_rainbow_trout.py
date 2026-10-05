from pathlib import Path
import csv

from rnaseq_nav.navigator import RNASeqNavigator
from rnaseq_nav.batch import BatchConfig, BatchExecutor


BASE = Path("case_studies/environmental_rainbow_trout")
MANIFEST = BASE / "environmental_rainbow_trout_published_inclusion_manifest.csv"
RESULTS = BASE / "results"


def load_accessions():
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            row["accession"].strip()
            for row in reader
            if row["accession"].strip()
        ]


def main():
    accessions = load_accessions()

    print(f"Loaded {len(accessions)} published environmental accessions.")

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

    navigator = RNASeqNavigator(email="gshankar.bbau@gmail.com")

    executor = BatchExecutor(
        navigator=navigator,
        config=config,
    )

    executor.run(
        accessions,
        resume=True,
    )

    print("\nEnvironmental rainbow trout batch complete.")
    print(f"Summary: {config.summary_csv_path}")
    print(f"Results: {config.results_jsonl_path}")


if __name__ == "__main__":
    main()
