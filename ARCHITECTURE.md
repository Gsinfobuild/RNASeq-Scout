# RNASeq Scout Architecture

**Version:** 0.1.0  
**Project:** RNASeq Scout  
**Repository:** https://github.com/Gsinfobuild/RNASeq-Scout

---

## 1. Overview

RNASeq Scout is an RNA-seq Experiment Intelligence Engine that transforms a sequencing accession into an experiment-aware interpretation and preliminary analysis plan.

Its central principle is:

> Metadata should be interpreted before an analysis workflow is proposed.

The system separates metadata retrieval from scientific interpretation and progressively evaluates an accession through normalization, validation, modality classification, experimental-design interpretation, dataset suitability, and analysis planning.

The architecture is intentionally conservative: explicit metadata evidence is distinguished from inference, and uncertainty is preserved when available metadata do not support a confident conclusion.

## 2. Canonical Pipeline

The canonical inspection pipeline is:

```text
SRA Accession
      |
      v
Metadata Retrieval
      |
      v
Normalization
      |
      v
Validation
      |
      v
Metadata Intelligence
      |
      v
Modality / Workflow Intelligence
      |
      v
Experimental Design Intelligence
      |
      v
Dataset Suitability
      |
      v
Analysis Planning
      |
      v
InspectionResult
      |
      +---------> GUI / JSON / PDF
```

`RNASeqNavigator.inspect()` is the canonical public inspection pipeline. Presentation layers should consume its result rather than implement separate scientific logic.

## 3. Metadata Processing

### Metadata Retrieval

The retrieval layer obtains project, study, experiment, run, and sample metadata associated with an SRA accession. Retrieval itself does not determine RNA-seq suitability.

### Normalization

Normalization converts source metadata into the internal RNASeq Scout data model and provides a stable representation for downstream intelligence layers.

### Validation

Validation checks whether normalized metadata are structurally usable for interpretation. Validation is distinct from scientific suitability: valid metadata do not necessarily imply suitability for RNA-seq analysis.

## 4. Layer 1 — Metadata Intelligence

Metadata Intelligence converts normalized metadata into a structured biological and sequencing context.

The `MetadataInsight` model currently captures:

- Organism
- Study type
- Biological system
- Experimental focus
- Sequencing summary
- Observations

The layer may infer broad biological context and experimental focus from available metadata. Such interpretations should not be presented as experimentally established facts when the source metadata are ambiguous.

## 5. Layer 1.5 — Modality / Workflow Intelligence

Modality / Workflow Intelligence establishes what type of sequencing experiment is represented before RNA-seq-specific suitability or workflow recommendations are made.

This layer was introduced to prevent non-RNA sequencing experiments from being incorrectly processed as RNA-seq datasets.

The `ModalityInsight` model records:

- Sequencing modality
- Library strategy
- Library source
- Library selection
- Workflow family
- RNA-seq compatibility
- Compatibility status
- Classification confidence
- Observed evidence
- Warnings
- Rationale

### Compatibility states

RNASeq Scout uses three conceptual compatibility states:

```text
True   = explicitly compatible with the conventional RNA-seq workflow
False  = explicitly incompatible with the RNA-seq workflow
None   = RNA-seq compatibility has not been established
```

The distinction between `False` and `None` is deliberate. An unknown sequencing strategy must not be treated as evidence that a dataset is incompatible.

### Current modality handling

The current implementation recognizes, among others:

| Strategy | Interpretation | RNA-seq compatibility |
|---|---|---|
| `RNA_SEQ` | RNA-seq | Compatible |
| `SMALL_RNA` | Specialized RNA modality | Specialized workflow |
| `NCRNA_SEQ` | Specialized RNA modality | Specialized workflow |
| `AMPLICON` | Amplicon sequencing | Not compatible |
| `WGS` / `WGA` | Whole-genome sequencing | Not compatible |
| `WXS` | Whole-exome sequencing | Not compatible |
| `CHIP_SEQ` | Chromatin profiling | Not compatible |
| `ATAC_SEQ` | Chromatin accessibility | Not compatible |
| Bisulfite sequencing | DNA methylation workflow | Not compatible |

