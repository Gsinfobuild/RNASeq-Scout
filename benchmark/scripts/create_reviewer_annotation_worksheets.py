#!/usr/bin/env python3

from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[2]

PILOT_MANIFEST = ROOT / "benchmark/annotations/pilot_manifest_v1.0.csv"

REVIEWER_CONFIG = {
    "reviewer_1": (
        ROOT / "benchmark/annotations/reviewer_1/ground_truth_reviewer_1.csv"
    ),
    "reviewer_2": (
        ROOT / "benchmark/annotations/reviewer_2/ground_truth_reviewer_2.csv"
    ),
}

FIELDS = [
    "modality",
    "rna_seq_compatibility",
    "condition",
    "control",
    "treatment",
    "time_point",
    "replicate_information",
    "experimental_design",
    "batch_information",
    "multimodality",
]


HEADER = [
    "benchmark_id",
    "accession",
    "accession_type",
    "study_family",
    "field",
    "repository_value",
    "repository_evidence_state",
    "experimental_truth",
    "experimental_evidence_state",
    "evidence_source",
    "evidence_identifier",
    "evidence_location",
    "reviewer_notes",
    "annotation_confidence",
]


def read_manifest():
    with PILOT_MANIFEST.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def create_rows(manifest):
    rows = []

    for record in manifest:
        for field in FIELDS:
            rows.append({
                "benchmark_id": record["benchmark_id"],
                "accession": record["accession"],
                "accession_type": record["accession_type"],
                "study_family": record["study_family"],
                "field": field,
                "repository_value": "",
                "repository_evidence_state": "",
                "experimental_truth": "",
                "experimental_evidence_state": "",
                "evidence_source": "",
                "evidence_identifier": "",
                "evidence_location": "",
                "reviewer_notes": "",
                "annotation_confidence": "",
            })

    return rows


def main():
    manifest = read_manifest()

    if len(manifest) != 5:
        raise SystemExit(
            f"Expected 5 pilot records, found {len(manifest)}."
        )

    rows = create_rows(manifest)

    for reviewer, output in REVIEWER_CONFIG.items():
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADER)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Created {reviewer}: {output}")
        print(f"  Rows: {len(rows)}")


if __name__ == "__main__":
    main()
