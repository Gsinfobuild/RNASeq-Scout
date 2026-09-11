import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RESULTS_FILE = (
    ROOT / "benchmark" / "results" / "benchmark_results.csv"
)

EVIDENCE_DIR = (
    ROOT / "benchmark" / "evidence"
)

OUTPUT_FILE = (
    ROOT / "benchmark" / "results" / "benchmark_audit.csv"
)


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def load_results():
    with RESULTS_FILE.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def load_evidence(accession):
    path = EVIDENCE_DIR / f"{accession}.json"

    if not path.exists():
        return None

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def add_flag(flags, code, description):
    flags.append(
        f"{code}: {description}"
    )


def audit_case(row, evidence):

    accession = clean(row["accession"])
    accession_type = clean(row["accession_type"])
    category = clean(row["candidate_category"])

    modality = clean(row["predicted_modality"])
    compatibility = clean(
        row["compatibility_status"]
    )
    suitability = clean(row["suitability"])
    readiness = clean(
        row["reanalysis_readiness"]
    )

    expected_modality = clean(
        row["candidate_expected_modality"]
    )

    expected_compatibility = clean(
        row["candidate_expected_compatibility"]
    )

    flags = []

    # ======================================================
    # Extract actual production prediction
    # ======================================================

    if evidence is None:

        add_flag(
            flags,
            "E001",
            "Evidence JSON file is missing",
        )

        scout = {}

    else:

        scout = evidence.get(
            "scout_prediction",
            {},
        )

        if not isinstance(scout, dict):

            add_flag(
                flags,
                "E002",
                "scout_prediction is missing or invalid",
            )

            scout = {}

    # ======================================================
    # Extract production-layer objects
    # ======================================================

    modality_obj = scout.get(
        "modality_insight",
        {},
    )

    design_obj = scout.get(
        "design_insight",
        {},
    )

    suitability_obj = scout.get(
        "suitability_insight",
        {},
    )

    readiness_obj = scout.get(
        "reanalysis_readiness",
        {},
    )

    landscape_obj = scout.get(
        "study_experimental_landscape",
        None,
    )

    # ======================================================
    # 1. Modality / compatibility consistency
    # ======================================================

    serialized_compatibility = clean(
        modality_obj.get(
            "compatibility_status"
        )
        if isinstance(modality_obj, dict)
        else ""
    )

    if (
        serialized_compatibility
        and serialized_compatibility != compatibility
    ):

        add_flag(
            flags,
            "M001",
            (
                "CSV compatibility status differs from "
                "serialized modality insight"
            ),
        )

    if (
        compatibility == "Not compatible"
        and "Not suitable" not in suitability
    ):

        add_flag(
            flags,
            "M002",
            (
                "Explicitly incompatible modality does not "
                "lead to RNA-seq unsuitability"
            ),
        )

    if (
        compatibility == "Specialized workflow"
        and "Not suitable" not in suitability
    ):

        add_flag(
            flags,
            "M003",
            (
                "Specialized RNA workflow is not gated from "
                "conventional RNA-seq suitability"
            ),
        )

    if (
        compatibility == "Uncertain"
        and "compatibility uncertain"
        not in suitability.lower()
    ):

        add_flag(
            flags,
            "M004",
            (
                "Uncertain modality compatibility is not "
                "reflected in suitability"
            ),
        )

    if (
        compatibility == "Uncertain"
        and readiness != "Insufficient evidence"
    ):

        add_flag(
            flags,
            "M005",
            (
                "Uncertain modality compatibility does not "
                "propagate to insufficient readiness"
            ),
        )

    # ======================================================
    # 2. Benchmark expectation consistency
    # ======================================================

    if expected_compatibility:

        if (
            expected_compatibility.lower()
            not in compatibility.lower()
        ):

            add_flag(
                flags,
                "B001",
                (
                    "Scout compatibility differs from "
                    "candidate registry expectation: "
                    f"expected '{expected_compatibility}', "
                    f"observed '{compatibility}'"
                ),
            )

    # ======================================================
    # 3. Study-level landscape
    # ======================================================

    if (
        accession_type in {"SRP", "ERP", "DRP"}
        and category == "mixed_assay_study"
    ):

        if not isinstance(
            landscape_obj,
            dict,
        ):

            add_flag(
                flags,
                "S001",
                "Mixed study lacks experimental landscape",
            )

        else:

            assay_counts = landscape_obj.get(
                "assay_family_counts",
                {},
            )

            if len(assay_counts) < 2:

                add_flag(
                    flags,
                    "S002",
                    (
                        "Benchmark identifies the study as "
                        "mixed, but fewer than two assay "
                        "families were observed"
                    ),
                )

            if readiness not in {
                "Conditionally reusable",
                "Exploratory use only",
                "Insufficient evidence",
                "Not suitable",
            }:

                add_flag(
                    flags,
                    "S003",
                    (
                        "Mixed study has an unexpected "
                        "reanalysis-readiness verdict"
                    ),
                )

    # ======================================================
    # 4. Reanalysis evidence-state consistency
    # ======================================================

    if not isinstance(
        readiness_obj,
        dict,
    ):

        add_flag(
            flags,
            "E003",
            "Reanalysis readiness object is unavailable",
        )

    else:

        observed = readiness_obj.get(
            "observed_evidence",
            [],
        )

        inferred = readiness_obj.get(
            "inferred_evidence",
            [],
        )

        not_established = readiness_obj.get(
            "not_established",
            [],
        )

        missing = readiness_obj.get(
            "missing_information",
            [],
        )

        observed_lower = {
            clean(x).lower()
            for x in observed
        }

        inferred_lower = {
            clean(x).lower()
            for x in inferred
        }

        not_established_lower = {
            clean(x).lower()
            for x in not_established
        }

        # --------------------------------------------------
        # Same evidence cannot simultaneously be observed
        # and not established.
        # --------------------------------------------------

        overlap = (
            observed_lower
            & not_established_lower
        )

        if overlap:

            add_flag(
                flags,
                "E004",
                (
                    "Evidence appears simultaneously as "
                    "observed and not established"
                ),
            )

        # --------------------------------------------------
        # Same evidence cannot simultaneously be observed
        # and inferred.
        # --------------------------------------------------

        overlap = (
            observed_lower
            & inferred_lower
        )

        if overlap:

            add_flag(
                flags,
                "E005",
                (
                    "Evidence appears simultaneously as "
                    "observed and inferred"
                ),
            )

        # --------------------------------------------------
        # Insufficient readiness should have an explicit
        # limitation.
        # --------------------------------------------------

        if (
            readiness == "Insufficient evidence"
            and not (
                not_established
                or missing
            )
        ):

            add_flag(
                flags,
                "E006",
                (
                    "Insufficient readiness has no explicit "
                    "not-established or missing evidence"
                ),
            )

    # ======================================================
    # 5. Suitability serialization consistency
    # ======================================================

    serialized_suitability = clean(
        suitability_obj.get(
            "overall"
        )
        if isinstance(
            suitability_obj,
            dict,
        )
        else ""
    )

    if (
        serialized_suitability
        and serialized_suitability != suitability
    ):

        add_flag(
            flags,
            "U001",
            (
                "CSV suitability differs from serialized "
                "suitability insight"
            ),
        )

    # ======================================================
    # 6. Design-layer scientific audit
    # ======================================================

    condition = clean(
        row["condition"]
    )

    control = clean(
        row["control"]
    )

    treatment = clean(
        row["treatment"]
    )

    replicate = clean(
        row["replicate_information"]
    )

    serialized_condition = clean(
        design_obj.get("condition")
        if isinstance(design_obj, dict)
        else ""
    )

    serialized_treatment = clean(
        design_obj.get("treatment")
        if isinstance(design_obj, dict)
        else ""
    )

    serialized_replicate = clean(
        design_obj.get(
            "replicate_information"
        )
        if isinstance(design_obj, dict)
        else ""
    )

    # ------------------------------------------------------
    # CSV versus production serialization
    # ------------------------------------------------------

    if (
        condition
        and serialized_condition
        and condition != serialized_condition
    ):

        add_flag(
            flags,
            "D001",
            (
                "CSV condition differs from serialized "
                "design insight"
            ),
        )

    if (
        treatment
        and serialized_treatment
        and treatment != serialized_treatment
    ):

        add_flag(
            flags,
            "D002",
            (
                "CSV treatment differs from serialized "
                "design insight"
            ),
        )

    if (
        replicate
        and serialized_replicate
        and replicate != serialized_replicate
    ):

        add_flag(
            flags,
            "D003",
            (
                "CSV replicate information differs from "
                "serialized design insight"
            ),
        )

    # ------------------------------------------------------
    # Scientific concern:
    #
    # A complete experiment title appearing identically
    # as both condition and treatment may indicate that
    # title/context was promoted to treatment assignment.
    # ------------------------------------------------------

    if (
        condition
        and treatment
        and condition == treatment
    ):

        add_flag(
            flags,
            "D004",
            (
                "Condition and treatment are identical; "
                "possible title-as-treatment overinterpretation"
            ),
        )

    # ------------------------------------------------------
    # Generic replicate labels must preserve unresolved
    # biological-versus-technical status.
    # ------------------------------------------------------

    if (
        replicate
        and "biological or technical"
        in replicate.lower()
    ):

        found_unresolved = False

        if isinstance(
            readiness_obj,
            dict,
        ):

            not_established = readiness_obj.get(
                "not_established",
                [],
            )

            found_unresolved = any(
                "biological versus technical replicate"
                in clean(x).lower()
                for x in not_established
            )

        if not found_unresolved:

            add_flag(
                flags,
                "D005",
                (
                    "Generic replicate label does not "
                    "propagate unresolved biological/technical "
                    "replicate status"
                ),
            )

    # ======================================================
    # 7. Run / evidence consistency
    # ======================================================

    metadata_obj = scout.get(
        "metadata",
        {},
    )

    run_obj = (
        metadata_obj.get("run", {})
        if isinstance(
            metadata_obj,
            dict,
        )
        else {}
    )

    if isinstance(
        run_obj,
        dict,
    ):

        total_spots = run_obj.get(
            "total_spots"
        )

        total_bases = run_obj.get(
            "total_bases"
        )

        run_accession = clean(
            run_obj.get("accession")
        )

        # The presence of sequencing quantity is valid
        # evidence even when the accession itself is absent.
        if (
            total_spots
            or total_bases
        ):

            readiness_observed = []

            if isinstance(
                readiness_obj,
                dict,
            ):
                readiness_observed = [
                    clean(x).lower()
                    for x in readiness_obj.get(
                        "observed_evidence",
                        [],
                    )
                ]

            has_run_evidence = any(
                "sequencing run information"
                in x
                for x in readiness_observed
            )

            if not has_run_evidence:

                add_flag(
                    flags,
                    "R001",
                    (
                        "Run quantity metadata are available "
                        "but sequencing-run evidence is not "
                        "propagated to readiness"
                    ),
                )

    # ======================================================
    # 8. Final audit status
    # ======================================================

    if not flags:

        audit_status = "PASS"
        severity = "PASS"

    else:

        audit_status = "REVIEW"

        high_codes = {
            "E001",
            "E002",
            "E004",
            "E005",
            "M002",
            "M003",
            "M005",
            "B001",
            "S001",
            "S002",
            "D005",
        }

        if any(
            flag.split(":")[0]
            in high_codes
            for flag in flags
        ):

            severity = "HIGH"

        else:

            severity = "MEDIUM"

    return {
        "accession": accession,
        "accession_type": accession_type,
        "candidate_category": category,
        "audit_status": audit_status,
        "severity": severity,
        "predicted_modality": modality,
        "compatibility_status": compatibility,
        "suitability": suitability,
        "reanalysis_readiness": readiness,
        "expected_modality": expected_modality,
        "expected_compatibility": expected_compatibility,
        "flags": " | ".join(flags),
    }


