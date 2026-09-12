#!/usr/bin/env python3

from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[2]

SOURCE = ROOT / "benchmark/annotations/evidence/RSB005_ERX15210614"
REGISTER = SOURCE / "evidence_register_RSB005_v1.0.csv"

REVIEWER_FILES = [
    ROOT / "benchmark/annotations/reviewer_1/pilot_evidence_reviewer_1.csv",
    ROOT / "benchmark/annotations/reviewer_2/pilot_evidence_reviewer_2.csv",
]


HEADER = [
    "benchmark_id",
    "accession",
    "field",
    "value",
    "evidence_state",
    "evidence_type",
    "evidence_source",
    "evidence_identifier",
    "evidence_location",
    "evidence_excerpt",
    "evidence_notes",
    "reviewer",
]


def neutralize_notes(field, notes):
    """
    Remove answer-like interpretation from the reviewer packet while
    retaining source-oriented information.
    """
    # Reviewer packets must not contain the assistant's interpretation.
    # Keep notes empty unless they are explicitly source-oriented.
    return ""


def main():
    if not REGISTER.exists():
        raise SystemExit(f"Missing source evidence register: {REGISTER}")

    with REGISTER.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise SystemExit("Source evidence register is empty.")

    neutral_rows = []

    for row in rows:
        neutral_rows.append({
            "benchmark_id": row["benchmark_id"],
            "accession": row["accession"],
            "field": row["field"],
            "value": row["value"],
            "evidence_state": row["evidence_state"],
            "evidence_type": row["evidence_type"],
            "evidence_source": row["evidence_source"],
            "evidence_identifier": row["evidence_identifier"],
            "evidence_location": row["evidence_location"],
            "evidence_excerpt": row["evidence_excerpt"],
            "evidence_notes": neutralize_notes(
                row["field"],
                row["evidence_notes"],
            ),
            "reviewer": "",
        })

    for output in REVIEWER_FILES:
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADER)
            writer.writeheader()
            writer.writerows(neutral_rows)

        print(f"Created: {output}")
        print(f"Rows: {len(neutral_rows)}")


if __name__ == "__main__":
    main()
