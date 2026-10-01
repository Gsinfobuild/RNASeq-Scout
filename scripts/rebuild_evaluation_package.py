#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]

FROZEN_COMMIT = "ebca981"
TIMEOUT_SECONDS = 120

DOCX_CANDIDATES = [
    ROOT / "Revised_preprint(3).docx",
    ROOT / "Revised_preprint_V1.docx",
    ROOT / "Revised_preprint(1).docx",
    ROOT / "Revised_preprint.docx",
]

DOCX_SEARCH_ROOTS = [
    ROOT,
    ROOT / "docs",
]


PANEL = [
    {
        "accession": "GSE135553",
        "cohort": "positive_rnaseq",
        "purpose": "GEO study routing, multi-organism study landscape, context extraction",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "Gallus gallus; Canis lupus familiaris",
        "expected_experiment_count": "16",
        "observed_benchmark_status": "PASS",
        "observed_time_seconds": "69.94",
        "observed_landscape": "DF1 cells=8; MDCK cells=8",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE135553",
        "ground_truth_basis": (
            "GEO Series record; directly validated implementation output"
        ),
    },
    {
        "accession": "GSE129516",
        "cohort": "positive_rnaseq",
        "purpose": "RNA-seq modality and study retrieval",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "6",
        "observed_benchmark_status": "PASS",
        "observed_time_seconds": "29.14",
        "observed_landscape": "Unspecified=6",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE129516",
        "ground_truth_basis": (
            "GEO Series record for modality/library strategy; "
            "directly validated implementation output"
        ),
    },
    {
        "accession": "GSE150728",
        "cohort": "positive_rnaseq",
        "purpose": "RNA-seq modality and heterogeneous study metadata",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "13",
        "observed_benchmark_status": "PASS",
        "observed_time_seconds": "84.27",
        "observed_landscape": "Unspecified=13",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE150728",
        "ground_truth_basis": (
            "GEO Series record for modality/library strategy; "
            "directly validated implementation output"
        ),
    },
    {
        "accession": "GSE148171",
        "cohort": "positive_rnaseq",
        "purpose": "bulk RNA-seq study retrieval",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "9",
        "observed_benchmark_status": "PASS",
        "observed_time_seconds": "42.20",
        "observed_landscape": "Unspecified=9",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE148171",
        "ground_truth_basis": (
            "GEO Series record for modality/library strategy; "
            "directly validated implementation output"
        ),
    },
    {
        "accession": "GSE148930",
        "cohort": "positive_rnaseq",
        "purpose": "RNA-seq study without linked publication",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "3",
        "observed_benchmark_status": "PASS",
        "observed_time_seconds": "15.58",
        "observed_landscape": "Unspecified=3",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE148930",
        "ground_truth_basis": (
            "GEO Series record for modality/library strategy; "
            "directly validated implementation output; no linked publication "
            "was established during enrichment"
        ),
    },
    {
        "accession": "GSE146711",
        "cohort": "positive_rnaseq",
        "purpose": "additional heterogeneous RNA-seq validation",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "12",
        "observed_benchmark_status": "PASS",
        "observed_time_seconds": "51.37",
        "observed_landscape": "Unspecified=12",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE146711",
        "ground_truth_basis": (
            "Directly validated implementation output; structured RNA-seq "
            "library-strategy evidence"
        ),
    },
    {
        "accession": "GSE111727",
        "cohort": "positive_rnaseq",
        "purpose": "large RNA-seq study scalability case",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "",
        "observed_benchmark_status": "TIMEOUT",
        "observed_time_seconds": "120.02",
        "observed_landscape": "",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE111727",
        "ground_truth_basis": (
            "RNA-seq positive-panel designation established before timeout; "
            "no post-timeout experiment-count assertion"
        ),
    },
    {
        "accession": "GSE111017",
        "cohort": "positive_rnaseq",
        "purpose": "GEO SuperSeries / large-study retrieval case",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "",
        "observed_benchmark_status": "TIMEOUT",
        "observed_time_seconds": "120.03",
        "observed_landscape": "",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE111017",
        "ground_truth_basis": (
            "RNA-seq positive-panel designation established before timeout; "
            "no post-timeout experiment-count assertion"
        ),
    },
    {
        "accession": "GSE150228",
        "cohort": "positive_rnaseq",
        "purpose": "RNA-seq study with biological and technical replicate structure",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "12",
        "observed_benchmark_status": "PASS",
        "observed_time_seconds": "51.31",
        "observed_landscape": "Unspecified=12",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE150228",
        "ground_truth_basis": (
            "GEO Series record for modality/library strategy; "
            "directly validated implementation output"
        ),
    },
    {
        "accession": "GSE10072",
        "cohort": "negative_non_rnaseq",
        "purpose": "array-expression negative control",
        "expected_modality": "Expression profiling by array",
        "expected_broad_modality": "microarray",
        "expected_rnaseq_compatible": "False",
        "expected_library_strategy": "",
        "expected_organism": "",
        "expected_experiment_count": "",
        "observed_benchmark_status": "TIMEOUT",
        "observed_time_seconds": "120.09",
        "observed_landscape": "",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE10072",
        "ground_truth_basis": (
            "GEO Series record explicitly identified as "
            "Expression profiling by array; retrieval timed out in benchmark"
        ),
    },
    {
        "accession": "GSE2034",
        "cohort": "negative_non_rnaseq",
        "purpose": "array-expression negative control",
        "expected_modality": "Expression profiling by array",
        "expected_broad_modality": "microarray",
        "expected_rnaseq_compatible": "False",
        "expected_library_strategy": "",
        "expected_organism": "",
        "expected_experiment_count": "",
        "observed_benchmark_status": "TIMEOUT",
        "observed_time_seconds": "120.11",
        "observed_landscape": "",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE2034",
        "ground_truth_basis": (
            "GEO Series record explicitly identified as "
            "Expression profiling by array; retrieval timed out in benchmark"
        ),
    },
    {
        "accession": "GSE5281",
        "cohort": "negative_non_rnaseq",
        "purpose": "array-expression negative control",
        "expected_modality": "Expression profiling by array",
        "expected_broad_modality": "microarray",
        "expected_rnaseq_compatible": "False",
        "expected_library_strategy": "",
        "expected_organism": "",
        "expected_experiment_count": "",
        "observed_benchmark_status": "TIMEOUT",
        "observed_time_seconds": "120.11",
        "observed_landscape": "",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE5281",
        "ground_truth_basis": (
            "GEO Series record explicitly identified as "
            "Expression profiling by array; retrieval timed out in benchmark"
        ),
    },
    {
        "accession": "GSE2553",
        "cohort": "negative_non_rnaseq",
        "purpose": "array-expression negative control",
        "expected_modality": "Expression profiling by array",
        "expected_broad_modality": "microarray",
        "expected_rnaseq_compatible": "False",
        "expected_library_strategy": "",
        "expected_organism": "",
        "expected_experiment_count": "",
        "observed_benchmark_status": "TIMEOUT",
        "observed_time_seconds": "120.11",
        "observed_landscape": "",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE2553",
        "ground_truth_basis": (
            "GEO Series record explicitly identified as "
            "Expression profiling by array; retrieval timed out in benchmark"
        ),
    },
    {
        "accession": "GSE110004",
        "cohort": "stress_rnaseq",
        "purpose": "large RNA-seq stress/performance test",
        "expected_modality": "RNA-seq",
        "expected_broad_modality": "RNA-seq",
        "expected_rnaseq_compatible": "True",
        "expected_library_strategy": "RNA_SEQ",
        "expected_organism": "",
        "expected_experiment_count": "",
        "observed_benchmark_status": "TIMEOUT",
        "observed_time_seconds": "120.11",
        "observed_landscape": "",
        "source": "NCBI GEO",
        "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE110004",
        "ground_truth_basis": (
            "RNA-seq stress-test designation; retrieval timed out in benchmark"
        ),
    },
]


