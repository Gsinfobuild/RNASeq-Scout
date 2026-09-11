# RNASeq Scout Independent Benchmark Protocol v1.1

## 1. Purpose

This protocol defines the independent benchmark for evaluating RNASeq Scout, an RNA-seq experiment intelligence engine.

The benchmark evaluates whether Scout can make defensible, evidence-based assessments of publicly available sequencing metadata.

The benchmark specifically evaluates:

1. sequencing modality;
2. RNA-seq compatibility;
3. experimental context;
4. treatment assignment;
5. control information;
6. time-point information;
7. replicate information;
8. study heterogeneity;
9. dataset suitability for RNA-seq analysis;
10. reanalysis readiness;
11. evidence and uncertainty classification.

The benchmark does not evaluate whether Scout can reconstruct experimental truth beyond the information available to its production workflow.

---

## 2. Benchmark design

The benchmark contains 50 independent evaluation units:

- 35 SRX experiment-level units;
- 5 SRR run-level units;
- 10 SRP study-level units.

The existing 13 development/regression cases are excluded from the headline independent evaluation.

They remain available for software quality assurance and regression testing.

---

## 3. Benchmark units

### 3.1 Experiment-level units

Thirty-five SRX accessions will be evaluated individually.

The experiment-level benchmark will include diverse sequencing modalities and metadata conditions.

Primary modality strata will include approximately:

- conventional RNA-seq;
- specialized RNA sequencing;
- non-RNA sequencing;
- mixed/multiomic or potentially misleading experiments;
- unknown or uncertain modality.

The exact number within each stratum may vary slightly when necessary to preserve scientific diversity.

### 3.2 Orthogonal experiment attributes

Design characteristics are treated as orthogonal attributes rather than mutually exclusive primary strata.

The benchmark will deliberately include experiments with:

- explicit treatment information;
- explicit control information;
- explicit biological replicate information;
- incomplete design information;
- ambiguous design information;
- contextual terms that could be incorrectly interpreted as treatment;
- generic replicate labels;
- missing design information.

An experiment may belong to more than one of these attribute categories.

This prevents double-counting or artificial exclusivity between modality and experimental-design characteristics.

### 3.3 Run-level units

Five SRR accessions will evaluate:

- sequencing-run availability;
- run-level metadata completeness;
- sequencing quantity evidence;
- RNA-seq compatibility;
- suitability implications;
- reanalysis-readiness implications.

Run-level cases should provide information that is not merely a duplicate of an SRX benchmark case.

### 3.4 Study-level units

Ten SRP accessions will evaluate study-level interpretation.

The study benchmark will include approximately:

- 3 homogeneous RNA-seq studies;
- 3 heterogeneous RNA/sRNA studies;
- 2 mixed RNA/non-RNA studies;
- 2 clearly non-RNA heterogeneous studies.

The study-level benchmark will focus on:

- experiment composition;
- sample composition;
- BioSample composition;
- run composition;
- assay-family classification;
- experimental contexts;
- study heterogeneity.

A heterogeneous study will not be reduced to its dominant assay family.

---

## 4. Candidate selection principles

Candidate selection will occur after this protocol has been frozen.

Candidates will be selected to maximize diversity in:

- sequencing modality;
- organism;
- experimental system;
- study size;
- metadata completeness;
- experimental-design complexity;
- assay heterogeneity;
- availability of linked publications;
- availability of supplementary experimental information.

The benchmark will deliberately include difficult cases.

The benchmark will contain both RNA-compatible and non-RNA sequencing experiments.

Cases will not be selected because Scout is expected to perform well on them.

Development and independent evaluation cases will remain separate.

Independent benchmark candidates must not be iteratively optimized using Scout predictions.

---

## 5. Evidence hierarchy

Ground truth will be established using two evidence levels.

### Repository evidence

Repository evidence includes information available from:

- NCBI SRA;
- BioProject;
- BioSample;
- linked repository metadata;
- other metadata directly accessible to Scout's production workflow.

### Experimental evidence

Experimental evidence includes information available from:

- the primary publication;
- Materials and Methods;
- figure legends;
- supplementary methods;
- supplementary tables;
- other primary experimental documentation.

Evidence sources and identifiers will be recorded for every annotated field where applicable.

Conflicting evidence will be documented rather than silently reconciled.

---

## 6. Repository-establishable truth versus experimental truth

Two distinct concepts will be maintained.

### Experimental truth

