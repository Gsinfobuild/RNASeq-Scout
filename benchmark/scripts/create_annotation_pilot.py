#!/usr/bin/env python3

"""
RNASeq Scout
============

Create the ground-truth annotation pilot from the frozen benchmark manifest.

This script does NOT inspect Scout predictions and does NOT establish
experimental truth.

It only creates the reproducible five-unit pilot package from the
already-frozen benchmark membership.
"""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MANIFEST = PROJECT_ROOT / "benchmark" / "benchmark_manifest_v1.0.csv"

ANNOTATION_DIR = PROJECT_ROOT / "benchmark" / "annotations"

PILOT_ACCESSIONS = {
    "ERX15210614",
    "ERX16565911",
    "SRX35166482",
    "ERX15160583",
    "SRX35203579",
}

PILOT_ORDER = [
    "ERX15210614",
    "ERX16565911",
    "SRX35166482",
    "ERX15160583",
    "SRX35203579",
]


def load_manifest() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    records = load_manifest()

    by_accession = {
        row["accession"]: row
        for row in records
    }

    missing = [
        accession
        for accession in PILOT_ORDER
        if accession not in by_accession
    ]

    if missing:
        raise RuntimeError(
            "Pilot accession(s) not present in frozen benchmark manifest: "
            + ", ".join(missing)
        )

    pilot_rows = []

    for accession in PILOT_ORDER:
        source = by_accession[accession]

        pilot_rows.append(
            {
                "pilot_id": f"PILOT{len(pilot_rows) + 1:02d}",
                "benchmark_id": source["benchmark_id"],
                "accession": source["accession"],
                "accession_type": source["accession_type"],
                "modality": source["modality"],
                "study_family": source["study_family"],
                "normalized_organism_group": source[
                    "normalized_organism_group"
                ],
                "scientific_review_decision": source[
                    "scientific_review_decision"
                ],
            }
        )

    output = ANNOTATION_DIR / "pilot_manifest_v1.0.csv"

    write_csv(
        output,
        pilot_rows,
        [
            "pilot_id",
            "benchmark_id",
            "accession",
            "accession_type",
            "modality",
            "study_family",
            "normalized_organism_group",
            "scientific_review_decision",
        ],
    )

    print("RNASeq Scout")
    print("============")
    print()
    print("Ground-truth annotation pilot")
    print("------------------------------")
    print(f"Frozen manifest : {MANIFEST.relative_to(PROJECT_ROOT)}")
    print(f"Pilot output    : {output.relative_to(PROJECT_ROOT)}")
    print(f"Pilot units     : {len(pilot_rows)}")
    print()

    for row in pilot_rows:
        print(
            f"{row['pilot_id']} | "
            f"{row['benchmark_id']} | "
            f"{row['accession']} | "
            f"{row['accession_type']} | "
            f"{row['modality']} | "
            f"{row['normalized_organism_group']}"
        )

    print()
    print("Pilot generated from frozen benchmark membership only.")
    print("No Scout prediction or publication evidence was used.")


if __name__ == "__main__":
    main()