def run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def current_commit() -> str:
    return run(["git", "rev-parse", "HEAD"])


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")

    root = ET.fromstring(xml)

    ns = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    }

    paragraphs = []

    for paragraph in root.findall(".//w:p", ns):
        pieces = []

        for node in paragraph.iter():
            if node.tag == f"{{{ns['w']}}}t":
                pieces.append(node.text or "")
            elif node.tag == f"{{{ns['w']}}}tab":
                pieces.append("\t")
            elif node.tag == f"{{{ns['w']}}}br":
                pieces.append("\n")

        text = "".join(pieces).strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def locate_preprint() -> Path | None:
    for candidate in DOCX_CANDIDATES:
        if candidate.exists():
            return candidate

    for root in DOCX_SEARCH_ROOTS:
        if not root.exists():
            continue

        for path in sorted(root.glob("*.docx")):
            if "preprint" in path.name.lower():
                return path

    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


STALE_PATTERNS = [
    (
        "old test-suite count",
        r"\b137\s+(?:automated\s+)?tests?\b",
    ),
    (
        "old passing-test count",
        r"\b135\s+passing\s+tests?\b",
    ),
    (
        "old HTTP-500 failure claim",
        r"\b2\s+(?:retrieval\s+)?failures?\b.*\bHTTP\s*500\b",
    ),
    (
        "old 34-accession benchmark",
        r"\b34[-\s]accession\b",
    ),
    (
        "old 29/34 exact-modality claim",
        r"\b29\s*/\s*34\b",
    ),
    (
        "old 34/34 claim",
        r"\b34\s*/\s*34\b",
    ),
    (
        "old SRR1039508 example",
        r"\bSRR1039508\b",
    ),
    (
        "old SRR13772342 example",
        r"\bSRR13772342\b",
    ),
]


