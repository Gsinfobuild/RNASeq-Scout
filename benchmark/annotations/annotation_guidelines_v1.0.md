# RNASeq Scout Benchmark v1.0
## Experimental-Truth Annotation Guidelines v1.0

### 1. Purpose

These guidelines define the procedure for establishing experimental truth
for the frozen RNASeq Scout Benchmark v1.0.

The benchmark contains 50 fixed public sequencing units selected before
experimental-truth annotation.

Ground-truth annotation MUST NOT alter benchmark membership.

The purpose of annotation is to establish the experimentally supported
characteristics of each benchmark unit using independent scientific evidence.

---

## 2. Evidence hierarchy

Use evidence in the following order when establishing experimental truth:

1. Primary research publication describing the dataset
2. Publication supplementary material
3. Study-specific experimental metadata
4. SRA / BioProject / BioSample repository records
5. Other authoritative repository-linked records

Repository metadata alone MUST NOT be treated as experimental truth when
the publication provides more specific experimental information.

Every experimental-truth claim must retain an evidence source and identifier.

---

## 3. Separation of evidence layers

Two evidence layers must be recorded separately.

### Repository evidence

Information directly established by the public repository record.

Examples:

- accession
- library strategy
- library source
- library selection
- layout
- platform
- organism
- run availability
- sample / BioSample relationship

### Experimental truth

Information established by the publication or supplementary material.

Examples:

- biological condition
- treatment
- control
- time point
- biological replicate identity
- technical replicate identity
- experimental group structure
- factorial design
- batch information

Do not silently replace repository evidence with publication evidence.

Both layers should remain traceable.

---

## 4. Evidence states

Each annotation must use one of four evidence states.

### OBSERVED

The evidence explicitly establishes the claim.

Example:

The publication explicitly states that three biological replicates were
sequenced.

### INFERRED

The claim is strongly supported by evidence but is not explicitly stated.

Inference must be conservative and scientifically defensible.

The evidence supporting the inference must be recorded.

### NOT_ESTABLISHED

Relevant evidence was examined, but it is insufficient to establish the claim.

Example:

A title contains "replicate 2", but the available evidence does not establish
whether the replicate is biological or technical.

### MISSING

The relevant information is explicitly absent, unavailable, or not provided
by the available evidence source.

NOT_ESTABLISHED and MISSING MUST NOT be used interchangeably.

---

## 5. Modality annotation

Record the experimentally established sequencing modality.

Allowed benchmark modality labels:

- RNA-Seq
- WGS
- WXS
- ATAC-seq
- ChIP-Seq
- Hi-C
- ncRNA-Seq
- miRNA-Seq
- AMPLICON

If the publication describes a more specific workflow, record the specific
workflow in the notes while retaining the benchmark modality category.

Examples:

- HiChIP may be recorded as a workflow-specific clarification when the
  repository classification is Hi-C.
- single-cell BCR sequencing should be explicitly described in notes if the
  repository strategy is RNA-Seq.
- targeted amplicon sequencing should remain AMPLICON even when the title
  contains "whole genome sequencing."

Never assign modality from title wording alone when stronger experimental
evidence is available.

---

## 6. RNA-seq compatibility

Record whether the benchmark unit is experimentally compatible with a
conventional RNA-seq analysis workflow.

Allowed values:

- Compatible
- Specialized workflow
- Not compatible
- Uncertain

"Not compatible" means not suitable for conventional RNA-seq analysis.

It does NOT mean that the dataset itself is scientifically poor or unusable.

Small RNA, miRNA, ncRNA, single-cell, immune-receptor, and other specialized
RNA workflows must be described explicitly rather than silently treated as
conventional bulk RNA-seq.

---

## 7. Experimental condition

Record the biological or experimental condition established by the evidence.

Examples:

- untreated
- heat stress
- starvation
- hypoxia
- infection
- nutrient limitation
- drug exposure

Do not convert a contextual word into a formal treatment assignment unless
the evidence establishes that relationship.

---

## 8. Treatment

Treatment must be explicitly supported.

Acceptable evidence includes statements such as:

- treated with X
- exposed to X
- treatment with X
- received X
- X-treated cells
- treatment group

Keyword presence alone is insufficient.

For example:

"RNA-seq under detergent stress"

does not automatically establish a treatment assignment unless the source
describes detergent as an administered exposure or treatment.

Record the treatment agent or treatment condition separately from the general
experimental context.

---

## 9. Control

A control must be explicitly established.

Examples:

- untreated control
- vehicle control
- mock control
- wild-type control
- control group
- matched control

Do not infer a control merely because a treatment exists.

