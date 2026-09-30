from pathlib import Path
from datetime import datetime


APP = Path("rnaseq_nav/ui/app.py")
BACKUP = APP.with_name(
    f"app.py.before-reanalysis-readiness-ui-{datetime.now():%Y%m%d_%H%M%S}"
)


OLD = '''        # --------------------------------------------------
        # Not established
        # --------------------------------------------------

        if not_established:

            st.subheader(
                "Not established"
            )

            for item in not_established:

                clean_item = escape(
                    clean_ui_value(item),
                    quote=True,
                )

                st.html(
                    f"""
<div style="
    margin: 5px 0;
    padding: 7px 10px;
    border-left: 3px solid rgba(128,128,128,0.45);
    line-height: 1.45;
">
    ! {clean_item}
</div>
"""
                )

        # --------------------------------------------------
        # Missing information
        # --------------------------------------------------

        if missing_information:

            st.subheader(
                "Missing information"
            )

            for item in missing_information:

                clean_item = escape(
                    clean_ui_value(item),
                    quote=True,
                )

                st.html(
                    f"""
<div style="
    margin: 5px 0;
    padding: 7px 10px;
    border-left: 3px solid rgba(128,128,128,0.45);
    line-height: 1.45;
">
    ? {clean_item}
</div>
"""
                )
'''

NEW = '''        # --------------------------------------------------
        # Modality-aware design evidence
        # --------------------------------------------------

        readiness_display = reanalysis_readiness_display(
            reanalysis_readiness,
            modality_insight,
        )

        if readiness_display["show_design_gap_evidence"]:

            # --------------------------------------------------
            # Not established
            # --------------------------------------------------

            if not_established:

                st.subheader(
                    "Not established"
                )

                for item in not_established:

                    clean_item = escape(
                        clean_ui_value(item),
                        quote=True,
                    )

                    st.html(
                        f"""
<div style="
    margin: 5px 0;
    padding: 7px 10px;
    border-left: 3px solid rgba(128,128,128,0.45);
    line-height: 1.45;
">
    ! {clean_item}
</div>
"""
                    )

            # --------------------------------------------------
            # Missing information
            # --------------------------------------------------

            if missing_information:

                st.subheader(
                    "Missing information"
                )

                for item in missing_information:

                    clean_item = escape(
                        clean_ui_value(item),
                        quote=True,
                    )

                    st.html(
                        f"""
<div style="
    margin: 5px 0;
    padding: 7px 10px;
    border-left: 3px solid rgba(128,128,128,0.45);
    line-height: 1.45;
">
    ? {clean_item}
</div>
"""
                    )

        elif readiness_display["explanation"]:

            st.info(
                readiness_display["explanation"]
            )
'''


def main():
    if not APP.exists():
        raise SystemExit(
            f"ERROR: {APP} does not exist."
        )

    text = APP.read_text()

    if OLD not in text:
        raise SystemExit(
            "ERROR: Expected Reanalysis Readiness evidence block "
            "was not found. No changes were made."
        )

    if "reanalysis_readiness_display(" in text:
        raise SystemExit(
            "ERROR: Reanalysis readiness UI refinement appears "
            "to have already been applied. No changes were made."
        )

    BACKUP.write_text(text)

    updated = text.replace(OLD, NEW, 1)

    APP.write_text(updated)

    print(f"Backup created: {BACKUP}")
    print(f"Updated: {APP}")


if __name__ == "__main__":
    main()
