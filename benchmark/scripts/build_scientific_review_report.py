#!/usr/bin/env python3

import csv
from pathlib import Path
from collections import Counter


ROOT = Path(__file__).resolve().parents[2]

PROPOSED = (
    ROOT
    / "benchmark"
    / "results"
    / "proposed_benchmark_50_v4.csv"
)

POOLS = [
    ROOT / "benchmark" / "candidate_pool.csv",
    ROOT / "benchmark" / "candidate_pool_expanded.csv",
]

OUTPUT = (
    ROOT
    / "benchmark"
    / "results"
    / "benchmark_scientific_review_report.csv"
)


FIELDS = [
    "accession",
    "benchmark_unit",
    "modality",
    "organism",
    "normalized_organism_group",
    "study_family",
    "candidate_category",

    "title",
    "library_strategy",
    "library_source",
    "library_selection",
    "layout",
    "platform",
    "instrument",

    "project_accession",
    "study_accession",
    "experiment_accession",
    "run_accession",
    "sample_accession",
    "biosample_accession",

    "metadata_field_count",
    "metadata_completeness",

    "biological_context_signal",
    "design_signal",
    "replicate_signal",
    "control_treatment_signal",

    "family_size_in_candidate_pool",
    "family_selected_count",

    "selection_stratum",
    "boundary_case_flag",
    "redundancy_flag",

    "scientific_concern",
    "review_decision",
    "review_notes",
]


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def first(row, *names):
    for name in names:
        value = clean(row.get(name, ""))
        if value:
            return value
    return ""


def accession(row):
    return first(row, "accession")


def family(row):
    return first(
        row,
        "discovery_family",
        "candidate_study_accession",
        "study_accession",
        "project_accession",
    )


def unit(row):
    value = first(
        row,
        "benchmark_unit",
        "accession_type",
    ).upper()

    if value in {"EXPERIMENT", "SRX", "ERX", "DRX"}:
        return "experiment"

    if value in {"RUN", "SRR", "ERR", "DRR"}:
        return "run"

    if value in {"STUDY", "SRP", "ERP", "DRP"}:
        return "study"

    acc = accession(row).upper()

    if acc.startswith(("SRX", "ERX", "DRX")):
        return "experiment"

    if acc.startswith(("SRR", "ERR", "DRR")):
        return "run"

    if acc.startswith(("SRP", "ERP", "DRP")):
        return "study"

    return value.lower()


def normalize_modality(value):
    value = clean(value)

    mapping = {
        "RNA-Seq": "RNA-Seq",
        "RNA_SEQ": "RNA-Seq",
        "RNA-seq": "RNA-Seq",
        "WGS": "WGS",
        "WXS": "WXS",
        "ATAC-seq": "ATAC-seq",
        "ATAC_SEQ": "ATAC-seq",
        "ChIP-Seq": "ChIP-Seq",
        "CHIP_SEQ": "ChIP-Seq",
        "Hi-C": "Hi-C",
        "HI-C": "Hi-C",
        "ncRNA-Seq": "ncRNA-Seq",
        "NCRNA_SEQ": "ncRNA-Seq",
        "miRNA-Seq": "miRNA-Seq",
        "MIRNA_SEQ": "miRNA-Seq",
        "AMPLICON": "AMPLICON",
    }

    return mapping.get(value, value)


def count_metadata_fields(row):
    fields = [
        "title",
        "library_strategy",
        "library_source",
        "library_selection",
        "layout",
        "platform",
        "instrument",
        "organism",
        "project_accession",
        "study_accession",
        "experiment_accession",
        "run_accession",
        "sample_accession",
        "biosample_accession",
    ]

    return sum(
        bool(clean(row.get(field, "")))
        for field in fields
    )


def completeness_label(count):
    if count >= 12:
        return "High"
    if count >= 8:
        return "Moderate"
    if count >= 4:
        return "Limited"
    return "Sparse"


def context_signal(title):
    text = clean(title).lower()

    terms = [
        "stress",
        "starvation",
        "hypoxia",
        "infection",
        "infected",
        "treatment",
        "treated",
        "exposure",
        "exposed",
        "control",
        "untreated",
        "mock",
        "drug",
        "antibiotic",
        "nutrient",
        "iron",
        "oxygen",
        "heat",
        "cold",
        "drought",
        "salt",
        "salinity",
        "development",
        "developmental",
        "differentiation",
        "cell",
        "tissue",
        "tumor",
        "cancer",
        "disease",
        "knockout",
        "knockdown",
        "mutant",
        "wild type",
        "wild-type",
    ]

    hits = [
        term
        for term in terms
        if term in text
    ]

    return "; ".join(hits[:8])


