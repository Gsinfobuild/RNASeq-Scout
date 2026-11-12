from pathlib import Path
import importlib.util
import sys

import pytest


@pytest.fixture
def scorer(monkeypatch):
    directory = Path(__file__).parent / "benchmark"
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location("v6_scorer_test_module", directory / "evaluate_v6.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_and_provisional_never_pass(scorer):
    checks = []
    observations = []
    for i in range(100):
        acc = str(i)
        result = dict(accession=acc, success="true")
        for metric, fields in scorer.FIELDS.items():
            if metric == "objective_metadata" and i >= 50:
                continue
            selected = sorted(fields) if metric == "objective_metadata" else [sorted(fields)[0]]
            for field in selected:
                result[field] = "test"
                checks.append(dict(accession=acc, metric=metric, field=field, expected="test",
                                   reference_type="reviewed", evidence="fixture"))
        observations.append(result)
    summary, _ = scorer.evaluate(checks, observations)
    assert all(m["target_verified"] for m in summary.values())
    checks[0]["reference_type"] = "strategy_baseline"
    summary, _ = scorer.evaluate(checks, observations[:-1])
    assert summary["exact_modality"]["failed_observation"] == 1
    assert summary["exact_modality"]["strategy_only_matches"] == 1
    assert not summary["exact_modality"]["target_verified"]
    with pytest.raises(ValueError, match="repeated benchmark"):
        scorer.evaluate(checks + [checks[0]], observations)
