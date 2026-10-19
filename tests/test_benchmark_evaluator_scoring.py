import importlib.util
from pathlib import Path


EVALUATOR_PATH = (
    Path(__file__).parent
    / "benchmark"
    / "evaluate_benchmark.py"
)

spec = importlib.util.spec_from_file_location(
    "benchmark_evaluator",
    EVALUATOR_PATH,
)
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


def test_accuracy_summary_excludes_unscored_and_missing_observations():
    correct, scored = evaluator.accuracy_summary(
        [
            "AGREEMENT",
            "DISAGREEMENT",
            "NOT SCORED",
            "MISSING OBSERVATION",
        ]
    )

    assert correct == 1
    assert scored == 2


def test_accuracy_summary_counts_only_actual_scored_predictions():
    correct, scored = evaluator.accuracy_summary(
        [
            "AGREEMENT",
            "AGREEMENT",
            "NOT SCORED",
        ]
    )

    assert correct == 2
    assert scored == 2


def test_failed_observation_is_not_counted_as_a_scored_prediction():
    comparisons = [
        "AGREEMENT",
        "FAILED OBSERVATION",
        "DISAGREEMENT",
    ]

    correct, scored = evaluator.accuracy_summary(comparisons)

    assert correct == 1
    assert scored == 2


def test_missing_and_failed_observations_are_excluded_from_denominator():
    comparisons = [
        "AGREEMENT",
        "MISSING OBSERVATION",
        "FAILED OBSERVATION",
        "NOT SCORED",
    ]

    correct, scored = evaluator.accuracy_summary(comparisons)

    assert correct == 1
    assert scored == 1


def test_field_group_excludes_failed_observation(capsys):
    truth_rows = {
        "SRR_FAILED": {"modality": "RNA-seq"},
        "SRR_OK": {"modality": "RNA-seq"},
    }
    observed_rows = {
        "SRR_FAILED": {
            "success": "False",
            "modality": "WGS",
        },
        "SRR_OK": {
            "success": "True",
            "modality": "RNA-seq",
        },
    }

    evaluator.print_field_group(
        "Test",
        truth_rows,
        observed_rows,
        ["modality"],
    )

    output = capsys.readouterr().out
    assert "modality: 1/1 agreement" in output
    assert "SRR_FAILED" not in output


def test_replicate_status_matches_not_established_explanatory_wording():
    assert evaluator.compare(
        'replicate_status', 'Not established', 'One sequencing run is represented by the inspected accession; biological replicate status is not established by this information alone.'
    ) == 'AGREEMENT'


def test_replicate_status_matches_partial_evidence_wording():
    assert evaluator.compare(
        'replicate_status', 'Partial evidence: biological replicate 2', "Biological replicate annotation 'biological replicate 2' is explicitly reported in the BioSample metadata. This provides partial replicate evidence; complete sample-level replicate structure is not established from the inspected accession alone."
    ) == 'AGREEMENT'


def test_replicate_status_keeps_not_applicable_distinct():
    assert evaluator.compare(
        'replicate_status', 'Not applicable', 'Biological replicate status is not established.'
    ) == 'DISAGREEMENT'
