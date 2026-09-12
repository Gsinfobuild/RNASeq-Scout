#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

DEFAULT_REVIEWER_1 = (
    BASE_DIR / "annotations" / "reviewer_1" / "ground_truth_reviewer_1.csv"
)

DEFAULT_REVIEWER_2 = (
    BASE_DIR / "annotations" / "reviewer_2" / "ground_truth_reviewer_2.csv"
)

DEFAULT_OUTPUT_DIR = BASE_DIR / "annotations" / "adjudication"


def load_annotations(path: Path):
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    required = {
        "benchmark_id",
        "accession",
        "field",
        "experimental_truth",
        "experimental_evidence_state",
    }

    if not rows:
        raise ValueError(f"No annotation rows found in {path}")

    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(
            f"{path} is missing required columns: {', '.join(sorted(missing))}"
        )

    return rows


def normalize(value):
    if value is None:
        return ""
    return value.strip()


def row_key(row):
    return (
        normalize(row.get("benchmark_id")),
        normalize(row.get("accession")),
        normalize(row.get("field")),
    )


def is_complete(row):
    value = normalize(row.get("experimental_truth"))
    state = normalize(row.get("experimental_evidence_state"))

    return bool(value and state)


def compare_rows(reviewer_1_rows, reviewer_2_rows):
    r1 = {row_key(row): row for row in reviewer_1_rows}
    r2 = {row_key(row): row for row in reviewer_2_rows}

    all_keys = sorted(set(r1) | set(r2))

    comparisons = []

    for key in all_keys:
        row1 = r1.get(key)
        row2 = r2.get(key)

        if row1 is None or row2 is None:
            status = "INCOMPLETE"
        elif not is_complete(row1) or not is_complete(row2):
            status = "INCOMPLETE"
        else:
            value1 = normalize(row1.get("experimental_truth"))
            value2 = normalize(row2.get("experimental_truth"))

            state1 = normalize(row1.get("experimental_evidence_state"))
            state2 = normalize(row2.get("experimental_evidence_state"))

            if value1 == value2 and state1 == state2:
                status = "AGREE"
            else:
                status = "DISAGREE"

        comparisons.append(
            {
                "benchmark_id": key[0],
                "accession": key[1],
                "field": key[2],
                "status": status,
                "reviewer_1_value": (
                    normalize(row1.get("experimental_truth"))
                    if row1
                    else ""
                ),
                "reviewer_2_value": (
                    normalize(row2.get("experimental_truth"))
                    if row2
                    else ""
                ),
                "reviewer_1_state": (
                    normalize(row1.get("experimental_evidence_state"))
                    if row1
                    else ""
                ),
                "reviewer_2_state": (
                    normalize(row2.get("experimental_evidence_state"))
                    if row2
                    else ""
                ),
            }
        )

    return comparisons


