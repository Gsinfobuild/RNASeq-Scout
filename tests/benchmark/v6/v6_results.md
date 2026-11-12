# RNASeq Scout v6 implementation and benchmark

The updated local inspection pipeline completed all 200 frozen-record tests. It now routes three case-study experiments to single-cell or single-nucleus workflows, flags a fourth experiment for conflicting RNA-Seq and amplicon evidence, and recognizes the piRNA assay identified in a fifth experiment title. The build also recognizes explicit numbered control titles and restricts protocol-derived sampling times to sampling statements. Each case and its changed outputs is in v6_changes_200.tsv.

## New 100-case development panel

| Metric | Result | Target |
|---|---:|---:|
| Exact modality | 97 agree with the strategy lookup | 100/100 |
| Broad modality | 98 agree with the strategy lookup | 100/100 |
| Objective metadata | 247 agree, 2 differ, 1 pending | 250/250 |
| Experimental design | 100 await independent reference labels | 100/100 |
| Suitability | 100 await independent reference labels | 100/100 |
| RNA-seq compatibility | 98 agree with the strategy lookup | 100/100 |

The exact modality differences are two cell-resolved experiments recorded under the broad RNA-Seq strategy (DRX1156855 and DRX1144356), and a piRNA experiment recorded under miRNA-Seq (SRX22201129). The two objective mismatches are the subtype and conventional compatibility for DRX1156855. Of 150 direct library-strategy, layout and organism comparisons, all 149 with a populated source reference agree. One organism value is missing. The other 100 objective comparisons use strategy-derived modality and compatibility labels. None of the six requested targets has been independently verified.

## Historical comparison

A fresh, live BioSample-enriched run completed all 34 legacy accessions. Under the original strict evaluator, design was 4/11, compared with 4/11 for v4 and 3/11 for v5. The existing semantic evaluator scores the same three runs at 4/11, 8/11 and 9/11, respectively. The archived October v6 also scored 9/11 under that evaluator. Different handling of the phrase for inapplicable replication accounts for the strict-versus-semantic difference. The remaining two semantic design discrepancies concern a treatment and time point in a BioSample where the reference expects a study-level result.

The new live run scored 29/34 exact modality, 34/34 broad modality, 160/165 objective metadata, 6/6 semantic suitability and 34/34 RNA-seq compatibility. All five exact-modality mismatches involve general specialized-RNA references paired with specific miRNA predictions. Interpret the small legacy and larger development panels separately.

## Verification

114 focused deterministic tests and 12 accession smoke-matrix tests passed. The latter include eight live accession cases. The 100-case results are based on a subset of the same 200 development records. They are not independent holdout data. The README gives the sampling rule, field allocation, reproducible inspection command and independent review workflow.