def design_signal(title):
    text = clean(title).lower()

    terms = [
        "replicate",
        "biological replicate",
        "technical replicate",
        "control",
        "untreated",
        "mock",
        "treated",
        "treatment",
        "group",
        "condition",
        "time point",
        "timepoint",
        "hour",
        "hours",
        "day",
        "days",
        "before",
        "after",
    ]

    hits = [
        term
        for term in terms
        if term in text
    ]

    return "; ".join(hits[:10])


def replicate_signal(title):
    text = clean(title).lower()

    terms = [
        "replicate",
        "biological replicate",
        "technical replicate",
        "biological rep",
        "technical rep",
    ]

    hits = [
        term
        for term in terms
        if term in text
    ]

    return "; ".join(hits)


def control_treatment_signal(title):
    text = clean(title).lower()

    terms = [
        "control",
        "untreated",
        "mock",
        "treated",
        "treatment",
        "exposure",
        "exposed",
        "received",
        "knockout",
        "knockdown",
        "wild type",
        "wild-type",
        "mutant",
    ]

    hits = [
        term
        for term in terms
        if term in text
    ]

    return "; ".join(hits[:10])


# ---------------------------------------------------------------------
# Load candidate registry
# ---------------------------------------------------------------------

candidate_by_accession = {}

for path in POOLS:

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open(
        newline="",
        encoding="utf-8",
    ) as f:

        for row in csv.DictReader(f):

            acc = accession(row)

            if not acc:
                continue

            # First occurrence wins.
            candidate_by_accession.setdefault(
                acc,
                row,
            )


# ---------------------------------------------------------------------
# Load proposed benchmark
# ---------------------------------------------------------------------

with PROPOSED.open(
    newline="",
    encoding="utf-8",
) as f:

    selected = list(csv.DictReader(f))


if len(selected) != 50:
    raise RuntimeError(
        f"Expected 50 benchmark units, found {len(selected)}"
    )


# ---------------------------------------------------------------------
# Family statistics
# ---------------------------------------------------------------------

candidate_family_counts = Counter()

for row in candidate_by_accession.values():

    fam = family(row)

    if fam:
        candidate_family_counts[fam] += 1


selected_family_counts = Counter()

for row in selected:

    fam = family(row)

    if fam:
        selected_family_counts[fam] += 1


# ---------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------

report = []

