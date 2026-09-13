"""
RNASeq Scout
Streamlit User Interface
Version 1.2

Purpose
-------
Provides a clean web interface for inspecting SRA accessions
through the RNASeq Scout API.

Supported accessions
--------------------
SRR...
SRX...
ERR...
ERX...
DRR...
DRX...

Exports
-------
JSON
PDF
"""

# ==========================================================
# Standard Library
# ==========================================================

import sys
import json
import os
import re

from pathlib import Path
from dataclasses import asdict, is_dataclass
from io import BytesIO
from html import escape, unescape


# ==========================================================
# Make project root importable
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ==========================================================
# Third-party
# ==========================================================

import streamlit as st


# ==========================================================
# UI ACCESSIBILITY AND TYPOGRAPHY
# ==========================================================

st.markdown(
    """
    <style>

    /* ------------------------------------------------------
       Global typography
       ------------------------------------------------------ */

    html,
    body,
    [class*="css"] {
        font-size: 16px;
    }

    .stApp {
        font-size: 16px;
    }

    /* ------------------------------------------------------
       Main content
       ------------------------------------------------------ */

    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 1500px !important;
        width: calc(100% - 2rem) !important;
        margin-left: auto !important;
        margin-right: auto !important;
        min-height: calc(100vh - 1rem);
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
    }

    /* ------------------------------------------------------
       Section headings
       ------------------------------------------------------ */

    h1 {
        font-size: 2.2rem !important;
        line-height: 1.25 !important;
        font-weight: 700 !important;
    }

    h2 {
        font-size: 1.55rem !important;
        line-height: 1.3 !important;
        font-weight: 700 !important;
        margin-top: 1.5rem !important;
    }

    h3 {
        font-size: 1.2rem !important;
        line-height: 1.35 !important;
        font-weight: 650 !important;
    }

    /* ------------------------------------------------------
       Normal Streamlit text
       ------------------------------------------------------ */

    p,
    li,
    label,
    .stMarkdown,
    .stText,
    .stCaption {
        font-size: 16px;
        line-height: 1.55;
    }

    /* Streamlit theme-aware text colour */
    p,
    li,
    label,
    .stMarkdown,
    .stText,
    .stCaption,
    .stMetric label,
    .stMetric [data-testid="stMetricValue"] {
        color: var(--text-color) !important;
    }

    /* ------------------------------------------------------
       Metadata cards
       ------------------------------------------------------ */

    .metadata-card {
        background: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.28) !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        margin: 7px 0 !important;
        min-height: 70px !important;
        box-sizing: border-box !important;
    }

    .metadata-card .small-label {
        color: var(--text-color) !important;
        opacity: 0.72 !important;
        font-size: 13px !important;
        line-height: 1.3 !important;
        font-weight: 600 !important;
        margin-bottom: 6px !important;
    }

    .metadata-card .small-value {
        color: var(--text-color) !important;
        font-size: 16px !important;
        line-height: 1.45 !important;
        font-weight: 500 !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }

    /* ------------------------------------------------------
       Metrics
       ------------------------------------------------------ */

    [data-testid="stMetric"] {
        background: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 10px !important;
        padding: 12px 14px !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
        opacity: 0.78 !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 22px !important;
        line-height: 1.25 !important;
        font-weight: 700 !important;
        color: var(--text-color) !important;
    }

    /* ------------------------------------------------------
       Text input
       ------------------------------------------------------ */

    div[data-baseweb="input"] input {
        font-size: 17px !important;
        color: var(--text-color) !important;
    }

    div[data-baseweb="input"] {
        background: var(--secondary-background-color) !important;
    }

    /* ------------------------------------------------------
       Buttons
       ------------------------------------------------------ */

    .stButton > button,
    .stDownloadButton > button {
        font-size: 15px !important;
        font-weight: 600 !important;
        min-height: 42px !important;
        padding: 8px 18px !important;
    }

    /* ------------------------------------------------------
       Expander
       ------------------------------------------------------ */

    [data-testid="stExpander"] {
        border-color: rgba(128, 128, 128, 0.28) !important;
    }

    [data-testid="stExpander"] summary {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: var(--text-color) !important;
    }

    /* ------------------------------------------------------
       Captions / secondary information
       ------------------------------------------------------ */

    [data-testid="stCaptionContainer"] {
        font-size: 14px !important;
        line-height: 1.45 !important;
    }

    /* ------------------------------------------------------
       Code / structured output
       ------------------------------------------------------ */

    pre,
    code {
        font-size: 14px !important;
        line-height: 1.5 !important;
    }

    /* ------------------------------------------------------
       Links
       ------------------------------------------------------ */

    a {
        font-size: inherit;
    }

    /* ------------------------------------------------------
       Improve readability on smaller screens
       ------------------------------------------------------ */

    @media (max-width: 768px) {

        h1 {
            font-size: 1.8rem !important;
        }

        h2 {
            font-size: 1.35rem !important;
        }

        h3 {
            font-size: 1.1rem !important;
        }

        p,
        li,
        .stMarkdown,
        .stText {
            font-size: 15px;
        }

        .metadata-card .small-value {
            font-size: 15px !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 19px !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)




# ==========================================================
# RNASeq Scout
# ==========================================================

from rnaseq_nav import RNASeqNavigator
from rnaseq_nav.usage.tracker import UsageTracker


# ==========================================================
# Experimental Design UI Helpers
# ==========================================================

def _design_evidence_status(value):
    """
    Convert a Layer 2 design value into a conservative
    presentation status.

    The GUI must not invent evidence states that are not
    represented by the backend. A populated design field
    therefore receives the neutral status
    'Established from available metadata', while an empty
    field is explicitly shown as 'Not established'.
    """

    value = clean_ui_value(value)

    if not value or value == "—":
        return "Not established"

    return "Established from available metadata"


def _render_design_card(
    label,
    value,
    *,
    long=False,
):
    """
    Render one experimental-design finding together with
    its evidence status.

    This is presentation-only. It does not perform any
    scientific inference.
    """

    display_value = clean_ui_value(value)

    if not display_value:
        display_value = "Not established"

    status = _design_evidence_status(
        value
    )

    value_html = escape(
        display_value,
        quote=True,
    )

    status_html = escape(
        status,
        quote=True,
    )

    height = "118px" if long else "108px"

    st.html(
        f"""
<div style="
    border: 1px solid #d9e2ec;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    background: #ffffff;
    min-height: {height};
    box-sizing: border-box;
">
    <div style="
        font-size: 0.78rem;
        color: #58708f;
        margin-bottom: 7px;
    ">
        {escape(label, quote=True)}
    </div>

    <div style="
        font-size: 1.02rem;
        font-weight: 650;
        color: #102a56;
        line-height: 1.35;
        margin-bottom: 9px;
    ">
        {value_html}
    </div>

    <div style="
        font-size: 0.73rem;
        color: #58708f;
    ">
        Evidence status: <strong>{status_html}</strong>
    </div>
</div>
        """
    )


# ==========================================================
# HTML Rendering Helper
# ==========================================================

def render_html(html):
    """
    Render custom HTML without Markdown treating indentation
    as a code block.
    """
    lines = html.strip().splitlines()
    cleaned = "\n".join(line.strip() for line in lines)
    st.markdown(cleaned, unsafe_allow_html=True)



# ==========================================================
# Page Configuration
# ==========================================================

st.set_page_config(
    page_title="RNASeq Scout",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# Global UI Styling
# ==========================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL APPLICATION
       ====================================================== */

    .stApp {
        background: #ffffff;
        color: #102a56;
    }

    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 1rem !important;
        max-width: 1500px !important;
        width: calc(100% - 2rem) !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Improve readability in both Streamlit themes */
    html, body, [class*="css"] {
        font-family: "Segoe UI", Arial, sans-serif;
    }

    /* ======================================================
       TOP BRAND HEADER
       ====================================================== */

    .rna-header {
        width: 100%;
        min-height: 105px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 24px;
        box-sizing: border-box;
        background: linear-gradient(
            90deg,
            #edf6ff 0%,
            #ffffff 50%,
            #f7fbff 100%
        );
        border-bottom: 1px solid #d8e6f5;
        margin-bottom: 20px;
    }

    .rna-brand {
        display: flex;
        align-items: center;
        gap: 14px;
        min-width: 430px;
    }

    .rna-logo {
        width: 62px;
        height: 76px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .rna-brand-text {
        line-height: 1.05;
    }

    .rna-title {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.8px;
        color: #1260bd;
        white-space: nowrap;
    }

    .rna-title-green {
        color: #348545;
    }

    .rna-tagline {
        margin-top: 7px;
        font-size: 0.95rem;
        color: #315a8f;
        letter-spacing: 0.15px;
    }

    .rna-tagline span {
        margin: 0 7px;
        color: #6f91b7;
    }

    .rna-gateway {
        flex: 1;
        text-align: center;
        font-size: 1.15rem;
        color: #204d82;
        white-space: nowrap;
    }

    .rna-impact {
        display: flex;
        align-items: center;
        gap: 13px;
        min-width: 175px;
        justify-content: flex-end;
    }

    .rna-impact-divider {
        width: 1px;
        height: 75px;
        background: #b7c8da;
    }

    .rna-leaf {
        font-size: 3.4rem;
        line-height: 1;
        color: #399447;
        transform: rotate(-15deg);
    }

    .rna-impact-text {
        font-size: 0.92rem;
        line-height: 1.45;
        color: #102a56;
        font-weight: 500;
    }

    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #f5f9fe 0%,
            #edf5fc 100%
        );
        border-right: 1px solid #dbe7f3;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 0.7rem;
    }

    .sidebar-nav {
        margin-top: 4px;
    }

    .sidebar-item {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 12px 15px;
        margin: 4px 0;
        border-radius: 7px;
        font-size: 1rem;
        color: #102a56;
    }

    .sidebar-item-active {
        background: linear-gradient(
            90deg,
            #1674df,
            #1767ce
        );
        color: white;
        font-weight: 600;
    }

    .sidebar-icon {
        width: 28px;
        text-align: center;
        font-size: 1.25rem;
    }

    .sidebar-quote {
        margin-top: 290px;
        padding: 22px 18px;
        background: #edf6ff;
        border: 1px solid #dceaf7;
        border-radius: 9px;
        color: #173e72;
        text-align: center;
        font-family: Georgia, serif;
        font-style: italic;
        font-size: 1rem;
        line-height: 1.55;
    }

    /* ======================================================
       MAIN TITLE
       ====================================================== */

    .main-title {
        font-size: 2.15rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 0.25rem;
        color: #102a56;
    }

    .main-title-blue {
        color: #1768c8;
    }

    .main-title-green {
        color: #348545;
    }

    .subtitle {
        font-size: 1.05rem;
        color: #173761;
        margin-bottom: 1.15rem;
    }

    /* ======================================================
       SECTION HEADINGS
       ====================================================== */

    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        line-height: 1.3;
        margin-top: 1.1rem;
        margin-bottom: 0.45rem;
        color: #102a56;
    }

    .section-description {
        font-size: 0.95rem;
        color: #31527b;
        margin-bottom: 1rem;
    }

    /* ======================================================
       CARDS
       ====================================================== */

    .metadata-card {
        background: #ffffff;
        border: 1px solid #d8e5f2;
        border-radius: 9px;
        padding: 15px 17px;
        margin-bottom: 12px;
        min-height: 105px;
        box-sizing: border-box;
        box-shadow: 0 1px 4px rgba(24, 66, 108, 0.04);
    }

    .metadata-label {
        font-size: 0.82rem;
        font-weight: 500;
        color: #31527b;
        margin-bottom: 7px;
        line-height: 1.3;
    }

    .metadata-value {
        font-size: 1rem;
        font-weight: 600;
        color: #102a56;
        line-height: 1.45;
        overflow-wrap: anywhere;
        word-break: break-word;
    }

    .metadata-card-long {
        min-height: 125px;
    }

    .metadata-value-long {
        font-size: 0.94rem;
        line-height: 1.55;
    }

    .accession-value {
        font-family: monospace;
        font-size: 1rem;
        letter-spacing: 0.2px;
    }

    .report-text {
        font-size: 1rem;
        line-height: 1.65;
        color: #172f52;
        margin-bottom: 1rem;
    }

    /* ======================================================
       INPUTS
       ====================================================== */

    div[data-baseweb="input"] {
        border-radius: 7px;
    }

    div[data-baseweb="input"] > div {
        background: #ffffff;
        border-color: #b9cee3;
    }

    input {
        color: #102a56 !important;
        font-size: 1.05rem !important;
    }

    /* ======================================================
       BUTTONS
       ====================================================== */

    .stButton > button,
    div.stDownloadButton > button {
        border-radius: 7px;
        min-height: 42px;
        font-size: 0.92rem;
        font-weight: 600;
    }

    .stButton > button {
        background: #176fd5;
        color: white;
        border: 1px solid #176fd5;
    }

    .stButton > button:hover {
        background: #125db6;
        border-color: #125db6;
        color: white;
    }

    div.stDownloadButton > button {
        background: #176fd5;
        color: white;
        border: 1px solid #176fd5;
    }

    /* ======================================================
       METRICS
       ====================================================== */

    [data-testid="stMetricLabel"] {
        font-size: 0.82rem;
        color: #31527b;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: #102a56;
    }

    /* ======================================================
       EXPANDERS / TABLES
       ====================================================== */

    div[data-testid="stExpander"] {
        border-color: #d8e5f2;
        border-radius: 8px;
    }

    .stDataFrame {
        border: 1px solid #d8e5f2;
        border-radius: 8px;
    }

    /* ======================================================
       FOOTER
       ====================================================== */

    footer {
        visibility: hidden;
    }

    /* ======================================================
       Landing page spacing
       ====================================================== */

    .rna-header {
        flex-shrink: 0;
    }

    .rna-footer {
        flex-shrink: 0;
    }

    .main .block-container > div {
        flex-shrink: 0;
    }

    .main .element-container {
        margin-bottom: 0.35rem !important;
    }


    .rna-footer {
        margin-top: auto !important;
        flex-shrink: 0;
        width: 100%;
        min-height: 54px;
        margin-top: 25px;
        padding: 9px 24px;
        box-sizing: border-box;
        background: linear-gradient(
            90deg,
            #edf6ff,
            #f8fbff
        );
        border-top: 1px solid #d8e6f5;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: #173e72;
        font-size: 0.78rem;
    }

    .rna-footer-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .rna-footer-brand {
        color: #1768c8;
        font-weight: 700;
    }

    .rna-footer-divider {
        color: #9bb1c8;
    }

    .rna-footer-center {
        display: flex;
        align-items: center;
        gap: 9px;
    }

    .rna-footer-name {
        color: #102a56;
        font-weight: 700;
    }

    .rna-footer-right {
        color: #2f5d8e;
        font-family: Georgia, serif;
        font-style: italic;
        text-align: right;
    }

    /* ======================================================
       USAGE TRACKER
       ====================================================== */

    .rna-usage-tracker {
        position: fixed;
        left: 18px;
        bottom: 18px;
        z-index: 999999;
        padding: 9px 13px;
        border: 1px solid #d8e5f2;
        border-radius: 9px;
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 2px 10px rgba(24, 66, 108, 0.12);
        color: #31527b;
        font-size: 0.78rem;
        line-height: 1.4;
        pointer-events: none;
        backdrop-filter: blur(5px);
    }

    .rna-usage-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        margin-right: 6px;
        border-radius: 50%;
        background: #348545;
        vertical-align: middle;
    }

    .rna-usage-count {
        color: #102a56;
        font-weight: 700;
    }

    .rna-usage-sub {
        margin-left: 13px;
        color: #58708f;
        font-size: 0.72rem;
    }


    /* ======================================================
       RESPONSIVE
       ====================================================== */

    @media (max-width: 1000px) {
        .rna-gateway {
            display: none;
        }

        .rna-brand {
            min-width: auto;
        }

        .rna-impact {
            min-width: auto;
        }

        .rna-title {
            font-size: 1.7rem;
        }

        .rna-footer {
            flex-direction: column;
            gap: 6px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# Helper Functions
# ==========================================================


def get_value(
    obj,
    attribute,
    default="—",
):
    """
    Safely retrieve a value from either an object or dictionary.
    """

    if obj is None:
        return default

    if isinstance(obj, dict):
        value = obj.get(attribute, default)

    else:
        value = getattr(
            obj,
            attribute,
            default,
        )

    if value is None:
        return default

    if value == "":
        return default

    return value


# ----------------------------------------------------------


def format_number(value):
    """
    Format numeric values with thousands separators.
    """

    if value is None:
        return "—"

    try:
        return f"{int(value):,}"

    except (
        TypeError,
        ValueError,
    ):
        return str(value)


# ----------------------------------------------------------


def object_to_dict(obj):
    """
    Convert dataclasses, objects, dictionaries,
    lists and tuples into JSON-compatible structures.
    """

    if obj is None:
        return None

    if is_dataclass(obj):

        data = asdict(obj)

        return {
            str(key): object_to_dict(value)
            for key, value in data.items()
        }

    if isinstance(obj, dict):

        return {
            str(key): object_to_dict(value)
            for key, value in obj.items()
        }

    if isinstance(obj, (list, tuple)):

        return [
            object_to_dict(item)
            for item in obj
        ]

    if hasattr(obj, "__dict__"):

        return {
            str(key): object_to_dict(value)
            for key, value in vars(obj).items()
        }

    return obj


# ----------------------------------------------------------


def clean_ui_value(value):
    """
    Convert a metadata value into clean plain text.

    This is the important fix for the current UI problem.

    Some values can arrive from upstream layers containing
    HTML fragments such as:

        <div class="small-value">
            SRX35160763
        </div>

    Those fragments must never be inserted directly into
    the Streamlit HTML.

    This function:
        1. Converts structured objects to text.
        2. Removes HTML tags.
        3. Decodes HTML entities.
        4. Normalizes whitespace.
    """

    if value is None:
        return "—"

    # Structured objects
    if isinstance(value, (dict, list, tuple)):

        try:

            text = json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        except Exception:

            text = str(value)

    else:

        text = str(value)

    # Decode entities first
    text = unescape(text)

    # Remove HTML tags
    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    # Normalize excessive whitespace
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n",
        text,
    )

    text = text.strip()

    if not text:
        return "—"

    return text


# ----------------------------------------------------------


def display_value(value):
    """
    Public formatting helper for UI/PDF output.
    """

    return clean_ui_value(value)


# ----------------------------------------------------------


def render_field(
    label,
    value,
    long=False,
    accession=False,
):
    """
    Render one clean metadata card.

    IMPORTANT:
    Values are HTML-escaped before insertion into the
    surrounding HTML. This prevents raw HTML fragments
    from appearing as code in the UI.
    """

    clean_label = clean_ui_value(label)
    clean_value = clean_ui_value(value)

    label_html = escape(
        clean_label,
        quote=True,
    )

    value_html = escape(
        clean_value,
        quote=True,
    )

    card_class = "metadata-card"

    if long:
        card_class += " metadata-card-long"

    value_class = "metadata-value"

    if long:
        value_class += " metadata-value-long"

    if accession:
        value_class += " accession-value"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="metadata-label">
                {label_html}
            </div>
            <div class="{value_class}">
                {value_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------


def render_section_title(
    title,
    description=None,
):
    """
    Render a consistent section heading.
    """

    title_html = escape(
        clean_ui_value(title),
        quote=True,
    )

    st.markdown(
        f"""
        <div class="section-title">
            {title_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if description:

        description_html = escape(
            clean_ui_value(description),
            quote=True,
        )

        st.markdown(
            f"""
            <div class="section-description">
                {description_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================================
# PDF Export
# ==========================================================

def build_pdf(
    result,
    accession,
):
    """
    Build a PDF inspection report.

    Returns
    -------
    bytes
        PDF document bytes.
    """

    try:

        from reportlab.lib import colors

        from reportlab.lib.enums import TA_CENTER

        from reportlab.lib.pagesizes import A4

        from reportlab.lib.styles import (
            getSampleStyleSheet,
            ParagraphStyle,
        )

        from reportlab.lib.units import mm

        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
        )

    except ImportError as exc:

        raise RuntimeError(
            "PDF export requires reportlab. "
            "Install it with: pip install reportlab"
        ) from exc


    # ======================================================
    # Extract objects
    # ======================================================

    report = getattr(
        result,
        "report",
        None,
    )

    metadata = getattr(
        result,
        "metadata",
        None,
    )

    validation = getattr(
        result,
        "validation",
        None,
    )

    normalization = getattr(
        result,
        "normalization",
        None,
    )


    # ======================================================
    # Dataset identity
    # ======================================================

    run = get_value(
        report,
        "run",
        None,
    )

    if run is None:
        run = get_value(
            report,
            "experiment",
            accession,
        )

    run = clean_ui_value(run)

    study = clean_ui_value(
        get_value(
            report,
            "study",
        )
    )

    experiment = clean_ui_value(
        get_value(
            report,
            "experiment",
        )
    )

    organism = clean_ui_value(
        get_value(
            report,
            "organism",
        )
    )

    project = clean_ui_value(
        get_value(
            report,
            "project",
        )
    )


    # ======================================================
    # BioSample
    # ======================================================

    sample = "—"

    if metadata is not None:

        sample_object = get_value(
            metadata,
            "sample",
            None,
        )

        sample = get_value(
            sample_object,
            "accession",
        )

    sample = clean_ui_value(sample)


    # ======================================================
    # Experiment information
    # ======================================================

    title = clean_ui_value(
        get_value(
            report,
            "title",
        )
    )

    strategy = clean_ui_value(
        get_value(
            report,
            "strategy",
        )
    )

    layout = clean_ui_value(
        get_value(
            report,
            "layout",
        )
    )

    sequencing_description = clean_ui_value(
        get_value(
            report,
            "sequencing",
        )
    )


    # ======================================================
    # Sequencing
    # ======================================================

    platform = clean_ui_value(
        get_value(
            report,
            "platform",
        )
    )

    instrument = clean_ui_value(
        get_value(
            report,
            "instrument",
        )
    )


    # ======================================================
    # Statistics
    # ======================================================

    total_spots = get_value(
        report,
        "total_spots",
        None,
    )

    total_bases = get_value(
        report,
        "total_bases",
        None,
    )


    # ======================================================
    # Public status
    # ======================================================

    public = "—"

    if metadata is not None:

        run_object = get_value(
            metadata,
            "run",
            None,
        )

        public_value = get_value(
            run_object,
            "public",
            None,
        )

        if public_value is not None:

            if isinstance(
                public_value,
                bool,
            ):

                public = (
                    "Yes"
                    if public_value
                    else "No"
                )

            else:

                public = str(
                    public_value
                )

    public = clean_ui_value(public)


    # ======================================================
    # Quality
    # ======================================================

    validation_score = clean_ui_value(
        get_value(
            report,
            "validation_score",
            None,
        )
    )

    normalization_changes = clean_ui_value(
        get_value(
            report,
            "normalization_changes",
            None,
        )
    )


    # ======================================================
    # Report text
    # ======================================================

    summary = clean_ui_value(
        get_value(
            report,
            "summary",
            "",
        )
    )

    sequencing = clean_ui_value(
        get_value(
            report,
            "sequencing",
            "",
        )
    )

    strengths = get_value(
        report,
        "strengths",
        [],
    )

    limitations = get_value(
        report,
        "limitations",
        [],
    )

    if strengths is None:
        strengths = []

    if limitations is None:
        limitations = []


    # ======================================================
    # PDF document
    # ======================================================

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=(
            f"{accession} - "
            "RNASeq Scout Report"
        ),
        author="RNASeq Scout",
    )


    # ======================================================
    # PDF styles
    # ======================================================

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RNASeqReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    section_style = ParagraphStyle(
        "RNASeqReportSection",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "RNASeqReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    )

    heading_style = ParagraphStyle(
        "RNASeqReportHeading",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        spaceBefore=5,
        spaceAfter=4,
    )


    # ======================================================
    # Story
    # ======================================================

    story = []


    # ======================================================
    # PDF title
    # ======================================================

    story.append(
        Paragraph(
            "RNASeq Scout",
            title_style,
        )
    )

    story.append(
        Paragraph(
            (
                "Dataset inspection report: "
                f"{escape(str(accession))}"
            ),
            body_style,
        )
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )


    # ======================================================
    # PDF table helper
    # ======================================================

    def add_table(rows):

        table_rows = []

        for label, value in rows:

            label_text = clean_ui_value(
                label
            )

            value_text = clean_ui_value(
                value
            )

            table_rows.append(
                [
                    Paragraph(
                        f"<b>{escape(label_text)}</b>",
                        body_style,
                    ),
                    Paragraph(
                        escape(value_text).replace(
                            "\n",
                            "<br/>",
                        ),
                        body_style,
                    ),
                ]
            )

        table = Table(
            table_rows,
            colWidths=[
                52 * mm,
                122 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                8,
            )
        )


    # ======================================================
    # Dataset Overview
    # ======================================================

    story.append(
        Paragraph(
            "Dataset Overview",
            section_style,
        )
    )

    add_table(
        [
            ("Run", run),
            ("Study", study),
            ("Experiment", experiment),
            ("Organism", organism),
        ]
    )


    # ======================================================
    # Dataset Identity
    # ======================================================

    story.append(
        Paragraph(
            "Dataset Identity",
            section_style,
        )
    )

    add_table(
        [
            (
                "Input / Run accession",
                run,
            ),
            (
                "Study accession",
                study,
            ),
            (
                "Experiment accession",
                experiment,
            ),
            (
                "BioProject",
                project,
            ),
            (
                "BioSample",
                sample,
            ),
            (
                "Organism",
                organism,
            ),
        ]
    )


    # ======================================================
    # Experiment Information
    # ======================================================

    story.append(
        Paragraph(
            "Experiment Information",
            section_style,
        )
    )

    add_table(
        [
            (
                "Experiment title",
                title,
            ),
            (
                "Library strategy",
                strategy,
            ),
            (
                "Layout",
                layout,
            ),
            (
                "Sequencing description",
                sequencing_description,
            ),
        ]
    )


    # ======================================================
    # Sequencing Information
    # ======================================================

    story.append(
        Paragraph(
            "Sequencing Information",
            section_style,
        )
    )

    add_table(
        [
            (
                "Platform",
                platform,
            ),
            (
                "Instrument",
                instrument,
            ),
            (
                "Layout",
                layout,
            ),
        ]
    )


    # ======================================================
    # Dataset Statistics
    # ======================================================

    story.append(
        Paragraph(
            "Dataset Statistics",
            section_style,
        )
    )

    add_table(
        [
            (
                "Reads / Spots",
                format_number(total_spots),
            ),
            (
                "Bases",
                format_number(total_bases),
            ),
            (
                "Public",
                public,
            ),
        ]
    )


    # ======================================================
    # Metadata Intelligence
    # ======================================================

    metadata_insight = getattr(
        result,
        "metadata_insight",
        None,
    )

    if metadata_insight is not None:

        render_section_title(
            "Metadata Intelligence",
            "Interpretation of the available dataset metadata.",
        )

        col1, col2 = st.columns(2)

        with col1:

            render_field(
                "Biological system",
                get_value(
                    metadata_insight,
                    "biological_system",
                ),
            )

            render_field(
                "Study type",
                get_value(
                    metadata_insight,
                    "study_type",
                ),
            )

        with col2:

            render_field(
                "Experimental focus",
                get_value(
                    metadata_insight,
                    "experimental_focus",
                ),
                long=True,
            )

            render_field(
                "Sequencing summary",
                get_value(
                    metadata_insight,
                    "sequencing_summary",
                ),
                long=True,
            )

        observations = get_value(
            metadata_insight,
            "observations",
            [],
        )

        if observations:

            st.subheader(
                "Observations"
            )

            for observation in observations:

                st.markdown(
                    f"- {escape(clean_ui_value(observation))}",
                    unsafe_allow_html=True,
                )


    # ======================================================
    # Modality / Workflow Intelligence
    # ======================================================

    modality_insight = getattr(
        result,
        "modality_insight",
        None,
    )

    if modality_insight is not None:

        render_section_title(
            "Modality / Workflow Intelligence",
            "Classification of the sequencing modality and its compatibility with conventional RNA-seq analysis.",
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            render_field(
                "Modality",
                get_value(
                    modality_insight,
                    "modality",
                ),
            )

        with col2:

            render_field(
                "Workflow family",
                get_value(
                    modality_insight,
                    "workflow_family",
                ),
            )

        with col3:

            compatible = get_value(
                modality_insight,
                "rna_seq_compatible",
                None,
            )

            if compatible is True:
                compatibility_label = "Yes"
            elif compatible is False:
                compatibility_label = "No"
            else:
                compatibility_label = "Uncertain"

            st.metric(
                "RNA-seq compatible",
                compatibility_label,
            )

        col1, col2 = st.columns(2)

        with col1:

            render_field(
                "Library strategy",
                get_value(
                    modality_insight,
                    "library_strategy",
                ),
            )

            render_field(
                "Library source",
                get_value(
                    modality_insight,
                    "library_source",
                ),
            )

        with col2:

            render_field(
                "Library selection",
                get_value(
                    modality_insight,
                    "library_selection",
                ),
            )

            render_field(
                "Compatibility status",
                get_value(
                    modality_insight,
                    "compatibility_status",
                ),
            )

        classification_confidence = clean_ui_value(
            get_value(
                modality_insight,
                "classification_confidence",
            )
        )

        st.metric(
            "Classification confidence",
            classification_confidence,
        )

        rationale = get_value(
            modality_insight,
            "rationale",
            "",
        )

        if rationale:

            st.subheader(
                "Classification rationale"
            )

            st.markdown(
                f"""
                <div class="report-text">
                    {escape(clean_ui_value(rationale))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        observed_evidence = get_value(
            modality_insight,
            "observed_evidence",
            [],
        )

        if observed_evidence:

            st.subheader(
                "Observed evidence"
            )

            for evidence in observed_evidence:

                st.markdown(
                    f"- {escape(clean_ui_value(evidence))}",
                    unsafe_allow_html=True,
                )

        warnings = get_value(
            modality_insight,
            "warnings",
            [],
        )

        if warnings:

            st.subheader(
                "Modality warnings"
            )

            for warning in warnings:

                st.markdown(
                    f"- {escape(clean_ui_value(warning))}",
                    unsafe_allow_html=True,
                )


    # ======================================================
    # Experimental Design Intelligence
    # ======================================================

    design_insight = getattr(
        result,
        "design_insight",
        None,
    )

    if design_insight is not None:

        render_section_title(
            "Experimental Design",
            "Experimental structure established from the available metadata.",
        )

        condition = get_value(
            design_insight,
            "condition",
            "",
        )

        control = get_value(
            design_insight,
            "control",
            "",
        )

        treatment = get_value(
            design_insight,
            "treatment",
            "",
        )

        time_point = get_value(
            design_insight,
            "time_point",
            "",
        )

        replicate_information = get_value(
            design_insight,
            "replicate_information",
            "",
        )

        # --------------------------------------------------
        # Primary design findings
        # --------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            _render_design_card(
                "Condition",
                condition,
                long=True,
            )

        with col2:
            _render_design_card(
                "Control",
                control,
                long=True,
            )

        with col3:
            _render_design_card(
                "Treatment",
                treatment,
                long=True,
            )

        col1, col2 = st.columns(2)

        with col1:
            _render_design_card(
                "Time point",
                time_point,
            )

        with col2:
            _render_design_card(
                "Replicate information",
                replicate_information,
                long=True,
            )

        # --------------------------------------------------
        # Overall design confidence
        # --------------------------------------------------

        design_confidence = clean_ui_value(
            get_value(
                design_insight,
                "design_confidence",
                "",
            )
        )

        st.metric(
            "Design confidence",
            design_confidence,
        )

        # --------------------------------------------------
        # Interpretation
        # --------------------------------------------------

        design_description = get_value(
            design_insight,
            "design_description",
            "",
        )

        if design_description:

            st.subheader(
                "Design interpretation"
            )

            st.markdown(
                f"""
                <div class="report-text">
                    {escape(clean_ui_value(design_description))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # --------------------------------------------------
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

            for warning in warnings:

                st.markdown(
                    f"- {escape(clean_ui_value(warning))}",
                    unsafe_allow_html=True,
                )

        # --------------------------------------------------
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

            for item in missing_information:

                st.markdown(
                    f"- {escape(clean_ui_value(item))}",
                    unsafe_allow_html=True,
                )

    # ======================================================
    # Dataset Suitability
    # ======================================================

    suitability_insight = getattr(
        result,
        "suitability_insight",
        None,
    )

    if suitability_insight is not None:

        render_section_title(
            "Dataset Suitability",
            "Assessment of whether the available evidence supports downstream RNA-seq analysis.",
        )

        overall = clean_ui_value(
            get_value(
                suitability_insight,
                "overall",
            )
        )

        score = get_value(
            suitability_insight,
            "score",
            None,
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Overall assessment",
                overall,
            )

        with col2:

            st.metric(
                "Suitability score",
                clean_ui_value(score),
            )

        rationale = get_value(
            suitability_insight,
            "rationale",
            "",
        )

        if rationale:

            st.subheader(
                "Rationale"
            )

            st.markdown(
                f"""
                <div class="report-text">
                    {escape(clean_ui_value(rationale))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        observed_evidence = get_value(
            suitability_insight,
            "observed_evidence",
            [],
        )

        if observed_evidence:

            st.subheader(
                "Observed evidence"
            )

            for evidence in observed_evidence:

                st.markdown(
                    f"- {escape(clean_ui_value(evidence))}",
                    unsafe_allow_html=True,
                )

        warnings = get_value(
            suitability_insight,
            "warnings",
            [],
        )

        if warnings:

            st.subheader(
                "Warnings"
            )

            for warning in warnings:

                st.markdown(
                    f"- {escape(clean_ui_value(warning))}",
                    unsafe_allow_html=True,
                )

        missing_information = get_value(
            suitability_insight,
            "missing_information",
            [],
        )

        if missing_information:

            st.subheader(
                "Missing information"
            )

            for item in missing_information:

                st.markdown(
                    f"- {escape(clean_ui_value(item))}",
                    unsafe_allow_html=True,
                )


    # ======================================================
    # Reanalysis Readiness
    # ======================================================

    reanalysis_readiness = getattr(
        result,
        "reanalysis_readiness",
        None,
    )

    if reanalysis_readiness is not None:

        render_section_title(
            "Reanalysis Readiness",
            "Evidence-based assessment of whether the available metadata support defensible downstream reanalysis.",
        )

        verdict = clean_ui_value(
            get_value(
                reanalysis_readiness,
                "verdict",
            )
        )

        rationale = clean_ui_value(
            get_value(
                reanalysis_readiness,
                "rationale",
                "",
            )
        )

        # --------------------------------------------------
        # Decision card
        # --------------------------------------------------

        verdict_html = escape(
            verdict,
            quote=True,
        )

        rationale_html = escape(
            rationale,
            quote=True,
        )

        st.html(
            f"""
<div style="
    border: 1px solid rgba(128,128,128,0.30);
    border-radius: 10px;
    padding: 18px 20px;
    margin: 8px 0 20px 0;
">
    <div style="
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.70;
        margin-bottom: 6px;
">
        Readiness verdict
    </div>

    <div style="
        font-size: 1.45rem;
        font-weight: 700;
        margin-bottom: 10px;
">
        {verdict_html}
    </div>

    <div style="
        font-size: 0.95rem;
        line-height: 1.55;
">
        {rationale_html}
    </div>
</div>
"""
        )

        # --------------------------------------------------
        # Study-level evidence snapshot
        # --------------------------------------------------

        experiment_at_glance = getattr(
            result,
            "experiment_at_glance",
            None,
        )

        landscape = getattr(
            result,
            "study_experimental_landscape",
            None,
        )

        if experiment_at_glance is not None or landscape is not None:

            st.subheader(
                "Evidence snapshot"
            )

            snapshot_values = []

            if experiment_at_glance is not None:

                experiment_count = get_value(
                    experiment_at_glance,
                    "experiment_count",
                    None,
                )

                run_count = get_value(
                    experiment_at_glance,
                    "run_count",
                    None,
                )

                if experiment_count is not None:
                    snapshot_values.append(
                        ("Experiments", experiment_count)
                    )

                if run_count is not None:
                    snapshot_values.append(
                        ("Runs", run_count)
                    )

            if landscape is not None:

                assay_counts = get_value(
                    landscape,
                    "assay_family_counts",
                    {},
                )

                contexts = get_value(
                    landscape,
                    "observed_contexts",
                    [],
                )

                if assay_counts:
                    snapshot_values.append(
                        ("Assay families", len(assay_counts))
                    )

                if contexts:
                    snapshot_values.append(
                        ("Experimental contexts", len(contexts))
                    )

            if snapshot_values:

                columns = st.columns(
                    len(snapshot_values)
                )

                for column, (label, value) in zip(
                    columns,
                    snapshot_values,
                ):
                    with column:
                        st.metric(
                            label,
                            clean_ui_value(value),
                        )

        # --------------------------------------------------
        # Categorized evidence
        # --------------------------------------------------

        observed_evidence = get_value(
            reanalysis_readiness,
            "observed_evidence",
            [],
        )

        inferred_evidence = get_value(
            reanalysis_readiness,
            "inferred_evidence",
            [],
        )

        not_established = get_value(
            reanalysis_readiness,
            "not_established",
            [],
        )

        missing_information = get_value(
            reanalysis_readiness,
            "missing_information",
            [],
        )

        warnings = get_value(
            reanalysis_readiness,
            "warnings",
            [],
        )

        # --------------------------------------------------
        # Established evidence
        # --------------------------------------------------

        if observed_evidence:

            st.subheader(
                "Established evidence"
            )

            for item in observed_evidence:

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
    ✓ {clean_item}
</div>
"""
                )

        # --------------------------------------------------
        # Inferred evidence
        # --------------------------------------------------

        if inferred_evidence:

            with st.expander(
                "Inferred evidence",
                expanded=False,
            ):

                for item in inferred_evidence:

                    st.markdown(
                        f"- {escape(clean_ui_value(item))}",
                        unsafe_allow_html=True,
                    )

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

        # --------------------------------------------------
        # Warnings
        # --------------------------------------------------

        if warnings:

            with st.expander(
                f"Warnings ({len(warnings)})",
                expanded=True,
            ):

                for warning in warnings:

                    st.markdown(
                        f"- {escape(clean_ui_value(warning))}",
                        unsafe_allow_html=True,
                    )


    # ======================================================
    # Analysis Planning
    # ======================================================

    analysis_plan = getattr(
        result,
        "analysis_plan",
        None,
    )

    if analysis_plan is not None:

        render_section_title(
            "Analysis Plan",
            "A provisional analysis workflow derived from the available dataset evidence and modality assessment.",
        )

        col1, col2 = st.columns(2)

        with col1:

            render_field(
                "Workflow",
                get_value(
                    analysis_plan,
                    "workflow",
                ),
                long=True,
            )

            render_field(
                "Alignment",
                get_value(
                    analysis_plan,
                    "alignment",
                ),
            )

            render_field(
                "Quantification",
                get_value(
                    analysis_plan,
                    "quantification",
                ),
            )

        with col2:

            render_field(
                "Differential analysis",
                get_value(
                    analysis_plan,
                    "differential_analysis",
                ),
                long=True,
            )

            render_field(
                "Design formula",
                get_value(
                    analysis_plan,
                    "design_formula",
                ),
                long=True,
            )

            render_field(
                "Replicate status",
                get_value(
                    analysis_plan,
                    "replicate_status",
                ),
                long=True,
            )

        confidence = clean_ui_value(
            get_value(
                analysis_plan,
                "confidence",
            )
        )

        st.metric(
            "Planning confidence",
            confidence,
        )

        rationale = get_value(
            analysis_plan,
            "rationale",
            "",
        )

        if rationale:

            st.subheader(
                "Planning rationale"
            )

            st.markdown(
                f"""
                <div class="report-text">
                    {escape(clean_ui_value(rationale))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        recommendations = get_value(
            analysis_plan,
            "recommendations",
            [],
        )

        if recommendations:

            st.subheader(
                "Recommendations"
            )

            for recommendation in recommendations:

                st.markdown(
                    f"- {escape(clean_ui_value(recommendation))}",
                    unsafe_allow_html=True,
                )

        warnings = get_value(
            analysis_plan,
            "warnings",
            [],
        )

        if warnings:

            st.subheader(
                "Analysis warnings"
            )

            for warning in warnings:

                st.markdown(
                    f"- {escape(clean_ui_value(warning))}",
                    unsafe_allow_html=True,
                )


    # ======================================================
    # Study Experimental Landscape
    # ======================================================
    #
    # Descriptive study-level summary of observed assay
    # families and experimental context labels.
    #
    # This section does not infer controls, treatments,
    # biological replicates, time points, or statistical
    # contrasts.

    study_experimental_landscape = get_value(
        result,
        "study_experimental_landscape",
        None,
    )

    if study_experimental_landscape is not None:

        render_section_title(
            "Study Experimental Landscape",
            "Observed assay families and experimental contexts across the study.",
        )

        assay_family_counts = get_value(
            study_experimental_landscape,
            "assay_family_counts",
            {},
        )

        context_counts = get_value(
            study_experimental_landscape,
            "context_counts",
            {},
        )

        assay_context_counts = get_value(
            study_experimental_landscape,
            "assay_context_counts",
            {},
        )

        warnings = get_value(
            study_experimental_landscape,
            "warnings",
            [],
        )

        # --------------------------------------------------
        # Assay Families
        # --------------------------------------------------

        st.subheader("Assay Families")

        if assay_family_counts:

            assay_columns = st.columns(
                min(len(assay_family_counts), 4)
            )

            for index, (assay, count) in enumerate(
                assay_family_counts.items()
            ):

                with assay_columns[
                    index % len(assay_columns)
                ]:

                    st.metric(
                        clean_ui_value(assay),
                        clean_ui_value(count),
                    )

        else:

            st.info(
                "No assay-family information was observed."
            )

        # --------------------------------------------------
        # Experimental Contexts
        # --------------------------------------------------

        st.subheader("Experimental Contexts")

        if context_counts:

            context_columns = st.columns(
                min(len(context_counts), 4)
            )

            for index, (context, count) in enumerate(
                context_counts.items()
            ):

                with context_columns[
                    index % len(context_columns)
                ]:

                    st.metric(
                        clean_ui_value(context),
                        clean_ui_value(count),
                    )

        else:

            st.info(
                "No experimental-context labels were observed."
            )

        # --------------------------------------------------
        # Assay × Context
        # --------------------------------------------------

        st.subheader("Assay × Context")

        if assay_context_counts:

            for assay, contexts in assay_context_counts.items():

                st.markdown(
                    f"**{clean_ui_value(assay)}**"
                )

                if contexts:

                    context_columns = st.columns(
                        min(len(contexts), 4)
                    )

                    for index, (context, count) in enumerate(
                        contexts.items()
                    ):

                        with context_columns[
                            index % len(context_columns)
                        ]:

                            st.metric(
                                clean_ui_value(context),
                                clean_ui_value(count),
                            )

                else:

                    st.write(
                        "No observed context labels."
                    )

        else:

            st.info(
                "No assay × context information was observed."
            )

        # --------------------------------------------------
        # Warnings
        # --------------------------------------------------

        if warnings:

            with st.expander(
                "Landscape warnings",
                expanded=False,
            ):

                for warning in warnings:

                    st.warning(
                        clean_ui_value(warning)
                    )


    # ======================================================
    # Metadata Quality
    # ======================================================

    story.append(
        Paragraph(
            "Metadata Quality",
            section_style,
        )
    )

    add_table(
        [
            (
                "Validation score",
                validation_score,
            ),
            (
                "Normalization changes",
                normalization_changes,
            ),
        ]
    )


    # ======================================================
    # Dataset Report
    # ======================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Dataset Report",
            section_style,
        )
    )


    if summary and summary != "—":

        story.append(
            Paragraph(
                "Summary",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                escape(summary).replace(
                    "\n",
                    "<br/>",
                ),
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                6,
            )
        )


    if sequencing and sequencing != "—":

        story.append(
            Paragraph(
                "Sequencing interpretation",
                heading_style,
            )
        )

        story.append(
            Paragraph(
                escape(sequencing).replace(
                    "\n",
                    "<br/>",
                ),
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                6,
            )
        )


    # ======================================================
    # Strengths
    # ======================================================

    if strengths:

        story.append(
            Paragraph(
                "Strengths",
                heading_style,
            )
        )

        for item in strengths:

            text = clean_ui_value(item)

            story.append(
                Paragraph(
                    "• "
                    + escape(text),
                    body_style,
                )
            )

        story.append(
            Spacer(
                1,
                6,
            )
        )


    # ======================================================
    # Limitations
    # ======================================================

    if limitations:

        story.append(
            Paragraph(
                "Limitations",
                heading_style,
            )
        )

        for item in limitations:

            text = clean_ui_value(item)

            story.append(
                Paragraph(
                    "• "
                    + escape(text),
                    body_style,
                )
            )


    # ======================================================
    # Validation Details
    # ======================================================

    story.append(
        Paragraph(
            "Validation Details",
            section_style,
        )
    )

    validation_text = json.dumps(
        object_to_dict(validation),
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    story.append(
        Paragraph(
            escape(validation_text).replace(
                "\n",
                "<br/>",
            ),
            body_style,
        )
    )


    # ======================================================
    # Normalization Details
    # ======================================================

    story.append(
        Paragraph(
            "Normalization Details",
            section_style,
        )
    )

    normalization_text = json.dumps(
        object_to_dict(normalization),
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    story.append(
        Paragraph(
            escape(normalization_text).replace(
                "\n",
                "<br/>",
            ),
            body_style,
        )
    )


    # ======================================================
    # Build PDF
    # ======================================================

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# ==========================================================
# Header
# ==========================================================

render_html(
    """
<div class="rna-header">

<div class="rna-brand">

<div class="rna-logo">
<svg viewBox="0 0 80 90" width="62" height="76" xmlns="http://www.w3.org/2000/svg">

<path d="M18 8 C58 25, 58 65, 18 82"
fill="none"
stroke="#1768c8"
stroke-width="5"/>

<path d="M58 8 C18 25, 18 65, 58 82"
fill="none"
stroke="#1768c8"
stroke-width="5"/>

<line x1="27" y1="18" x2="49" y2="25"
stroke="#1768c8" stroke-width="3"/>

<line x1="22" y1="32" x2="54" y2="39"
stroke="#1768c8" stroke-width="3"/>

<line x1="22" y1="48" x2="54" y2="41"
stroke="#1768c8" stroke-width="3"/>

<line x1="27" y1="64" x2="49" y2="57"
stroke="#1768c8" stroke-width="3"/>

<path d="M48 50
C61 37, 73 39, 75 37
C72 54, 62 67, 45 67
C47 60, 47 55, 48 50Z"
fill="#4a9d43"/>

<path d="M45 67
C52 59, 59 51, 70 42"
fill="none"
stroke="#2e7734"
stroke-width="2"/>

</svg>
</div>

<div class="rna-brand-text">

<div class="rna-title">
RNASeq <span class="rna-title-green">Scout</span>
</div>

<div class="rna-tagline">
Explore <span>•</span>
Interpret <span>•</span>
Plan <span>•</span>
Accelerate
</div>

</div>

</div>

<div class="rna-gateway">
From SRA accession to experiment-aware analysis plan
</div>

<div class="rna-impact">

<div class="rna-impact-divider"></div>

<div class="rna-leaf">🍃</div>

<div class="rna-impact-text">
Biology<br>
Data<br>
Impact
</div>

</div>

</div>
    """
)


# ==========================================================
# Introduction
# ==========================================================

st.write(
    "Enter any valid SRA accession to inspect the available "
    "dataset metadata."
)

st.caption(
    "Examples: SRR17730393, SRR17730394, SRR17730395, "
    "SRX35161265"
)


# ==========================================================
# Dataset Accession
# ==========================================================

render_section_title(
    "Dataset accession"
)

accession = st.text_input(
    "Enter an SRA accession",
    value="SRR17730393",
    placeholder="e.g. SRR17730393",
)


# ==========================================================
# NCBI Configuration
# ==========================================================
#
# IMPORTANT:
# The email is used internally only.
# It is NOT displayed anywhere in the Streamlit UI.
#

NCBI_EMAIL = os.environ.get(
    "NCBI_EMAIL",
    "gshankar.bbaul@gmail.com",
)


# ==========================================================
# Usage Tracking
# ==========================================================

usage_tracker = UsageTracker()


# ==========================================================
# Inspect Button
# ==========================================================

inspect_clicked = st.button(
    "🔍 Inspect Dataset",
    type="primary",
    use_container_width=True,
)


# ==========================================================
# Inspection
# ==========================================================

if inspect_clicked:

    accession = accession.strip().upper()


    # ------------------------------------------------------
    # Input validation
    # ------------------------------------------------------

    if not accession:

        st.error(
            "Please enter an SRA accession number."
        )

        st.stop()


    # ------------------------------------------------------
    # Run inspection
    # ------------------------------------------------------

    with st.spinner(
        f"Retrieving dataset information for {accession}..."
    ):

        try:

            navigator = RNASeqNavigator(
                email=NCBI_EMAIL
            )

            result = navigator.inspect(
                accession
            )

        except Exception as exc:

            st.error(
                "RNASeq Scout encountered an unexpected error."
            )

            st.exception(exc)

            st.stop()


    # ------------------------------------------------------
    # Inspection failure
    # ------------------------------------------------------

    if not result.success:

        st.error(
            f"RNASeq Scout could not inspect {accession}."
        )

        if result.error:

            st.code(
                str(result.error)
            )

        st.stop()


    # ------------------------------------------------------
    # Success
    # ------------------------------------------------------

    usage_tracker.record_success(
        accession
    )


    st.success(
        f"Dataset information retrieved for {accession}"
    )


    # ======================================================
    # Extract objects
    # ======================================================

    report = result.report

    metadata = result.metadata

    normalization = result.normalization

    validation = result.validation


    # ======================================================
    # Dataset Overview
    # ======================================================

    render_section_title(
        "Dataset Overview",
        "Basic identity and biological information.",
    )


    # ------------------------------------------------------
    # Accession handling
    # ------------------------------------------------------
    #
    # Keep accession types semantically distinct.
    # An experiment accession must never be displayed as a run.
    # ------------------------------------------------------

    run = get_value(
        report,
        "run",
        None,
    )

    study = get_value(
        report,
        "study",
        None,
    )

    experiment = get_value(
        report,
        "experiment",
        None,
    )

    organism = get_value(
        report,
        "organism",
        None,
    )

    project = get_value(
        report,
        "project",
        None,
    )


    # ------------------------------------------------------
    # Accession-aware overview
    # ------------------------------------------------------
    #
    # The overview reflects the type of accession supplied
    # by the user. Accession types are never substituted for
    # one another.
    # ------------------------------------------------------

    accession_upper = accession.strip().upper()

    if accession_upper.startswith(("SRX", "ERX", "DRX")):
        primary_label = "Experiment"
        primary_value = experiment
    elif accession_upper.startswith(("SRR", "ERR", "DRR")):
        primary_label = "Run"
        primary_value = run
    elif accession_upper.startswith(("SRP", "ERP", "DRP")):
        primary_label = "Study"
        primary_value = study
    elif accession_upper.startswith(("PRJNA", "PRJEB", "PRJDB")):
        primary_label = "Project"
        primary_value = project
    else:
        primary_label = "Accession"
        primary_value = accession

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            primary_label,
            clean_ui_value(primary_value),
        )


    with col2:

        st.metric(
            "Study",
            clean_ui_value(study),
        )


    with col3:

        st.metric(
            "BioProject",
            clean_ui_value(project),
        )


    with col4:

        st.metric(
            "Organism",
            clean_ui_value(organism),
        )


    # ======================================================
    # Dataset Identity
    # ======================================================

    render_section_title(
        "Dataset Identity"
    )


    # ------------------------------------------------------
    # BioSample
    # ------------------------------------------------------

    sample = "—"

    if metadata is not None:

        sample_object = get_value(
            metadata,
            "sample",
            None,
        )

        sample = get_value(
            sample_object,
            "accession",
        )


    col1, col2 = st.columns(2)


    with col1:

        render_field(
            "Input accession",
            accession,
            accession=True,
        )

        render_field(
            "Study accession",
            study,
            accession=True,
        )

        render_field(
            "Experiment accession",
            experiment,
            accession=True,
        )


    with col2:

        render_field(
            "BioProject",
            project,
            accession=True,
        )

        render_field(
            "BioSample",
            sample,
            accession=True,
        )

        if run:

            render_field(
                "Run accession",
                run,
                accession=True,
            )


    # ======================================================
    # Experiment Information
    # ======================================================

    render_section_title(
        "Experiment Information",
        "Information describing the sequencing experiment.",
    )


    title = get_value(
        report,
        "title",
    )

    strategy = get_value(
        report,
        "strategy",
    )

    layout = get_value(
        report,
        "layout",
    )

    sequencing_description = get_value(
        report,
        "sequencing",
    )


    col1, col2 = st.columns(2)


    with col1:

        render_field(
            "Experiment title",
            title,
            long=True,
        )

        render_field(
            "Library strategy",
            strategy,
        )


    with col2:

        render_field(
            "Layout",
            layout,
        )

        render_field(
            "Sequencing description",
            sequencing_description,
            long=True,
        )


    # ======================================================
    # Sequencing Information
    # ======================================================

    render_section_title(
        "Sequencing Information"
    )


    platform = get_value(
        report,
        "platform",
    )

    instrument = get_value(
        report,
        "instrument",
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Platform",
            clean_ui_value(platform),
        )


    with col2:

        st.metric(
            "Instrument",
            clean_ui_value(instrument),
        )


    with col3:

        st.metric(
            "Layout",
            clean_ui_value(layout),
        )


    # ======================================================
    # Dataset Statistics
    # ======================================================

    render_section_title(
        "Dataset Statistics",
        "Sequencing statistics reported for the run.",
    )


    total_spots = get_value(
        report,
        "total_spots",
        None,
    )

    total_bases = get_value(
        report,
        "total_bases",
        None,
    )


    # ------------------------------------------------------
    # Public status
    # ------------------------------------------------------

    public = "—"

    if metadata is not None:

        run_object = get_value(
            metadata,
            "run",
            None,
        )

        public_value = get_value(
            run_object,
            "public",
            None,
        )

        if public_value is not None:

            if isinstance(
                public_value,
                bool,
            ):

                public = (
                    "Yes"
                    if public_value
                    else "No"
                )

            else:

                public = str(
                    public_value
                )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Reads / Spots",
            format_number(total_spots),
        )


    with col2:

        st.metric(
            "Bases",
            format_number(total_bases),
        )


    with col3:

        st.metric(
            "Public",
            clean_ui_value(public),
        )


    # ======================================================
    # Experiment at a Glance
    # ======================================================
    #
    # Study-level context retrieved by the navigator.
    # This section is available for study accessions such as
    # SRP, ERP, and DRP. Individual run/experiment accessions
    # intentionally do not trigger study-wide retrieval.

    experiment_at_glance = get_value(
        result,
        "experiment_at_glance",
        None,
    )

    if experiment_at_glance is not None:

        render_section_title(
            "Experiment at a Glance",
            "Study-level context for rapid understanding of the experiment collection.",
        )

        study_title = get_value(
            experiment_at_glance,
            "study_title",
            "",
        )

        study_description = get_value(
            experiment_at_glance,
            "study_description",
            "",
        )

        unique_sample_count = get_value(
            experiment_at_glance,
            "unique_sample_count",
            0,
        )

        unique_biosample_count = get_value(
            experiment_at_glance,
            "unique_biosample_count",
            0,
        )

        experiment_count = get_value(
            experiment_at_glance,
            "experiment_count",
            0,
        )

        run_count = get_value(
            experiment_at_glance,
            "run_count",
            0,
        )

        if study_title:

            st.subheader(
                clean_ui_value(study_title)
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "SRA samples",
                clean_ui_value(
                    unique_sample_count
                ),
            )

        with col2:

            st.metric(
                "BioSamples",
                clean_ui_value(
                    unique_biosample_count
                ),
            )

        with col3:

            st.metric(
                "Experiments",
                clean_ui_value(
                    experiment_count
                ),
            )

        with col4:

            st.metric(
                "Runs",
                clean_ui_value(
                    run_count
                ),
            )

        if study_description:

            with st.expander(
                "Study description",
                expanded=False,
            ):

                st.write(
                    clean_ui_value(
                        study_description
                    )
                )


    # ======================================================
    # Metadata Quality
    # ======================================================

    render_section_title(
        "Metadata Quality",
        "Information produced by the validation and normalization layers.",
    )


    validation_score = get_value(
        report,
        "validation_score",
        None,
    )

    normalization_changes = get_value(
        report,
        "normalization_changes",
        None,
    )


    col1, col2 = st.columns(2)


    with col1:

        st.subheader(
            "Validation"
        )

        st.metric(
            "Validation score",
            (
                clean_ui_value(validation_score)
                if validation_score is not None
                else "—"
            ),
        )

        if validation is not None:

            issues = get_value(
                validation,
                "issues",
                None,
            )

            if issues is not None:

                try:
                    issue_count = len(issues)
                except TypeError:
                    issue_count = 0

                st.write(
                    f"Issues reported: {issue_count}"
                )


    with col2:

        st.subheader(
            "Normalization"
        )

        st.metric(
            "Normalization changes",
            (
                clean_ui_value(normalization_changes)
                if normalization_changes is not None
                else "—"
            ),
        )


    # ======================================================
    # Dataset Report
    # ======================================================

    render_section_title(
        "Dataset Report",
        "Integrated information available from the reporting layer.",
    )


    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    summary = get_value(
        report,
        "summary",
        "",
    )

    if summary:

        st.subheader(
            "Summary"
        )

        st.markdown(
            f"""
            <div class="report-text">
                {escape(clean_ui_value(summary))}
            </div>
            """,
            unsafe_allow_html=True,
        )


    # ------------------------------------------------------
    # Sequencing interpretation
    # ------------------------------------------------------

    sequencing = get_value(
        report,
        "sequencing",
        "",
    )

    if sequencing:

        st.subheader(
            "Sequencing interpretation"
        )

        st.markdown(
            f"""
            <div class="report-text">
                {escape(clean_ui_value(sequencing))}
            </div>
            """,
            unsafe_allow_html=True,
        )


    # ------------------------------------------------------
    # Strengths
    # ------------------------------------------------------

    strengths = get_value(
        report,
        "strengths",
        [],
    )

    if strengths:

        st.subheader(
            "Strengths"
        )

        for strength in strengths:

            st.markdown(
                f"- {escape(clean_ui_value(strength))}",
                unsafe_allow_html=True,
            )


    # ------------------------------------------------------
    # Limitations
    # ------------------------------------------------------

    limitations = get_value(
        report,
        "limitations",
        [],
    )

    if limitations:

        st.subheader(
            "Limitations"
        )

        for limitation in limitations:

            st.markdown(
                f"- {escape(clean_ui_value(limitation))}",
                unsafe_allow_html=True,
            )


    # ======================================================
    # Structured Metadata
    # ======================================================

    with st.expander(
        "View structured metadata"
    ):

        metadata_dict = object_to_dict(
            metadata
        )

        st.json(
            metadata_dict
        )


    # ======================================================
    # Normalization Details
    # ======================================================

    with st.expander(
        "View normalization details"
    ):

        normalization_dict = object_to_dict(
            normalization
        )

        st.json(
            normalization_dict
        )


    # ======================================================
    # Validation Details
    # ======================================================

    with st.expander(
        "View validation details"
    ):

        validation_dict = object_to_dict(
            validation
        )

        st.json(
            validation_dict
        )


    # ======================================================
    # Complete Inspection Result
    # ======================================================

    with st.expander(
        "View complete inspection result"
    ):

        result_dict = object_to_dict(
            result
        )

        st.json(
            result_dict
        )


    # ======================================================
    # Export
    # ======================================================

    render_section_title(
        "Export"
    )


    result_dict = object_to_dict(
        result
    )


    # ------------------------------------------------------
    # JSON
    # ------------------------------------------------------

    json_data = json.dumps(
        result_dict,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


    col1, col2 = st.columns(2)


    with col1:

        st.download_button(
            label="⬇️ Download inspection result (JSON)",
            data=json_data,
            file_name=f"{accession}_inspection.json",
            mime="application/json",
            use_container_width=True,
        )


    # ------------------------------------------------------
    # PDF
    # ------------------------------------------------------

    with col2:

        try:

            pdf_data = build_pdf(
                result,
                accession,
            )

            st.download_button(
                label="⬇️ Download inspection report (PDF)",
                data=pdf_data,
                file_name=f"{accession}_inspection.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        except RuntimeError as exc:

            st.warning(
                str(exc)
            )

        except Exception:

            st.error(
                "PDF report could not be generated."
            )


# ==========================================================
# Initial State
# ==========================================================

else:

    st.info(
        "Enter an SRA accession above and click "
        "'Inspect Dataset' to begin."
    )


# ==========================================================
# Usage Tracker Display
# ==========================================================

usage_summary = usage_tracker.summary()

total_checks = usage_summary[
    "total_checks"
]

unique_accessions = usage_summary[
    "unique_accessions"
]

render_html(
    f"""
<div class="rna-usage-tracker">
    <span class="rna-usage-dot"></span>
    <span class="rna-usage-count">
        {format_number(total_checks)}
    </span>
    accessions checked
    <div class="rna-usage-sub">
        {format_number(unique_accessions)} unique
    </div>
</div>
    """
)


# ==========================================================
# Application Footer
# ==========================================================

render_html(
    """
<div class="rna-footer">

<div class="rna-footer-left">

<span class="rna-footer-brand">
RNASeq Scout
</span>

<span class="rna-footer-divider">|</span>

<span>
v0.1.0
</span>

<span class="rna-footer-divider">|</span>

<span>
An open-source project for the scientific community
</span>

</div>

<div class="rna-footer-center">

<span>
Developed by
</span>

<span class="rna-footer-name">
Dr. G. Shankar
</span>

<span class="rna-footer-divider">|</span>

<span class="rna-footer-name">
Dr. Ranjana Soni
</span>

<span class="rna-footer-divider">|</span>

<span>
🟢 0000-0002-8972-6670
</span>

<span class="rna-footer-divider">|</span>

<span>
✉ gshankar.bbau@gmail.com
</span>

</div>

<div class="rna-footer-right">
Data for a healthier planet<br>
and a brighter tomorrow
</div>

</div>
    """
)
