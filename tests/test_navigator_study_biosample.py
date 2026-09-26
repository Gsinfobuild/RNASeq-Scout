from types import SimpleNamespace

import rnaseq_nav.navigator as navigator_module

from rnaseq_nav.core.results import (
    ExperimentAtGlance,
    InspectionResult,
)

from rnaseq_nav.intelligence.study_biosample_evidence import (
    StudyBioSampleEvidence,
)

from rnaseq_nav.navigator import RNASeqNavigator


def make_test_navigator():
    navigator = object.__new__(RNASeqNavigator)

    client = object()

    navigator.discovery = SimpleNamespace(
        client=client
    )

    navigator.normalizer = SimpleNamespace(
        normalize=lambda metadata: SimpleNamespace(
            metadata=metadata
        )
    )

    navigator.validator = SimpleNamespace(
        validate=lambda metadata: "validation"
    )

    navigator.interpreter = SimpleNamespace(
        describe=lambda metadata, modality_insight=None:
        "description"
    )

    navigator.report_builder = SimpleNamespace(
        build=lambda metadata,
        normalization,
        validation,
        description:
        "report"
    )

    navigator.fetch = lambda accession: "metadata"

    return navigator, client


def patch_pipeline(monkeypatch, experiment_at_glance):
    monkeypatch.setattr(
        RNASeqNavigator,
        "_build_experiment_at_a_glance",
        lambda self, accession: experiment_at_glance,
    )

    monkeypatch.setattr(
        navigator_module,
        "generate_study_experimental_landscape",
        lambda records: "landscape",
    )

    monkeypatch.setattr(
        navigator_module,
        "generate_modality_insight",
        lambda metadata: "modality",
    )

    monkeypatch.setattr(
        navigator_module,
        "generate_metadata_insight",
        lambda metadata, modality_insight=None:
        "metadata insight",
    )

    monkeypatch.setattr(
        navigator_module,
        "generate_design_insight",
        lambda metadata: "design",
    )

    monkeypatch.setattr(
        navigator_module,
        "generate_suitability_insight",
        lambda metadata, design_insight, modality_insight:
        "suitability",
    )

    monkeypatch.setattr(
        navigator_module,
        "generate_reanalysis_readiness",
        lambda *args: "readiness",
    )

    monkeypatch.setattr(
        navigator_module,
        "generate_analysis_plan",
        lambda *args: "analysis plan",
    )


def test_inspection_result_has_optional_study_biosample_field():
    result = InspectionResult()

    assert result.study_biosample_evidence is None


def test_default_inspection_does_not_retrieve_study_biosamples(
    monkeypatch,
):
    study_experiments = [
        SimpleNamespace(
            sample_accession="SRS_TEST",
            biosample_accession="SAMN_TEST",
            experiment_accession="SRX_TEST",
            run_accessions=["SRR_TEST"],
        )
    ]

    experiment_at_glance = ExperimentAtGlance(
        study_experiments=study_experiments
    )

    navigator, _ = make_test_navigator()

    patch_pipeline(
        monkeypatch,
        experiment_at_glance,
    )

    calls = []

    def fake_generate(records, client):
        calls.append((records, client))
        return StudyBioSampleEvidence(
            total_study_experiments=len(records),
            unique_biosample_count=1,
        )

    monkeypatch.setattr(
        navigator_module,
        "generate_study_biosample_evidence",
        fake_generate,
    )

    result = navigator.inspect(
        "SRP_TEST"
    )

    assert result.success is True
    assert result.study_biosample_evidence is None
    assert calls == []


def test_study_biosample_enrichment_is_opt_in_and_reuses_study_records(
    monkeypatch,
):
    study_experiments = [
        SimpleNamespace(
            sample_accession="SRS_TEST",
            biosample_accession="SAMN_TEST",
            experiment_accession="SRX_TEST",
            run_accessions=["SRR_TEST"],
        )
    ]

    experiment_at_glance = ExperimentAtGlance(
        study_experiments=study_experiments
    )

    navigator, client = make_test_navigator()

    patch_pipeline(
        monkeypatch,
        experiment_at_glance,
    )

    calls = []

    evidence = StudyBioSampleEvidence(
        total_study_experiments=1,
        unique_biosample_count=1,
        retrieved_biosample_count=1,
    )

    def fake_generate(records, received_client):
        calls.append(
            (records, received_client)
        )
        return evidence

    monkeypatch.setattr(
        navigator_module,
        "generate_study_biosample_evidence",
        fake_generate,
    )

    result = navigator.inspect(
        "SRP_TEST",
        enrich_study_biosamples=True,
    )

    assert result.success is True
    assert result.study_biosample_evidence is evidence

    assert len(calls) == 1
    assert calls[0][0] is study_experiments
    assert calls[0][1] is client


def test_study_biosample_enrichment_does_not_run_for_run_accession(
    monkeypatch,
):
    navigator, _ = make_test_navigator()

    patch_pipeline(
        monkeypatch,
        experiment_at_glance=None,
    )

    calls = []

    def fake_generate(records, client):
        calls.append((records, client))
        return StudyBioSampleEvidence()

    monkeypatch.setattr(
        navigator_module,
        "generate_study_biosample_evidence",
        fake_generate,
    )

    result = navigator.inspect(
        "SRR_TEST",
        enrich_study_biosamples=True,
    )

    assert result.success is True
    assert result.study_biosample_evidence is None
    assert calls == []
