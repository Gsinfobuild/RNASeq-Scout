# RNASeq Scout Independent Benchmark Protocol v1.0

## 1. Objective

The independent benchmark evaluates whether RNASeq Scout can reliably assess publicly available sequencing accessions with respect to:

1. sequencing modality;
2. RNA-seq compatibility;
3. experimental context;
4. treatment assignment;
5. control information;
6. time-point information;
7. replicate information;
8. study-level heterogeneity;
9. dataset suitability for RNA-seq analysis;
10. reanalysis readiness; and
11. evidence/uncertainty classification.

The benchmark evaluates evidence-aware interpretation. It does not require reconstruction of experimental information that is absent from the evidence available to Scout.

## 2. Benchmark size and units

The benchmark will contain 50 independent units:

- 35 experiment-level units (SRX);
- 5 run-level units (SRR);
- 10 study-level units (SRP).

The 13 cases previously used during software development remain development/regression cases and are not included in headline independent-test performance estimates.

## 3. Experiment-level strata

The 35 experiment-level units will approximately comprise:

- 7 conventional bulk RNA-seq;
- 5 specialized RNA sequencing;
- 5 experiments with explicit design information;
- 5 experiments with incomplete or ambiguous design information;
- 8 non-RNA sequencing experiments;
- 3 mixed, multiomic, or potentially misleading cases;
- 2 unknown or uncertain modality cases.

The final allocation may differ by one case where necessary to obtain scientifically appropriate examples, but the benchmark must retain representation across these categories.

## 4. Run-level strata

Five SRR units will evaluate:

- sequencing-run availability;
- run metadata completeness;
- read/run quantity evidence;
- RNA-seq compatibility;
- implications for suitability and reanalysis readiness.

Run-level units should not simply duplicate experiment-level benchmark cases.

## 5. Study-level strata

Ten SRP units will approximately comprise:

- 3 homogeneous RNA-seq studies;
- 3 heterogeneous RNA/sRNA studies;
- 2 mixed RNA/non-RNA studies;
- 2 clearly non-RNA heterogeneous studies.

Study-level evaluation will assess assay composition and heterogeneity rather than reducing each study to a single experiment.

## 6. Case-selection principles

Benchmark selection will occur only after this protocol is frozen.

Selection must:

- provide diversity of assay types, organisms, experimental designs, and metadata completeness;
- include difficult and potentially failure-inducing cases;
- include both RNA-seq-compatible and non-RNA cases;
- avoid selecting cases solely because Scout performs well on them;
- avoid selecting cases solely because Scout produces an interesting output;
- maintain separation between development cases and the independent evaluation set.

The independent benchmark must not be iteratively optimized using Scout results.

## 7. Evidence hierarchy

Ground-truth annotation may use:

### Repository evidence

- SRA;
- BioProject;
- BioSample;
- linked repository metadata where relevant.

### Experimental evidence

- primary publication;
- methods sections;
- figure legends;
- supplementary methods;
- supplementary tables.

For each annotation, the evidence source and identifier must be recorded.

Conflicts between repository and publication evidence must be documented and must not be silently reconciled.

## 8. Repository evidence versus experimental truth

Repository evidence and experimental truth are separate annotation dimensions.

For example, repository metadata may fail to establish biological replication while the publication explicitly reports biological replicates.

Scout must not be penalized for failing to recover information that was unavailable in the metadata supplied to the production pipeline.

Field-level evaluation will therefore consider the evidence actually available to Scout.

## 9. Ground-truth fields

The benchmark will annotate, where evaluable:

- modality;
- RNA-seq compatibility;
- experimental context;
- treatment;
- control;
- time point;
- replicate structure;
- study heterogeneity;
- dataset suitability;
- reanalysis readiness.

Each field will include:

- truth value;
- evidence state;
- evidence source;
- evidence identifier;
- annotation notes.

## 10. Evidence states

The benchmark uses four evidence states:

### OBSERVED

The information is directly documented in the relevant evidence.

### INFERRED

The information is strongly supported by available evidence but is not directly documented in the target field.

### NOT ESTABLISHED

The available evidence does not establish the information.

### MISSING

An expected information element is absent from the relevant evidence.

Evidence states must not be converted into binary positive/negative labels without justification.

## 11. Treatment annotation rule

Treatment is established only when an explicit treatment relationship is documented.

Examples include:

- treated with X;
- treatment with X;
- exposed to X;
- exposure to X;
- received X;
- X-treated cells or samples;
- treatment group.