def write_disagreements(comparisons, output_path):
    disagreements = [
        row for row in comparisons if row["status"] == "DISAGREE"
    ]

    fieldnames = [
        "benchmark_id",
        "accession",
        "field",
        "reviewer_1_value",
        "reviewer_2_value",
        "reviewer_1_state",
        "reviewer_2_state",
        "status",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in disagreements:
            writer.writerow(row)


def write_report(
    comparisons,
    output_path,
    reviewer_1_path,
    reviewer_2_path,
    label,
):
    total = len(comparisons)

    agree = sum(row["status"] == "AGREE" for row in comparisons)
    disagree = sum(row["status"] == "DISAGREE" for row in comparisons)
    incomplete = sum(row["status"] == "INCOMPLETE" for row in comparisons)

    completed = agree + disagree

    value_comparable = [
        row
        for row in comparisons
        if row["status"] in {"AGREE", "DISAGREE"}
    ]

    value_agreement = sum(
        normalize(row["reviewer_1_value"])
        == normalize(row["reviewer_2_value"])
        for row in value_comparable
    )

    state_agreement = sum(
        normalize(row["reviewer_1_state"])
        == normalize(row["reviewer_2_state"])
        for row in value_comparable
    )

    field_counts = {}

    for row in comparisons:
        field = row["field"]

        if field not in field_counts:
            field_counts[field] = {
                "AGREE": 0,
                "DISAGREE": 0,
                "INCOMPLETE": 0,
            }

        field_counts[field][row["status"]] += 1

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Reviewer Agreement Report — {label}\n\n")

        handle.write("## Annotation files\n\n")
        handle.write(f"- Reviewer 1: `{reviewer_1_path}`\n")
        handle.write(f"- Reviewer 2: `{reviewer_2_path}`\n\n")

        handle.write("## Overall status\n\n")
        handle.write(f"- Compared rows: {total}\n")
        handle.write(f"- AGREE: {agree}\n")
        handle.write(f"- DISAGREE: {disagree}\n")
        handle.write(f"- INCOMPLETE: {incomplete}\n")
        handle.write(f"- Completed rows: {completed}\n\n")

        handle.write("## Agreement among completed rows\n\n")

        if value_comparable:
            handle.write(
                f"- Value agreement: {value_agreement}/{len(value_comparable)}\n"
            )
            handle.write(
                f"- State agreement: {state_agreement}/{len(value_comparable)}\n"
            )
        else:
            handle.write("- Value agreement: not estimable\n")
            handle.write("- State agreement: not estimable\n")

        handle.write("\n## Field-level status\n\n")
        handle.write(
            "| Field | Agree | Disagree | Incomplete |\n"
            "|---|---:|---:|---:|\n"
        )

        for field in sorted(field_counts):
            counts = field_counts[field]
            handle.write(
                f"| {field} | {counts['AGREE']} | "
                f"{counts['DISAGREE']} | {counts['INCOMPLETE']} |\n"
            )

        handle.write("\n## Interpretation\n\n")

        if incomplete == total:
            handle.write(
                "No reviewer rows are complete enough for inter-rater "
                "agreement assessment. This is expected before independent "
                "annotation is performed.\n"
            )
        elif disagree == 0:
            handle.write(
                "No disagreements were detected among completed rows. "
                "Incomplete rows were excluded from adjudication.\n"
            )
        else:
            handle.write(
                f"{disagree} completed row(s) require adjudication. "
                "Incomplete rows were not treated as disagreements.\n"
            )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare two independent RNASeq Scout reviewer annotation files."
        )
    )

    parser.add_argument(
        "--reviewer-1",
        type=Path,
        default=DEFAULT_REVIEWER_1,
        help="Reviewer 1 annotation CSV.",
    )

    parser.add_argument(
        "--reviewer-2",
        type=Path,
        default=DEFAULT_REVIEWER_2,
        help="Reviewer 2 annotation CSV.",
    )

    parser.add_argument(
        "--label",
        default="pilot",
        help="Label used for generated reports.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated comparison outputs.",
    )

    args = parser.parse_args()

    reviewer_1_path = args.reviewer_1.resolve()
    reviewer_2_path = args.reviewer_2.resolve()
    output_dir = args.output_dir.resolve()

    if not reviewer_1_path.exists():
        raise FileNotFoundError(
            f"Reviewer 1 file not found: {reviewer_1_path}"
        )

    if not reviewer_2_path.exists():
        raise FileNotFoundError(
            f"Reviewer 2 file not found: {reviewer_2_path}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    reviewer_1_rows = load_annotations(reviewer_1_path)
    reviewer_2_rows = load_annotations(reviewer_2_path)

    comparisons = compare_rows(
        reviewer_1_rows,
        reviewer_2_rows,
    )

    label_safe = args.label.replace("/", "_").replace(" ", "_")

    disagreement_path = (
        output_dir / f"{label_safe}_disagreements_v1.0.csv"
    )

    report_path = (
        output_dir / f"{label_safe}_agreement_report_v1.0.md"
    )

    write_disagreements(
        comparisons,
        disagreement_path,
    )

    write_report(
        comparisons,
        report_path,
        reviewer_1_path,
        reviewer_2_path,
        args.label,
    )

    total = len(comparisons)
    agree = sum(row["status"] == "AGREE" for row in comparisons)
    disagree = sum(row["status"] == "DISAGREE" for row in comparisons)
    incomplete = sum(row["status"] == "INCOMPLETE" for row in comparisons)

    completed = agree + disagree

    value_comparable = [
        row for row in comparisons
        if row["status"] in {"AGREE", "DISAGREE"}
    ]

    value_agreement = sum(
        normalize(row["reviewer_1_value"])
        == normalize(row["reviewer_2_value"])
        for row in value_comparable
    )

    state_agreement = sum(
        normalize(row["reviewer_1_state"])
        == normalize(row["reviewer_2_state"])
        for row in value_comparable
    )

    print(f"Compared rows: {total}")
    print(f"AGREE: {agree}")
    print(f"DISAGREE: {disagree}")
    print(f"INCOMPLETE: {incomplete}")
    print(f"Completed rows: {completed}")

    if value_comparable:
        print(
            f"Value agreement: "
            f"{value_agreement}/{len(value_comparable)}"
        )
        print(
            f"State agreement: "
            f"{state_agreement}/{len(value_comparable)}"
        )
    else:
        print("Value agreement: not estimable")
        print("State agreement: not estimable")

    print(f"Disagreements: {disagree}")
    print(f"Disagreement file: {disagreement_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
