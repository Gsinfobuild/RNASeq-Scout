#!/usr/bin/env python3

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rnaseq_nav.navigator import RNASeqNavigator
from rnaseq_nav.evidence.source_enrichment import enrich_source_evidence


RNA_SEQ_CASES = [
    "GSE135553",
    "GSE129516",
    "GSE150728",
    "GSE148171",
    "GSE148930",
]

NEGATIVE_CASES = [
    "GSE10072",
]

ALL_CASES = RNA_SEQ_CASES + NEGATIVE_CASES


def check_app_public_status_rule():
    """
    Confirm that the GEO-specific public-status rule exists
    in the Streamlit UI layer.
    """
    path = Path("rnaseq_nav/ui/app.py")

    if not path.exists():
        return False

    text = path.read_text(encoding="utf-8")

    return (
        "RNASEQ_SCOUT_GEO_PUBLIC_STATUS_REFINEMENT" in text
        or (
            'startswith("GSE")' in text
            and "public = True" in text
        )
    )


def run_case(navigator, accession, expect_rnaseq):
    print()
    print("=" * 78)
    print(f"ACCESSION: {accession}")
    print("=" * 78)

    result = navigator.inspect(
        accession,
        enrich_study_biosamples=True,
    )

    success = getattr(result, "success", False)

    print(f"Inspection success       : {success}")

    if not success:
        print(f"ERROR                    : {getattr(result, 'error', '')}")
        return False

    metadata = getattr(result, "metadata", None)

    glance = getattr(
        result,
        "experiment_at_a_glance",
        None,
    )

    landscape = getattr(
        result,
        "study_experimental_landscape",
        None,
    )

    modality = getattr(
        result,
        "modality_insight",
        None,
    )

    print(
        "Study accession          : "
        f"{getattr(getattr(metadata, 'study', None), 'accession', '')}"
    )

    if glance is not None:
        print(
            "Study experiments        : "
            f"{getattr(glance, 'experiment_count', 0)}"
        )

        print(
            "Unique GEO samples       : "
            f"{getattr(glance, 'unique_sample_count', 0)}"
        )

        print(
            "Unique BioSamples        : "
            f"{getattr(glance, 'unique_biosample_count', 0)}"
        )

    if modality is not None:
        modality_name = getattr(
            modality,
            "modality",
            "",
        )

        compatible = getattr(
            modality,
            "rna_seq_compatible",
            None,
        )

        confidence = getattr(
            modality,
            "classification_confidence",
            "",
        )

        strategy = getattr(
            modality,
            "library_strategy",
            "",
        )

        print(f"Library strategy         : {strategy}")
        print(f"Modality                 : {modality_name}")
        print(f"RNA-seq compatible       : {compatible}")
        print(f"Classification confidence: {confidence}")

        if expect_rnaseq:
            if modality_name != "RNA-seq":
                print(
                    "FAIL: expected RNA-seq classification."
                )
                return False

            if compatible is not True:
                print(
                    "FAIL: expected RNA-seq compatibility."
                )
                return False

        else:
            if modality_name == "RNA-seq":
                print(
                    "FAIL: array negative control was classified "
                    "as RNA-seq."
                )
                return False

    else:
        print("Modality                 : MISSING")

        if expect_rnaseq:
            return False

    if landscape is not None:
        total = getattr(
            landscape,
            "total_experiments",
            0,
        )

        contexts = getattr(
            landscape,
            "context_counts",
            {},
        )

        assays = getattr(
            landscape,
            "assay_family_counts",
            {},
        )

        print(f"Landscape experiments    : {total}")
        print(f"Landscape assays         : {assays}")
        print(f"Landscape contexts       : {contexts}")

        if total <= 0:
            print(
                "FAIL: study landscape contains no experiments."
            )
            return False

    else:
        print("Study landscape          : MISSING")
        return False

    print()
    print("Source-aware enrichment")

    try:
        evidence = enrich_source_evidence(
            accession
        )

        print(
            "Enrichment attempted     : "
            f"{getattr(evidence, 'attempted', None)}"
        )

        print(
            "Enrichment status        : "
            f"{getattr(evidence, 'retrieval_status', '')}"
        )

        print(
            "PubMed records           : "
            f"{getattr(evidence, 'publication_count', 0)}"
        )

        print(
            "PMC records              : "
            f"{getattr(evidence, 'pmc_count', 0)}"
        )

        warnings = getattr(
            evidence,
            "warnings",
            [],
        )

        if warnings:
            print(
                "Enrichment warnings      : "
                f"{warnings}"
            )

    except Exception as exc:
        print(
            "FAIL: source enrichment raised an exception:"
        )
        print(
            f"      {type(exc).__name__}: {exc}"
        )
        return False

    # GEO records should remain publicly represented by the
    # Streamlit-specific GEO public-status rule.
    print()
    print(
        "GEO public-status rule   : "
        "checked in app.py"
    )

    return True


def main():
    print("=" * 78)
    print("RNA-SEQ SCOUT — CROSS-GEO FEATURE VALIDATION")
    print("=" * 78)

    print()
    print("RNA-seq validation cases:")
    for accession in RNA_SEQ_CASES:
        print(f"  - {accession}")

    print()
    print("Negative control:")
    for accession in NEGATIVE_CASES:
        print(f"  - {accession}")

    print()

    if not check_app_public_status_rule():
        print(
            "FAIL: GEO public-status rule was not found in app.py."
        )
        return 1

    print(
        "GEO public-status rule    : PRESENT"
    )

    navigator = RNASeqNavigator(
        email="gshankar.bbau@gmail.com"
    )

    failures = []

    for accession in RNA_SEQ_CASES:
        try:
            passed = run_case(
                navigator,
                accession,
                expect_rnaseq=True,
            )
        except Exception as exc:
            print()
            print(
                f"FAIL: {accession} raised "
                f"{type(exc).__name__}: {exc}"
            )
            passed = False

        if not passed:
            failures.append(accession)

    for accession in NEGATIVE_CASES:
        try:
            passed = run_case(
                navigator,
                accession,
                expect_rnaseq=False,
            )
        except Exception as exc:
            print()
            print(
                f"FAIL: {accession} raised "
                f"{type(exc).__name__}: {exc}"
            )
            passed = False

        if not passed:
            failures.append(accession)

    print()
    print("=" * 78)
    print("FINAL CROSS-GEO VALIDATION")
    print("=" * 78)

    if failures:
        print()
        print("FAILED ACCESSIONS:")
        for accession in failures:
            print(f"  - {accession}")

        print()
        print(
            f"Result: {len(ALL_CASES) - len(failures)}/"
            f"{len(ALL_CASES)} accessions passed."
        )

        return 1

    print()
    print(
        f"PASS: all {len(ALL_CASES)} GEO accessions passed."
    )

    print()
    print("RNA-seq positive cases:")
    for accession in RNA_SEQ_CASES:
        print(f"  PASS  {accession}")

    print()
    print("RNA-seq negative control:")
    for accession in NEGATIVE_CASES:
        print(f"  PASS  {accession}")

    print()
    print(
        "Cross-GEO feature validation completed successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
