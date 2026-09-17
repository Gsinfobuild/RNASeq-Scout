"""
RNASeq Scout

Regression tests for validation of incomplete run statistics.
"""

from types import SimpleNamespace

from rnaseq_nav.validation.validator import MetadataValidator


def make_metadata():
    """Create minimal valid metadata for validator testing."""
    return SimpleNamespace(
        project=SimpleNamespace(
            accession="PRJNA_TEST",
        ),
        study=SimpleNamespace(
            accession="SRP_TEST",
        ),
        experiment=SimpleNamespace(
            accession="SRX_TEST",
            library_strategy="RNA_SEQ",
            library_source="TRANSCRIPTOMIC",
            library_selection="cDNA",
            layout="PAIRED",
            platform="ILLUMINA",
        ),
        run=SimpleNamespace(
            accession="SRR_TEST",
            total_spots=None,
            total_bases=None,
            public=True,
        ),
        sample=SimpleNamespace(
            organism="Mycobacterium tuberculosis H37Rv",
        ),
    )


def test_validator_handles_missing_run_statistics():
    """Missing run statistics must produce warnings, not crash."""
    metadata = make_metadata()

    result = MetadataValidator().validate(metadata)

    assert result is not None

    assert any(
        issue.field == "total_spots"
        and issue.message == "Sequencing depth unavailable."
        for issue in result.issues
    )

    assert any(
        issue.field == "total_bases"
        and issue.message == "Total bases unavailable."
        for issue in result.issues
    )
