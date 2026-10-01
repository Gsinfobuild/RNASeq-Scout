#!/usr/bin/env python3

"""
RNA-Seq Scout — Diverse GEO Validation Benchmark

Validates the existing Navigator API using the fields actually exposed
by InspectionResult.

This script does not modify production code.

Benchmark layers:
    1. GEO RNA-seq studies
    2. GEO negative controls
    3. Study landscape
    4. Study BioSample evidence
    5. Large-study stress case

A timeout is reported as a retrieval/scalability observation, not
silently converted into a scientific failure.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TIMEOUT_SECONDS = 120


RNA_SEQ_PANEL = [
    "GSE135553",
    "GSE129516",
    "GSE150728",
    "GSE148171",
    "GSE148930",
    "GSE146711",
    "GSE111727",
    "GSE111017",
    "GSE150228",
]


NEGATIVE_PANEL = [
    "GSE10072",
    "GSE2034",
    "GSE5281",
    "GSE2553",
]


STRESS_PANEL = [
    "GSE110004",
]


WORKER = r'''
import json
import os
import sys
import traceback

from rnaseq_nav.navigator import RNASeqNavigator


accession = sys.argv[1]

try:

    email = os.environ.get("NCBI_EMAIL")

    if not email:
        raise RuntimeError(
            "NCBI_EMAIL is not set."
        )

    navigator = RNASeqNavigator(
        email=email
    )

    result = navigator.inspect(
        accession,
        enrich_study_biosamples=True,
    )

    payload = {
        "success": bool(
            getattr(
                result,
                "success",
                False,
            )
        ),

        "error": getattr(
            result,
            "error",
            None,
        ),
    }

    # ----------------------------------------------------------
    # Normalized metadata
    # ----------------------------------------------------------

    metadata = getattr(
        result,
        "metadata",
        None,
    )

    if metadata is not None:

        experiment = getattr(
            metadata,
            "experiment",
            None,
        )

        sample = getattr(
            metadata,
            "sample",
            None,
        )

        if experiment is not None:
            payload["strategy"] = getattr(
                experiment,
                "library_strategy",
                "",
            )

        if sample is not None:
            payload["organism"] = getattr(
                sample,
                "organism",
                "",
            )

    # ----------------------------------------------------------
    # Modality intelligence
    # ----------------------------------------------------------

    modality = getattr(
        result,
        "modality_insight",
        None,
    )

    if modality is not None:

        payload["modality"] = getattr(
            modality,
            "modality",
            None,
        )

        payload["rna_seq_compatible"] = getattr(
            modality,
            "rna_seq_compatible",
            None,
        )

        payload["classification_confidence"] = getattr(
            modality,
            "classification_confidence",
            None,
        )

    # ----------------------------------------------------------
    # Experiment-at-a-Glance
    # ----------------------------------------------------------

    glance = getattr(
        result,
        "experiment_at_glance",
        None,
    )

    if glance is not None:

        payload["experiment_count"] = getattr(
            glance,
            "experiment_count",
            0,
        )

        payload["sample_count"] = getattr(
            glance,
            "unique_sample_count",
            0,
        )

        payload["biosample_count"] = getattr(
            glance,
            "unique_biosample_count",
            0,
        )

        payload["run_count"] = getattr(
            glance,
            "run_count",
            0,
        )

        study_experiments = getattr(
            glance,
            "study_experiments",
            [],
        ) or []

        payload["study_experiment_records"] = len(
            study_experiments
        )

    # ----------------------------------------------------------
    # Study experimental landscape
    # ----------------------------------------------------------

    landscape = getattr(
        result,
        "study_experimental_landscape",
        None,
    )

    if landscape is not None:

        payload["landscape"] = str(
            landscape
        )

        assays = getattr(
            landscape,
            "assay_counts",
            None,
        )

        contexts = getattr(
            landscape,
            "context_counts",
            None,
        )

        if assays is not None:
            payload["assay_counts"] = assays

        if contexts is not None:
            payload["context_counts"] = contexts

    # ----------------------------------------------------------
    # Study BioSample evidence
    # ----------------------------------------------------------

    biosample_evidence = getattr(
        result,
        "study_biosample_evidence",
        None,
    )

    if biosample_evidence is not None:

        payload["biosample_evidence"] = {
            "study_experiment_count": getattr(
                biosample_evidence,
                "study_experiment_count",
                None,
            ),
            "unique_biosample_count": getattr(
                biosample_evidence,
                "unique_biosample_count",
                None,
            ),
            "retrieved_count": getattr(
                biosample_evidence,
                "retrieved_count",
                None,
            ),
            "failed_count": getattr(
                biosample_evidence,
                "failed_count",
                None,
            ),
            "missing_count": getattr(
                biosample_evidence,
                "missing_count",
                None,
            ),
        }

    print(
        json.dumps(
            payload,
            default=str,
        )
    )

except Exception as exc:

    print(
        json.dumps(
            {
                "success": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
    )

    raise SystemExit(2)
'''


def run_accession(
    accession: str,
) -> dict:

    command = [
        sys.executable,
        "-c",
        WORKER,
        accession,
    ]

    start = time.perf_counter()

    try:

        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env=os.environ.copy(),
        )

        elapsed = (
            time.perf_counter() - start
        )

        payload = None

        for line in reversed(
            completed.stdout.splitlines()
        ):

            line = line.strip()

            if not line:
                continue

            try:

                candidate = json.loads(
                    line
                )

                if isinstance(
                    candidate,
                    dict,
                ):

                    payload = candidate
                    break

            except json.JSONDecodeError:
                continue

        if payload is None:

            payload = {
                "success": False,
                "error": (
                    "No structured result "
                    "returned by worker."
                ),
            }

        payload["elapsed_seconds"] = round(
            elapsed,
            2,
        )

        return payload

    except subprocess.TimeoutExpired:

        elapsed = (
            time.perf_counter() - start
        )

        return {
            "success": False,
            "timeout": True,
            "elapsed_seconds": round(
                elapsed,
                2,
            ),
            "error": (
                f"Timed out after "
                f"{TIMEOUT_SECONDS} seconds."
            ),
        }


def print_result(
    accession: str,
    result: dict,
) -> None:

    if result.get("timeout"):

        print(
            f"{accession:<12} "
            f"TIMEOUT "
            f"{result['elapsed_seconds']:>7.2f}s"
        )

        return

    if not result.get("success"):

        print(
            f"{accession:<12} "
            f"FAIL    "
            f"{result.get('elapsed_seconds', 0):>7.2f}s"
        )

        print(
            "              "
            f"{result.get('error', 'Unknown error')}"
        )

        return

    print(
        f"{accession:<12} "
        f"PASS    "
        f"strategy={str(result.get('strategy', '')):<10} "
        f"modality={str(result.get('modality', '')):<12} "
        f"compatible={str(result.get('rna_seq_compatible', '')):<5} "
        f"experiments={result.get('experiment_count', 0):>3} "
        f"time={result.get('elapsed_seconds', 0):>7.2f}s"
    )

    print(
        "              "
        f"BioSamples={result.get('biosample_count', 0)} "
        f"runs={result.get('run_count', 0)}"
    )

    if result.get("context_counts"):

        print(
            "              "
            f"contexts={result['context_counts']}"
        )


def run_panel(
    title: str,
    accessions: list[str],
) -> list[dict]:

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    results = []

    for accession in accessions:

        result = run_accession(
            accession
        )

        result["accession"] = accession

        results.append(
            result
        )

        print_result(
            accession,
            result,
        )

    return results


def main() -> int:

    os.chdir(ROOT)

    print("=" * 78)
    print(
        "RNA-SEQ SCOUT — "
        "DIVERSE GEO VALIDATION BENCHMARK"
    )
    print("=" * 78)

    print()
    print(
        f"Repository : {ROOT}"
    )

    print(
        f"Per-study timeout : "
        f"{TIMEOUT_SECONDS} seconds"
    )

    results = []

    results.extend(
        run_panel(
            "PASS 1 — RNA-SEQ GEO STUDIES",
            RNA_SEQ_PANEL,
        )
    )

    results.extend(
        run_panel(
            "PASS 2 — NON-RNA-SEQ GEO CONTROLS",
            NEGATIVE_PANEL,
        )
    )

    results.extend(
        run_panel(
            "PASS 3 — LARGE-STUDY STRESS TEST",
            STRESS_PANEL,
        )
    )

    print()
    print("=" * 78)
    print("BENCHMARK SUMMARY")
    print("=" * 78)

    passed = sum(
        1
        for item in results
        if item.get("success")
    )

    timed_out = sum(
        1
        for item in results
        if item.get("timeout")
    )

    failed = len(results) - passed - timed_out

    print(
        f"Total cases : {len(results)}"
    )

    print(
        f"Passed      : {passed}"
    )

    print(
        f"Timed out   : {timed_out}"
    )

    print(
        f"Failed      : {failed}"
    )

    print()
    print(
        "Interpretation:"
    )

    print(
        "  PASS    = Navigator completed successfully."
    )

    print(
        "  TIMEOUT = retrieval exceeded the benchmark limit."
    )

    print(
        "  FAIL    = Navigator returned an execution error."
    )

    print()
    print(
        "Production source files were not modified."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
