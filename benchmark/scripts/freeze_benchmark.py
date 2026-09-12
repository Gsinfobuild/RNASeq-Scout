import csv
import hashlib
from pathlib import Path


INPUT = Path(
    "benchmark/results/benchmark_scientific_review.csv"
)

OUTPUT = Path(
    "benchmark/benchmark_manifest_v1.0.csv"
)

SHA_OUTPUT = Path(
    "benchmark/benchmark_manifest_v1.0.sha256"
)


REQUIRED_COLUMNS = [
    "accession",
    "benchmark_unit",
    "modality",
    "study_family",
    "normalized_organism_group",
    "scientific_review_decision",
]


with INPUT.open(
    encoding="utf-8",
    newline=""
) as f:
    rows = list(csv.DictReader(f))


if len(rows) != 50:
    raise SystemExit(
        f"ERROR: expected 50 records, found {len(rows)}"
    )


missing = [
    field
    for field in REQUIRED_COLUMNS
    if field not in rows[0]
]

if missing:
    raise SystemExit(
        "ERROR: missing required columns: "
        + ", ".join(missing)
    )


accessions = [
    row["accession"].strip()
    for row in rows
]

if len(accessions) != len(set(accessions)):
    raise SystemExit(
        "ERROR: duplicate accession detected."
    )


if any(
    row["scientific_review_decision"] != "RETAIN"
    for row in rows
):
    raise SystemExit(
        "ERROR: benchmark contains a non-RETAIN record."
    )


# ------------------------------------------------------------
# Frozen manifest
#
# Deliberately contains only selection-level information.
# No Scout predictions and no experimental truth.
# ------------------------------------------------------------

manifest_columns = [
    "benchmark_id",
    "accession",
    "accession_type",
    "modality",
    "study_family",
    "normalized_organism_group",
    "scientific_review_decision",
]


manifest = []

for i, row in enumerate(rows, 1):

    manifest.append(
        {
            "benchmark_id": f"RSB{i:03d}",
            "accession": row["accession"].strip(),
            "accession_type": row["benchmark_unit"].strip(),
            "modality": row["modality"].strip(),
            "study_family": row["study_family"].strip(),
            "normalized_organism_group": row[
                "normalized_organism_group"
            ].strip(),
            "scientific_review_decision": row[
                "scientific_review_decision"
            ].strip(),
        }
    )


with OUTPUT.open(
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=manifest_columns
    )

    writer.writeheader()
    writer.writerows(manifest)


# ------------------------------------------------------------
# SHA-256 checksum
# ------------------------------------------------------------

digest = hashlib.sha256(
    OUTPUT.read_bytes()
).hexdigest()


SHA_OUTPUT.write_text(
    digest + "  " + OUTPUT.name + "\n",
    encoding="utf-8"
)


print("=" * 110)
print("RNASeq Scout — BENCHMARK FREEZE")
print("=" * 110)
print()

print(
    f"Benchmark units : {len(manifest)}"
)

print(
    f"Manifest        : {OUTPUT}"
)

print(
    f"SHA-256         : {digest}"
)

print(
    f"Checksum file   : {SHA_OUTPUT}"
)

print()
print(
    "The manifest contains selection metadata only."
)

print(
    "Scout predictions and experimental truth are NOT included."
)

print()
print("BENCHMARK MANIFEST CREATED")
print("=" * 110)
