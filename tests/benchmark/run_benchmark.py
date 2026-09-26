"""
RNA-Seq Scout scientific benchmark runner.

Executes the public RNASeqNavigator API against the independently
curated benchmark manifest and records Scout observations only.

Ground-truth annotations are never supplied to the Navigator and
are never modified by this script.

Scientific evaluation is performed separately.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rnaseq_nav import RNASeqNavigator


DEFAULT_MANIFEST = Path(
    "tests/benchmark/benchmark_manifest.tsv"
)

DEFAULT_OUTPUT = Path(
    "tests/benchmark/benchmark_results.tsv"
)


OUTPUT_FIELDS = [
    "accession",
    "timestamp_utc",
    "scout_commit",
    "success",
    "error",
    "modality",
    "rna_seq_compatible",
    "compatibility_status",
    "classification_confidence",
    "library_strategy",
    "layout",
    "organism",
    "condition",
    "control",
    "treatment",
    "time_point",
    "replicate_status",
    "design_confidence",
    "suitability",
    "suitability_evidence_strength",
    "reanalysis_readiness",
    "analysis_plan_confidence",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the RNA-Seq Scout scientific benchmark."
        )
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    return parser.parse_args()


def get_git_commit() -> str:
    """Return the current Git commit."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (
        OSError,
        subprocess.CalledProcessError,
    ):
        return "unknown"

    commit = result.stdout.strip()

    return commit or "unknown"


def get_value(
    obj: Any,
    field: str,
    default: Any = "",
) -> Any:
    """Safely retrieve an attribute from an optional result object."""

    if obj is None:
        return default

    return getattr(
        obj,
        field,
        default,
    )


def stringify(value: Any) -> str:
    """Convert a result value into a stable TSV representation."""

    if value is None:
        return ""

    if isinstance(value, bool):
        return "True" if value else "False"

    if isinstance(value, (list, tuple, set)):
        return "; ".join(
            str(item)
            for item in value
            if item is not None
        )

    return str(value)


