from types import SimpleNamespace

from rnaseq_nav.intelligence.design_intelligence import (
    generate_design_insight,
)


def make_metadata():
    return SimpleNamespace(
        project=SimpleNamespace(accession="PRJNA_TEST"),
        study=SimpleNamespace(accession="SRP_TEST"),
        experiment=SimpleNamespace(
            accession="SRX_TEST",
            title="RNA sequencing study",
            library_strategy="RNA_SEQ",
            library_source="TRANSCRIPTOMIC",
            library_selection="cDNA",
            layout="PAIRED",
            platform="ILLUMINA",
            instrument="Illumina instrument",
            construction_protocol="",
        ),
        run=SimpleNamespace(
            accession="SRR_TEST",
            total_spots=1000,
            total_bases=100000,
            public=True,
        ),
        sample=SimpleNamespace(
            accession="SRS_TEST",
            biosample="SAMN_TEST",
            organism="Homo sapiens",
            title="",
            description="",
            attributes=[],
        ),
    )


def make_evidence():
    return SimpleNamespace(
        unique_biosample_count=12,
        retrieved_biosample_count=12,
        failed_biosample_count=0,
        warnings=[],
        attribute_values={
            "treatment": {
                "Control": 4,
                "Acidification": 4,
                "Warming": 4,
            },
            "time": {
                "Day0": 4,
                "Day15": 4,
                "Day30": 4,
            },
        },
    )


def test_study_biosample_patterns_are_reported_as_observed_features():
    insight = generate_design_insight(
        make_metadata(),
        study_biosample_evidence=make_evidence(),
    )

    observed = "\n".join(insight.observed_features)

    assert "12 of 12 unique BioSamples" in observed
    assert "Control (4 BioSamples)" in observed
    assert "Acidification (4 BioSamples)" in observed
    assert "Warming (4 BioSamples)" in observed
    assert "Day0 (4 BioSamples)" in observed
    assert "Day15 (4 BioSamples)" in observed
    assert "Day30 (4 BioSamples)" in observed
    assert "not confirmed independent biological replicates" in observed


def test_study_patterns_do_not_overwrite_study_level_assignments():
    insight = generate_design_insight(
        make_metadata(),
        study_biosample_evidence=make_evidence(),
    )

    # Aggregate sample attributes must not be promoted to a single
    # study-level treatment, time point, or replicate assignment.
    assert insight.treatment == ""
    assert insight.time_point == ""
    assert insight.replicate_information != (
        "4 biological replicates per group"
    )


def test_incomplete_study_biosample_retrieval_adds_warning():
    evidence = make_evidence()
    evidence.unique_biosample_count = 12
    evidence.retrieved_biosample_count = 10
    evidence.warnings = [
        "Study-level BioSample evidence is incomplete."
    ]

    insight = generate_design_insight(
        make_metadata(),
        study_biosample_evidence=evidence,
    )

    assert any(
        "10 of 12 unique BioSamples" in feature
        for feature in insight.observed_features
    )
    assert any(
        "Study BioSample enrichment: "
        "Study-level BioSample evidence is incomplete."
        in warning
        for warning in insight.warnings
    )


def test_design_insight_still_accepts_metadata_without_study_evidence():
    insight = generate_design_insight(make_metadata())

    assert insight is not None
    assert isinstance(insight.observed_features, list)
    assert not any(
        "Study BioSample metadata retrieved" in feature
        for feature in insight.observed_features
    )
