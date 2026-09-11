from types import SimpleNamespace

from rnaseq_nav.intelligence.modality_intelligence import (
    generate_modality_insight,
)
from rnaseq_nav.intelligence.design_intelligence import (
    generate_design_insight,
)
from rnaseq_nav.intelligence.suitability import (
    generate_suitability_insight,
)
from rnaseq_nav.intelligence.analysis_planner import (
    generate_analysis_plan,
)
from rnaseq_nav.intelligence.metadata_intelligence import (
    generate_metadata_insight,
)


from rnaseq_nav.intelligence.study_landscape import (
    generate_study_experimental_landscape,
)
from rnaseq_nav.models import StudyExperiment


def make_metadata(
    strategy="RNA_SEQ",
    title="Control and treated samples",
    organism="Mycobacterium tuberculosis H37Rv",
    layout="PAIRED",
    platform="ILLUMINA",
    source="TRANSCRIPTOMIC",
    selection="cDNA",
    run_accession="SRR17730393",
):
    return SimpleNamespace(
        project=SimpleNamespace(
            accession="PRJNA_TEST"
        ),
        study=SimpleNamespace(
            accession="SRP_TEST"
        ),
        experiment=SimpleNamespace(
            accession="SRX_TEST",
            title=title,
            library_strategy=strategy,
            library_source=source,
            library_selection=selection,
            layout=layout,
            platform=platform,
            instrument="Illumina instrument",
        ),
        run=SimpleNamespace(
            accession=run_accession,
            total_spots=1000,
            total_bases=100000,
            public=True,
        ),
        sample=SimpleNamespace(
            accession="SRS_TEST",
            biosample="SAMN_TEST",
            organism=organism,
        ),
    )


def test_rna_seq_is_classified_as_compatible():
    metadata = make_metadata(strategy="RNA_SEQ")

    insight = generate_modality_insight(metadata)

    assert insight.modality == "RNA-seq"
    assert insight.workflow_family == "bulk_rna_seq"
    assert insight.rna_seq_compatible is True
    assert insight.compatibility_status == "Compatible"
    assert insight.classification_confidence == "High"


def test_amplicon_is_not_rna_seq_compatible():
    metadata = make_metadata(
        strategy="AMPLICON",
        source="GENOMIC",
        selection="PCR",
    )

    insight = generate_modality_insight(metadata)

    assert insight.modality == "Amplicon sequencing"
    assert insight.workflow_family == "amplicon"
    assert insight.rna_seq_compatible is False
    assert insight.compatibility_status == "Not compatible"
    assert insight.classification_confidence == "High"

    assert any(
        "AMPLICON" in warning
        for warning in insight.warnings
    )


def test_unknown_strategy_remains_uncertain():
    metadata = make_metadata(strategy="")

    insight = generate_modality_insight(metadata)

    assert insight.rna_seq_compatible is None
    assert insight.compatibility_status == "Uncertain"
    assert insight.classification_confidence == "Low"


def test_small_rna_is_not_automatically_conventional_rna_seq():
    metadata = make_metadata(
        strategy="SMALL_RNA",
        source="TRANSCRIPTOMIC",
        selection="size fractionation",
    )

    insight = generate_modality_insight(metadata)

    assert insight.modality == "Small RNA sequencing"
    assert insight.workflow_family == "specialized_rna"
    assert insight.rna_seq_compatible is False
    assert insight.compatibility_status == "Specialized workflow"


def test_design_does_not_assume_biological_replicates_from_one_run():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="Iron stress treatment",
    )

    insight = generate_design_insight(metadata)

    assert "biological replicate" in (
        insight.replicate_information.lower()
    )

    assert "One sequencing run" in insight.replicate_information


def test_design_detects_explicit_biological_replicate():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title=(
            "GSM9401457: Low passage retinoblastoma cell line "
            "RB028, expressing non-specific shRNA biological "
            "replicate 2; Homo sapiens; RNA-Seq"
        ),
    )

    insight = generate_design_insight(metadata)

    assert (
        insight.replicate_information
        == (
            "Biological replicate 2 is explicitly identified "
            "in the experiment title."
        )
    )


