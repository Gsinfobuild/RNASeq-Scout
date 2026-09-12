# RNASeq Scout Benchmark v1.0
## Independent Reviewer Annotation Instructions v1.0

### Purpose

You are independently annotating experimental truth for the RNASeq Scout
Benchmark v1.0.

The benchmark contains five pilot units selected before experimental-truth
annotation.

Your task is to determine what is actually established by the supplied
scientific evidence.

Do not infer information that the evidence does not establish.

---

## 1. Independence requirement

Reviewer 1 and Reviewer 2 must work independently.

Before submitting your annotation, do NOT inspect:

- the other reviewer's annotation
- adjudicated ground truth
- Scout's output
- internal Scout evidence registers containing interpreted conclusions

Your annotation must be based only on the supplied source packet and the
benchmark annotation guidelines.

---

## 2. Evidence hierarchy

Use evidence in this order:

1. Primary research publication
2. Publication supplementary material
3. Study-specific experimental metadata
4. SRA / BioProject / BioSample repository records
5. Other authoritative repository-linked records

Repository evidence and experimental truth must remain distinguishable.

Repository metadata may establish technical facts such as:

- library strategy
- library source
- library selection
- sequencing layout
- platform
- organism
- run availability
- sample/BioSample relationship

Experimental truth concerns experimentally meaningful attributes such as:

- biological condition
- genotype
- treatment
- control
- time point
- biological replicate
- technical replicate
- experimental group structure
- batch information

---

## 3. Evidence states

Use exactly one evidence state for each applicable annotation.

### OBSERVED

The source explicitly establishes the claim.

Example:

A source explicitly states:
"biological replicate 3"

This can support an OBSERVED replicate annotation.

### INFERRED

The claim is strongly supported by contextual evidence but is not stated
directly.

Use this state sparingly.

Do not use INFERRED merely because a claim seems biologically obvious.

### NOT_ESTABLISHED

Relevant evidence was examined, but it is insufficient to establish the
claim.

Examples:

- a title contains "stress" but does not establish treatment assignment
- multiple samples exist but biological replication is unclear
- wild type and mutant samples are present but their control relationship
  is not explicitly established

### MISSING

The relevant information is absent or unavailable from the applicable
source.

Use MISSING when the source does not provide the information needed for the
annotation.

Do not use NOT_ESTABLISHED and MISSING interchangeably.

---

## 4. Unsupported inference

Actively look for cases where an apparently obvious conclusion is not
actually established.

Do NOT infer:

- treatment from the mere presence of a stress term
- control from the presence of a wild-type sample
- biological replication from multiple runs
- technical replication from repeated sequencing information
- experimental groups from sample names alone
- a design formula without explicit support
- accession-to-sample mappings from similarly named samples

Unsupported inference is a primary benchmark error category.

---

## 5. Field-specific instructions

### modality

Record the sequencing modality established for the benchmark unit.

Use the strongest explicit source evidence.

Examples:

- RNA-Seq
- miRNA-Seq
- ncRNA-Seq
- WGS
- WXS
- ATAC-seq
- ChIP-Seq
- Hi-C
- AMPLICON

### rna_seq_compatibility

Determine whether the unit is suitable for conventional RNA-seq analysis.

Do not treat all RNA-derived sequencing workflows as conventional bulk
RNA-seq.

Specialized workflows such as miRNA-seq may be RNA-derived but still require
a specialized analysis workflow.

### condition

Record the biological condition only when supported by the evidence.

Do not convert a contextual keyword into a formal treatment assignment.

### control

Record a control only when the source establishes the control relationship.

The presence of wild-type, untreated, mock, or reference material does not
automatically establish a control group.

### treatment

Record a treatment only when the source explicitly establishes a treatment
relationship.

Examples of explicit evidence include:

- treated with X
- treatment with X
- exposed to X
- exposure to X
- X-treated
- treatment group

A title containing only "stress", "exposure", or another contextual term
does not automatically establish treatment assignment.

### time_point

Record a time point only when explicitly supported.

Examples:

- 6 h
- 24 hours
- time point 2
- sampling at day 7

Do not infer time points from filenames or accession numbering.

### replicate_information

Distinguish carefully between:

- biological replicate
- technical replicate
- generic replicate
- no established replication

Multiple sequencing runs do not automatically establish biological
replication.

### experimental_design

Record the design only to the level actually supported.

Examples:

- two-group comparison
- treatment versus control
- mutant versus wild type
- multifactorial design

Do not construct a statistical design formula unless the source explicitly
supports it.

### batch_information

Record sequencing, library preparation, experimental, or processing batch
information only when explicitly documented.

If the relevant source does not provide batch information, use MISSING.

### multimodality

Record whether the study contains multiple assay families when that is
relevant to the benchmark unit.

Do not assume that a representative experiment describes the complete
design of a study-level unit.

---

## 6. Evidence traceability

Every nontrivial experimental-truth annotation should contain:

- evidence source
- evidence identifier
- evidence location where possible
- concise reviewer note

Examples:

- DOI
- PMID
- SRA accession
- BioProject accession
- BioSample accession
- Methods section
- Results section
- Figure number
- Supplementary Table number

---

## 7. Conflicting evidence

If repository and publication evidence disagree:

1. Record the repository observation.
2. Record the publication observation.
3. Describe the discrepancy.
4. Use the strongest evidence for experimental truth.
5. Do not silently overwrite the repository observation.

---

## 8. Confidence

Use annotation confidence to indicate how certain you are that the source
supports your annotation.

Recommended values:

- HIGH
- MEDIUM
- LOW

Confidence should reflect the evidence, not how biologically plausible the
answer appears.

---

## 9. Reviewer notes

Reviewer notes should briefly explain the evidence supporting the
annotation.

Good:

"BioSample description explicitly states 'biological replica 3'."

Good:

"Study describes mutant and wild-type material, but the source does not
explicitly establish this accession as the control."

Avoid:

"I think this is probably the control."

---

## 10. Completion rule

Do not leave an applicable field blank.

Use the appropriate evidence state:

- OBSERVED
- INFERRED
- NOT_ESTABLISHED
- MISSING

If the field genuinely does not apply to the unit, explain this in the
reviewer notes.

---

## 11. Final independence check

Before submitting:

1. Confirm that you did not inspect the other reviewer's annotation.
2. Confirm that you did not inspect adjudicated ground truth.
3. Confirm that every nontrivial claim has an evidence trace.
4. Confirm that unsupported inference has not been used.
5. Confirm that NOT_ESTABLISHED and MISSING have been distinguished.
6. Confirm that the annotation reflects the source rather than Scout's
   prediction.

Only after both reviewers have completed their annotations will the two
annotations be compared and disagreements adjudicated.