Experimental truth describes what the underlying experiment actually did, based on the strongest available experimental evidence.

### Repository-establishable truth

Repository-establishable truth describes what can be established from the public metadata available to Scout's production workflow.

These concepts must not be conflated.

For example, a publication may establish biological replication even when the repository metadata supplied to Scout does not.

Scout will not be penalized for failing to recover information that is unavailable to its production evidence sources.

---

## 7. Scout information boundary

For the independent benchmark, Scout will be executed using its frozen production workflow.

The Scout prediction stage will receive only the benchmark accession and the normal information sources available to the production implementation.

Publication text, supplementary material, expert annotations, and benchmark ground truth will not be supplied to Scout during prediction.

Experimental evidence from publications and supplementary material will be used independently to establish benchmark truth after the Scout prediction has been generated.

This separation prevents information leakage between prediction and evaluation.

---

## 8. Ground-truth fields

The benchmark will annotate the following dimensions:

- modality;
- RNA-seq compatibility;
- experimental context;
- treatment;
- control;
- time point;
- replicate;
- study heterogeneity;
- suitability;
- reanalysis readiness.

Each field will include:

- experimental truth;
- repository evidence;
- evidence state;
- Scout result;
- expert result;
- evidence source;
- evidence identifier;
- notes.

---

## 9. Evidence states

Four evidence states will be used.

### OBSERVED

The target information is directly documented by the available evidence.

Example:

A metadata record explicitly states `RNA-Seq`.

### INFERRED

The target information is strongly supported by available evidence but is not directly documented in the target field.

Inference must be justified by the evidence.

### NOT ESTABLISHED

Relevant evidence exists or was examined, but it is insufficient to establish the target claim.

Example:

A title states `detergent stress`, but there is no explicit treatment relationship.

The experimental context may be established, while formal treatment assignment remains NOT ESTABLISHED.

Another example:

A sample is labelled `replicate C`, but the available evidence does not establish whether the replicate is biological or technical.

### MISSING

The relevant information element is explicitly absent, unavailable, or not provided by the evidence source being evaluated.

Example:

No control annotation is present in the relevant repository metadata or experimental documentation.

### Operational distinction

`NOT ESTABLISHED` means that evidence was available or examined but does not establish the requested claim.

`MISSING` means that the relevant information itself is absent or unavailable from the evidence source being evaluated.

These states must not be collapsed during annotation or evaluation.

---

## 10. Treatment annotation rule

Treatment will be considered established only when an explicit treatment relationship is documented.

Examples include:

- treated with X;
- treatment with X;
- exposed to X;
- exposure to X;
- received X;
- X-treated cells or samples;
- treatment group.

Contextual terms alone do not establish treatment assignment.

Examples include:

- stress;
- starvation;
- hypoxia;
- iron stress;
- detergent stress;
- infection;
- antibiotic exposure.

For example:

`RNA-seq of M. tuberculosis H37Rv: detergent stress`

may establish experimental context but does not, by itself, establish a formal treatment assignment.

Keyword presence must not be treated as equivalent to treatment assignment.

---

## 11. Control annotation rule

Control status will be established only from explicit evidence.

Examples include:

- control;
- untreated;
- vehicle control;
- mock control;
- mock-treated;
- control group.

Treatment, condition, stress, or experimental context will not be used to infer the existence of a control.

---

## 12. Replicate annotation rule

Replicate information will be classified as:

- biological replicate;
- technical replicate;
- generic replicate;
- replicate status not established;
- replicate information missing.

Repeated runs must not automatically be interpreted as biological replicates.

A generic label such as `replicate C` establishes the presence of a replicate label but does not establish its biological or technical nature unless independent evidence supports that distinction.

---

## 13. Study-level annotation

For study-level units, the benchmark will record:

- experiment count;
- sample count;
- BioSample count;
- run count;
- assay-family composition;
- experimental contexts;
- study heterogeneity.

Heterogeneous study composition will not be reduced to the most frequent assay.

---

## 14. Field evaluability

Not every benchmark field will necessarily be evaluable for every unit.

If a field cannot be evaluated reliably from the available evidence, this limitation will be recorded explicitly.

Non-evaluable fields will not be converted into arbitrary positive or negative labels.

Field-specific performance calculations will report the relevant denominator.

---

## 15. Error taxonomy

Disagreements will be classified using the following taxonomy.

### E1 — Incorrect observation

Scout reports information that is directly contradicted by available evidence.

