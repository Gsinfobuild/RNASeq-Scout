"""
RNASeq Scout
============

Benchmark Execution

Purpose
-------
Run the same production inspection pipeline used by RNASeq Scout
against benchmark candidates.

Important
---------
This script records Scout predictions only.

It does NOT establish experimental truth and does NOT calculate
accuracy, agreement, or error rates. Those require independently
curated benchmark evidence.
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from rnaseq_nav.navigator import RNASeqNavigator


INPUT_FILE = (
    PROJECT_ROOT
    / "benchmark"
    / "candidate_accessions.csv"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "benchmark"
    / "results"
)

EVIDENCE_DIR = (
    PROJECT_ROOT
    / "benchmark"
    / "evidence"
)

OUTPUT_FILE = (
    RESULTS_DIR
    / "benchmark_results.csv"
)


def clean(value) -> str:
    """Normalize a value for compact CSV output."""

    if value is None:
        return ""

    return " ".join(
        str(value).split()
    )


def serialize(value):
    """
    Convert dataclasses and nested Python objects into
    JSON-serializable structures.
    """

    if is_dataclass(value):
        return {
            key: serialize(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            str(key): serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            serialize(item)
            for item in value
        ]

    if isinstance(value, set):
        return sorted(
            serialize(item)
            for item in value
        )

    return value


def get_attr(
    object_,
    attribute: str,
    default="",
):
    """Safely retrieve an attribute."""

    if object_ is None:
        return default

    return getattr(
        object_,
        attribute,
        default,
    )


def extract_result_row(
    candidate: dict,
    inspection,
) -> dict:
    """
    Extract the major production-pipeline outputs into
    one machine-readable benchmark row.
    """

    modality = inspection.modality_insight
    design = inspection.design_insight
    suitability = inspection.suitability_insight
    readiness = inspection.reanalysis_readiness
    analysis_plan = inspection.analysis_plan
    landscape = inspection.study_experimental_landscape
    glance = inspection.experiment_at_glance

    return {
        # --------------------------------------------------
        # Benchmark identity
        # --------------------------------------------------

        "accession": clean(
            candidate.get("accession")
        ),

        "accession_type": clean(
            candidate.get("accession_type")
        ).upper(),

        "benchmark_unit": clean(
            candidate.get("category")
        ),

        "candidate_category": clean(
            candidate.get("category")
        ),

        # --------------------------------------------------
        # Inspection status
        # --------------------------------------------------

        "inspection_success": bool(
            get_attr(
                inspection,
                "success",
                False,
            )
        ),

        # --------------------------------------------------
        # Modality / workflow intelligence
        # --------------------------------------------------

        "predicted_modality": clean(
            get_attr(
                modality,
                "modality",
            )
        ),

        "workflow_family": clean(
            get_attr(
                modality,
                "workflow_family",
            )
        ),

        "rna_seq_compatible": get_attr(
            modality,
            "rna_seq_compatible",
            "",
        ),

        "compatibility_status": clean(
            get_attr(
                modality,
                "compatibility_status",
            )
        ),

        "classification_confidence": clean(
            get_attr(
                modality,
                "classification_confidence",
            )
        ),

        # --------------------------------------------------
        # Experimental design intelligence
        # --------------------------------------------------

        "condition": clean(
            get_attr(
                design,
                "condition",
            )
        ),

        "control": clean(
            get_attr(
                design,
                "control",
            )
        ),

        "treatment": clean(
            get_attr(
                design,
                "treatment",
            )
        ),

        "time_point": clean(
            get_attr(
                design,
                "time_point",
            )
        ),

        "replicate_information": clean(
            get_attr(
                design,
                "replicate_information",
            )
        ),

        "design_confidence": clean(
            get_attr(
                design,
                "design_confidence",
            )
        ),

        # --------------------------------------------------
        # Dataset suitability
        # --------------------------------------------------

        "suitability": clean(
            get_attr(
                suitability,
                "overall",
            )
        ),

        "suitability_score": get_attr(
            suitability,
            "score",
            "",
        ),

        "suitability_rationale": clean(
            get_attr(
                suitability,
                "rationale",
            )
        ),

        # --------------------------------------------------
        # Reanalysis readiness
        # --------------------------------------------------

        "reanalysis_readiness": clean(
            get_attr(
                readiness,
                "verdict",
            )
        ),

        "reanalysis_rationale": clean(
            get_attr(
                readiness,
                "rationale",
            )
        ),

        # --------------------------------------------------
        # Analysis planning
        # --------------------------------------------------

        "analysis_plan_status": clean(
            get_attr(
                analysis_plan,
                "status",
            )
        ),

        "analysis_plan_recommendation": clean(
            get_attr(
                analysis_plan,
                "recommendation",
            )
        ),

        # --------------------------------------------------
        # Study-level context
        # --------------------------------------------------

        "study_experiment_count": get_attr(
            glance,
            "experiment_count",
            "",
        ),

        "study_sample_count": get_attr(
            glance,
            "unique_sample_count",
            "",
        ),

        "study_biosample_count": get_attr(
            glance,
            "unique_biosample_count",
            "",
        ),

        "study_run_count": get_attr(
            glance,
            "run_count",
            "",
        ),

        "study_assay_families": "; ".join(
            clean(item)
            for item in get_attr(
                landscape,
                "observed_assay_families",
                [],
            )
            if clean(item)
        ),

        "study_contexts": "; ".join(
            clean(item)
            for item in get_attr(
                landscape,
                "observed_contexts",
                [],
            )
            if clean(item)
        ),

        # --------------------------------------------------
        # Evidence counts
        # --------------------------------------------------

        "readiness_observed_count": len(
            get_attr(
                readiness,
                "observed_evidence",
                [],
            )
        ),

        "readiness_inferred_count": len(
            get_attr(
                readiness,
                "inferred_evidence",
                [],
            )
        ),

        "readiness_not_established_count": len(
            get_attr(
                readiness,
                "not_established",
                [],
            )
        ),

        "readiness_missing_count": len(
            get_attr(
                readiness,
                "missing_information",
                [],
            )
        ),

        "readiness_warning_count": len(
            get_attr(
                readiness,
                "warnings",
                [],
            )
        ),

        # --------------------------------------------------
        # Candidate claims retained separately
        # --------------------------------------------------

        "candidate_expected_modality": clean(
            candidate.get(
                "expected_modality"
            )
        ),

        "candidate_expected_compatibility": clean(
            candidate.get(
                "expected_rna_seq_compatibility"
            )
        ),

        "candidate_publication_identifier": clean(
            candidate.get(
                "publication_identifier"
            )
        ),

        "candidate_selection_status": clean(
            candidate.get(
                "selection_status"
            )
        ),
    }


def write_evidence(
    candidate: dict,
    inspection,
    accession: str,
) -> None:
    """
    Preserve detailed Scout output for independent review.
    """

    output = {
        "benchmark_metadata": {
            "accession": accession,
            "accession_type": clean(
                candidate.get(
                    "accession_type"
                )
            ).upper(),
            "candidate_category": clean(
                candidate.get(
                    "category"
                )
            ),
        },

        "scout_prediction": serialize(
            inspection
        ),
    }

    output_file = (
        EVIDENCE_DIR
        / f"{accession}.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as handle:

        json.dump(
            output,
            handle,
            indent=2,
            ensure_ascii=False,
        )


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {INPUT_FILE}"
        )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EVIDENCE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        candidates = list(
            csv.DictReader(handle)
        )

    print(
        f"Loaded {len(candidates)} benchmark candidates."
    )

    navigator = RNASeqNavigator(
        email="gshankar.bbau@gmail.com"
    )

    rows = []

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        accession = clean(
            candidate.get("accession")
        )

        selection_status = clean(
            candidate.get(
                "selection_status"
            )
        )

        # Only execute candidates explicitly selected
        # for benchmark use.
        if selection_status not in {
            "selected",
            "existing_regression",
            "existing_negative",
        }:

            print(
                f"[{index}/{len(candidates)}] "
                f"{accession}: skipped "
                f"(selection_status={selection_status})"
            )

            continue

        print(
            f"[{index}/{len(candidates)}] "
            f"{accession}: inspecting..."
        )

        try:

            inspection = navigator.inspect(
                accession
            )

            row = extract_result_row(
                candidate,
                inspection,
            )

            write_evidence(
                candidate,
                inspection,
                accession,
            )

            rows.append(
                row
            )

            print(
                f"    modality="
                f"{row['predicted_modality']} | "
                f"compatibility="
                f"{row['compatibility_status']} | "
                f"suitability="
                f"{row['suitability']} | "
                f"readiness="
                f"{row['reanalysis_readiness']}"
            )

        except Exception as error:

            print(
                f"    ERROR: "
                f"{type(error).__name__}: {error}"
            )

            rows.append(
                {
                    "accession": accession,
                    "accession_type": clean(
                        candidate.get(
                            "accession_type"
                        )
                    ).upper(),
                    "candidate_category": clean(
                        candidate.get(
                            "category"
                        )
                    ),
                    "inspection_success": False,
                    "predicted_modality": "",
                    "workflow_family": "",
                    "rna_seq_compatible": "",
                    "compatibility_status": "",
                    "classification_confidence": "",
                    "condition": "",
                    "control": "",
                    "treatment": "",
                    "time_point": "",
                    "replicate_information": "",
                    "design_confidence": "",
                    "suitability": "",
                    "suitability_score": "",
                    "suitability_rationale": "",
                    "reanalysis_readiness": "",
                    "reanalysis_rationale": "",
                    "analysis_plan_status": "",
                    "analysis_plan_recommendation": "",
                    "study_experiment_count": "",
                    "study_sample_count": "",
                    "study_biosample_count": "",
                    "study_run_count": "",
                    "study_assay_families": "",
                    "study_contexts": "",
                    "readiness_observed_count": "",
                    "readiness_inferred_count": "",
                    "readiness_not_established_count": "",
                    "readiness_missing_count": "",
                    "readiness_warning_count": "",
                    "candidate_expected_modality": clean(
                        candidate.get(
                            "expected_modality"
                        )
                    ),
                    "candidate_expected_compatibility": clean(
                        candidate.get(
                            "expected_rna_seq_compatibility"
                        )
                    ),
                    "candidate_publication_identifier": clean(
                        candidate.get(
                            "publication_identifier"
                        )
                    ),
                    "candidate_selection_status": selection_status,
                }
            )

    if not rows:
        print(
            "No benchmark candidates were selected."
        )
        return

    fieldnames = list(
        rows[0].keys()
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    successful = sum(
        1
        for row in rows
        if row.get(
            "inspection_success"
        )
    )

    print()
    print(
        "Benchmark execution complete."
    )
    print(
        f"Successful inspections: "
        f"{successful}/{len(rows)}"
    )
    print(
        f"CSV results: {OUTPUT_FILE}"
    )
    print(
        f"Evidence directory: {EVIDENCE_DIR}"
    )


if __name__ == "__main__":
    main()