def read_manifest(
    path: Path,
) -> list[dict[str, str]]:
    """
    Read benchmark accessions.

    Only the accession is consumed by the benchmark runner.

    All other manifest columns are independent ground-truth
    annotations and remain outside the Scout inference path.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark manifest not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        reader = csv.DictReader(
            handle,
            delimiter="\t",
        )

        if reader.fieldnames is None:
            raise ValueError(
                "Benchmark manifest has no header."
            )

        if "accession" not in reader.fieldnames:
            raise ValueError(
                "Benchmark manifest must contain "
                "an 'accession' column."
            )

        rows: list[dict[str, str]] = []

        for row in reader:
            accession = (
                row.get("accession", "")
                .strip()
            )

            if accession:
                rows.append(
                    {
                        "accession": accession,
                    }
                )

    return rows


def empty_observation(
    accession: str,
    timestamp_utc: str,
    commit: str,
    error: str = "",
) -> dict[str, str]:
    """Create an empty observation row for a failed inspection."""

    row = {
        field: ""
        for field in OUTPUT_FIELDS
    }

    row["accession"] = accession
    row["timestamp_utc"] = timestamp_utc
    row["scout_commit"] = commit

    if error:
        row["success"] = "False"
        row["error"] = error

    return row


def build_observation(
    accession: str,
    result: Any,
    timestamp_utc: str,
    commit: str,
) -> dict[str, str]:
    """Extract Scout observations from an InspectionResult."""

    if not result.success:
        return empty_observation(
            accession,
            timestamp_utc,
            commit,
            stringify(result.error),
        )

    metadata = result.metadata
    modality = result.modality_insight
    design = result.design_insight
    suitability = result.suitability_insight
    readiness = result.reanalysis_readiness
    analysis_plan = result.analysis_plan

    experiment = get_value(
        metadata,
        "experiment",
        None,
    )

    library_strategy = get_value(
        experiment,
        "library_strategy",
        "",
    )

    layout = get_value(
        experiment,
        "layout",
        "",
    )

    if not library_strategy:
        library_strategy = get_value(
            metadata,
            "library_strategy",
            "",
        )

    if not layout:
        layout = get_value(
            metadata,
            "layout",
            "",
        )

    evidence_strength = get_value(
        suitability,
        "score",
        "",
    )

    return {
        "accession": accession,
        "timestamp_utc": timestamp_utc,
        "scout_commit": commit,
        "success": "True",
        "error": "",
        "modality": stringify(
            get_value(
                modality,
                "modality",
            )
        ),
        "rna_seq_compatible": stringify(
            get_value(
                modality,
                "rna_seq_compatible",
            )
        ),
        "compatibility_status": stringify(
            get_value(
                modality,
                "compatibility_status",
            )
        ),
        "classification_confidence": stringify(
            get_value(
                modality,
                "classification_confidence",
            )
        ),
        "library_strategy": stringify(
            library_strategy
        ),
        "layout": stringify(
            layout
        ),
        "organism": stringify(
            get_value(
                get_value(metadata, "sample", None),
                "organism",
            )
        ),
        "condition": stringify(
            get_value(
                design,
                "condition",
            )
        ),
        "control": stringify(
            get_value(
                design,
                "control",
            )
        ),
        "treatment": stringify(
            get_value(
                design,
                "treatment",
            )
        ),
        "time_point": stringify(
            get_value(
                design,
                "time_point",
            )
        ),
        "replicate_status": stringify(
            get_value(
                design,
                "replicate_information",
            )
        ),
        "design_confidence": stringify(
            get_value(
                design,
                "design_confidence",
            )
        ),
        "suitability": stringify(
            get_value(
                suitability,
                "overall",
            )
        ),
        "suitability_evidence_strength": stringify(
            evidence_strength
        ),
        "reanalysis_readiness": stringify(
            get_value(
                readiness,
                "verdict",
            )
        ),
        "analysis_plan_confidence": stringify(
            get_value(
                analysis_plan,
                "confidence",
            )
        ),
    }


def write_results(
    path: Path,
    rows: list[dict[str, str]],
) -> None:
    """Write observed benchmark results as TSV."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=OUTPUT_FIELDS,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()

    manifest_rows = read_manifest(
        args.manifest
    )

    commit = get_git_commit()

    print(
        "RNA-Seq Scout scientific benchmark"
    )
    print(
        f"Manifest: {args.manifest}"
    )
    print(
        f"Accessions: {len(manifest_rows)}"
    )
    print(
        f"Scout commit: {commit}"
    )

    navigator = RNASeqNavigator(email=os.environ["NCBI_EMAIL"])

    observations: list[dict[str, str]] = []

    for index, row in enumerate(
        manifest_rows,
        start=1,
    ):
        accession = row["accession"]

        print(
            f"[{index}/{len(manifest_rows)}] "
            f"{accession} ... ",
            end="",
            flush=True,
        )

        timestamp_utc = (
            datetime.now(timezone.utc)
            .isoformat()
        )

        try:
            result = navigator.inspect(
                accession
            )

            observation = build_observation(
                accession,
                result,
                timestamp_utc,
                commit,
            )

            observations.append(
                observation
            )

            if result.success:
                print("SUCCESS")
            else:
                print("FAILED")

        except Exception as exc:
            observations.append(
                empty_observation(
                    accession,
                    timestamp_utc,
                    commit,
                    str(exc),
                )
            )

            print("ERROR")

    write_results(
        args.output,
        observations,
    )

    successful = sum(
        row["success"] == "True"
        for row in observations
    )

    failed = len(observations) - successful

    print(
        "\nBenchmark execution complete."
    )
    print(
        f"Successful: {successful}"
    )
    print(
        f"Failed: {failed}"
    )
    print(
        f"Results: {args.output}"
    )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
