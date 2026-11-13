# Five-field experimental design benchmark

The target is 50 agreements per field on the same 50 distinct public experiments. These are real records taken from the previous 100-experiment development cohort. Select the first 50 accessions sorted by the SHA-256 digest of the UTF-8 string five-design-fields-v1|ACCESSION. Selection uses only accession identifiers. The reference contains 250 AI-assisted judgments, with the 50 overlapping judgments retained from the previous review. Other judgments were assigned using submitted records before measuring the new panel scores. Prior exposure and use during development limit generalization. This is not a human or held-out benchmark.

Run from the source root with the root on PYTHONPATH:

    python tests/benchmark/run_five_field_panel.py tests/benchmark/v6/v6_snapshot.zip tests/benchmark/five_fields/source.tsv tests/benchmark/five_fields/reference.tsv results.tsv

The driver replays frozen experiment summaries, frozen publication enrichment and SRA-submitted sample attributes serialized into BioSample XML for the existing enrichment parser. It exercises inspect(enrich_biosample=True). The replay does not measure live BioSample retrieval or guarantee the live BioSample has identical fields. A populated sample-scoped design output takes precedence over the experiment-level output for this accession-level review. The same rule was used before and after. Age and developmental stage are reported separately in the UI and do not automatically fill a sampling interval. The reference sometimes uses age or stage as the time endpoint. An exposure duration is evidence about time under treatment and does not in itself establish time of collection.

The semantic comparison uses the existing evaluate_v6 field canonicalizer, including explicit absent assignments. This is label agreement; differences can reflect evidence scope, wording, or an incorrect extraction. Control and treatment results include agreements on unassigned values. Reaching 50/50 on all five fields is still an open target. Earlier scores out of 20 per field came from different assignments under default enrichment. Use the same-panel Before and After columns in the accompanying TSV for revision comparisons.

The follow-up implementation reproduces after_followup.tsv: condition 29/50, control 50/50, treatment 44/50, time point 35/50 and replicate status 48/50 (206/250). The before.tsv and after.tsv files preserve the earlier 162/250 and 184/250 runs, respectively.