def find_stale_claims(text: str) -> list[dict]:
    findings = []

    lines = text.splitlines()

    for label, pattern in STALE_PATTERNS:
        regex = re.compile(pattern, flags=re.IGNORECASE)

        for line_number, line in enumerate(lines, start=1):
            if regex.search(line):
                findings.append(
                    {
                        "label": label,
                        "line": line_number,
                        "text": line.strip(),
                    }
                )

    return findings


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_panel() -> None:
    evaluation_dir = ROOT / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    fields = [
        "accession",
        "cohort",
        "purpose",
        "expected_modality",
        "expected_broad_modality",
        "expected_rnaseq_compatible",
        "expected_library_strategy",
        "expected_organism",
        "expected_experiment_count",
        "observed_benchmark_status",
        "observed_time_seconds",
        "observed_landscape",
        "timeout_seconds",
        "source",
        "source_url",
        "ground_truth_basis",
    ]

    csv_path = evaluation_dir / "frozen_evaluation_panel.csv"

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()

        for record in PANEL:
            row = dict(record)
            row["timeout_seconds"] = TIMEOUT_SECONDS
            writer.writerow(row)

    json_payload = {
        "name": "RNA-Seq Scout Frozen GEO Evaluation Panel",
        "version": "1.1",
        "frozen_software_commit": FROZEN_COMMIT,
        "panel_size": len(PANEL),
        "cohorts": {
            "positive_rnaseq": sum(
                x["cohort"] == "positive_rnaseq"
                for x in PANEL
            ),
            "negative_non_rnaseq": sum(
                x["cohort"] == "negative_non_rnaseq"
                for x in PANEL
            ),
            "stress_rnaseq": sum(
                x["cohort"] == "stress_rnaseq"
                for x in PANEL
            ),
        },
        "ground_truth_policy": {
            "principle": (
                "Only repository-derived or directly validated fields "
                "are populated."
            ),
            "unknown_value": "",
            "unsupported_values_removed": True,
            "timeout_is_not_classification_failure": True,
            "research_question_specific_suitability_not_evaluated": True,
        },
        "records": PANEL,
    }

    write_json(
        evaluation_dir / "frozen_evaluation_panel.json",
        json_payload,
    )