Contextual terms such as:

- stress;
- starvation;
- hypoxia;
- iron;
- detergent;
- infection;
- antibiotic;
- drug

do not by themselves establish a formal treatment assignment.

For example, "detergent stress" may establish an experimental context without establishing detergent as a treatment.

## 12. Control annotation rule

A control is established only when explicit control-related evidence is present.

Examples include:

- control;
- untreated;
- vehicle control;
- mock control;
- mock-treated;
- control group.

The existence of a treatment or experimental condition does not imply a control.

## 13. Replicate annotation rule

The benchmark distinguishes:

- biological replicate;
- technical replicate;
- generic replicate;
- replicate structure not established.

Multiple sequencing runs must not be interpreted as biological replicates unless independent evidence establishes their biological relationship.

## 14. Study-level annotation

Study-level units will record, where available:

- number of experiments;
- number of samples;
- number of BioSamples;
- number of runs;
- assay families;
- experimental contexts;
- study heterogeneity.

A heterogeneous study must not be reduced to a single assay category solely because one assay family is dominant.

## 15. Field evaluability

Not every field is expected to be evaluable for every benchmark unit.

If the relevant evidence does not establish a field, the annotation must preserve that uncertainty rather than forcing a negative value.

Such fields will be excluded from field-specific accuracy calculations where appropriate.

## 16. Scout error taxonomy

Disagreements between Scout and benchmark truth will be classified as:

### E1 — Incorrect observation

Scout reports information as documented when it is not documented.

### E2 — Unsupported inference

Scout infers information that is not supported by the evidence available to Scout.

### E3 — Missed evidence

Relevant evidence available to Scout is not detected.

### E4 — Incorrect classification

Scout assigns an incorrect modality or workflow classification.

### E5 — Overgeneralization

Information from one level or component is incorrectly propagated to another level.

### E6 — Genuine ambiguity

The available evidence does not permit a confident distinction.

Genuine ambiguity will not automatically be counted as a Scout error.

## 17. Primary evaluation endpoints

The independent benchmark will evaluate:

### Modality classification

- accuracy;
- precision;
- recall;
- F1 score.

### Evidence-state agreement

Agreement between Scout and benchmark annotation for:

- OBSERVED;
- INFERRED;
- NOT ESTABLISHED;
- MISSING.

### Unsupported inference rate

Unsupported Scout claims divided by all Scout inferred claims.

### Experimental-design agreement

Field-level agreement for:

- condition/context;
- treatment;
- control;
- time point;
- replicate information.

### Suitability agreement

Agreement between Scout's suitability assessment and independently established benchmark assessment.

### Reanalysis-readiness agreement

Agreement between Scout's readiness assessment and independently established evidence-based assessment.

### Study heterogeneity detection

Agreement between Scout and independent annotation for heterogeneous study composition.

## 18. Secondary evaluation

Secondary measures include:

- inspection success rate;
- retrieval failure rate;
- handling of incomplete metadata;
- runtime;
- reproducibility;
- failure categories.

## 19. Benchmark locking

The benchmark protocol is frozen before candidate selection.

After the 50 benchmark units are selected:

1. the accession registry is frozen;
2. independent ground-truth annotation is performed;
3. ground truth is locked;
4. Scout is run using the frozen software version;
5. Scout predictions are locked;
6. comparison and statistical evaluation are performed.

Benchmark rules must not be changed after Scout results are inspected.

If a methodological change becomes necessary, it must be documented as a protocol amendment and applied transparently.

## 20. Development and independent evaluation

The existing 13 development/regression cases are used for software quality assurance.

The new 50-unit benchmark is the independent evaluation set.

Headline performance claims will be based on the independent evaluation set and will not combine development and test cases.

## 21. Reproducibility

The benchmark will preserve:

- accession registry;
- benchmark protocol;
- ground-truth annotations;
- evidence identifiers;
- Scout software version;
- benchmark scripts;
- generated predictions;
- evaluation results.

The software version used for the independent benchmark must be recorded explicitly.

## 22. Scientific interpretation

The benchmark evaluates whether RNASeq Scout makes defensible evidence-based assessments from available public metadata.

A disagreement does not automatically indicate software failure. Each disagreement must be classified according to the error taxonomy and reviewed for metadata limitation, genuine ambiguity, unsupported inference, or implementation error.

No benchmark result will be interpreted as demonstrating that Scout reconstructs experimental truth beyond the evidence available to it.
