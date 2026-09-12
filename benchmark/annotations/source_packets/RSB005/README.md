# RSB005 — ERX15210614

## Benchmark unit

- Benchmark ID: RSB005
- Accession: ERX15210614
- Accession type: experiment
- Study: ERP183101
- Project: PRJEB101698
- Organism group: Arabidopsis

## Source packet

This directory contains source evidence for independent experimental-truth
annotation.

The packet is evidence-oriented and must not be treated as a Scout answer key.

## Source files

1. `repository_evidence.csv`
2. `publication_evidence.md`
3. `supplementary_evidence.md`

## Reviewer independence

Reviewer 1 and Reviewer 2 must work independently.

A reviewer must not inspect:

- the other reviewer's annotation
- Scout output
- the internal evidence register
- an adjudicated answer

before completing their own annotation.

## Important distinction

Source evidence is not itself the final annotation.

For example, the BioSamples source contains:

`title=RNAseq_ago1-27.3`

and:

`description=RNAseq, ago1-27, biological replica 3`

The reviewer must independently determine what experimental-truth fields
these observations establish and what evidence state is appropriate.

## Evidence hierarchy

Use the benchmark annotation guidelines:

1. Primary research publication
2. Publication supplementary material
3. Study-specific experimental metadata
4. SRA / BioProject / BioSample repository records
5. Other authoritative repository-linked records

## Supplementary accession mapping

The inspected supplementary tables did not directly contain:

- ERX15210614
- ERS27170638
- ERR15811000

Therefore, reviewers must not infer an accession-to-sample mapping merely
from the presence of sample names such as `ago1-27` in Table S1.

## Annotation boundary

Do not construct:

- treatment assignments
- control assignments
- design formulas
- experimental groups

unless the source explicitly establishes them.

Unsupported inference is a primary benchmark error category.
