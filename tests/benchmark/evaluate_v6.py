"""Evaluate the six v6 targets from a frozen long-form truth TSV and Scout result TSV."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from evaluate_benchmark import DESIGN_FIELDS, OBJECTIVE_FIELDS, normalize_broad_modality, normalize_for_field

TARGETS = {"exact_modality": 100, "broad_modality": 100, "objective_metadata": 250,
           "experimental_design": 100, "suitability": 100, "rna_seq_compatibility": 100}
FIELDS = {"exact_modality": {"modality"}, "broad_modality": {"modality"},
          "objective_metadata": set(OBJECTIVE_FIELDS), "experimental_design": set(DESIGN_FIELDS),
          "suitability": {"suitability"}, "rna_seq_compatibility": {"rna_seq_compatible"}}

def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))

def canonical(metric, field, value):
    if metric == "broad_modality":
        label = normalize_broad_modality(value)
        if label in {"single-cell rna-seq", "single-nucleus rna-seq", "non-coding rna sequencing", "pirna sequencing", "small rna sequencing"}:
            return "specialized_rna"
        return label
    label = value.strip().casefold()
    if field == "suitability" and label in {"not suitable", "not suitable for rna-seq analysis"}:
        return "not suitable"
    if field == "replicate_status" and label.startswith("not applicable to rna-seq experimental-design assessment"):
        return "not_applicable"
    if field == "library_strategy":
        return value.strip().casefold().replace("-", "_")
    return normalize_for_field(field, value)

def evaluate(checks, results):
    counts = defaultdict(Counter)
    keys = set()
    panels = defaultdict(set)
    observed = {}
    for row in results:
        accession = row["accession"].strip()
        if not accession or accession in observed:
            raise ValueError(f"Missing or duplicate observation accession: {accession}")
        observed[accession] = row
    details = []
    for check in checks:
        acc, metric, field = (check[k].strip() for k in ("accession", "metric", "field"))
        key = (acc, metric, field)
        if not acc or key in keys or field not in FIELDS.get(metric, set()):
            raise ValueError(f"Invalid or repeated benchmark check: {key}")
        keys.add(key)
        panels[metric].add(acc)
        expected = check["expected"].strip()
        origin = check["reference_type"].strip()
        result = observed.get(acc, {})
        if result.get("success", "").lower() == "true" and field not in result:
            raise ValueError(f"Missing observation column {field} for {acc}")
        actual = result.get(field, "")
        if field == "rna_seq_compatible" and not actual and result.get("compatibility_status") == "Uncertain":
            actual = "uncertain"
        if not expected:
            state = "pending"
        else:
            if origin not in {"reviewed", "repository", "strategy_baseline"} or not check["evidence"].strip():
                raise ValueError(f"Missing reference provenance for {key}")
            if result.get("success", "").lower() != "true":
                state = "failed_observation"
            elif (expected == "[absent]" and not actual) or canonical(metric, field, expected) == canonical(metric, field, actual):
                state = "match"
                if origin == "strategy_baseline":
                    counts[metric]["provisional_matches"] += 1
            else:
                state = "mismatch"
        counts[metric][state] += 1
        details.append(dict(**check, observed=actual, outcome=state))
    panel = panels["exact_modality"]
    if len(panel) != 100 or set(observed)-panel:
        raise ValueError("Expected a 100-accession panel and no unplanned observations")
    for metric, target in TARGETS.items():
        if sum(r["metric"] == metric for r in checks) != target:
            raise ValueError(f"Expected {target} opportunities for {metric}")
        if metric == "objective_metadata":
            if not panels[metric] <= panel:
                raise ValueError("Objective checks contain an accession outside the panel")
        elif panels[metric] != panel:
            raise ValueError(f"Inconsistent accession panel for {metric}")
    summary = {}
    for metric, target in TARGETS.items():
        count = counts[metric]
        summary[metric] = dict(target=target, matched=count["match"], pending=count["pending"],
                               mismatch=count["mismatch"], failed_observation=count["failed_observation"],
                               strategy_only_matches=count["provisional_matches"],
                               target_verified=count["match"]==target and not count["provisional_matches"])
    return summary, details

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("truth",type=Path)
    parser.add_argument("results",type=Path)
    parser.add_argument("--details",type=Path)
    args = parser.parse_args()
    summary, details = evaluate(read(args.truth),read(args.results))
    if args.details:
        with args.details.open("w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=details[0],delimiter="\t")
            writer.writeheader()
            writer.writerows(details)
    print(json.dumps(summary,indent=2))
    return 0 if all(row["target_verified"] for row in summary.values()) else 1

if __name__=="__main__":
    raise SystemExit(main())


