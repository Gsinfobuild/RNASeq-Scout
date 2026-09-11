# RNASeq Scout Benchmark

This directory contains the validation framework for RNASeq Scout.

## Purpose

The benchmark evaluates whether RNASeq Scout can:

1. classify sequencing modality;
2. distinguish RNA-seq-compatible from non-compatible datasets;
3. identify experimentally documented metadata;
4. distinguish observed evidence from unsupported inference;
5. assess dataset suitability for RNA-seq analysis;
6. assess reanalysis readiness;
7. generate conservative analysis plans.

## Ground-truth principle

Two levels of evidence are maintained separately:

### Repository evidence
Information that can be established from publicly available
repository metadata such as SRA, BioProject and BioSample.

### Experimental truth
Information established by the associated publication,
supplementary information, or other authoritative experimental
documentation.

The benchmark must not penalize RNASeq Scout for failing to infer
information that is absent from repository metadata.

## Evidence states

Each experimental-design field should be classified as:

- OBSERVED
- INFERRED
- NOT_ESTABLISHED
- MISSING

## Primary evaluation dimensions

### Modality classification
Accuracy, precision, recall and F1 where appropriate.

### Experimental-design interpretation
Condition, treatment, control, time point, replicate and batch
information.

### Unsupported inference
Rate of claims made without sufficient repository evidence.

### Dataset suitability
Agreement with independent expert assessment.

### Reanalysis readiness
Agreement with independent expert consensus.

### Reproducibility
Consistency across repeated runs.

## Benchmark policy

Accessions should be selected to represent both clear and difficult
real-world cases.

The benchmark should include positive, negative, ambiguous,
incomplete and mixed-assay datasets.

Ground-truth annotation must be performed independently of
RNASeq Scout output wherever possible.
