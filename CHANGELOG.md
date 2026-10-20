## Experimental-Design Confidence and Evidence Separation
Date: 2026-10-20

### Implementation
- Added a human-readable explanation for experimental-design confidence.
- Kept BioSample-level treatment and time-point observations separate
  from study-level experimental-design assignments.
- Updated the Streamlit interface to display the confidence rationale
  and available BioSample-level observations separately.
- Added regression tests for confidence explanations and evidence separation.

### Validation
- Full test suite: 178 passed.
- Python syntax checks passed.
- Git whitespace check passed.
- Commit: `8a2caaa` — Explain experimental design confidence and evidence.

### Remaining Work
- Validate confidence assignments against representative real RNA-seq studies.
- Evaluate incomplete and conflicting metadata and avoid unsupported design claims.
- Assess confidence calibration against independently curated evidence.

---

# RNASeq Navigator Development Log

## Version 0.4.0
Date: 2026-08-02

### Major Milestone
Implemented a complete metadata discovery framework capable of discovering, parsing, ranking, and selecting representative RNA-seq datasets directly from NCBI.

---

## New Features

### Metadata Retrieval Engine

- Implemented Entrez-based metadata retrieval
- Automatic accession resolution
- Automatic ESummary retrieval
- Retrieval of ExpXml and Runs metadata

---

### Metadata Parser

Implemented a production-ready SRA parser capable of extracting:

- BioProject
- Study
- Experiment
- Run
- BioSample
- Organism
- Library Strategy
- Library Source
- Library Selection
- Library Layout
- Platform
- Instrument Model
- Sequencing Statistics
    - Total Spots
    - Total Bases

Metadata are now stored in structured dataclass objects instead of dictionaries.

---

### Metadata Models

Introduced strongly typed metadata classes:

- Metadata
- ProjectMetadata
- StudyMetadata
- ExperimentMetadata
- RunMetadata
- SampleMetadata

---

### Regression Testing Framework

Implemented automated regression testing for metadata parsing.

Capabilities:

- Batch testing
- Metadata validation
- Category-wise reporting
- Parser accuracy calculation

---

### Dataset Verification

Implemented automatic verification of benchmark datasets.

Checks include:

- Organism consistency
- Library strategy
- Layout
- Category assignment
- Benchmark integrity

This revealed incorrectly categorized benchmark datasets, demonstrating successful metadata validation.

---

### Dataset Discovery Engine

Implemented automatic RNA-seq dataset discovery using biological search criteria.

Supported filters:

- Organism
- Library Strategy
- Library Layout
- Maximum Results

The discovery engine now returns fully parsed Metadata objects rather than accession IDs.

---

### Dataset Diversity Engine

Implemented representative dataset selection.

Supported strategies:

- Unique BioProject
- Unique Study
- Unique Run

This removes redundant technical replicates from benchmark datasets.

---

### Dataset Ranking Engine

Implemented quality-based ranking of candidate datasets.

Current scoring incorporates:

- Sequencing depth
- Metadata completeness
- Library strategy
- Platform information
- Instrument information
- Public availability

Representative datasets are now selected based on metadata quality rather than first occurrence.

---

## Testing

Successfully validated:

- Metadata parsing
- Dataset discovery
- Dataset ranking
- Representative dataset selection

Example:

Query:

Organism:
Mycobacterium tuberculosis

Strategy:
RNA-Seq

Layout:
PAIRED

Results:

- 20 candidate datasets
- 19 metadata records parsed
- 4 representative BioProjects selected automatically

---

## Architecture

Current workflow:

User Query
    ↓
Dataset Discovery
    ↓
NCBI Entrez Search
    ↓
Metadata Retrieval
    ↓
Metadata Parser
    ↓
Metadata Objects
    ↓
Dataset Ranking
    ↓
Representative Selection

---

## Current Development Status

Completed:

- Metadata retrieval
- Metadata parsing
- Metadata models
- Regression testing
- Dataset discovery
- Dataset verification
- Diversity filtering
- Dataset ranking

Remaining:

- Metadata normalization
- Metadata validation
- Metadata cache integration
- CLI enhancements
- Dataset recommendation engine

Overall completion of metadata subsystem:

≈98%
