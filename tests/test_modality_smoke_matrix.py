"""
RNA-Seq Scout

Modality Intelligence Smoke Matrix
-----------------------------------

Curated accession-level smoke tests for the modality
intelligence layer.

The matrix verifies that structured SRA library strategies
are translated into the expected modality, workflow
classification, RNA-seq compatibility, and compatibility
status.

Structured library strategy is treated as the primary
modality evidence.
"""

import os

import pytest

from rnaseq_nav.navigator import RNASeqNavigator


# ==========================================================
# Curated accession matrix
# ==========================================================

CASES = [
    # accession       strategy       modality
    # compatibility   status

    (
        "SRR17730393",
        "RNA_SEQ",
        "RNA-seq",
        True,
        "Compatible",
    ),

    (
        "SRR1039508",
        "RNA_SEQ",
        "RNA-seq",
        True,
        "Compatible",
    ),

    (
        "SRR5127200",
        "MIRNA_SEQ",
        "miRNA sequencing",
        False,
        "Specialized workflow",
    ),

    (
        "SRR17731267",
        "AMPLICON",
        "Amplicon sequencing",
        False,
        "Not compatible",
    ),

    (
        "SRR35754973",
        "WGS",
        "Whole-genome sequencing",
        False,
        "Not compatible",
    ),

    (
        "SRR29888391",
        "WXS",
        "Whole-exome sequencing",
        False,
        "Not compatible",
    ),

    (
        "SRR492446",
        "CHIP_SEQ",
        "ChIP-seq",
        False,
        "Not compatible",
    ),

    (
        "SRR13772342",
        "ATAC_SEQ",
        "ATAC-seq",
        False,
        "Not compatible",
    ),
]


# ==========================================================
# Navigator fixture
# ==========================================================

@pytest.fixture(scope="module")
def navigator():
    """
    Create one navigator for the complete smoke matrix.
    """

    email = os.environ.get("NCBI_EMAIL")

    if not email:
        pytest.fail(
            "NCBI_EMAIL environment variable is required "
            "for accession-level smoke tests."
        )

    return RNASeqNavigator(email=email)


# ==========================================================
# Accession-level modality smoke test
# ==========================================================

@pytest.mark.parametrize(
    (
        "accession,"
        "expected_strategy,"
        "expected_modality,"
        "expected_compatibility,"
        "expected_status"
    ),
    CASES,
)
def test_curated_modality_smoke_matrix(
    navigator,
    accession,
    expected_strategy,
    expected_modality,
    expected_compatibility,
    expected_status,
):
    """
    Verify modality classification for each curated
    SRA accession.
    """

    result = navigator.inspect(accession)

    assert result.success, (
        f"{accession} failed inspection: {result.error}"
    )

    insight = result.modality_insight

    assert insight is not None, (
        f"{accession} produced no modality insight."
    )

    assert insight.library_strategy == expected_strategy, (
        f"{accession}: expected strategy "
        f"{expected_strategy!r}, got "
        f"{insight.library_strategy!r}"
    )

    assert insight.modality == expected_modality, (
        f"{accession}: expected modality "
        f"{expected_modality!r}, got "
        f"{insight.modality!r}"
    )

    assert insight.rna_seq_compatible is expected_compatibility, (
        f"{accession}: expected RNA-seq compatibility "
        f"{expected_compatibility!r}, got "
        f"{insight.rna_seq_compatible!r}"
    )

    assert insight.compatibility_status == expected_status, (
        f"{accession}: expected compatibility status "
        f"{expected_status!r}, got "
        f"{insight.compatibility_status!r}"
    )


# ==========================================================
# Unknown / incomplete metadata
# ==========================================================

def test_unknown_strategy_is_uncertain():
    """
    Verify that missing library strategy remains uncertain
    rather than being incorrectly classified as RNA-seq or
    another supported modality.
    """

    from rnaseq_nav.intelligence.modality_intelligence import (
        generate_modality_insight,
    )
    from rnaseq_nav.models import (
        ExperimentMetadata,
        Metadata,
        SampleMetadata,
    )

    metadata = Metadata(
        experiment=ExperimentMetadata(
            library_strategy="",
            library_source="",
            library_selection="",
            layout="PAIRED",
            platform="ILLUMINA",
        ),
        sample=SampleMetadata(
            organism="Unknown organism",
        ),
    )

    insight = generate_modality_insight(metadata)

    assert insight.modality == (
        "Sequencing modality not established"
    )

    assert insight.workflow_family == "Unknown"

    assert insight.rna_seq_compatible is None

    assert insight.compatibility_status == "Uncertain"

    assert insight.classification_confidence == "Low"