def test_design_detects_replicate_without_assigning_biological_status():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title=(
            "GSM9724256: PC3 SLK-KO cells + MYC, "
            "replicate C; Homo sapiens; RNA-Seq"
        ),
    )

    insight = generate_design_insight(metadata)

    assert (
        insight.replicate_information
        == (
            "Replicate C is explicitly identified in the "
            "experiment title; biological or technical "
            "replicate status is not established."
        )
    )

    assert "biological replicate" not in (
        insight.replicate_information.lower()
    )


def test_design_marks_control_as_missing_when_not_explicit():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="Iron stress treatment",
    )

    insight = generate_design_insight(metadata)

    assert not insight.control

    assert (
        "Control-group annotation"
        in insight.missing_information
    )


def test_amplicon_is_not_suitable_for_rna_seq():
    metadata = make_metadata(
        strategy="AMPLICON",
        source="GENOMIC",
        selection="PCR",
    )

    modality = generate_modality_insight(metadata)
    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    assert (
        suitability.overall
        == "Not suitable for RNA-seq analysis"
    )

    assert suitability.score == 0


def test_suitability_recognizes_run_evidence_without_run_accession():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        run_accession="",
    )

    modality = generate_modality_insight(metadata)
    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    assert any(
        "Sequencing run information available"
        in item
        for item in suitability.observed_evidence
    )

    assert (
        "Sequencing run information"
        not in suitability.missing_information
    )


def test_suitability_treats_explicit_biological_replicate_as_observed():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title=(
            "GSM9401457: Low passage retinoblastoma cell line "
            "RB028, expressing non-specific shRNA biological "
            "replicate 2; Homo sapiens; RNA-Seq"
        ),
    )

    modality = generate_modality_insight(metadata)
    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    assert any(
        "Biological replicate 2 is explicitly identified"
        in item
        for item in suitability.observed_evidence
    )

    assert not any(
        "Biological replicate 2 is explicitly identified"
        in item
        for item in suitability.warnings
    )

    assert (
        "Biological replicate annotation"
        not in suitability.missing_information
    )


def test_suitability_preserves_uncertainty_for_generic_replicate():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title=(
            "GSM9724256: PC3 SLK-KO cells + MYC, "
            "replicate C; Homo sapiens; RNA-Seq"
        ),
    )

    modality = generate_modality_insight(metadata)
    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    assert any(
        "Replicate C is explicitly identified"
        in item
        for item in suitability.observed_evidence
    )

    assert any(
        "Biological versus technical replicate status"
        in item
        for item in suitability.warnings
    )

    assert (
        "Biological versus technical replicate status"
        in suitability.missing_information
    )

    assert (
        "Biological replicate annotation"
        not in suitability.missing_information
    )


def test_unknown_modality_does_not_become_suitable():
    metadata = make_metadata(strategy="")

    modality = generate_modality_insight(metadata)
    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    assert (
        suitability.overall
        == "RNA-seq compatibility uncertain"
    )

    assert suitability.score == 0


def test_rna_seq_receives_rna_seq_analysis_plan():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="RNA-seq experiment",
    )

    metadata_insight = generate_metadata_insight(metadata)
    modality = generate_modality_insight(metadata)
    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    plan = generate_analysis_plan(
        metadata,
        metadata_insight,
        design,
        suitability,
        modality,
    )

    assert plan.workflow == "RNA-seq analysis"
    assert plan.alignment == "STAR"
    assert plan.quantification == "featureCounts"
    assert plan.differential_analysis == "DESeq2"


def test_amplicon_cannot_receive_rna_seq_tools():
    metadata = make_metadata(
        strategy="AMPLICON",
        source="GENOMIC",
        selection="PCR",
        title="16S amplicon sequencing",
    )

    metadata_insight = generate_metadata_insight(metadata)
    modality = generate_modality_insight(metadata)
    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    plan = generate_analysis_plan(
        metadata,
        metadata_insight,
        design,
        suitability,
        modality,
    )

    assert (
        plan.workflow
        == "RNA-seq workflow not applicable"
    )

    assert plan.alignment == "Not applicable"
    assert plan.quantification == "Not applicable"
    assert plan.differential_analysis == "Not applicable"
    assert plan.design_formula == "Not applicable"
    assert plan.confidence == "High"


