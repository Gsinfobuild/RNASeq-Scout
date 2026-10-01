# Frozen Evaluation Panel

## Frozen software

- Commit: `ebca981`
- Repository HEAD when regenerated: `ebca9815ca5c196aab2f858e65684d9756e69ef5`
- Production implementation is not modified by this package.

## Panel

The panel contains 14 GEO accessions:

- 9 positive RNA-seq cases
- 4 non-RNA-seq negative controls
- 1 RNA-seq stress/performance case

The panel is intended to evaluate structured repository interpretation,
accession routing, RNA-seq compatibility, library-strategy interpretation,
study retrieval, and selected study-level evidence propagation.

## Ground-truth policy

Ground-truth fields are populated only when supported by:

1. a repository-derived structured record; or
2. a directly observed and previously validated implementation result.

Unsupported fields are intentionally left blank.

A blank field means **not established by the frozen evaluation evidence**.
It does not mean that the biological property is absent.

Experiment counts for timeout cases are not asserted because the frozen
benchmark did not complete those retrievals.

## Timeout policy

The benchmark used a per-study timeout of 120 seconds.

A timeout is recorded as a performance/scalability outcome. It is not
treated as evidence that the expected biological modality is incorrect.

## What this panel does not establish

This panel is not a universal ground truth for:

- research-question-specific suitability;
- biological interpretation;
- causal relationships;
- statistical validity;
- differential-expression correctness;
- downstream alignment or quantification quality;
- biological replicate validity.

Those properties require downstream analysis and/or explicit experimental
evidence.

## Preprint under audit

No candidate preprint DOCX was found in the repository.

The preprint audit is stored separately under `docs/`.
