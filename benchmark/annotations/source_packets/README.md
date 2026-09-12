# RNASeq Scout Benchmark v1.0
## Independent Reviewer Source Packets

These directories contain source evidence supplied to Reviewer 1 and
Reviewer 2 for independent experimental-truth annotation.

## Independence rule

Reviewer 1 and Reviewer 2 receive equivalent source evidence.

Neither reviewer may inspect the other reviewer's annotation before
submitting their own annotation.

The source packets must contain evidence, not Scout's final interpretation.

## Evidence layers

Each packet should distinguish:

1. Repository evidence
2. Publication evidence
3. Supplementary evidence
4. Other authoritative evidence

## Important restriction

Do NOT populate reviewer packets with Scout's inferred or adjudicated
experimental-truth values.

Examples of prohibited preprocessing:

- converting a title into a treatment assignment
- converting a sample name into a control assignment
- declaring a replicate biological or technical without source support
- constructing an experimental design formula
- filling missing fields with inferred values

## Reviewer workflow

1. Read the source evidence.
2. Annotate independently.
3. Record evidence source and identifier.
4. Record evidence state.
5. Record uncertainty explicitly.
6. Do not inspect the other reviewer's annotation.
7. Submit the completed annotation before comparison.

## Adjudication

Disagreements are examined only after both independent annotations are
complete.

Each disagreement must be classified as:

- genuine evidence disagreement
- interpretation disagreement
- evidence availability disagreement
- annotation-rule ambiguity

The adjudicator records:

- final value
- final evidence state
- supporting evidence
- disagreement classification
