#!/usr/bin/env python3

import csv
from pathlib import Path
from collections import Counter, defaultdict


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
    / "scientific_review_triage.csv"
)


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


def get_accession(row):
    return first(row, "accession")


def get_family(row):
    return first(
        row,
        "discovery_family",
        "candidate_study_accession",
        "study_accession",
        "project_accession",
    )


def get_unit(row):
    value = first(
        row,
        "benchmark_unit",
        "accession_type",
    ).lower()

    if value in {"experiment", "run", "study"}:
        return value

    accession = get_accession(row).upper()

    if accession.startswith(("SRX", "ERX", "DRX")):
        return "experiment"

    if accession.startswith(("SRR", "ERR", "DRR")):
        return "run"

    if accession.startswith(("SRP", "ERP", "DRP")):
        return "study"

    return value


def normalize_modality(value):
    value = clean(value)

    mapping = {
        "RNA_SEQ": "RNA-Seq",
        "RNA-Seq": "RNA-Seq",
        "RNA-seq": "RNA-Seq",

        "WGS": "WGS",
        "WXS": "WXS",

        "ATAC_SEQ": "ATAC-seq",
        "ATAC-seq": "ATAC-seq",

        "CHIP_SEQ": "ChIP-Seq",
        "ChIP-Seq": "ChIP-Seq",

        "HI-C": "Hi-C",
        "Hi-C": "Hi-C",

        "NCRNA_SEQ": "ncRNA-Seq",
        "ncRNA-Seq": "ncRNA-Seq",

        "MIRNA_SEQ": "miRNA-Seq",
        "miRNA-Seq": "miRNA-Seq",

        "AMPLICON": "AMPLICON",
    }

    return mapping.get(value, value)


def get_modality(row):
    return normalize_modality(
        first(
            row,
            "modality",
            "library_strategy",
        )
    )


# ---------------------------------------------------------------------
# Load candidate registry
# ---------------------------------------------------------------------

candidate_rows = {}

for path in POOLS:

    if not path.exists():
        continue

    with path.open(
        encoding="utf-8",
        newline="",
    ) as f:

        for row in csv.DictReader(f):

            accession = get_accession(row)

            if accession:
                candidate_rows.setdefault(
                    accession,
                    row,
                )


if not candidate_rows:
    raise RuntimeError(
        "No candidate records found."
    )


# ---------------------------------------------------------------------
# Build family-level repository landscape
# ---------------------------------------------------------------------

family_records = defaultdict(list)

for row in candidate_rows.values():

    family = get_family(row)

    if family:
        family_records[family].append(row)


family_modalities = {}

for family, records in family_records.items():

    modalities = sorted(
        {
            get_modality(row)
            for row in records
            if get_modality(row)
        }
    )

    family_modalities[family] = modalities


# ---------------------------------------------------------------------
# Load proposed benchmark
# ---------------------------------------------------------------------

with PROPOSED.open(
    encoding="utf-8",
    newline="",
) as f:

    selected = list(csv.DictReader(f))


if len(selected) != 50:
    raise RuntimeError(
        f"Expected 50 selected records, found {len(selected)}"
    )


selected_accessions = {
    get_accession(row)
    for row in selected
}


selected_family_counts = Counter(
    get_family(row)
    for row in selected
    if get_family(row)
)


# ---------------------------------------------------------------------
# Organism normalization
# ---------------------------------------------------------------------

