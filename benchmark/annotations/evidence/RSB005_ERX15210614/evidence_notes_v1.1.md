# RSB005 — ERX15210614 Evidence Dossier

## Accession chain

- Experiment: ERX15210614
- Run: ERR15811000
- Study/Project: PRJEB101698
- BioSample: SAMEA120469952
- SRA sample: ERS27170638
- Sample name / submitter ID: 36

## Repository evidence

ENA File Report for ERX15210614 establishes:

- library strategy: RNA-Seq
- library source: TRANSCRIPTOMIC
- library selection: cDNA_randomPriming
- layout: PAIRED
- platform: ILLUMINA
- instrument: Illumina NovaSeq 6000
- organism: Arabidopsis thaliana
- run: ERR15811000
- sample: SAMEA120469952

BioSample SAMEA120469952 establishes:

- title: RNAseq_ago1-27.3
- description: RNAseq, ago1-27, biological replica 3
- ecotype: Col-0
- tissue_type: Inflorescences
- organism: Arabidopsis thaliana
- SRA accession: ERS27170638

## Ground-truth interpretation

The accession-specific biological identity is explicitly established by the BioSample record.

- Modality: RNA-seq — OBSERVED
- RNA-seq compatibility: compatible — OBSERVED
- Organism: Arabidopsis thaliana — OBSERVED
- Genotype: ago1-27 — OBSERVED
- Biological replicate: replicate 3 — OBSERVED
- Replicate type: biological — OBSERVED
- Ecotype: Col-0 — OBSERVED
- Tissue: Inflorescences — OBSERVED
- Treatment: NOT_ESTABLISHED
- Control: NOT_ESTABLISHED
- Time point: NOT_ESTABLISHED

## Evidence source

European Nucleotide Archive / BioSamples:
SAMEA120469952

The accession-level mapping was established from the BioSample record rather than inferred from Supplementary Table S1.

## Supplementary material

The supplementary package was inspected. Table S1 contains RNA-seq expression/count data with sample columns including Col-0, ago1-27, wtAGO1, nucAGO1 and cytAGO1, but does not contain ERX15210614, ERS27170638 or ERR15811000. Therefore S1 was not used to establish the accession-specific mapping.

## Important annotation distinction

Col-0 is recorded as the ecotype. The experimental genotype is ago1-27. These should not be conflated.

## Remaining uncertainty

The BioSample record establishes the sample as ago1-27 biological replicate 3, but does not by itself establish a formal control assignment, treatment assignment, or time point for this accession.
