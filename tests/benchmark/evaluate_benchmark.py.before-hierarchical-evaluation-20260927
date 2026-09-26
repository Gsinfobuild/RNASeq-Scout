"""
RNA-Seq Scout scientific benchmark evaluator.

Compares independently curated benchmark annotations against
Scout observations produced by run_benchmark.py.

Evaluation is field-specific and conservative:
- blank ground-truth fields are not scored;
- explicit states such as "Not established", "Not applicable",
  and "Not yet evaluated" are preserved;
- objective metadata fields are reported separately from
  experimental-design and interpretive fields;
- structured library-strategy representations are compared
  using canonical values;
- no single aggregate scientific accuracy score is produced.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


DEFAULT_MANIFEST = Path(
    "tests/benchmark/benchmark_manifest.tsv"
)

DEFAULT_RESULTS = Path(
    "tests/benchmark/benchmark_results.tsv"
)


OBJECTIVE_FIELDS = [
    "modality",
    "rna_seq_compatible",
    "library_strategy",
    "layout",
    "organism",
]

DESIGN_FIELDS = [
    "condition",
    "control",
    "treatment",
    "time_point",
    "replicate_status",
]

INTERPRETIVE_FIELDS = [
    "design_confidence",
    "suitability",
    "reanalysis_readiness",
]


OBJECTIVE_CANONICAL_VALUES = {
    "rna-seq": "rna_seq",
    "rna_seq": "rna_seq",
    "mirna-seq": "mirna_seq",
    "mirna_seq": "mirna_seq",
    "chip-seq": "chip_seq",
    "chip_seq": "chip_seq",
    "atac-seq": "atac_seq",
    "atac_seq": "atac_seq",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate RNA-Seq Scout scientific benchmark results."
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )

    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS,
    )

    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def normalize(value: str) -> str:
    return " ".join(
        (value or "").strip().lower().split()
    )


def normalize_for_field(
    field: str,
    value: str,
) -> str:
    normalized = normalize(value)

    if field == "library_strategy":
        return OBJECTIVE_CANONICAL_VALUES.get(
            normalized,
            normalized,
        )

    return normalized


def is_scorable_truth(value: str) -> bool:
    return bool((value or "").strip())


def compare(
    field: str,
    truth: str,
    observed: str,
) -> str:
    if not is_scorable_truth(truth):
        return "NOT SCORED"

    if normalize_for_field(
        field,
        truth,
    ) == normalize_for_field(
        field,
        observed,
    ):
        return "AGREEMENT"

    return "DISAGREEMENT"


def accuracy_summary(
    comparisons: Iterable[str],
) -> tuple[int, int]:
    correct = 0
    scored = 0

    for result in comparisons:
        if result == "NOT SCORED":
            continue

        scored += 1

        if result == "AGREEMENT":
            correct += 1

    return correct, scored


def print_field_group(
    name: str,
    truth_rows: dict[str, dict[str, str]],
    observed_rows: dict[str, dict[str, str]],
    fields: list[str],
) -> None:
    print(f"\n===== {name.upper()} =====")

    group_comparisons: list[str] = []

    for field in fields:
        comparisons: list[str] = []

        for accession, truth in truth_rows.items():
            observed = observed_rows.get(accession)

            if observed is None:
                result = "MISSING OBSERVATION"
            else:
                result = compare(
                    field,
                    truth.get(field, ""),
                    observed.get(field, ""),
                )

            comparisons.append(result)

            if result == "DISAGREEMENT":
                print(
                    f"{accession}\t{field}\t"
                    f"truth={truth.get(field, '')}\t"
                    f"observed={observed.get(field, '')}"
                )

        correct, scored = accuracy_summary(
            comparisons
        )

        group_comparisons.extend(comparisons)

        if scored:
            print(
                f"{field}: "
                f"{correct}/{scored} agreement"
            )
        else:
            print(
                f"{field}: "
                "no scorable ground-truth values"
            )

    correct, scored = accuracy_summary(
        group_comparisons
    )

    if scored:
        print(
            f"{name} total: "
            f"{correct}/{scored} agreement"
        )
    else:
        print(
            f"{name} total: "
            "no scorable values"
        )


def main() -> int:
    args = parse_args()

    truth_records = read_tsv(
        args.manifest
    )

    observed_records = read_tsv(
        args.results
    )

    truth_rows = {
        row["accession"].strip(): row
        for row in truth_records
        if row.get("accession", "").strip()
    }

    observed_rows = {
        row["accession"].strip(): row
        for row in observed_records
        if row.get("accession", "").strip()
    }

    print(
        "RNA-Seq Scout scientific benchmark evaluation"
    )
    print(
        f"Manifest: {args.manifest}"
    )
    print(
        f"Results: {args.results}"
    )
    print(
        f"Curated accessions: {len(truth_rows)}"
    )
    print(
        f"Observed accessions: {len(observed_rows)}"
    )

    missing = sorted(
        set(truth_rows) - set(observed_rows)
    )

    unexpected = sorted(
        set(observed_rows) - set(truth_rows)
    )

    print(
        f"Missing observations: {len(missing)}"
    )

    for accession in missing:
        print(f"  - {accession}")

    print(
        f"Unexpected observations: {len(unexpected)}"
    )

    for accession in unexpected:
        print(f"  - {accession}")

    successful = sum(
        normalize(row.get("success", "")) == "true"
        for row in observed_rows.values()
    )

    print(
        f"Successful Scout observations: "
        f"{successful}/{len(truth_rows)}"
    )

    print_field_group(
        "Objective metadata",
        truth_rows,
        observed_rows,
        OBJECTIVE_FIELDS,
    )

    print_field_group(
        "Experimental design",
        truth_rows,
        observed_rows,
        DESIGN_FIELDS,
    )

    print_field_group(
        "Interpretive outputs",
        truth_rows,
        observed_rows,
        INTERPRETIVE_FIELDS,
    )

    print(
        "\n===== RNA-SEQ COMPATIBILITY CHECK ====="
    )

    compatibility: list[str] = []

    for accession, truth in truth_rows.items():
        observed = observed_rows.get(accession)

        if observed is None:
            continue

        result = compare(
            "rna_seq_compatible",
            truth.get("rna_seq_compatible", ""),
            observed.get("rna_seq_compatible", ""),
        )

        compatibility.append(result)

        print(
            f"{accession}: {result} "
            f"(truth={truth.get('rna_seq_compatible', '')}, "
            f"observed={observed.get('rna_seq_compatible', '')})"
        )

    correct, scored = accuracy_summary(
        compatibility
    )

    if scored:
        print(
            f"RNA-seq compatibility: "
            f"{correct}/{scored} agreement"
        )
    else:
        print(
            "RNA-seq compatibility: "
            "no scorable values"
        )

    print("\n===== NOTE =====")
    print(
        "Library-strategy comparisons use canonical "
        "representations so equivalent values such as "
        "'RNA-Seq' and 'RNA_SEQ' are treated as agreement."
    )
    print(
        "Agreement percentages are field-specific and must not "
        "be interpreted as a single overall scientific accuracy."
    )
    print(
        "Interpretive discrepancies require scientific review "
        "before Scout code is changed."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
