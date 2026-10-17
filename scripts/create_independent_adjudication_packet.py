#!/usr/bin/env python3
"""Prepare a blinded independent-adjudication packet.

This script does NOT determine scientific truth or change official benchmark
files. It separates source evidence from existing candidate labels/predictions
so an independent reviewer can adjudicate without seeing those labels.

All generated files are written to /tmp.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmark/annotations/biological_benchmark_results"
EVIDENCE_ROOT = ROOT / "benchmark/annotations/repository_evidence"

ORIGINAL = RESULTS / "scoring_eligibility_50.csv"
RECONCILED = Path(
    "/tmp/rnaseq_scout_candidate_gt_review/"
    "scoring_eligibility_50_reconciled.csv"
)
PREDICTIONS = ROOT / (
    "benchmark/results/independent_50_hic_fix/scout_predictions.csv"
)

OUTDIR = Path("/tmp/rnaseq_scout_independent_adjudication")
ENDPOINTS = ("assay_modality", "rna_seq_compatibility")

# These are the questions reviewers must answer independently.
ENDPOINT_GUIDANCE = {
    "assay_modality": (
        "Identify the sequencing assay/modality supported by the repository "
        "evidence. Preserve specialized assays and unresolved conflicts."
    ),
    "rna_seq_compatibility": (
        "Decide whether the documented assay is compatible with conventional "
        "RNA-seq gene-expression analysis. Do not infer compatibility merely "
        "because the study mentions RNA."
    ),
}


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required input file not found: {path}")


def load_csv(path: Path) -> pd.DataFrame:
    require_file(path)
    return pd.read_csv(path, dtype="string").fillna("")


def local_name(tag: str) -> str:
    """Remove an XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1].upper()