def organism_group(row):

    value = first(
        row,
        "normalized_organism_group",
        "organism",
        "organism_common_name",
    )

    value = value.lower()

    if "homo sapiens" in value or value == "human":
        return "Homo sapiens"

    if "mus musculus" in value or value == "mouse":
        return "Mus musculus"

    if "drosophila" in value:
        return "Drosophila"

    if "caenorhabditis elegans" in value:
        return "C. elegans"

    if "danio rerio" in value:
        return "Danio rerio"

    if "escherichia coli" in value or value == "e. coli":
        return "E. coli"

    if "bacillus subtilis" in value:
        return "Bacillus subtilis"

    if "arabidopsis" in value:
        return "Arabidopsis"

    if "zea mays" in value:
        return "Zea mays"

    if "candida albicans" in value:
        return "Candida albicans"

    if "plasmodium falciparum" in value:
        return "Plasmodium falciparum"

    if "pseudomonas aeruginosa" in value:
        return "Pseudomonas aeruginosa"

    if "mycobacterium tuberculosis" in value:
        return "Mycobacterium tuberculosis"

    if "solanum lycopersicum" in value:
        return "Solanum lycopersicum"

    if "populus trichocarpa" in value:
        return "Populus trichocarpa"

    if not value:
        return "Unknown"

    return first(
        row,
        "normalized_organism_group",
        "organism",
        "organism_common_name",
    )


# ---------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------