def write_readme(preprint_path: Path | None) -> None:
    evaluation_dir = ROOT / "evaluation"

    text = f"""# Frozen Evaluation Panel

## Frozen software

- Commit: `{FROZEN_COMMIT}`
- Repository HEAD when regenerated: `{current_commit()}`
- Production implementation is not modified by this package.

## Panel

The panel contains 14 GEO accessions:

- 9 positive RNA-seq cases
- 4 non-RNA-seq negative controls
- 1 RNA-seq stress/performance case

The panel is intended to evaluate structured repository interpretation,
accession routing, RNA-seq compatibility, library-strategy interpretation,
study retrieval, and selected study-level evidence propagation.

## Ground-truth policy

Ground-truth fields are populated only when supported by:

1. a repository-derived structured record; or
2. a directly observed and previously validated implementation result.

Unsupported fields are intentionally left blank.

A blank field means **not established by the frozen evaluation evidence**.
It does not mean that the biological property is absent.

Experiment counts for timeout cases are not asserted because the frozen
benchmark did not complete those retrievals.

## Timeout policy

The benchmark used a per-study timeout of {TIMEOUT_SECONDS} seconds.

A timeout is recorded as a performance/scalability outcome. It is not
treated as evidence that the expected biological modality is incorrect.

## What this panel does not establish

This panel is not a universal ground truth for:

- research-question-specific suitability;
- biological interpretation;
- causal relationships;
- statistical validity;
- differential-expression correctness;
- downstream alignment or quantification quality;
- biological replicate validity.

Those properties require downstream analysis and/or explicit experimental
evidence.

## Preprint under audit

{preprint_path.name if preprint_path else "No candidate preprint DOCX was found in the repository."}

The preprint audit is stored separately under `docs/`.
"""

    (evaluation_dir / "README.md").write_text(
        text,
        encoding="utf-8",
    )