def find_xml_strings(obj):
    """Yield XML-looking strings from arbitrarily nested JSON."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and (
                key.lower().endswith("xml") or "<" in value
            ):
                yield value
            else:
                yield from find_xml_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from find_xml_strings(value)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_xml_fragments(text: str):
    """Parse XML, including concatenated SRA XML fragments."""
    candidates = [text]
    # SRA esummary files may contain adjacent XML elements.
    candidates.append(f"<EvidenceRoot>{text}</EvidenceRoot>")

    for candidate in candidates:
        try:
            return ET.fromstring(candidate)
        except ET.ParseError:
            continue
    return None


def extract_evidence(accession: str, benchmark_id: str) -> dict[str, str]:
    """Extract a summary while preserving experiment/run evidence separately."""
    folder = EVIDENCE_ROOT / benchmark_id / accession
    esummary_path = folder / "esummary_records.json"
    metadata_path = folder / "metadata.json"

    result = {
        "library_strategy": "",
        "library_source": "",
        "library_selection": "",
        "library_layout": "",
        "library_protocol": "",
        "study_title": "",
        "organism": "",
        "platform": "",
        "instrument": "",
        "evidence_file": "",
        "evidence_status": "",
    }

    found: dict[str, list[str]] = {}
    evidence_files = []

    def add(key: str, value: str) -> None:
        value = (value or "").strip()
        if value:
            found.setdefault(key, [])
            if value not in found[key]:
                found[key].append(value)

    for path in (esummary_path, metadata_path):
        if not path.is_file():
            continue
        evidence_files.append(str(path))
        payload = read_json(path)
        if payload is None:
            continue

        for xml_text in find_xml_strings(payload):
            root = parse_xml_fragments(xml_text)
            if root is None:
                continue

            for element in root.iter():
                tag = local_name(element.tag)
                value = (element.text or "").strip()

                if tag in {
                    "LIBRARY_STRATEGY", "LIBRARY_SOURCE",
                    "LIBRARY_SELECTION", "LIBRARY_CONSTRUCTION_PROTOCOL",
                    "DESIGN_DESCRIPTION", "TITLE", "STUDY_TITLE",
                    "PLATFORM",
                }:
                    add(tag, value)

                for attr_key, attr_value in element.attrib.items():
                    attr = local_name(attr_key)
                    if tag == "ORGANISM" and attr == "SCIENTIFICNAME":
                        add("SCIENTIFIC_NAME", attr_value)
                    elif tag == "PLATFORM" and attr == "INSTRUMENT_MODEL":
                        add("INSTRUMENT_MODEL", attr_value)
                    elif tag == "INSTRUMENT":
                        # SRA often encodes the model as an attribute whose
                        # name is the platform, e.g. ILLUMINA="NovaSeq X".
                        add("INSTRUMENT_MODEL", attr_value)
                    elif tag in {"EXPERIMENT", "RUN"} and attr == "ACC":
                        add(f"{tag}_ACCESSION", attr_value)

                if tag == "LIBRARY_LAYOUT":
                    for child in list(element):
                        add("LIBRARY_LAYOUT", local_name(child.tag))

    aliases = {
        "library_strategy": ["LIBRARY_STRATEGY"],
        "library_source": ["LIBRARY_SOURCE"],
        "library_selection": ["LIBRARY_SELECTION"],
        "library_layout": ["LIBRARY_LAYOUT"],
        "library_protocol": [
            "LIBRARY_CONSTRUCTION_PROTOCOL", "DESIGN_DESCRIPTION",
        ],
        "study_title": ["STUDY_TITLE", "TITLE"],
        "organism": ["SCIENTIFIC_NAME"],
        "platform": ["PLATFORM"],
        "instrument": ["INSTRUMENT_MODEL"],
    }

    for output_field, tags in aliases.items():
        values = []
        for tag in tags:
            values.extend(found.get(tag, []))
        result[output_field] = " | ".join(dict.fromkeys(v for v in values if v) )

    result["evidence_file"] = "Cached repository evidence; see source records"
    if result["library_strategy"] or result["study_title"] or result["organism"]:
        result["evidence_status"] = "parsed_cached_repository_evidence"
    elif evidence_files:
        result["evidence_status"] = "cached_file_found_but_structured_fields_not_parsed"
    else:
        result["evidence_status"] = "cached_evidence_file_not_found"
    return result


def extract_experiment_evidence(
    accession: str, benchmark_id: str, review_id: str
) -> list[dict[str, str]]:
    """Return one evidence row per cached experiment/run record."""
    folder = EVIDENCE_ROOT / benchmark_id / accession
    path = folder / "esummary_records.json"
    if not path.is_file():
        return [{
            "review_id": review_id,
            "experiment_accession": "",
            "run_accession": "",
            "library_strategy": "",
            "library_source": "",
            "library_selection": "",
            "library_layout": "",
            "organism": "",
            "platform": "",
            "instrument": "",
            "study_title": "",
            "source_record_uid": "",
            "evidence_file": "Cached repository experiment records",
            "evidence_status": "cached_esummary_not_found",
        }]

    payload = read_json(path)
    if not isinstance(payload, list):
        return [{
            "review_id": review_id,
            "experiment_accession": "",
            "run_accession": "",
            "library_strategy": "",
            "library_source": "",
            "library_selection": "",
            "library_layout": "",
            "organism": "",
            "platform": "",
            "instrument": "",
            "study_title": "",
            "source_record_uid": "",
            "evidence_file": "Cached repository experiment records",
            "evidence_status": "cached_esummary_unreadable",
        }]

    rows = []
    for record in payload:
        if not isinstance(record, dict):
            continue

        exp_xml = record.get("ExpXml", "")
        run_xml = record.get("Runs", "")
        root = parse_xml_fragments(f"{exp_xml}{run_xml}")
        if root is None:
            continue

        def first(tag: str) -> str:
            node = next(
                (n for n in root.iter() if local_name(n.tag) == tag.upper()),
                None,
            )
            return (node.text or "").strip() if node is not None else ""

        def attr(tag: str, key: str) -> str:
            node = next(
                (n for n in root.iter() if local_name(n.tag) == tag.upper()),
                None,
            )
            if node is None:
                return ""
            return next(
                (v.strip() for k, v in node.attrib.items()
                 if local_name(k) == key.upper()),
                "",
            )

        layout_node = next(
            (n for n in root.iter()
             if local_name(n.tag) == "LIBRARY_LAYOUT"),
            None,
        )
        layout = (
            " | ".join(local_name(child.tag) for child in list(layout_node))
            if layout_node is not None else ""
        )

        organism = attr("Organism", "ScientificName")
        if not organism:
            common_name = attr("Organism", "CommonName")
            taxid = attr("Organism", "taxid")
            if common_name and taxid:
                organism = f"{common_name} (taxid {taxid})"
            elif common_name:
                organism = common_name
            elif taxid:
                organism = f"taxid {taxid}"
        platform_node = next(
            (n for n in root.iter() if local_name(n.tag) == "PLATFORM"),
            None,
        )
        instrument = attr("Platform", "instrument_model")
        if not instrument:
            instrument_node = next(
                (n for n in root.iter() if local_name(n.tag) == "INSTRUMENT"),
                None,
            )
            if instrument_node is not None and instrument_node.attrib:
                instrument = next(iter(instrument_node.attrib.values()))

        row = {
            "review_id": review_id,
            "experiment_accession": attr("Experiment", "acc"),
            "run_accession": attr("Run", "acc"),
            "library_strategy": first("LIBRARY_STRATEGY"),
            "library_source": first("LIBRARY_SOURCE"),
            "library_selection": first("LIBRARY_SELECTION"),
            "library_layout": layout,
            "organism": organism,
            "platform": (
                (platform_node.text or "").strip()
                if platform_node is not None else ""
            ),
            "instrument": instrument,
            "study_title": first("Title"),
            "source_record_uid": str(record.get("Id", "")),
            "evidence_file": "Cached repository experiment records",
            "evidence_status": "parsed_experiment_run_record",
        }
        rows.append(row)

    return rows


def main() -> int:
    original = load_csv(ORIGINAL)
    reconciled = load_csv(RECONCILED)
    predictions = load_csv(PREDICTIONS)

    required_candidate_columns = {
        "benchmark_id", "accession", "field",
        "candidate_ground_truth", "field_status", "scoring_eligibility",
    }
    missing = required_candidate_columns - set(original.columns)
    if missing:
        raise ValueError(
            f"Original candidate file is missing columns: {sorted(missing)}"
        )
    missing = required_candidate_columns - set(reconciled.columns)
    if missing:
        raise ValueError(
            f"Reconciled candidate file is missing columns: {sorted(missing)}"
        )
    required_prediction_columns = {
        "benchmark_id", "accession", "predicted_modality", "rna_seq_compatible"
    }
    missing = required_prediction_columns - set(predictions.columns)
    if missing:
        raise ValueError(
            f"Prediction file is missing columns: {sorted(missing)}"
        )

    original = original[original["field"].isin(ENDPOINTS)].copy()
    reconciled = reconciled[reconciled["field"].isin(ENDPOINTS)].copy()

    # One stable row per benchmark accession.
    units = original[["benchmark_id", "accession"]].drop_duplicates()
    if units["benchmark_id"].duplicated().any():
        raise ValueError(
            "An original benchmark ID maps to multiple accessions; "
            "resolve the mapping before preparing a blinded packet."
        )

    if len(units) != 50:
        print(
            f"WARNING: expected 50 benchmark units; found {len(units)}.",
            file=sys.stderr,
        )

    # The reviewer packet deliberately contains no candidate labels or
    # predictions. Existing labels are retained only in a separate key.
    packet_rows = []
    evidence_rows = []
    review_id_by_benchmark = {}

    for number, unit in enumerate(units.to_dict("records"), start=1):
        benchmark_id = unit["benchmark_id"]
        accession = unit["accession"]
        review_id = f"REV{number:03d}"
        review_id_by_benchmark[benchmark_id] = review_id

        evidence = extract_evidence(accession, benchmark_id)
        experiment_rows = extract_experiment_evidence(
            accession, benchmark_id, review_id
        )
        evidence_rows.extend(experiment_rows)

        for endpoint in ENDPOINTS:
            packet_rows.append({
                "review_id": review_id,
                "endpoint": endpoint,
                "review_question": ENDPOINT_GUIDANCE[endpoint],
                **evidence,
                "independent_label": "",
                "reviewer_rationale": "",
                "adjudication_status": "PENDING",
                "reviewer_id_or_initials": "",
                "review_date_YYYY_MM_DD": "",
                "secondary_review_required": "",
            })

    packet = pd.DataFrame(packet_rows)
    experiment_evidence = pd.DataFrame(evidence_rows)

    # A separate comparison key is NOT for the independent reviewer.
    # Keep it sealed until the independent labels have been finalized.
    key_rows = []
    for endpoint in ENDPOINTS:
        old = original[original["field"] == endpoint]
        new = reconciled[reconciled["field"] == endpoint]

        for unit in units.to_dict("records"):
            benchmark_id = unit["benchmark_id"]
            accession = unit["accession"]

            old_rows = old[
                (old["benchmark_id"] == benchmark_id)
                & (old["accession"] == accession)
            ]
            new_rows = new[
                (new["benchmark_id"] == benchmark_id)
                & (new["accession"] == accession)
            ]
            pred_rows = predictions[
                (predictions["benchmark_id"] == benchmark_id)
                & (predictions["accession"] == accession)
            ]

            old_row = old_rows.iloc[0].to_dict() if len(old_rows) else {}
            new_row = new_rows.iloc[0].to_dict() if len(new_rows) else {}
            pred_row = pred_rows.iloc[0].to_dict() if len(pred_rows) else {}

            prediction = (
                pred_row.get("predicted_modality", "")
                if endpoint == "assay_modality"
                else pred_row.get("rna_seq_compatible", "")
            )

            key_rows.append({
                "review_id": review_id_by_benchmark[benchmark_id],
                "benchmark_id": benchmark_id,
                "accession": accession,
                "endpoint": endpoint,
                "original_candidate_label": old_row.get(
                    "candidate_ground_truth", ""
                ),
                "original_field_status": old_row.get("field_status", ""),
                "original_eligibility": old_row.get("scoring_eligibility", ""),
                "reconciled_candidate_label": new_row.get(
                    "candidate_ground_truth", ""
                ),
                "reconciled_field_status": new_row.get("field_status", ""),
                "reconciled_eligibility": new_row.get(
                    "scoring_eligibility", ""
                ),
                "scout_prediction": prediction,
                "independent_label": "",
                "final_comparison_status": "NOT_READY",
            })

    OUTDIR.mkdir(parents=True, exist_ok=True)
    packet_path = OUTDIR / "BLINDED_adjudication_packet.csv"
    key_path = OUTDIR / "SEALED_comparison_key.csv"
    experiment_path = OUTDIR / "BLINDED_experiment_evidence.csv"
    manifest_path = OUTDIR / "packet_manifest.txt"

    packet.to_csv(packet_path, index=False)
    experiment_evidence.to_csv(experiment_path, index=False)
    pd.DataFrame(key_rows).to_csv(key_path, index=False)

    manifest_path.write_text(
        "RNA-Seq Scout independent adjudication packet\n"
        "==============================================\n"
        f"Benchmark units found: {len(units)}\n"
        f"Endpoint rows in blinded packet: {len(packet)}\n"
        f"Endpoints: {', '.join(ENDPOINTS)}\n"
        f"Blinded packet: {packet_path}\n"
        f"Blinded experiment evidence: {experiment_path}\n"
        f"SEALED comparison key: {key_path}\n\n"
        "Reviewer files use pseudonymous review IDs; source metadata may reveal study identity.\n"
        "Never share the sealed comparison key or Scout predictions with the reviewer.\n"
        "Instructions:\n"
        "1. Give the reviewer BOTH BLINDED_adjudication_packet.csv and\n"
        "   BLINDED_experiment_evidence.csv.\n"
        "2. Keep SEALED_comparison_key.csv private until adjudication is finalized.\n"
        "3. Assign labels from source evidence, not from Scout predictions or candidate labels.\n"
        "4. Distinguish experiment-specific evidence from study-level evidence.\n"
        "5. Overlap warning: REV042 is study SRP686131; its cached evidence includes\n"
        "   experiment SRX35199249, also represented separately by REV039.\n"
        "   Do not treat these two review units as independent biological studies.\n"
        "6. Cite evidence and record uncertainty, conflicts, and insufficient evidence.\n"
        "7. Resolve disagreements through a documented second review.\n"
        "8. Only after labels are finalized, join independent labels to the sealed key.\n"
        "9. Do not describe agreement as independent accuracy until adjudication is\n"
        "   independent, documented, and the comparison procedure is frozen.\n\n"
        "This script prepares review materials; it does not validate labels.\n",
        encoding="utf-8",
    )

    print("Independent-adjudication packet created.")
    print(f"Benchmark units: {len(units)}")
    print(f"Blinded endpoint rows: {len(packet)}")
    print(f"Packet: {packet_path}")
    print(f"Experiment evidence: {experiment_path}")
    print(f"SEALED key (do not share with reviewer): {key_path}")
    print(f"Instructions: {manifest_path}")
    print("\nEvidence extraction status:")
    print(packet.groupby("evidence_status")["review_id"].nunique().to_string())
    print("\nNo official benchmark file was changed.")
    print("Independent performance has NOT been computed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