CONTEXT_TERMS = [
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
    "differentiation",
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


BOUNDARY_TERMS = [
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


def signals(text, terms):
    text = clean(text).lower()

    hits = []

    for term in terms:
        if term.lower() in text:
            hits.append(term)

    return hits


# ---------------------------------------------------------------------
# Create triage rows
# ---------------------------------------------------------------------

triage = []

for row in selected:

    accession = get_accession(row)

    candidate = candidate_rows.get(accession)

    if candidate is None:
        raise RuntimeError(
            f"{accession} not found in candidate registry"
        )

    unit = get_unit(row)
    modality = get_modality(row)

    family = get_family(candidate)

    title = first(
        candidate,
        "experiment_title",
        "study_title",
        "title",
    )

    organism = first(
        candidate,
        "organism",
        "organism_common_name",
    )

    organism_norm = organism_group(candidate)

    strategy = first(
        candidate,
        "library_strategy",
    )

    source = first(
        candidate,
        "library_source",
    )

    selection = first(
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

    sample = first(
        candidate,
        "sample_accession",
    )

    biosample = first(
        candidate,
        "biosample_accession",
    )

    context_hits = signals(
        title,
        CONTEXT_TERMS,
    )

    boundary_hits = signals(
        title,
        BOUNDARY_TERMS,
    )

    family_mods = family_modalities.get(
        family,
        [],
    )

    # ---------------------------------------------------------------
    # Potential issues
    # ---------------------------------------------------------------

    flags = []

    if len(family_mods) > 1:
        flags.append(
            "MULTIMODALITY_FAMILY"
        )

    if boundary_hits:
        flags.append(
            "SPECIALIZED_OR_BOUNDARY_WORKFLOW"
        )

    if not organism:
        flags.append(
            "ORGANISM_FIELD_INCOMPLETE"
        )

    if not title:
        flags.append(
            "TITLE_CONTEXT_INCOMPLETE"
        )

    if not strategy:
        flags.append(
            "LIBRARY_STRATEGY_INCOMPLETE"
        )

    if not layout:
        flags.append(
            "LAYOUT_INCOMPLETE"
        )

    if not platform:
        flags.append(
            "PLATFORM_INCOMPLETE"
        )

    if selected_family_counts.get(family, 0) > 1:
        flags.append(
            "MULTIPLE_SELECTED_UNITS_IN_FAMILY"
        )

    # Same BioSample among selected units.
    same_biosample = []

    if biosample:

        for other in selected:

            other_acc = get_accession(other)

            if other_acc == accession:
                continue

            other_candidate = candidate_rows.get(
                other_acc
            )

            if not other_candidate:
                continue

            if (
                first(
                    other_candidate,
                    "biosample_accession",
                )
                == biosample
            ):
                same_biosample.append(
                    other_acc
                )

    if same_biosample:
        flags.append(
            "SAME_BIOSAMPLE_AS_OTHER_SELECTED_UNIT"
        )

    # ---------------------------------------------------------------
    # Triage priority
    # ---------------------------------------------------------------

    if (
        "ORGANISM_FIELD_INCOMPLETE" in flags
        or "LIBRARY_STRATEGY_INCOMPLETE" in flags
    ):
        priority = "HIGH"

    elif (
        "MULTIMODALITY_FAMILY" in flags
        or "SAME_BIOSAMPLE_AS_OTHER_SELECTED_UNIT" in flags
        or "SPECIALIZED_OR_BOUNDARY_WORKFLOW" in flags
    ):
        priority = "HIGH"

    elif (
        "MULTIPLE_SELECTED_UNITS_IN_FAMILY" in flags
        or context_hits
    ):
        priority = "MEDIUM"

    else:
        priority = "LOW"

    # ---------------------------------------------------------------
    # Preliminary review category
    # ---------------------------------------------------------------

    if "MULTIMODALITY_FAMILY" in flags:
        category = "Multimodality family"

    elif "SAME_BIOSAMPLE_AS_OTHER_SELECTED_UNIT" in flags:
        category = "Same BioSample / distinct selected unit"

    elif "SPECIALIZED_OR_BOUNDARY_WORKFLOW" in flags:
        category = "Specialized or workflow-boundary case"

    elif context_hits:
        category = "Informative biological context"

    else:
        category = "Clean repository case"

    triage.append(
        {
            "accession": accession,
            "benchmark_unit": unit,
            "modality": modality,
            "organism": organism,
            "normalized_organism_group": organism_norm,
            "study_family": family,

            "title": title,
            "library_strategy": strategy,
            "library_source": source,
            "library_selection": selection,
            "layout": layout,
            "platform": platform,

            "sample_accession": sample,
            "biosample_accession": biosample,

            "family_repository_modalities": (
                "; ".join(family_mods)
            ),

            "family_candidate_count": str(
                len(family_records.get(family, []))
            ),

            "selected_units_in_family": str(
                selected_family_counts.get(
                    family,
                    0,
                )
            ),

            "same_biosample_selected_units": (
                "; ".join(same_biosample)
            ),

            "biological_context_signals": (
                "; ".join(context_hits)
            ),

            "boundary_signals": (
                "; ".join(boundary_hits)
            ),

            "triage_category": category,
            "triage_priority": priority,
            "triage_flags": "; ".join(flags),

            # Human scientific-review fields.
            "review_decision": "",
            "review_notes": "",
        }
    )


# ---------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------

FIELDS = list(triage[0].keys())

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
    writer.writerows(triage)


# ---------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------

print("=" * 80)
print("RNASeq Scout — SCIENTIFIC REVIEW TRIAGE")
print("=" * 80)

print()
print(f"Benchmark units: {len(triage)}")
print(f"Output: {OUTPUT}")

print()
print("Triage priority:")

for key in ["HIGH", "MEDIUM", "LOW"]:

    count = sum(
        r["triage_priority"] == key
        for r in triage
    )

    print(
        f"  {key:6s}: {count}"
    )

print()
print("Triage categories:")

category_counts = Counter(
    r["triage_category"]
    for r in triage
)

for category, count in category_counts.most_common():
    print(
        f"  {count:2d}  {category}"
    )

print()
print("Flag counts:")

flag_counts = Counter()

for r in triage:

    for flag in r["triage_flags"].split("; "):

        if flag:
            flag_counts[flag] += 1

for flag, count in flag_counts.most_common():

    print(
        f"  {count:2d}  {flag}"
    )

print()
print("HIGH-priority records:")
print()

for r in triage:

    if r["triage_priority"] != "HIGH":
        continue

    print(
        f"{r['accession']:12s} | "
        f"{r['benchmark_unit']:10s} | "
        f"{r['modality']:12s} | "
        f"{r['organism'][:28]:28s} | "
        f"{r['triage_category']}"
    )

print()
print("=" * 80)
print("No Scout predictions or publication evidence were used.")
print("No benchmark selection was modified.")
print("=" * 80)