The purpose of this layer is not to classify every sequencing technology. Its primary role is to establish a conservative boundary around RNA-seq workflow applicability.

## 6. Layer 2 — Experimental Design Intelligence

Experimental Design Intelligence evaluates how the experiment appears to be organized using the available metadata.

The `ExperimentalDesignInsight` model currently captures:

- Condition
- Control
- Treatment
- Time point
- Replicate information
- Design description
- Design confidence
- Confidence explanation
- Observed features
- Inferred features
- Warnings
- Missing information

### Observed versus inferred information

RNASeq Scout distinguishes evidence directly supported by metadata from interpretations derived from that evidence.

BioSample-level treatment and time-point annotations are retained as
sample-level observations. They do not independently establish study-level
treatment assignments, control groups, or the complete experimental design.

The `confidence_explanation` field provides a human-readable rationale for
the assigned design-confidence category. It identifies unresolved aspects
of the design and, when available, describes sample-level evidence without
promoting it to a study-level conclusion. The explanation supplements the
confidence classification; it does not independently validate the design.

### Biological replicates

Runs are not automatically interpreted as biological replicates. Multiple runs may represent technical replicates, sequencing lanes, repeated measurements, biological replicates, or other experimental structures.

Biological replication is therefore reported only when supported by available metadata.

### Missing information

When controls, treatments, time points, or replicate information cannot be established, RNASeq Scout records the missing information rather than inventing an experimental design.

## 7. Layer 3 — Dataset Suitability

Dataset Suitability evaluates whether the available evidence is sufficient to justify the intended RNA-seq analysis workflow.

Suitability is analysis-specific. It is not a judgement about the overall scientific quality or usefulness of the underlying dataset.

The `SuitabilityInsight` model captures:

- Overall assessment
- Score
- Observed evidence
- Warnings
- Missing information
- Rationale

### Modality compatibility gate

Modality compatibility is evaluated before ordinary RNA-seq suitability scoring.

```text
Explicitly incompatible
        |
        +--> Not suitable for RNA-seq analysis
        |    Score = 0

Unknown modality
        |
        +--> RNA-seq compatibility uncertain
        |    Score = 0

Explicitly compatible
        |
        +--> Evaluate RNA-seq evidence
             |
             +--> Suitability assessment
```

This gate prevents an AMPLICON or other non-RNA sequencing dataset from receiving a positive RNA-seq suitability assessment merely because technically complete sequencing metadata are present.

### Suitability categories

The current categories are:

- Suitable
- Potentially suitable
- Insufficient information
- Not suitable for RNA-seq analysis
- RNA-seq compatibility uncertain

Each assessment is accompanied by supporting evidence, warnings, or missing-information statements where appropriate.

## 8. Layer 4 — Analysis Planning

Analysis Planning translates the preceding interpretation into a preliminary workflow recommendation.

The `AnalysisPlan` model captures:

- Workflow
- Alignment
- Quantification
- Differential analysis
- Design formula
- Replicate status
- Confidence
- Rationale
- Recommendations
- Warnings

For a compatible conventional RNA-seq dataset, the current workflow can include:

```text
RNA-seq analysis
      |
      v
STAR
      |
      v
featureCounts
      |
      v
DESeq2
```

The design formula is proposed only when the experimental metadata support it. Otherwise RNASeq Scout reports that the design formula is not established from the available metadata.

This conservative behavior prevents the system from inventing experimental factors or statistical contrasts.

### Analysis compatibility gate

The analysis planner receives modality information and applies the same workflow boundary established by Layer 1.5.

For explicitly incompatible modalities, the RNA-seq workflow is marked not applicable.

For uncertain modality, RNASeq Scout reports that RNA-seq workflow applicability is uncertain rather than selecting an RNA-seq toolchain.