### E2 — Unsupported inference

Scout makes an inference that is not sufficiently supported by the available evidence.

### E3 — Missed evidence

Relevant evidence available to Scout is not detected or incorporated.

### E4 — Incorrect classification

Scout assigns an incorrect modality or workflow classification.

### E5 — Overgeneralization

Information from one level or component is incorrectly propagated to another level.

### E6 — Genuine ambiguity

The available evidence does not permit a confident distinction.

Genuine ambiguity will not automatically be counted as a Scout error.

---

## 16. Primary evaluation endpoints

The independent benchmark will evaluate the following primary endpoints.

### 16.1 Modality classification

The following will be reported:

- accuracy;
- micro-averaged precision;
- micro-averaged recall;
- micro-averaged F1;
- macro-averaged precision;
- macro-averaged recall;
- macro-averaged F1;
- per-class precision;
- per-class recall;
- per-class F1;
- confusion matrix.

### 16.2 Evidence-state agreement

Agreement between Scout and benchmark annotation will be assessed for:

- OBSERVED;
- INFERRED;
- NOT ESTABLISHED;
- MISSING.

### 16.3 Unsupported inference rate

Unsupported inference rate will be defined as:

`unsupported Scout claims / all Scout inferred claims`

The numerator and denominator will be reported explicitly.

This is a primary endpoint because evidence-aware restraint is a central property of RNASeq Scout.

### 16.4 Experimental-design agreement

Field-level agreement will be assessed for:

- condition/context;
- treatment;
- control;
- time point;
- replicate information.

### 16.5 Suitability agreement

Agreement will be assessed between Scout's suitability assessment and the independently established benchmark assessment.

### 16.6 Reanalysis-readiness agreement

Agreement will be assessed between Scout's readiness assessment and the independently established evidence-based assessment.

### 16.7 Study heterogeneity detection

Agreement will be assessed between Scout and independent annotation for heterogeneous study composition.

---

## 17. Uncertainty reporting

Where appropriate, benchmark performance estimates will be accompanied by 95% confidence intervals.

Confidence intervals will be calculated using methods appropriate for categorical proportions and classification metrics.

The limited size of the benchmark will be explicitly considered when interpreting small differences between metrics or benchmark categories.

No performance difference will be described as meaningful solely because of a numerical difference without considering uncertainty and sample size.

---

## 18. Secondary evaluation

Secondary measures include:

- inspection success rate;
- retrieval failure rate;
- handling of incomplete metadata;
- runtime;
- reproducibility;
- failure categories.

---

## 19. Ground-truth annotation and adjudication

Ground-truth annotation will be performed independently from Scout predictions wherever practical.

At least two independent reviewers will annotate benchmark truth for the key evaluation dimensions.

Disagreements will be resolved by discussion and, where necessary, adjudication by a third reviewer or predefined consensus procedure.

The final consensus annotation will be locked before benchmark comparison.

Evidence supporting disputed fields will be retained in the benchmark evidence records.

---

## 20. Benchmark locking

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

---

## 21. Development and independent evaluation

The existing 13 development/regression cases are used for software quality assurance.

The new 50-unit benchmark is the independent evaluation set.

Headline performance claims will be based on the independent evaluation set and will not combine development and test cases.

---

## 22. Reproducibility

The benchmark will preserve:

- accession registry;
- benchmark protocol;
- ground-truth annotations;
- evidence identifiers;
- Scout software version;
- benchmark scripts;
- generated predictions;
- evaluation results.

The exact software version used for the independent benchmark must be recorded explicitly.

The benchmark execution environment and relevant dependency versions should also be recorded where practical.

---

## 23. Scientific interpretation

The benchmark evaluates whether RNASeq Scout makes defensible evidence-based assessments from available public metadata.

A disagreement does not automatically indicate software failure.

Each disagreement will be classified according to the error taxonomy and reviewed for:

- metadata limitation;
- genuine ambiguity;
- unsupported inference;
- implementation error;
- incorrect classification;
- overgeneralization.

No benchmark result will be interpreted as demonstrating that Scout reconstructs experimental truth beyond the evidence available to it.

The principal scientific claim will therefore concern evidence-aware interpretation of sequencing experiments rather than unrestricted reconstruction of experimental design.

---

## 24. Protocol status

This document constitutes Benchmark Protocol v1.1.

Once reviewed and approved, the protocol will be frozen before independent candidate selection.

Subsequent changes will require a documented protocol amendment.
