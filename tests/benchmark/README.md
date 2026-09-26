# RNA-Seq Scout Scientific Benchmark

This directory contains the independent scientific validation framework
for RNA-Seq Scout.

The benchmark is distinct from the unit and regression tests.

## Purpose

The benchmark evaluates whether RNA-Seq Scout correctly interprets
public sequencing accessions with respect to:

1. sequencing modality;
2. conventional RNA-seq compatibility;
3. experimental-design evidence;
4. suitability for RNA-seq reanalysis;
5. reanalysis readiness; and
6. downstream analysis planning.

## Ground truth

Ground-truth annotations must be established independently of
RNA-Seq Scout predictions.

Ground truth may use:

- SRA experiment metadata;
- BioSample metadata;
- BioProject/study information;
- deposited experimental descriptions or protocols; and
- explicit curator notes where interpretation is required.

Scout output must never be used to establish its own benchmark labels.

## Benchmark design

The benchmark should use stratified accessions covering:

- conventional RNA-seq;
- specialized RNA sequencing;
- amplicon sequencing;
- whole-genome sequencing;
- whole-exome sequencing;
- ChIP-seq;
- ATAC-seq;
- metadata-poor or ambiguous accessions; and
- contradictory metadata.

Objective metadata fields and interpretive fields should be evaluated
separately.

## Important distinction

Benchmark execution success is not scientific accuracy.

A dataset is not considered correctly classified merely because
RNA-Seq Scout successfully retrieves and processes the accession.

## Reproducibility

Benchmark runs should record:

- accession;
- timestamp;
- Scout version/commit;
- observed Scout outputs;
- independent ground-truth annotations; and
- evaluation results.

The benchmark should be rerunnable after changes to the Scout
intelligence layers.