Do not infer that wild type is a control unless the experimental description
supports that interpretation.

---

## 10. Time point

Record time point only when explicitly supported.

Examples:

- 6 h
- 24 h
- day 7
- time point 2

Multiple time points should be recorded in notes when necessary.

Do not infer a time course from multiple samples alone.

---

## 11. Replicates

Replicate annotation is critical.

Distinguish:

- biological replicate
- technical replicate
- replicate type not established

A label such as:

- replicate 1
- replicate 2
- Replicate A
- Replicate B

does NOT by itself establish biological replication.

If the publication explicitly identifies biological replicates, record them
as OBSERVED.

If a replicate exists but its biological/technical status cannot be
established, record:

NOT_ESTABLISHED

Never treat repeated sequencing runs as biological replicates solely because
multiple runs exist.

---

## 12. Experimental design

Record the simplest design that is explicitly supported.

Possible descriptions include:

- single-condition experiment
- treated versus untreated
- control versus treatment
- multiple treatment levels
- time-course experiment
- factorial treatment × condition
- genotype comparison
- mutant versus wild type
- multifactorial design

Do not construct a design formula unless the source explicitly supports it.

Do not infer missing experimental groups.

---

## 13. Batch information

Record batch information only when explicitly documented.

Examples:

- sequencing batch
- library preparation batch
- experimental batch
- processing batch

Absence of batch information should be recorded as MISSING when the relevant
source does not provide it.

---

## 14. Study-level annotation

Study-level benchmark units require special handling.

A study accession may contain multiple experiments, samples, conditions,
assays, or sequencing strategies.

Do not treat the representative experiment as the complete experimental truth
of the study.

Record:

- number of relevant experiments when established
- major assay families
- experimental contexts
- multimodality
- whether the complete study design can be established

If the study contains multiple assay families, explicitly record this.

---

## 15. Multiple selected units from one study

Different benchmark units may belong to the same study family.

This is intentional.

Same-study units must NOT be considered duplicates merely because they share:

- BioProject
- BioSample
- study accession

Distinct experiments or sequencing runs remain distinct benchmark units when
their accession and experimental identity differ.

A shared BioSample does not automatically imply duplicate sequencing.

---

## 16. Conflicting evidence

When repository metadata and publication evidence disagree:

1. Record the repository observation.
2. Record the publication observation.
3. Describe the discrepancy.
4. Use the strongest evidence for experimental truth.
5. Do not silently overwrite the repository record.

The conflict itself should be retained as an annotation note.

---

## 17. Unsupported inference

Annotators must actively look for opportunities where an apparently obvious
claim is NOT actually established.

Examples:

- title contains "stress" but treatment is not established
- multiple runs but biological replication is not established
- wild type appears but control relationship is not established
- several samples exist but experimental groups are unclear
- RNA-Seq strategy is present but workflow is specialized

Unsupported inference is a primary benchmark error category.

---

## 18. Required evidence traceability

Every nontrivial experimental-truth annotation should contain:

- evidence source
- publication identifier or repository identifier
- relevant section / figure / table / supplementary file where possible
- concise evidence note

Examples:

- PMID
- DOI
- SRA accession
- BioProject accession
- BioSample accession
- Supplementary Table S2
- Methods section
- Figure 1
- experimental design paragraph

---

## 19. Reviewer independence

Reviewer 1 and Reviewer 2 must annotate independently.

Reviewer 2 should NOT inspect Reviewer 1's annotations before completing
their own annotation.

Disagreements are resolved only after both independent annotations are
complete.

---

## 20. Adjudication

Disagreements must be classified as:

- genuine evidence disagreement
- interpretation disagreement
- evidence availability disagreement
- annotation-rule ambiguity

The adjudicator must record:

1. final value
2. final evidence state
3. supporting evidence
4. reason for resolving the disagreement

---

## 21. Principle of conservative annotation

When evidence is insufficient:

DO NOT GUESS.

Prefer:

NOT_ESTABLISHED

over unsupported biological interpretation.

The benchmark evaluates whether RNASeq Scout appropriately distinguishes
established information from unsupported inference.

---

## 22. Benchmark immutability

The benchmark membership is defined by:

benchmark/benchmark_manifest_v1.0.csv

and its SHA-256 checksum.

Experimental-truth annotation MUST NOT:

- add benchmark units
- remove benchmark units
- replace benchmark units
- change benchmark modality strata
- change benchmark unit types

If a benchmark unit becomes difficult to interpret, annotate the ambiguity.

Do not replace it.

---

## 23. Annotation version

This document defines:

Annotation Guidelines v1.0

Any substantive change after pilot annotation must be documented as a new
guideline version.