for row in selected:

    acc = accession(row)

    candidate = candidate_by_accession.get(acc)

    if candidate is None:
        raise RuntimeError(
            f"{acc} is not present in candidate registry"
        )

    benchmark_unit = unit(row)

    modality = normalize_modality(
        first(
            row,
            "modality",
            "library_strategy",
        )
    )

    organism = first(
        row,
        "organism",
    )

    normalized_organism = first(
        row,
        "normalized_organism_group",
    )

    study_family = family(row)

    title = first(
        candidate,
        "title",
        "experiment_title",
        "study_title",
    )

    library_strategy = first(
        candidate,
        "library_strategy",
    )

    library_source = first(
        candidate,
        "library_source",
    )

    library_selection = first(
        candidate,
        "library_selection",
    )

    layout = first(
        candidate,
        "layout",
    )

    platform = first(
        candidate,
        "platform",
    )

    instrument = first(
        candidate,
        "instrument",
    )

    project_accession = first(
        candidate,
        "project_accession",
        "bioproject_accession",
    )

    study_accession = first(
        candidate,
        "candidate_study_accession",
        "study_accession",
    )

    experiment_accession = first(
        candidate,
        "experiment_accession",
    )

    run_accession = first(
        candidate,
        "run_accession",
    )

    sample_accession = first(
        candidate,
        "sample_accession",
    )

    biosample_accession = first(
        candidate,
        "biosample_accession",
    )

    metadata_count = count_metadata_fields(
        {
            "title": title,
            "library_strategy": library_strategy,
            "library_source": library_source,
            "library_selection": library_selection,
            "layout": layout,
            "platform": platform,
            "instrument": instrument,
            "organism": organism,
            "project_accession": project_accession,
            "study_accession": study_accession,
            "experiment_accession": experiment_accession,
            "run_accession": run_accession,
            "sample_accession": sample_accession,
            "biosample_accession": biosample_accession,
        }
    )

    family_size = candidate_family_counts.get(
        study_family,
        0,
    )

    family_selected = selected_family_counts.get(
        study_family,
        0,
    )

    # These are deliberately heuristic review signals.
    # They are NOT ground truth and NOT Scout predictions.
    biological_context = context_signal(title)
    design = design_signal(title)
    replicate = replicate_signal(title)
    control_treatment = control_treatment_signal(title)

    # Boundary flag is intentionally conservative.
    boundary_terms = [
        "single cell",
        "single-cell",
        "scrna",
        "scRNA",
        "bcr",
        "tcr",
        "small rna",
        "small-rna",
        "mirna",
        "miRNA",
        "ribosome",
        "ribosomal",
        "amplicon",
        "targeted",
        "capture",
        "metagen",
        "metatranscript",
    ]

    lower_title = title.lower()

    boundary_hits = [
        term
        for term in boundary_terms
        if term.lower() in lower_title
    ]

    boundary_flag = (
        "Potential boundary case: "
        + "; ".join(boundary_hits)
        if boundary_hits
        else ""
    )

    redundancy_flag = ""

    if family_selected > 1:
        redundancy_flag = (
            f"Family represented by {family_selected} "
            f"selected units; inspect whether units provide "
            f"meaningfully different benchmark behavior."
        )

    concerns = []

    if not organism:
        concerns.append(
            "Organism label unavailable in candidate metadata."
        )

    if not title:
        concerns.append(
            "Title/context unavailable."
        )

    if not library_strategy:
        concerns.append(
            "Library strategy unavailable."
        )

    if not layout:
        concerns.append(
            "Library layout unavailable."
        )

    if not platform:
        concerns.append(
            "Sequencing platform unavailable."
        )

    if boundary_flag:
        concerns.append(
            "Potential modality/workflow boundary case."
        )

    if redundancy_flag:
        concerns.append(
            "Multiple units selected from same study family."
        )

    scientific_concern = " | ".join(concerns)

    selection_stratum = (
        f"{modality} × {benchmark_unit}"
    )

    report.append(
        {
            "accession": acc,
            "benchmark_unit": benchmark_unit,
            "modality": modality,
            "organism": organism,
            "normalized_organism_group": normalized_organism,
            "study_family": study_family,
            "candidate_category": first(
                row,
                "candidate_category",
            ),

            "title": title,
            "library_strategy": library_strategy,
            "library_source": library_source,
            "library_selection": library_selection,
            "layout": layout,
            "platform": platform,
            "instrument": instrument,

            "project_accession": project_accession,
            "study_accession": study_accession,
            "experiment_accession": experiment_accession,
            "run_accession": run_accession,
            "sample_accession": sample_accession,
            "biosample_accession": biosample_accession,

            "metadata_field_count": str(metadata_count),
            "metadata_completeness": completeness_label(
                metadata_count
            ),

            "biological_context_signal": biological_context,
            "design_signal": design,
            "replicate_signal": replicate,
            "control_treatment_signal": control_treatment,

            "family_size_in_candidate_pool": str(
                family_size
            ),
            "family_selected_count": str(
                family_selected
            ),

            "selection_stratum": selection_stratum,

            "boundary_case_flag": boundary_flag,
            "redundancy_flag": redundancy_flag,

            "scientific_concern": scientific_concern,

            # Human review fields.
            "review_decision": "",
            "review_notes": "",
        }
    )


# ---------------------------------------------------------------------
# Write report
# ---------------------------------------------------------------------

with OUTPUT.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=FIELDS,
    )

    writer.writeheader()
    writer.writerows(report)


# ---------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------

print("=" * 80)
print("RNASeq Scout — SCIENTIFIC REVIEW REPORT")
print("=" * 80)

print()
print(f"Benchmark units : {len(report)}")
print(f"Output          : {OUTPUT}")

print()
print("Unit composition:")

for key, value in sorted(
    Counter(r["benchmark_unit"] for r in report).items()
):
    print(f"  {key:10s}: {value}")

print()
print("Modality composition:")

for key, value in sorted(
    Counter(r["modality"] for r in report).items()
):
    print(f"  {key:12s}: {value}")

print()
print("Metadata completeness:")

for key, value in sorted(
    Counter(r["metadata_completeness"] for r in report).items()
):
    print(f"  {key:10s}: {value}")

print()
print(
    "Potential boundary cases:",
    sum(bool(r["boundary_case_flag"]) for r in report),
)

print(
    "Multiple-unit family cases:",
    sum(bool(r["redundancy_flag"]) for r in report),
)

print()
print("Review fields remain blank.")
print(
    "This report is repository-metadata-based and does not "
    "contain experimental ground truth."
)

print()
print("=" * 80)