def test_modality_gate_propagates_through_suitability_and_planning():
    metadata = make_metadata(
        strategy="AMPLICON",
        source="GENOMIC",
        selection="PCR",
        title="16S amplicon sequencing",
    )

    modality = generate_modality_insight(metadata)

    assert modality.rna_seq_compatible is False

    design = generate_design_insight(metadata)

    suitability = generate_suitability_insight(
        metadata,
        design_insight=design,
        modality_insight=modality,
    )

    assert suitability.score == 0
    assert (
        suitability.overall
        == "Not suitable for RNA-seq analysis"
    )

    metadata_insight = generate_metadata_insight(metadata)

    plan = generate_analysis_plan(
        metadata,
        metadata_insight,
        design,
        suitability,
        modality,
    )

    assert (
        plan.workflow
        == "RNA-seq workflow not applicable"
    )

    assert plan.alignment == "Not applicable"
    assert plan.quantification == "Not applicable"
    assert plan.differential_analysis == "Not applicable"
    assert plan.design_formula == "Not applicable"



def make_study_experiment(title):
    return StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title=title,
        run_accessions=["SRR_TEST"],
        organism="Mycobacterium tuberculosis H37Rv",
    )


def test_study_landscape_classifies_assay_families():
    records = [
        make_study_experiment(
            "RNA-seq of M. tuberculosis H37Rv: kanamycin"
        ),
        make_study_experiment(
            "sRNA-seq of M. tuberculosis H37Rv: starvation"
        ),
        make_study_experiment(
            "TEX+ RNA-seq of M. tuberculosis H37Rv: excess iron"
        ),
    ]

    landscape = generate_study_experimental_landscape(
        records
    )

    assert landscape.total_experiments == 3

    assert landscape.assay_family_counts == {
        "RNA-seq": 1,
        "sRNA-seq": 1,
        "TEX+ RNA-seq": 1,
    }


def test_study_landscape_extracts_context_after_final_colon():
    records = [
        make_study_experiment(
            "RNA-seq of M. tuberculosis H37Rv: kanamycin"
        ),
        make_study_experiment(
            "RNA-seq of M. tuberculosis H37Rv: excess iron"
        ),
    ]

    landscape = generate_study_experimental_landscape(
        records
    )

    assert landscape.context_counts == {
        "kanamycin": 1,
        "excess iron": 1,
    }


def test_study_landscape_preserves_observed_context_labels():
    records = [
        make_study_experiment(
            "RNA-seq of M. tuberculosis H37Rv: detergent stress"
        ),
        make_study_experiment(
            "TEX+ RNA-seq of M. tuberculosis H37Rv: detergent"
        ),
    ]

    landscape = generate_study_experimental_landscape(
        records
    )

    assert "detergent stress" in landscape.observed_contexts
    assert "detergent" in landscape.observed_contexts

    assert landscape.context_counts["detergent stress"] == 1
    assert landscape.context_counts["detergent"] == 1


def test_study_landscape_marks_missing_context_as_unspecified():
    records = [
        make_study_experiment(
            "RNA-seq of M. tuberculosis H37Rv"
        ),
    ]

    landscape = generate_study_experimental_landscape(
        records
    )

    assert landscape.context_counts == {
        "Unspecified": 1
    }


def test_study_landscape_unrecognized_assay_is_unclassified():
    records = [
        make_study_experiment(
            "Unknown sequencing workflow: condition A"
        ),
    ]

    landscape = generate_study_experimental_landscape(
        records
    )

    assert landscape.assay_family_counts == {
        "Unclassified": 1
    }

    assert any(
        "could not be assigned" in warning
        for warning in landscape.warnings
    )


def test_study_landscape_empty_records_are_handled():
    landscape = generate_study_experimental_landscape([])

    assert landscape.total_experiments == 0
    assert landscape.assay_family_counts == {}
    assert landscape.context_counts == {}
    assert landscape.assay_context_counts == {}
    assert landscape.observed_assay_families == []
    assert landscape.observed_contexts == []

    assert landscape.warnings





