# RNASeq Scout v6 benchmark

The six release targets are 100 exact-modality, 100 broad-modality, 250 objective metadata, 100 experimental-design, 100 suitability and 100 conventional RNA-seq compatibility agreements. A target passes only when every planned comparison agrees with a completed reference beyond a strategy-only baseline. Missing or failed inspections retain their place in the denominator. The October 34-accession v6 results are a separate historical series.

## Reproduce the 100-experiment panel

Run from the project root with the project's Python environment. On Linux, set PYTHONPATH to the repository root first.

    export PYTHONPATH="$PWD"
    python tests/benchmark/run_v6_frozen.py tests/benchmark/v6/v6_snapshot.zip v6_observations.tsv
    python tests/benchmark/evaluate_v6.py tests/benchmark/v6/v6_reference.tsv v6_observations.tsv --details v6_breakdown.tsv

The evaluator exits 1 while any target is unmet. The script reads no reference labels during inspection. It replays NCBI SRA summaries and archived publication-enrichment results, uses the default experiment-level inspection settings, and records a digest of the Python package in its observation TSV.

The 100 experiments were drawn from the earlier 200-experiment development panel, one per study and BioProject. Within each strategy, sort by SHA-256 of the UTF-8 string v6-100|ACCESSION. Sort the eight strategy names lexicographically and take 13 cases per stratum in the first four strata and 12 in the other four. Sort the resulting panel by the same hash. Earlier observations of these experiments informed the current code, so these figures describe development performance. Use independently sampled experiments for a held-out estimate.

## Comparisons and curation

All 100 experiments contribute one comparison each for exact modality, broad modality, experimental design, suitability and conventional RNA-seq compatibility. To preserve the five legacy objective field types, the first 50 ranked cases contribute modality, compatibility, strategy, layout and organism (250 comparisons). The design comparison cycles through condition, control, treatment, time point and replicate status, giving 20 of each. This tests one design field per case. It does not establish the complete design of 100 studies.

v6_reference.tsv contains SRA field references and provisional strategy lookup labels. The latter express only what can be inferred from the structured strategy. Exact and broad modality are scored separately. Specialized cell-resolved and small RNA subtypes map to the broad specialized RNA class; the exact score preserves distinctions such as piRNA versus miRNA. Suitability uses the legacy semantic equivalence for the two wordings of an unsuitable conventional RNA-seq experiment.

Give independent reviewers v6_review_blinded.tsv before providing Scout results. Review the indicated accession-level field and source records. Enter the expected value, record the supporting source and location in evidence, and set reference_type to reviewed for adjudicated labels. Use uncertain for an explicitly unresolved compatibility decision. Keep pending fields blank. Where a field was specifically assessed as absent, use the reserved label [absent] to expect an empty output value. Do not erase rows. Record review dates, reviewer identities and adjudication outside the prediction file. Copy reviewed values consistently to duplicated objective comparisons. Run the same scorer on the completed reference.

The strategy-only baseline does not evaluate manual time saved or scientific correctness of downstream design choices. Those claims need independent human review.
