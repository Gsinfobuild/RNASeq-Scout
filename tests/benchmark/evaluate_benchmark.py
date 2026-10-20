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
- modality is evaluated both strictly and at a broader
  scientific classification level;
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


BROAD_MODALITY_VALUES = {
    "rna_seq": "rna_seq",
    "rna-seq": "rna_seq",
    "mirna_seq": "specialized_rna",
    "mirna-seq": "specialized_rna",
    "mirna sequencing": "specialized_rna",
    "specialized rna sequencing": "specialized_rna",
    "chip_seq": "chip_seq",
    "chip-seq": "chip_seq",
    "atac_seq": "atac_seq",
    "atac-seq": "atac_seq",
    "amplicon sequencing": "amplicon",
    "amplicon": "amplicon",
    "wgs": "wgs",
    "whole-genome sequencing": "wgs",
    "wxs": "wxs",
    "whole-exome sequencing": "wxs",
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

    if field == "replicate_status":
        if normalized == "not applicable":
            return "not_applicable"

        if normalized == "not established":
            return "not_established"

        if "biological replicate status is not established" in normalized:
            return "not_established"

        if "partial evidence" in normalized or "partial replicate evidence" in normalized:
            import re

            match = re.search(r"biological replicate\s+([0-9]+)", normalized)
            if match:
                return f"partial_evidence:biological_replicate_{match.group(1)}"

    return normalized

def normalize_broad_modality(value: str) -> str:
    normalized = normalize(value)

    if normalized in BROAD_MODALITY_VALUES:
        return BROAD_MODALITY_VALUES[normalized]

    return normalized


def is_scorable_truth(value: str, field: str = "") -> bool:
    normalized = normalize(value)

    if not normalized:
        return False

    if field in INTERPRETIVE_FIELDS and normalized in {
        "not applicable",
        "not established",
        "not yet evaluated",
    }:
        return False

    return True


def compare(
    field: str,
    truth: str,
    observed: str,
) -> str:
    if not is_scorable_truth(truth, field):
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


def compare_broad_modality(
    truth: str,
    observed: str,
) -> str:
    if not is_scorable_truth(truth):
        return "NOT SCORED"

    truth_class = normalize_broad_modality(truth)
    observed_class = normalize_broad_modality(observed)

    if truth_class == observed_class:
        return "AGREEMENT"

    return "DISAGREEMENT"


def accuracy_summary(
    comparisons: Iterable[str],
) -> tuple[int, int]:
    correct = 0
    scored = 0

    for result in comparisons:
        if result in {
            "NOT SCORED",
            "MISSING OBSERVATION",
            "FAILED OBSERVATION",
        }:
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
            elif observed.get("success", "").strip().lower() != "true":
                result = "FAILED OBSERVATION"
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



def print_sample_level_summary(
    truth_rows: dict[str, dict[str, str]],
    observed_rows: dict[str, dict[str, str]],
) -> None:
    """Compare sample-level annotations separately from study-level design."""

    print("\\n===== SAMPLE-LEVEL ANNOTATION VALIDATION =====")
    print(
        "Exploratory comparison only: the current manifest does not "
        "contain independently curated sample-level truth columns."
    )

    for truth_field, observed_field in (
        ("treatment", "sample_treatment"),
        ("time_point", "sample_time_point"),
    ):
        comparisons = []
        for accession, truth in truth_rows.items():
            expected = truth.get(truth_field, "").strip()
            if not is_scorable_truth(expected):
                continue

            observed = observed_rows.get(accession)
            if observed is None:
                result = "MISSING OBSERVATION"
            elif observed.get("success", "").strip().lower() != "true":
                result = "FAILED OBSERVATION"
            elif not observed.get(observed_field, "").strip():
                result = "DISAGREEMENT"
            else:
                result = compare(
                    truth_field,
                    expected,
                    observed[observed_field],
                )

            comparisons.append(result)
            actual = (
                observed.get(observed_field, "")
                if observed is not None else ""
            )
            print(
                f"{accession}\\t{truth_field}\\t{result} "
                f"(curated={expected}, sample annotation={actual})"
            )

        correct, scored = accuracy_summary(comparisons)
        print(
            f"{truth_field}: {correct}/{scored} agreement "
            f"across existing curated nonblank values"
        )
        print(
            "Note: this is not independent validation of sample-level "
            "accuracy because the manifest does not distinguish "
            "sample-level from study-level curation."
        )


def print_modality_summary(
    truth_rows: dict[str, dict[str, str]],
    observed_rows: dict[str, dict[str, str]],
) -> None:
    print("\n===== MODALITY CLASSIFICATION =====")

    exact_comparisons: list[str] = []
    broad_comparisons: list[str] = []

    for accession, truth in truth_rows.items():
        observed = observed_rows.get(accession)

        if observed is None:
            exact_result = "MISSING OBSERVATION"
            broad_result = "MISSING OBSERVATION"
        elif observed.get("success", "").strip().lower() != "true":
            exact_result = "FAILED OBSERVATION"
            broad_result = "FAILED OBSERVATION"
        else:
            truth_modality = truth.get(
                "modality",
                "",
            )
            observed_modality = observed.get(
                "modality",
                "",
            )

            exact_result = compare(
                "modality",
                truth_modality,
                observed_modality,
            )

            broad_result = compare_broad_modality(
                truth_modality,
                observed_modality,
            )

            if (
                exact_result == "DISAGREEMENT"
                and broad_result == "AGREEMENT"
            ):
                print(
                    f"{accession}\t"
                    f"broad-class agreement\t"
                    f"truth={truth_modality}\t"
                    f"observed={observed_modality}"
                )

        exact_comparisons.append(
            exact_result
        )
        broad_comparisons.append(
            broad_result
        )

    exact_correct, exact_scored = accuracy_summary(
        exact_comparisons
    )
    broad_correct, broad_scored = accuracy_summary(
        broad_comparisons
    )

    print(
        f"Exact modality: "
        f"{exact_correct}/{exact_scored} agreement"
    )

    print(
        f"Broad modality class: "
        f"{broad_correct}/{broad_scored} agreement"
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

    truth_accessions = set(
        truth_rows
    )
    observed_accessions = set(
        observed_rows
    )

    missing = sorted(
        truth_accessions - observed_accessions
    )

    unexpected = sorted(
        observed_accessions - truth_accessions
    )

    successful = sum(
        row.get("success", "").strip().lower()
        == "true"
        for row in observed_rows.values()
    )
    failed = len(observed_rows) - successful

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
    print(
        f"Missing observations: {len(missing)}"
    )
    print(
        f"Unexpected observations: {len(unexpected)}"
    )
    print(
        f"Successful Scout observations: "
        f"{successful}/{len(observed_rows)}"
    )
    print(
        f"Failed Scout observations: {failed}"
    )

    if missing:
        print(
            "Missing accessions: "
            + ", ".join(missing)
        )

    if unexpected:
        print(
            "Unexpected accessions: "
            + ", ".join(unexpected)
        )

    print_modality_summary(
        truth_rows,
        observed_rows,
    )

    print_sample_level_summary(
        truth_rows,
        observed_rows,
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

    compatibility_comparisons: list[str] = []

    for accession, truth in truth_rows.items():
        observed = observed_rows.get(accession)

        if observed is None:
            compatibility_comparisons.append("MISSING OBSERVATION")
            continue

        if observed.get("success", "").strip().lower() != "true":
            compatibility_comparisons.append("FAILED OBSERVATION")
            continue

        result = compare(
            "rna_seq_compatible",
            truth.get(
                "rna_seq_compatible",
                "",
            ),
            observed.get(
                "rna_seq_compatible",
                "",
            ),
        )

        compatibility_comparisons.append(
            result
        )

        print(
            f"{accession}: "
            f"{result} "
            f"(truth={truth.get('rna_seq_compatible', '')}, "
            f"observed={observed.get('rna_seq_compatible', '')})"
        )

    correct, scored = accuracy_summary(
        compatibility_comparisons
    )

    print(
        f"RNA-seq compatibility: "
        f"{correct}/{scored} agreement"
    )

    print(
        "\n===== NOTE ====="
    )
    print(
        "Library-strategy comparisons use canonical "
        "representations so equivalent values such as "
        "'RNA-Seq' and 'RNA_SEQ' are treated as agreement."
    )
    print(
        "Modality is reported at both exact and broad "
        "classification levels; broad classification does "
        "not erase the more specific Scout output."
    )
    print(
        "Experimental-design and interpretive fields remain "
        "conservative and are not converted into agreement "
        "merely because two labels are directionally similar."
    )
    print(
        "Agreement percentages are field-specific and must "
        "not be interpreted as a single overall scientific accuracy."
    )
    print(
        "Interpretive discrepancies require scientific review "
        "before Scout code is changed."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