def _make_test_metadata(
    accession="SRR_TEST",
    organism="Homo sapiens",
    library_strategy="RNA-Seq",
    library_source="TRANSCRIPTOMIC",
    library_selection="cDNA",
    layout="PAIRED",
    platform="ILLUMINA",
):
    from rnaseq_nav.models import (
        Metadata,
        ExperimentMetadata,
        SampleMetadata,
    )

    return Metadata(
        experiment=ExperimentMetadata(
            accession=accession,
            library_strategy=library_strategy,
            library_source=library_source,
            library_selection=library_selection,
            layout=layout,
            platform=platform,
        ),
        sample=SampleMetadata(
            organism=organism,
        ),
    )


def test_reanalysis_readiness_rna_seq_with_established_design():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )

    metadata = _make_test_metadata(
        accession="SRR17730393",
        organism="Mycobacterium tuberculosis H37Rv",
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "RNA-seq",
            "compatibility_status": "Compatible",
        },
    )()

    design = type(
        "Design",
        (),
        {
            "condition": "treatment",
            "control": "control",
            "treatment": "drug treatment",
            "time_point": "not established",
            "replicate_information": "biological replicates established",
            "design_confidence": "High",
        },
    )()

    suitability = type(
        "Suitability",
        (),
        {
            "overall": "Suitable",
            "warnings": [],
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        design,
        suitability,
    )

    assert result.verdict == "Ready for reanalysis"

    assert any(
        "compatible with RNA-seq analysis" in item
        for item in result.observed_evidence
    )

    assert any(
        "Replicate information" in item
        for item in result.observed_evidence
    )


def test_reanalysis_readiness_does_not_assume_replicates():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )

    metadata = _make_test_metadata(
        accession="SRR17730393",
        organism="Mycobacterium tuberculosis H37Rv",
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "RNA-seq",
            "compatibility_status": "Compatible",
        },
    )()

    design = type(
        "Design",
        (),
        {
            "condition": "treatment",
            "control": "not established",
            "treatment": "not established",
            "time_point": "not established",
            "replicate_information": "could not be established",
            "design_confidence": "Insufficient information",
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        design,
        None,
    )

    assert result.verdict == "Exploratory use only"

    assert any(
        "Biological replicate structure" in item
        for item in result.not_established
    )


def test_reanalysis_readiness_preserves_explicit_biological_replicate():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )

    metadata = _make_test_metadata(
        accession="SRX31545771",
        organism="Homo sapiens",
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "RNA-seq",
            "compatibility_status": "Compatible",
        },
    )()

    design = type(
        "Design",
        (),
        {
            "condition": "",
            "control": "",
            "treatment": "",
            "time_point": "",
            "replicate_information": (
                "Biological replicate 2 is explicitly identified "
                "in the experiment title."
            ),
            "design_confidence": "Partially characterized",
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        design,
        None,
    )

    assert any(
        "Biological replicate 2 is explicitly identified"
        in item
        for item in result.observed_evidence
    )

    assert not any(
        "Biological replicate structure could not be established"
        in item
        for item in result.not_established
    )


def test_reanalysis_readiness_preserves_generic_replicate_uncertainty():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )

    metadata = _make_test_metadata(
        accession="SRX33270018",
        organism="Homo sapiens",
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "RNA-seq",
            "compatibility_status": "Compatible",
        },
    )()

    design = type(
        "Design",
        (),
        {
            "condition": "",
            "control": "",
            "treatment": "",
            "time_point": "",
            "replicate_information": (
                "Replicate C is explicitly identified in the "
                "experiment title; biological or technical "
                "replicate status is not established."
            ),
            "design_confidence": "Partially characterized",
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        design,
        None,
    )

    assert any(
        "Replicate C is explicitly identified"
        in item
        for item in result.observed_evidence
    )

    assert any(
        "Biological versus technical replicate status could not be established"
        in item
        for item in result.not_established
    )


def test_reanalysis_readiness_records_available_run_evidence():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )
    from rnaseq_nav.models import RunMetadata

    metadata = _make_test_metadata(
        accession="SRR17730393",
        organism="Mycobacterium tuberculosis H37Rv",
    )

    metadata.run = RunMetadata(
        accession="SRR17730393",
        total_spots=100000,
        total_bases=10000000,
        public=True,
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "RNA-seq",
            "compatibility_status": "Compatible",
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        None,
        None,
    )

    assert any(
        "Sequencing run" in item
        for item in result.observed_evidence
    )


