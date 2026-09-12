#!/usr/bin/env python3

"""
RNASeq Scout — Final Pre-Freeze Benchmark Selection Audit

Audits the proposed benchmark against the candidate registry.

This script:
    - does NOT call NCBI
    - does NOT run RNASeq Scout
    - does NOT inspect publications
    - does NOT alter the benchmark

It verifies that the proposed 50-unit benchmark satisfies the
pre-specified structural constraints.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PROPOSED = (
    ROOT
    / "benchmark"
    / "results"
    / "proposed_benchmark_50_v4.csv"
)

POOL_FILES = [
    ROOT / "benchmark" / "candidate_pool.csv",
    ROOT / "benchmark" / "candidate_pool_expanded.csv",
]

TARGET_UNITS = {
    "experiment": 35,
    "run": 5,
    "study": 10,
}

TARGET_MODALITIES = {
    "RNA-Seq": 14,
    "WGS": 6,
    "WXS": 4,
    "ATAC-seq": 4,
    "ChIP-Seq": 4,
    "Hi-C": 5,
    "ncRNA-Seq": 5,
    "miRNA-Seq": 4,
    "AMPLICON": 4,
}

TARGET_MATRIX = {
    "RNA-Seq": {
        "experiment": 9,
        "run": 2,
        "study": 3,
    },
    "WGS": {
        "experiment": 4,
        "run": 1,
        "study": 1,
    },
    "WXS": {
        "experiment": 3,
        "run": 0,
        "study": 1,
    },
    "ATAC-seq": {
        "experiment": 3,
        "run": 0,
        "study": 1,
    },
    "ChIP-Seq": {
        "experiment": 3,
        "run": 0,
        "study": 1,
    },
    "Hi-C": {
        "experiment": 4,
        "run": 0,
        "study": 1,
    },
    "ncRNA-Seq": {
        "experiment": 4,
        "run": 0,
        "study": 1,
    },
    "miRNA-Seq": {
        "experiment": 3,
        "run": 0,
        "study": 1,
    },
    "AMPLICON": {
        "experiment": 2,
        "run": 2,
        "study": 0,
    },
}

MAX_UNITS_PER_FAMILY = 2

EXCLUDED_ACCESSIONS = {
    "SRR17730393",
    "SRR17730394",
    "SRR17730395",
    "SRX31545771",
    "SRX33270018",
    "SRX32342160",
    "SRX35157977",
    "SRP356545",
}


def acc(row: dict) -> str:
    return (
        row.get("accession")
        or row.get("candidate_accession")
        or ""
    ).strip().upper()


def family(row: dict) -> str:
    return (
        row.get("candidate_study_accession")
        or row.get("study_accession")
        or row.get("project_accession")
        or ""
    ).strip().upper()


def unit(row: dict) -> str:
    value = (
        row.get("benchmark_unit")
        or row.get("accession_type")
        or ""
    ).strip().lower()

    if value in {"experiment", "experiments"}:
        return "experiment"

    if value in {"run", "runs"}:
        return "run"

    if value in {"study", "studies"}:
        return "study"

    accession = acc(row)

    if accession.startswith(("SRX", "ERX", "DRX")):
        return "experiment"

    if accession.startswith(("SRR", "ERR", "DRR")):
        return "run"

    if accession.startswith(("SRP", "ERP", "DRP")):
        return "study"

    return "unknown"


def modality(row: dict) -> str:
    return (
        row.get("modality")
        or row.get("library_strategy")
        or row.get("strategy")
        or ""
    ).strip()


def load_pool():

    pool = {}

    for path in POOL_FILES:

        with path.open(
            newline="",
            encoding="utf-8",
        ) as f:

            for row in csv.DictReader(f):

                accession = acc(row)

                if accession:
                    pool.setdefault(
                        accession,
                        row,
                    )

    return pool


def main():

    print("=" * 80)
    print("RNASeq Scout — FINAL PRE-FREEZE BENCHMARK AUDIT")
    print("=" * 80)

    if not PROPOSED.exists():
        raise FileNotFoundError(
            f"Missing proposed benchmark: {PROPOSED}"
        )

    candidate_pool = load_pool()

    with PROPOSED.open(
        newline="",
        encoding="utf-8",
    ) as f:
        selected = list(csv.DictReader(f))

    print(
        f"\nCandidate registry accessions : "
        f"{len(candidate_pool)}"
    )

    print(
        f"Proposed benchmark units       : "
        f"{len(selected)}"
    )

    failures = []

    # -------------------------------------------------------------
    # 1. Total
    # -------------------------------------------------------------

    if len(selected) != 50:
        failures.append(
            f"Expected 50 units; found {len(selected)}"
        )

    # -------------------------------------------------------------
    # 2. Unique accession check
    # -------------------------------------------------------------

    accessions = [acc(r) for r in selected]

    duplicates = [
        accession
        for accession, count in Counter(accessions).items()
        if count > 1
    ]

    print("\n1. Duplicate accession check")

    if duplicates:
        print("   FAIL:", duplicates)
        failures.append(
            f"Duplicate accessions: {duplicates}"
        )
    else:
        print("   PASS")

    # -------------------------------------------------------------
    # 3. Candidate-registry membership
    # -------------------------------------------------------------

    missing = [
        accession
        for accession in accessions
        if accession not in candidate_pool
    ]

    print("\n2. Candidate-registry membership")

    if missing:
        print("   FAIL:", missing)
        failures.append(
            f"Selected accessions absent from candidate pool: "
            f"{missing}"
        )
    else:
        print("   PASS — all selected accessions found")

    # -------------------------------------------------------------
    # 4. Development exclusions
    # -------------------------------------------------------------

    excluded_present = [
        accession
        for accession in accessions
        if accession in EXCLUDED_ACCESSIONS
    ]

    print("\n3. Development/regression exclusion")

    if excluded_present:
        print(
            "   FAIL:",
            excluded_present,
        )
        failures.append(
            f"Development cases present: "
            f"{excluded_present}"
        )
    else:
        print("   PASS")

    # -------------------------------------------------------------
    # 5. Unit composition
    # -------------------------------------------------------------

    units = Counter(
        unit(r)
        for r in selected
    )

    print("\n4. Unit composition")

    for expected_unit, expected_count in TARGET_UNITS.items():

        observed = units[expected_unit]

        status = (
            "PASS"
            if observed == expected_count
            else "FAIL"
        )

        print(
            f"   {expected_unit:10s}: "
            f"{observed:2d} / "
            f"{expected_count:2d} "
            f"[{status}]"
        )

        if observed != expected_count:
            failures.append(
                f"{expected_unit}: "
                f"{observed} instead of "
                f"{expected_count}"
            )

    # -------------------------------------------------------------
    # 6. Exact modality totals
    # -------------------------------------------------------------

    modalities = Counter(
        modality(r)
        for r in selected
    )

    print("\n5. Exact modality totals")

    for expected_modality, expected_count in TARGET_MODALITIES.items():

        observed = modalities[expected_modality]

        status = (
            "PASS"
            if observed == expected_count
            else "FAIL"
        )

        print(
            f"   {expected_modality:12s}: "
            f"{observed:2d} / "
            f"{expected_count:2d} "
            f"[{status}]"
        )

        if observed != expected_count:
            failures.append(
                f"{expected_modality}: "
                f"{observed} instead of "
                f"{expected_count}"
            )

    unexpected_modalities = [
        mod
        for mod in modalities
        if mod not in TARGET_MODALITIES
    ]

    if unexpected_modalities:
        failures.append(
            f"Unexpected modalities: "
            f"{unexpected_modalities}"
        )

    # -------------------------------------------------------------
    # 7. Unit × modality matrix
    # -------------------------------------------------------------

    matrix = Counter(
        (
            modality(r),
            unit(r),
        )
        for r in selected
    )

    print("\n6. Unit × modality matrix")

    for mod, targets in TARGET_MATRIX.items():

        exp = matrix[(mod, "experiment")]
        run = matrix[(mod, "run")]
        study = matrix[(mod, "study")]

        print(
            f"   {mod:12s} "
            f"experiment={exp:2d} "
            f"run={run:2d} "
            f"study={study:2d}"
        )

        for unit_name, expected in targets.items():

            observed = matrix[
                (mod, unit_name)
            ]

            if observed != expected:
                failures.append(
                    f"Matrix mismatch: "
                    f"{mod} × {unit_name}: "
                    f"{observed} instead of "
                    f"{expected}"
                )

    # -------------------------------------------------------------
    # 8. Family cap
    # -------------------------------------------------------------

    families = Counter(
        family(r)
        for r in selected
    )

    print("\n7. Study-family constraint")

    print(
        f"   Unique families: "
        f"{len(families)}"
    )

    violations = {
        fam: count
        for fam, count in families.items()
        if count > MAX_UNITS_PER_FAMILY
    }

    if violations:
        print(
            "   FAIL:",
            violations,
        )
        failures.append(
            f"Family cap violations: "
            f"{violations}"
        )
    else:
        print(
            f"   PASS — maximum usage "
            f"is {max(families.values())}"
        )

    # -------------------------------------------------------------
    # 9. Family duplication
    # -------------------------------------------------------------

    duplicated = {
        fam: count
        for fam, count in families.items()
        if count > 1
    }

    print("\n8. Families represented twice")

    if duplicated:
        for fam, count in sorted(
            duplicated.items()
        ):
            print(
                f"   {fam:20s}: {count}"
            )
    else:
        print("   None")

    # -------------------------------------------------------------
    # 10. Recent cohort
    # -------------------------------------------------------------

    recent = [
        r
        for r in selected
        if family(r).startswith(
            ("SRP734", "SRP735")
        )
    ]

    print(
        "\n9. SRP734xxx/SRP735xxx concentration"
    )

    print(
        f"   {len(recent)} / "
        f"{len(selected)} units"
    )

    if len(recent) > 10:
        failures.append(
            "Recent SRP734/SRP735 concentration "
            "exceeds audit threshold."
        )
        print("   WARNING")
    else:
        print("   PASS")

    # -------------------------------------------------------------
    # 11. Study-family × unit overview
    # -------------------------------------------------------------

    family_units = defaultdict(list)

    for row in selected:

        family_units[
            family(row)
        ].append(
            (
                acc(row),
                unit(row),
                modality(row),
            )
        )

    print("\n10. Families represented by multiple units")

    for fam, records in sorted(
        family_units.items()
    ):

        if len(records) > 1:

            print(
                f"   {fam}:"
            )

            for accession, unit_name, mod in records:
                print(
                    f"      {accession:14s} "
                    f"{unit_name:10s} "
                    f"{mod}"
                )

    # -------------------------------------------------------------
    # 12. Provenance fields
    # -------------------------------------------------------------

    print("\n11. Provenance-field check")

    provenance_fields = [
        "candidate_selection_status",
        "discovery_family",
        "selection_basis",
    ]

    for field in provenance_fields:

        missing_values = [
            acc(r)
            for r in selected
            if not r.get(field, "").strip()
        ]

        if missing_values:

            print(
                f"   {field}: "
                f"WARNING — missing in "
                f"{len(missing_values)} units"
            )

        else:

            print(
                f"   {field}: PASS"
            )

    # -------------------------------------------------------------
    # 13. Selection independence declaration
    # -------------------------------------------------------------

    print("\n12. Selection-independence check")

    basis_values = Counter(
        r.get(
            "selection_basis",
            "",
        ).strip()
        for r in selected
    )

    for basis, count in basis_values.items():

        print(
            f"   {count:2d} units: "
            f"{basis}"
        )

    # -------------------------------------------------------------
    # Final verdict
    # -------------------------------------------------------------

    print("\n" + "=" * 80)

    if failures:

        print("FINAL VERDICT: FAIL")
        print(
            "\nProblems requiring correction:"
        )

        for failure in failures:
            print(
                f"  - {failure}"
            )

        raise SystemExit(1)

    print("FINAL VERDICT: PASS")
    print(
        "\nThe proposed v4 benchmark satisfies "
        "all hard structural constraints."
    )

    print(
        "\nThis does NOT yet freeze the benchmark."
    )

    print(
        "The next stage is scientific review of "
        "the 50 selected records before ground-truth annotation."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()
