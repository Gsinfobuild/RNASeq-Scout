#!/usr/bin/env python3

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "benchmark"
    / "results"
    / "proposed_benchmark_50_v4.csv"
)

OUTPUT = (
    ROOT
    / "benchmark"
    / "results"
    / "benchmark_scientific_review.csv"
)


REVIEW_FIELDS = [
    "accession",
    "benchmark_unit",
    "modality",
    "organism",
    "normalized_organism_group",
    "study_family",
    "candidate_category",

    # Repository-level review
    "repository_title",
    "library_strategy",
    "library_source",
    "library_selection",
    "layout",
    "platform",

    # Scientific-review fields
    "metadata_informative",
    "biological_context_visible",
    "design_information_visible",
    "replicate_information_visible",
    "control_treatment_information_visible",

    # Selection-quality assessment
    "boundary_case",
    "potential_redundancy",
    "selection_concern",
    "review_decision",
    "review_notes",
]


def first(row, *names):
    for name in names:
        value = row.get(name, "")
        if value and value.strip():
            return value.strip()
    return ""


with INPUT.open(
    newline="",
    encoding="utf-8",
) as f:
    rows = list(csv.DictReader(f))


review_rows = []

for row in rows:

    out = {
        "accession": first(
            row,
            "accession",
        ),

        "benchmark_unit": first(
            row,
            "benchmark_unit",
            "accession_type",
        ),

        "modality": first(
            row,
            "modality",
            "library_strategy",
        ),

        "organism": first(
            row,
            "organism",
        ),

        "normalized_organism_group": first(
            row,
            "normalized_organism_group",
        ),

        "study_family": first(
            row,
            "discovery_family",
            "candidate_study_accession",
            "study_accession",
            "project_accession",
        ),

        "candidate_category": first(
            row,
            "candidate_category",
        ),

        "repository_title": first(
            row,
            "title",
            "experiment_title",
            "study_title",
        ),

        "library_strategy": first(
            row,
            "library_strategy",
            "modality",
        ),

        "library_source": first(
            row,
            "library_source",
        ),

        "library_selection": first(
            row,
            "library_selection",
        ),

        "layout": first(
            row,
            "layout",
        ),

        "platform": first(
            row,
            "platform",
        ),

        # Deliberately blank: these are human-review fields.
        "metadata_informative": "",
        "biological_context_visible": "",
        "design_information_visible": "",
        "replicate_information_visible": "",
        "control_treatment_information_visible": "",
        "boundary_case": "",
        "potential_redundancy": "",
        "selection_concern": "",
        "review_decision": "",
        "review_notes": "",
    }

    review_rows.append(out)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with OUTPUT.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=REVIEW_FIELDS,
    )

    writer.writeheader()
    writer.writerows(review_rows)


print(
    f"Created scientific-review worksheet "
    f"for {len(review_rows)} benchmark units:"
)

print(
    OUTPUT
)

print(
    "\nHuman-review fields were intentionally left blank."
)

print(
    "\nThe worksheet is NOT ground truth and should not "
    "be populated using Scout predictions."
)