def test_reanalysis_readiness_rejects_incompatible_modality():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )

    metadata = _make_test_metadata(
        accession="SRX35157977",
        organism="Homo sapiens",
        library_strategy="AMPLICON",
        library_source="GENOMIC",
        library_selection="PCR",
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "Amplicon sequencing",
            "compatibility_status": "Not compatible",
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        None,
        None,
    )

    assert result.verdict == "Not suitable"

    assert any(
        "not compatible" in item.lower()
        for item in result.warnings
    )


def test_reanalysis_readiness_uncertain_modality_is_conservative():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )

    metadata = _make_test_metadata(
        accession="SRX_UNKNOWN",
        organism="Homo sapiens",
        library_strategy="",
        library_source="",
        library_selection="",
        layout="",
        platform="",
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "Unknown",
            "compatibility_status": "Uncertain",
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        None,
        None,
    )

    assert result.verdict == "Insufficient evidence"

    assert any(
        "modality" in item.lower()
        for item in result.not_established
    )


def test_reanalysis_readiness_is_not_a_percentage_score():
    from rnaseq_nav.intelligence.reanalysis_readiness import (
        generate_reanalysis_readiness,
    )

    metadata = _make_test_metadata(
        accession="SRR_TEST",
        organism="Homo sapiens",
    )

    modality = type(
        "Modality",
        (),
        {
            "modality": "RNA-seq",
            "compatibility_status": "Compatible",
        },
    )()

    result = generate_reanalysis_readiness(
        metadata,
        modality,
        None,
        None,
    )

    assert not hasattr(result, "score")

    assert result.verdict in {
        "Ready for reanalysis",
        "Conditionally reusable",
        "Exploratory use only",
        "Insufficient evidence",
        "Not suitable",
    }


def test_study_landscape_uses_explicit_rna_seq_strategy():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="GSM123456: treated sample; Homo sapiens",
        library_strategy="RNA-Seq",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "RNA-seq": 1
    }


def test_study_landscape_uses_explicit_amplicon_strategy():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="patient sample 01",
        library_strategy="AMPLICON",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "Amplicon sequencing": 1
    }


def test_study_landscape_uses_explicit_wgs_strategy():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="tumor sample 01",
        library_strategy="WGS",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "Whole-genome sequencing": 1
    }


def test_study_landscape_uses_explicit_atac_strategy():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="chromatin accessibility sample",
        library_strategy="ATAC-seq",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "ATAC-seq": 1
    }


def test_study_landscape_uses_explicit_small_rna_strategy():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="plasma sample",
        library_strategy="SMALL_RNA",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "Small RNA sequencing": 1
    }


def test_study_landscape_uses_explicit_ncrna_strategy():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="small RNA sample",
        library_strategy="ncRNA-Seq",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "ncRNA-Seq": 1
    }


def test_study_landscape_falls_back_to_title_when_strategy_is_missing():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="RNA-seq of M. tuberculosis H37Rv: kanamycin",
        library_strategy="",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "RNA-seq": 1
    }


def test_study_landscape_keeps_unknown_strategy_unclassified():
    record = StudyExperiment(
        sample_accession="SRS_TEST",
        biosample_accession="SAMN_TEST",
        experiment_accession="SRX_TEST",
        experiment_title="patient sample without assay description",
        library_strategy="UNKNOWN_WORKFLOW",
    )

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts == {
        "Unclassified": 1
    }

    assert landscape.warnings


def test_study_landscape_classifies_hic_strategy():
    record = make_study_experiment("HCC1395BL HiC")
    record.library_strategy = "Hi-C"

    landscape = generate_study_experimental_landscape([record])

    assert landscape.assay_family_counts["Hi-C"] == 1
    assert landscape.observed_assay_families == ["Hi-C"]
    assert landscape.warnings == []
