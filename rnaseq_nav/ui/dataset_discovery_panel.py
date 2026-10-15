"""Streamlit interface for public sequencing dataset discovery."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from rnaseq_nav.discovery.dataset_discovery import DatasetDiscovery


def _nested_value(record: Any, *path: str) -> str:
    """Read a nested metadata value safely for display."""
    value = record
    for name in path:
        if value is None:
            return ""
        value = getattr(value, name, None)

    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return str(value).strip()

    return ""


def _metadata_to_row(metadata: Any) -> dict[str, str]:
    """Convert a discovery result to a predictable table row."""
    run = _nested_value(metadata, "run", "accession")
    experiment = _nested_value(metadata, "experiment", "accession")

    return {
        "Run accession": run or experiment,
        "Study accession": _nested_value(metadata, "study", "accession"),
        "Project accession": _nested_value(metadata, "project", "accession"),
        "Organism": (
            _nested_value(metadata, "organism")
            or _nested_value(metadata, "study", "organism")
        ),
        "Title": (
            _nested_value(metadata, "experiment", "title")
            or _nested_value(metadata, "title")
        ),
        "Layout": _nested_value(metadata, "experiment", "layout"),
        "Platform": _nested_value(metadata, "experiment", "platform"),
        "Library source": _nested_value(
            metadata, "experiment", "library_source"
        ),
        "Library selection": _nested_value(
            metadata, "experiment", "library_selection"
        ),
    }


def render_dataset_discovery_panel(st: Any, email: str) -> None:
    """Render the discovery form and its results in the Streamlit app."""
    st.divider()
    st.subheader("Discover public sequencing datasets")
    st.caption(
        "Search public SRA records by organism and sequencing strategy, "
        "then narrow the results using the available experiment metadata."
    )

    with st.form("dataset_discovery_search_form"):
        organism = st.text_input(
            "Organism",
            value="Homo sapiens",
            help="Use an organism name such as Homo sapiens or Mus musculus.",
        )

        strategy = st.text_input(
            "Sequencing strategy",
            value="RNA-Seq",
            help="This value is passed to the existing discovery backend.",
        )

        col1, col2 = st.columns(2)
        with col1:
            max_results = st.number_input(
                "Maximum records to retrieve",
                min_value=1,
                max_value=100,
                value=20,
                step=1,
            )
        with col2:
            diversity = st.selectbox(
                "Result diversity",
                options=["project", "study", "run"],
                index=0,
                format_func=lambda value: {
                    "project": "One best record per project",
                    "study": "One record per study",
                    "run": "Keep individual records",
                }[value],
            )

        st.markdown("**Optional exact-match filters**")
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            layout = st.text_input(
                "Layout",
                placeholder="e.g. PAIRED",
                help="Leave blank to include all layouts.",
            )
            platform = st.text_input(
                "Platform",
                placeholder="e.g. ILLUMINA",
                help="Leave blank to include all platforms.",
            )

        with filter_col2:
            source = st.text_input(
                "Library source",
                placeholder="e.g. TRANSCRIPTOMIC",
                help="Leave blank to include all library sources.",
            )
            selection = st.text_input(
                "Library selection",
                placeholder="e.g. cDNA",
                help="Leave blank to include all selection methods.",
            )

        submitted = st.form_submit_button(
            "Search datasets",
            type="primary",
            width="stretch",
        )

    if submitted:
        if not organism.strip():
            st.error("Enter an organism before searching.")
            return

        if not strategy.strip():
            st.error("Enter a sequencing strategy before searching.")
            return

        try:
            discovery = DatasetDiscovery(email=email)
            results = discovery.search(
                organism=organism.strip(),
                strategy=strategy.strip(),
                layout=layout.strip() or None,
                platform=platform.strip() or None,
                source=source.strip() or None,
                selection=selection.strip() or None,
                max_results=int(max_results),
                diversity=diversity,
            )
            st.session_state["dataset_discovery_rows"] = [
                _metadata_to_row(item) for item in results
            ]
            st.session_state["dataset_discovery_error"] = None
            st.session_state["dataset_discovery_query"] = {
                "organism": organism.strip(),
                "strategy": strategy.strip(),
            }

        except Exception as exc:
            st.session_state["dataset_discovery_rows"] = None
            st.session_state["dataset_discovery_error"] = (
                f"{type(exc).__name__}: {exc}"
            )

    error = st.session_state.get("dataset_discovery_error")
    if error:
        st.error(
            "Dataset search failed. Check the search inputs and NCBI "
            f"connectivity, then try again. Details: {error}"
        )
        return

    rows = st.session_state.get("dataset_discovery_rows")
    if rows is None:
        return

    query = st.session_state.get("dataset_discovery_query", {})
    st.markdown(
        f"**Results for {query.get('organism', '')} — "
        f"{query.get('strategy', '')}**"
    )

    if not rows:
        st.info(
            "No records matched these filters. Try clearing optional filters "
            "or increasing the retrieval limit."
        )
        return

    st.success(f"Found {len(rows)} matching record(s).")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

    st.download_button(
        "Download results as CSV",
        data=output.getvalue(),
        file_name="rnaseq_scout_dataset_discovery.csv",
        mime="text/csv",
    )
