#!/usr/bin/env python3

from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[2]

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

BASE = {
    "benchmark_id": "RSB005",
    "accession": "ERX15210614",
    "accession_type": "experiment",
    "study_family": "ERP183101",
}


def build_rows():
    rows = []

    for field in FIELDS:
        row = dict(BASE)
        row["field"] = field

        for column in HEADER:
            if column not in row:
                row[column] = ""

        rows.append(row)

    return rows


def write_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(build_rows())

    print(f"Created: {path}")


def main():
    write_file(
        ROOT
        / "benchmark/annotations/reviewer_1/RSB005_annotation.csv"
    )

    write_file(
        ROOT
        / "benchmark/annotations/reviewer_2/RSB005_annotation.csv"
    )


if __name__ == "__main__":
    main()