This prevents RNA-seq-specific tools from being recommended simply because sequencing data exist.

## 9. InspectionResult

All intelligence layers are integrated into a common `InspectionResult`.

The result provides a structured representation of the accession inspection, including normalized metadata, metadata intelligence, modality/workflow intelligence, experimental-design intelligence, suitability assessment, analysis plan, dataset interpretation, dataset report, and success or failure information.

`InspectionResult` acts as the common contract between the scientific intelligence engine and the presentation layers.

## 10. Presentation Layers

RNASeq Scout exposes the inspection pipeline through the graphical application and command-line interface.

The GUI presents the major outputs in the following order:

```text
Dataset Statistics
       |
Metadata Intelligence
       |
Modality / Workflow Intelligence
       |
Experimental Design
       |
Dataset Suitability
       |
Analysis Plan
       |
Metadata Quality
       |
Dataset Report
       |
Export
```

The PDF export presents the inspection result and does not independently perform scientific inference.

## 11. Core Design Principles

### Evidence before inference

The system prefers explicit metadata evidence over heuristic interpretation.

### Preserve uncertainty

Unknown information remains unknown rather than being converted into a confident conclusion.

### Observed versus inferred information

Metadata directly supported by the source are distinguished from interpretations derived from those metadata.

### Modality before workflow

The sequencing modality must be established before an RNA-seq workflow is proposed.

### Biological replication is not assumed

Runs are not automatically considered biological replicates.

### Suitability is analysis-specific

A dataset may be scientifically useful while still being unsuitable for the particular RNA-seq workflow evaluated by RNASeq Scout.

### Recommendations are preliminary

The analysis plan is a metadata-driven starting point and does not replace researcher judgement, experimental records, or methodological validation.

## 12. Scientific Scope

RNASeq Scout v0.1.0 is primarily an experiment-intelligence and workflow-planning system.

It does not itself perform:

- Read alignment
- Transcript quantification
- Differential-expression computation
- Genome assembly
- Variant calling
- Biological validation

Instead, it evaluates sequencing metadata and proposes a preliminary analysis direction. The resulting plan should therefore be interpreted as a research planning aid.

## 13. Regression Validation

The architecture is validated using both positive and negative real SRA accession regressions.

### Conventional RNA-seq regression

`SRR17730393` is classified as RNA-seq with workflow family `bulk_rna_seq` and is marked RNA-seq compatible. The resulting plan is RNA-seq analysis using STAR, featureCounts, and DESeq2. The dataset is assessed as potentially suitable.

### Non-RNA-seq regression

`SRX35157977` is classified as Amplicon sequencing with workflow family `amplicon` and is marked not compatible with RNA-seq. The dataset is therefore assessed as not suitable for RNA-seq analysis, and the RNA-seq analysis workflow is marked not applicable.

These regressions test not only metadata retrieval but propagation of modality classification through suitability assessment and analysis planning.

## 14. Version 0.1.0 Architectural Boundary

RNASeq Scout v0.1.0 establishes the following architectural boundary:

```text
Metadata
   |
   v
Interpretation
   |
   v
Modality
   |
   v
Experimental Design
   |
   v
Suitability
   |
   v
Analysis Planning
```

Future versions may extend individual layers, add additional sequencing modalities, improve experimental-design inference, or introduce additional downstream analysis planning.

Extensions should preserve the core principles of evidence, uncertainty, and explicit workflow compatibility.

## 15. Ownership and Attribution

RNASeq Scout source code is owned by **Dr. Gauri Shankar** and distributed under the MIT License.

The graphical interface credits **Dr. G. Shankar** and **Dr. Ranjana Soni**.

The underlying sequencing metadata are obtained from public NCBI SRA resources. RNASeq Scout is an independent open-source project and is not affiliated with or endorsed by NCBI.

---

**RNASeq Scout v0.1.0**

*Data for a healthier planet and a brighter tomorrow.*