def write_audit(preprint_path: Path | None, stale_claims: list[dict]) -> None:
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    commit = current_commit()

    payload = {
        "name": "RNA-Seq Scout Implementation-to-Preprint Audit",
        "frozen_software_commit": FROZEN_COMMIT,
        "current_head": commit,
        "commit_matches_frozen_baseline": commit == FROZEN_COMMIT,
        "preprint_found": preprint_path is not None,
        "preprint": (
            {
                "path": str(preprint_path.relative_to(ROOT)),
                "sha256": sha256(preprint_path),
            }
            if preprint_path
            else None
        ),
        "stale_claims": stale_claims,
        "stale_claims_detected": bool(stale_claims),
        "evaluation_panel_size": len(PANEL),
        "benchmark": {
            "positive_rnaseq": 9,
            "negative_non_rnaseq": 4,
            "stress_rnaseq": 1,
            "completed": 7,
            "timeouts": 7,
            "execution_failures": 0,
            "timeout_seconds": TIMEOUT_SECONDS,
        },
        "required_action": (
            "Reconcile stale manuscript claims before submission."
            if stale_claims
            else "No stale claims detected by the configured audit patterns."
        ),
    }

    write_json(
        docs_dir / "implementation_preprint_audit.json",
        payload,
    )

    lines = [
        "# RNA-Seq Scout Implementation-to-Preprint Audit",
        "",
        f"**Frozen software checkpoint:** `{FROZEN_COMMIT}`",
        f"**Current HEAD at audit time:** `{commit}`",
        "",
        "## 1. Frozen implementation state",
        "",
        f"- Commit matches frozen baseline: **{commit == FROZEN_COMMIT}**",
        "- Automated test suite at frozen checkpoint: **141 passed**",
        "- Production source changes are not introduced by this audit package.",
        "",
        "## 2. Validation state",
        "",
        "| Item | Frozen state |",
        "|---|---|",
        "| Automated tests | 141 passed |",
        "| Five-GSE feature validation | Completed |",
        "| Diverse GEO benchmark | 14 accessions |",
        "| Benchmark completed successfully | 7 |",
        "| Benchmark timeouts | 7 |",
        "| Benchmark execution failures | 0 |",
        f"| Timeout threshold | {TIMEOUT_SECONDS} s/study |",
        "",
        "Timeouts are recorded as retrieval-performance observations and are "
        "not counted as scientific classification failures.",
        "",
        "## 3. Preprint audit",
        "",
    ]

    if preprint_path:
        lines.extend(
            [
                f"- Preprint inspected: `{preprint_path.relative_to(ROOT)}`",
                f"- SHA-256: `{sha256(preprint_path)}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- No candidate preprint DOCX was found.",
                "",
            ]
        )

    if stale_claims:
        lines.extend(
            [
                "### Stale quantitative or implementation claims detected",
                "",
            ]
        )

        for finding in stale_claims:
            lines.append(
                f"- **{finding['label']}** "
                f"(line {finding['line']}): `{finding['text']}`"
            )

        lines.extend(
            [
                "",
                "These findings must be reconciled with the frozen "
                "implementation before manuscript submission.",
            ]
        )
    else:
        lines.extend(
            [
                "No configured stale quantitative claims were detected.",
                "",
                "This statement applies only to the configured patterns; "
                "it is not a substitute for manual manuscript reconciliation.",
            ]
        )

    lines.extend(
        [
            "",
            "## 4. Evaluation-panel policy",
            "",
            "The evaluation panel uses source-grounded fields only. "
            "Unsupported organism or experiment-count assertions are omitted "
            "rather than guessed.",
            "",
            "The panel evaluates structured technical metadata interpretation "
            "and retrieval behavior. It does not establish universal "
            "research-question-specific suitability, biological mechanism, "
            "causal interpretation, or statistical validity.",
            "",
            "## 5. Required manuscript action",
            "",
            (
                "Update the manuscript to replace stale benchmark/test-count "
                "claims and explicitly describe the seven benchmark timeouts "
                "as retrieval-performance observations."
                if stale_claims
                else
                "Perform final manual reconciliation of benchmark and "
                "test-count statements before submission."
            ),
            "",
        ]
    )

    (docs_dir / "implementation_preprint_audit.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    print("=" * 78)
    print("RNA-SEQ SCOUT — REBUILD FROZEN EVALUATION PACKAGE")
    print("=" * 78)

    commit = current_commit()

    print(f"Current HEAD : {commit}")
    print(f"Frozen base  : {FROZEN_COMMIT}")

    if not commit.startswith(FROZEN_COMMIT):        
          raise SystemExit(
            "ERROR: HEAD does not match the frozen checkpoint. "
            "No artifacts were regenerated."
        )

    preprint_path = locate_preprint()

    if preprint_path:
        print(f"Preprint     : {preprint_path.relative_to(ROOT)}")
        text = extract_docx_text(preprint_path)
        stale_claims = find_stale_claims(text)
    else:
        print("Preprint     : NOT FOUND")
        stale_claims = []

    write_panel()
    write_readme(preprint_path)
    write_audit(preprint_path, stale_claims)

    print()
    print("Evaluation panel rebuilt.")
    print("Audit rebuilt.")

    print()
    print("STALE CLAIMS:")
    if stale_claims:
        for item in stale_claims:
            print(
                f"- {item['label']} "
                f"(line {item['line']}): {item['text']}"
            )
    else:
        print("- None detected by configured patterns.")

    print()
    print("Artifacts:")
    for path in [
        ROOT / "evaluation" / "README.md",
        ROOT / "evaluation" / "frozen_evaluation_panel.csv",
        ROOT / "evaluation" / "frozen_evaluation_panel.json",
        ROOT / "docs" / "implementation_preprint_audit.md",
        ROOT / "docs" / "implementation_preprint_audit.json",
    ]:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
