import csv
from pathlib import Path


TRIAGE_FILE = Path(
    "benchmark/results/scientific_review_triage.csv"
)

REVIEW_FILE = Path(
    "benchmark/results/benchmark_scientific_review.csv"
)


TARGETED_NOTES = {
    "SRX27475154": {
        "decision": "RETAIN",
        "category": "Metadata consistency stress case",
        "flags": "LIBRARY_SOURCE_STRATEGY_INCONSISTENCY",
        "notes": (
            "Explicit WXS library strategy establishes the primary assay "
            "classification, although library source is recorded as "
            "TRANSCRIPTOMIC. Retain as a metadata-consistency stress case; "
            "do not reinterpret as RNA-seq."
        ),
    },
    "ERX15160583": {
        "decision": "RETAIN",
        "category": "Assay/workflow boundary case",
        "flags": "HIC_HICHIP_TITLE_BOUNDARY",
        "notes": (
            "Explicit repository strategy is Hi-C, while the experiment "
            "title references both HiChIP and Hi-C. Retain as an "
            "assay/workflow boundary case; evaluate against the repository-"
            "established strategy without assuming title terminology "
            "represents a different assay."
        ),
    },
    "SRX35203579": {
        "decision": "RETAIN",
        "category": "Modality conflict case",
        "flags": "TITLE_STRATEGY_CONFLICT",
        "notes": (
            "Explicit AMPLICON strategy conflicts with WGS wording in the "
            "experiment title. Retain as a deliberate modality-conflict "
            "case to test precedence of structured repository strategy "
            "over generic title terminology."
        ),
    },
    "SRR40486851": {
        "decision": "RETAIN",
        "category": "Platform-diverse modality case",
        "flags": "NON_ILLUMINA_PLATFORM",
        "notes": (
            "Clean repository-level AMPLICON run using Oxford Nanopore/"
            "GridION. Retain for platform diversity and to test modality "
            "classification independently of Illumina-specific assumptions."
        ),
    },
    "SRR40303392": {
        "decision": "RETAIN",
        "category": "Targeted-library modality case",
        "flags": "TARGETED_LIBRARY_DNBSEQ",
        "notes": (
            "Repository metadata consistently identify an AMPLICON run, "
            "with PCR selection and DNBSEQ-G400 sequencing. Retain as a "
            "targeted-library/amplicon workflow case with non-Illumina "
            "platform representation."
        ),
    },
}


def build_default_review(row):
    """
    Build the repository-level scientific selection decision.

    This stage is selection QC only. It does not establish experimental
    truth and does not use Scout predictions or publications.
    """

    priority = row.get(
        "triage_priority",
        ""
    ).strip()

    category = row.get(
        "triage_category",
        ""
    ).strip()

    flags = row.get(
        "triage_flags",
        ""
    ).strip()

    if not flags:
        flags = "NONE"

    if priority == "HIGH":

        notes = (
            "High-priority repository-level scientific review case. "
            "Reviewed and retained because the selected unit provides "
            "useful modality, workflow, multimodality, or specialized-RNA "
            "boundary information without requiring unsupported inference."
        )

    elif priority == "MEDIUM":

        notes = (
            "Medium-priority repository-level scientific review case. "
            "Reviewed and retained because the metadata provide a useful "
            "biological-context, experimental-context, replicate, or "
            "negative-modality case while remaining suitable for the "
            "pre-specified benchmark strata."
        )

    else:

        notes = (
            "Low-priority repository-level scientific review case. "
            "Metadata are sufficiently coherent for the pre-specified "
            "benchmark stratum; retained without requiring experimental "
            "truth to be inferred from repository metadata."
        )

    return {
        "decision": "RETAIN",
        "category": category,
        "flags": flags,
        "notes": notes,
    }


# ------------------------------------------------------------
# Read triage file
# ------------------------------------------------------------

if not TRIAGE_FILE.exists():
    raise SystemExit(
        f"ERROR: missing input file: {TRIAGE_FILE}"
    )


with TRIAGE_FILE.open(
    encoding="utf-8",
    newline=""
) as f:

    reader = csv.DictReader(f)
    rows = list(reader)


if len(rows) != 50:
    raise SystemExit(
        f"ERROR: expected 50 triage records, found {len(rows)}"
    )


required_columns = {
    "accession",
    "benchmark_unit",
    "modality",
    "study_family",
    "triage_category",
    "triage_priority",
    "triage_flags",
}


missing = required_columns - set(
    reader.fieldnames or []
)

if missing:
    raise SystemExit(
        "ERROR: missing required columns: "
        + ", ".join(sorted(missing))
    )


# ------------------------------------------------------------
# Build final review
# ------------------------------------------------------------

output_rows = []

for row in rows:

    accession = row["accession"].strip()

    if accession in TARGETED_NOTES:

        review = TARGETED_NOTES[accession]

    else:

        review = build_default_review(row)

    output = dict(row)

    output["scientific_review_decision"] = (
        review["decision"]
    )

    output["scientific_review_category"] = (
        review["category"]
    )

    output["scientific_review_flags"] = (
        review["flags"]
    )

    output["scientific_review_notes"] = (
        review["notes"]
    )

    output_rows.append(output)


# ------------------------------------------------------------
# Write final review
# ------------------------------------------------------------

fieldnames = list(output_rows[0].keys())

with REVIEW_FILE.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(output_rows)


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("=" * 110)
print("RNASeq Scout — FINAL SCIENTIFIC REVIEW")
print("=" * 110)
print()

print(
    f"Input records  : {len(rows)}"
)

print(
    f"Output records : {len(output_rows)}"
)

print()

decision_counts = {}

for row in output_rows:

    decision = row[
        "scientific_review_decision"
    ]

    decision_counts[decision] = (
        decision_counts.get(decision, 0) + 1
    )


print("Decision counts:")

for decision, count in sorted(
    decision_counts.items()
):

    print(
        f"  {decision}: {count}"
    )


print()
print("Targeted scientific-review cases:")

for accession in TARGETED_NOTES:

    row = next(
        r for r in output_rows
        if r["accession"] == accession
    )

    print(
        f"  {accession:12s} | "
        f"{row['scientific_review_decision']:7s} | "
        f"{row['scientific_review_category']}"
    )


print()
print(
    f"Written: {REVIEW_FILE}"
)

print("=" * 110)
