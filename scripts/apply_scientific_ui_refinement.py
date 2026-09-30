#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]

APP = ROOT / "rnaseq_nav" / "ui" / "app.py"
HELPER = ROOT / "rnaseq_nav" / "ui" / "evidence_presentation.py"
TEST = ROOT / "tests" / "test_evidence_presentation.py"


def replace_once(text, old, new, label):
    count = text.count(old)

    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly 1 match, found {count}"
        )

    return text.replace(old, new, 1)


def backup(path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = path.with_name(
        f"{path.name}.before-scientific-ui-{timestamp}"
    )

    shutil.copy2(path, backup_path)

    return backup_path


def main():

    if not APP.exists():
        raise RuntimeError(f"Required file not found: {APP}")

    app = APP.read_text(encoding="utf-8")

    # ======================================================
    # 1. Add presentation helper import
    # ======================================================

    import_anchor = (
        "from rnaseq_nav.usage.tracker import UsageTracker\n"
    )

    helper_import = (
        "from rnaseq_nav.ui.evidence_presentation import (\n"
        "    analysis_plan_display,\n"
        "    experimental_design_display,\n"
        "    inspection_summary_planning_value,\n"
        ")\n"
    )

    if helper_import not in app:

        app = replace_once(
            app,
            import_anchor,
            import_anchor + helper_import,
            "presentation helper import",
        )

    # ======================================================
    # 2. Inspection Summary
    # ======================================================

    old = '''    planning_confidence = clean_ui_value(
        get_value(
            analysis_plan,
            "confidence",
        )
    )
'''

    new = '''    planning_confidence = inspection_summary_planning_value(
        analysis_plan,
        modality_insight,
    )
'''

    app = replace_once(
        app,
        old,
        new,
        "inspection summary planning value",
    )

    # ======================================================
    # 3. Experimental Design: modality-aware status
    # ======================================================

    old = '''    if design_insight is not None:

        design_confidence = clean_ui_value(
            get_value(
                design_insight,
                "design_confidence",
                "",
            )
        )
'''

    new = '''    if design_insight is not None:

        design_display = experimental_design_display(
            modality_insight,
        )

        design_not_applicable = (
            design_display["show_design_warnings"] is False
        )

        if design_not_applicable:
            st.info(
                design_display["interpretation"]
            )

        design_confidence = (
            design_display["status"]
            if design_not_applicable
            else clean_ui_value(
                get_value(
                    design_insight,
                    "design_confidence",
                    "",
                )
            )
        )
'''

    app = replace_once(
        app,
        old,
        new,
        "experimental design presentation",
    )

    # ======================================================
    # 4. Experimental Design: warnings
    #
    # Use the unique surrounding section rather than the
    # generic "if warnings:" construct.
    # ======================================================

    old = '''        # --------------------------------------------------
        # Warnings
        # --------------------------------------------------

        warnings = get_value(
            design_insight,
            "warnings",
            [],
        )

        if warnings:

            st.subheader(
                "Design warnings"
            )
'''

    new = '''        # --------------------------------------------------
        # Warnings
        # --------------------------------------------------

        warnings = get_value(
            design_insight,
            "warnings",
            [],
        )

        if warnings and not design_not_applicable:

            st.subheader(
                "Design warnings"
            )
'''

    app = replace_once(
        app,
        old,
        new,
        "experimental design warning gate",
    )

    # ======================================================
    # 5. Experimental Design: missing information
    # ======================================================

    old = '''        # --------------------------------------------------
        # Missing information
        # --------------------------------------------------

        missing_information = get_value(
            design_insight,
            "missing_information",
            [],
        )

        if missing_information:

            st.subheader(
                "Information not established"
            )
'''

    new = '''        # --------------------------------------------------
        # Missing information
        # --------------------------------------------------

        missing_information = get_value(
            design_insight,
            "missing_information",
            [],
        )

        if (
            missing_information
            and not design_not_applicable
        ):

            st.subheader(
                "Information not established"
            )
'''

    app = replace_once(
        app,
        old,
        new,
        "experimental design missing-information gate",
    )

    # ======================================================
    # 6. Analysis Plan: applicability-aware status
    # ======================================================

    old = '''        confidence = clean_ui_value(
            get_value(
                analysis_plan,
                "confidence",
            )
        )

        st.metric(
            "Planning confidence",
            confidence,
        )
'''

    new = '''        plan_display = analysis_plan_display(
            analysis_plan,
            modality_insight,
        )

        st.metric(
            plan_display["label"],
            plan_display["value"],
        )

        if plan_display["explanation"]:
            st.caption(
                plan_display["explanation"]
            )
'''

    app = replace_once(
        app,
        old,
        new,
        "analysis plan applicability presentation",
    )

    # ======================================================
    # 7. Presentation helper
    # ======================================================

    helper_source = '''"""Evidence-aware presentation helpers for RNA-Seq Scout."""

from __future__ import annotations


def is_rna_seq_compatible(modality_insight):
    """Return backend RNA-seq compatibility without inference."""

    if modality_insight is None:
        return None

    value = getattr(
        modality_insight,
        "rna_seq_compatible",
        None,
    )

    if value is True:
        return True

    if value is False:
        return False

    return None


def experimental_design_display(modality_insight):
    """Return modality-aware experimental-design presentation state."""

    compatible = is_rna_seq_compatible(
        modality_insight
    )

    if compatible is False:
        return {
            "status": "Not applicable",
            "interpretation": (
                "Experimental-design fields used for conventional "
                "RNA-seq analysis are not assessed for this "
                "sequencing modality."
            ),
            "show_design_warnings": False,
            "show_missing_information": False,
        }

    if compatible is True:
        return {
            "status": "Assessing available metadata",
            "interpretation": "",
            "show_design_warnings": True,
            "show_missing_information": True,
        }

    return {
        "status": "Insufficient information",
        "interpretation": (
            "RNA-seq compatibility could not be established, "
            "so experimental-design assessment remains conservative."
        ),
        "show_design_warnings": True,
        "show_missing_information": True,
    }


def analysis_plan_display(
    analysis_plan,
    modality_insight,
):
    """Separate analysis-plan applicability from confidence."""

    compatible = is_rna_seq_compatible(
        modality_insight
    )

    workflow = str(
        getattr(
            analysis_plan,
            "workflow",
            "",
        ) or ""
    ).strip()

    if (
        compatible is False
        or "not applicable" in workflow.lower()
    ):
        return {
            "label": "Planning status",
            "value": "Not applicable",
            "explanation": (
                "No conventional RNA-seq analysis plan is "
                "applicable to the identified sequencing modality."
            ),
        }

    confidence = str(
        getattr(
            analysis_plan,
            "confidence",
            "",
        ) or ""
    ).strip()

    return {
        "label": "Planning confidence",
        "value": confidence or "Not established",
        "explanation": "",
    }


def inspection_summary_planning_value(
    analysis_plan,
    modality_insight,
):
    """Return compact planning value for Inspection Summary."""

    return analysis_plan_display(
        analysis_plan,
        modality_insight,
    )["value"]
'''

    # ======================================================
    # 8. Focused regression tests
    # ======================================================

    test_source = '''from types import SimpleNamespace


from rnaseq_nav.ui.evidence_presentation import (
    analysis_plan_display,
    experimental_design_display,
    inspection_summary_planning_value,
)


def modality(compatible):
    return SimpleNamespace(
        rna_seq_compatible=compatible
    )


def plan(
    workflow="RNA-seq analysis",
    confidence="Moderate",
):
    return SimpleNamespace(
        workflow=workflow,
        confidence=confidence,
    )


def test_non_rna_seq_design_is_not_applicable():

    result = experimental_design_display(
        modality(False)
    )

    assert result["status"] == "Not applicable"
    assert result["show_design_warnings"] is False
    assert result["show_missing_information"] is False


def test_rna_seq_design_remains_assessable():

    result = experimental_design_display(
        modality(True)
    )

    assert result["status"] == (
        "Assessing available metadata"
    )
    assert result["show_design_warnings"] is True
    assert result["show_missing_information"] is True


def test_unknown_modality_is_conservative():

    result = experimental_design_display(
        modality(None)
    )

    assert result["status"] == "Insufficient information"
    assert result["show_design_warnings"] is True
    assert result["show_missing_information"] is True


def test_non_rna_seq_plan_is_not_applicable():

    result = analysis_plan_display(
        plan(
            workflow="RNA-seq workflow not applicable",
            confidence="High",
        ),
        modality(False),
    )

    assert result["label"] == "Planning status"
    assert result["value"] == "Not applicable"


def test_rna_seq_plan_retains_confidence():

    result = analysis_plan_display(
        plan(),
        modality(True),
    )

    assert result["label"] == "Planning confidence"
    assert result["value"] == "Moderate"


def test_inspection_summary_uses_applicability():

    result = inspection_summary_planning_value(
        plan(
            workflow="RNA-seq workflow not applicable",
            confidence="High",
        ),
        modality(False),
    )

    assert result == "Not applicable"
'''

    # ======================================================
    # 9. Backup and write
    # ======================================================

    backup_path = backup(APP)

    HELPER.write_text(
        helper_source,
        encoding="utf-8",
    )

    TEST.write_text(
        test_source,
        encoding="utf-8",
    )

    APP.write_text(
        app,
        encoding="utf-8",
    )

    print("Migration completed successfully.")
    print(f"Backup:  {backup_path}")
    print(f"Updated: {APP}")
    print(f"Added:   {HELPER}")
    print(f"Added:   {TEST}")


if __name__ == "__main__":
    main()
