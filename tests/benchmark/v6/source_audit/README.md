# v6 source audit

The 100 experiments and 750 planned comparisons are the same ones published in v6. The only updated reference is the previously empty organism for ERX16536766. The source SRA summary provides taxon 10090 and common name house mouse. The matching ENA BioSample ERS29754726 independently exposes both Mus musculus and house mouse. The parser now preserves the reported common name when the scientific name is absent. The original v6 references and outputs remain available for comparison.

The frozen replay completed all 100 inspections. Of 250 objective comparisons, 248 match, including 150/150 direct organism, layout and library-strategy checks. The remaining two differences concern the modality and conventional RNA-seq compatibility of one cell-resolved experiment. The full SRA experiment records corroborate the recorded protocol evidence for DRX1156855 and DRX1144356 and the piRNA experiment title of SRX22201129. Evidence inspected after a prediction is a discrepancy audit, not a blinded benchmark.

review_evidence_100.tsv contains fresh SRA EFetch experiment titles, design descriptions, library protocols and submitted sample attributes for the existing panel. All 100 have sample attributes and 67 include a library construction protocol. An independent reviewer can fill the three blank reviewer columns. A sample annotation alone does not establish a study-wide group assignment or replicate structure. Human reviewers can use these records alongside the v6 blinded worksheet and linked publications. No human design or suitability judgments have been recorded by this audit.

To reproduce from the repository root on Linux, export PYTHONPATH="$PWD" and run:

    python tests/benchmark/run_v6_frozen.py tests/benchmark/v6/v6_snapshot.zip observations.tsv
    python tests/benchmark/evaluate_v6.py tests/benchmark/v6/source_audit/reference.tsv observations.tsv --details comparisons.tsv

An exit code of 1 indicates that the release targets are still open.