def main():

    if not RESULTS_FILE.exists():

        raise SystemExit(
            f"Missing benchmark results: {RESULTS_FILE}"
        )

    rows = load_results()

    if len(rows) != 13:

        raise SystemExit(
            f"Expected 13 benchmark results, found {len(rows)}"
        )

    audits = []

    for row in rows:

        accession = clean(
            row["accession"]
        )

        evidence = load_evidence(
            accession
        )

        audits.append(
            audit_case(
                row,
                evidence,
            )
        )

    fields = [
        "accession",
        "accession_type",
        "candidate_category",
        "audit_status",
        "severity",
        "predicted_modality",
        "compatibility_status",
        "suitability",
        "reanalysis_readiness",
        "expected_modality",
        "expected_compatibility",
        "flags",
    ]

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(audits)

    passed = sum(
        x["audit_status"] == "PASS"
        for x in audits
    )

    review = len(audits) - passed

    high = sum(
        x["severity"] == "HIGH"
        for x in audits
    )

    print()
    print("==============================================")
    print("RNASeq Scout — Benchmark Audit")
    print("==============================================")
    print(f"Cases audited : {len(audits)}")
    print(f"PASS          : {passed}")
    print(f"REVIEW        : {review}")
    print(f"HIGH severity : {high}")
    print()
    print("Case summary:")
    print("----------------------------------------------")

    for audit in audits:

        print(
            f"{audit['accession']}: "
            f"{audit['audit_status']} | "
            f"{audit['severity']}"
        )

        if audit["flags"]:

            print(
                f"    {audit['flags']}"
            )

    print("----------------------------------------------")
    print(
        f"Audit CSV: {OUTPUT_FILE}"
    )
    print()


if __name__ == "__main__":
    main()
