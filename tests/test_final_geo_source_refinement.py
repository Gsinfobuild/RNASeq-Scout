
from rnaseq_nav.models import StudyExperiment
from rnaseq_nav.intelligence.study_landscape import (
    generate_study_experimental_landscape,
)


def _record(sample_name="", experiment_title=""):
    return StudyExperiment(
        sample_accession="GSMTEST",
        biosample_accession="SAMNTEST",
        experiment_accession="SRXTEST",
        experiment_title=experiment_title,
        library_strategy="RNA-Seq",
        organism="Homo sapiens",
        sample_name=sample_name,
    )


def test_geo_context_uses_observed_record_labels():
    records = [
        _record(sample_name="DF1_0_07_Run_1"),
        _record(sample_name="DF1_0_07_Run_2"),
        _record(sample_name="MDCK_0_2_Run_1"),
        _record(sample_name="MDCK_0_6_Run_2"),
    ]

    landscape = generate_study_experimental_landscape(records)

    assert landscape.context_counts["DF1 cells"] == 2
    assert landscape.context_counts["MDCK cells"] == 2


def test_existing_generic_context_extraction_is_preserved():
    records = [
        _record(
            experiment_title="RNA-seq of M. tuberculosis H37Rv: kanamycin"
        )
    ]

    landscape = generate_study_experimental_landscape(records)

    assert landscape.context_counts["kanamycin"] == 1
