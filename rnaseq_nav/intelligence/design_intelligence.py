"""
RNASeq Scout

Layer 2: Experimental Design Intelligence
==========================================

This module interprets experimental-design information from publicly
available sequencing metadata.

Evidence sources
----------------
1. Experiment title
2. Library construction protocol
3. Run metadata, only for identifying the presence of a sequencing run

Scientific policy
-----------------
The module distinguishes:

1. Observed information
   Explicitly documented in available metadata.

2. Inferred information
   Reasonably suggested by metadata but not explicitly established.

3. Not-established information
   Relevant information was examined but cannot be established.

4. Missing information
   The relevant field is not represented in the available metadata.

The module must not invent:

- biological replicates
- control groups
- treatment assignments
- time points
- statistical contrasts
- DESeq2 design formulas

A sequencing run is never treated as a biological replicate.

A contextual word such as "stress", "infection", "iron", or "detergent"
does not by itself establish a treatment assignment.

Protocol statements are treated as observed evidence only when the
language explicitly supports the interpretation.
"""

from dataclasses import dataclass, field
import re


# ==========================================================
# Data model
# ==========================================================

@dataclass
class ExperimentalDesignInsight:
    """
    Structured interpretation of experimental design metadata.
    """

    condition: str = ""

    control: str = ""

    treatment: str = ""

    time_point: str = ""

    # Explicit BioSample-level annotations. These are kept separate
    # from study-level assignments because one sample does not
    # establish the complete experimental group structure.
    sample_treatment: str = ""

    sample_time_point: str = ""

    replicate_information: str = ""

    design_description: str = ""

    design_confidence: str = "Insufficient information"

    # Human-readable explanation of the confidence assessment.
    # This does not replace or override the confidence classification.
    confidence_explanation: str = ""

    observed_features: list[str] = field(
        default_factory=list
    )

    inferred_features: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    missing_information: list[str] = field(
        default_factory=list
    )

    sample_condition: str = ""
    sample_control: str = ""
    sample_replicate_status: str = ""
    sample_age: str = ""
    sample_developmental_stage: str = ""


# ==========================================================
# Utility functions
# ==========================================================

def _clean(value):
    """
    Normalize a metadata value to a clean string.
    """

    if value is None:
        return ""

    value = str(value).strip()

    if value.lower() in {
        "",
        "none",
        "null",
        "nan",
        "n/a",
        "na",
        "unknown",
        "not available",
        "not specified",
    }:
        return ""

    return value


def _append_unique(items, value):
    """
    Append a value only once.
    """

    value = _clean(value)

    if value and value not in items:
        items.append(value)


def _get_experiment(metadata):
    """
    Retrieve experiment metadata safely.
    """

    if metadata is None:
        return None

    return getattr(
        metadata,
        "experiment",
        None,
    )


def _get_sample(metadata):
    """
    Retrieve sample metadata safely.
    """

    if metadata is None:
        return None

    return getattr(
        metadata,
        "sample",
        None,
    )


def _get_run(metadata):
    """
    Retrieve run metadata safely.
    """

    if metadata is None:
        return None

    return getattr(
        metadata,
        "run",
        None,
    )


def _collect_observed_metadata(metadata):
    """
    Collect directly observed experiment/sample metadata.

    Construction protocol is preserved as a separate evidence source.
    """

    observed = {}

    experiment = _get_experiment(metadata)
    sample = _get_sample(metadata)

    if experiment is not None:

        fields = [
            "title",
            "library_strategy",
            "layout",
            "platform",
            "library_source",
            "library_selection",
            "instrument",
            "construction_protocol",
        ]

        for field_name in fields:

            observed[field_name] = _clean(
                getattr(
                    experiment,
                    field_name,
                    "",
                )
            )

    if sample is not None:

        observed["organism"] = _clean(
            getattr(
                sample,
                "organism",
                "",
            )
        )

        observed["biosample"] = _clean(
            getattr(
                sample,
                "biosample",
                "",
            )
        )

    return observed


# ==========================================================
# Evidence helpers
# ==========================================================

def _protocol(metadata):
    """
    Return the deposited library construction protocol, if available.
    """

    experiment = _get_experiment(metadata)

    if experiment is None:
        return ""

    return _clean(
        getattr(
            experiment,
            "construction_protocol",
            "",
        )
    )


def _evidence_source_label(source):
    """
    Human-readable evidence source.
    """

    if source == "protocol":
        return "library construction protocol"

    if source == "title":
        return "experiment title"

    return "available metadata"


# ==========================================================
# Condition / Experimental Context
# ==========================================================

def _detect_condition(title, protocol=""):
    """
    Identify an experimental condition or biological context.

    Context does not automatically establish a treatment assignment.

    Returns a concise phrase rather than an entire title/protocol.
    """

    # ------------------------------------------------------
    # Title-level contextual phrases
    # ------------------------------------------------------

    if title:

        # "infected with ... pathogens" establishes a concise
        # pathogen-infection context. Do not use the pathogen
        # descriptor itself as the condition value.
        if re.search(
            r"\binfected\s+with\b.*\bpathogen(?:s)?\b",
            title,
            flags=re.IGNORECASE,
        ):
            return "pathogen infection"

        title_patterns = [
            r"\b([A-Za-z0-9_-]+\s+stress)\b",
            r"\b(stress\s+(?:condition|response))\b",
            r"\b([A-Za-z0-9_-]+\s+starvation)\b",
            r"\b(starvation)\b",
            r"\b(hypoxia)\b",
            r"\b([A-Za-z0-9_-]+\s+hypoxia)\b",
            r"\b([A-Za-z0-9_-]+\s+limitation)\b",
            r"\b(nutrient\s+(?:limitation|deprivation|restriction))\b",
            r"\b(iron\s+(?:stress|limitation|depletion|exposure))\b",
            r"\b(detergent\s+stress)\b",
            r"\b(antibiotic\s+(?:stress|exposure))\b",

            # Prefer explicit infection context over the generic
            # adjective "infected".
            r"\binfected\s+with\s+(?:a\s+)?"
            r"(?:combination\s+of\s+)?"
            r"([A-Za-z0-9_.,\-+\s]+?)(?:\s*$)",

            r"\b(infection)\b",
        ]

        for pattern in title_patterns:

            match = re.search(
                pattern,
                title,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

    # ------------------------------------------------------
    # Protocol-level explicit contexts
    # ------------------------------------------------------

    if protocol:

        # Explicit pathogen/infection context.
        if re.search(
            r"\b(?:pathogen|pathogens)\b.*\b(?:infect|infection)\b|"
            r"\b(?:infect|infection)\b.*\b(?:pathogen|pathogens)\b",
            protocol,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            return "pathogen infection"

        protocol_patterns = [
            r"\bfirst\s+stressor\b",
            r"\bsecond\s+stressor\b",
            r"\bnematode\s+treatment\b",
            r"\bpathogen\s+(?:infection|treatment)\b",
            r"\bmock\s+treatment\b",
            r"\bexperimental\s+treatment\b",
        ]

        for pattern in protocol_patterns:

            match = re.search(
                pattern,
                protocol,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0).strip()

    # Restrict compact genotype labels to an identified gene and sample token.
    label = re.split(r"^GSM\d+:\s*", title or "", flags=re.I)[-1]
    knockout = re.match(r"^([A-Za-z][A-Za-z0-9.-]*)[_ -]KO(?=$|[_ ,;])", label)
    if knockout:
        return knockout.group(1) + " knockout"
    # Preserve an explicitly labeled sample group, including unexpanded group codes.
    group = re.search(r"(?:^|[;,]\s*)(?:condition|experimental group)\s*[:=]\s*([^;,]+)", label, re.I)
    if group:
        return _clean(group.group(1))
    context = re.search(r"\b([A-Za-z][\w.-]*\s+tethering)\b", label, re.I)
    if context:
        return context.group(1)
    age_genotype = re.search(r"(?:^|[_ ,;])(young|aged|adult|old)[_ -]+wt(?:$|[_ ,;])", label, re.I)
    if age_genotype:
        return age_genotype.group(1).lower() + " wild type"

    return ""


# ==========================================================
# Control Detection
# ==========================================================

def _detect_control(title, protocol=""):
    """
    Detect explicitly documented control information.

    The existence of a treatment/stressor does not imply a control.

    Control information is returned only when explicit control or mock
    language is present.
    """

    texts = []

    if title:
        texts.append(("title", title))

    if protocol:
        texts.append(("protocol", protocol))

    if re.search(r"(?:^|:\s*)(?:control[-_]\d+|\d+\s+control)(?=$|[;,])", title or "", re.I):
        return "control"

    patterns = [
        # Mock treatment / mock control
        (
            r"\bmock\s+(?:treatment|control|treated|treatment\s+group)\b",
            "mock treatment",
        ),
        (
            r"\bmock[-\s]?treated\b",
            "mock-treated",
        ),
        (
            r"\bvehicle\s+control\b",
            "vehicle control",
        ),
        (
            r"\buntreated\s+(?:control|samples?|cells?|plants?|groups?)\b",
            "untreated control",
        ),
        (
            r"\bcontrol\s+(?:group|sample|cells?|plants?|condition)\b",
            "control",
        ),
    ]

    for source, text in texts:

        for pattern, label in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                if source == "protocol":

                    return label

                return match.group(0).strip()

    return ""


# ==========================================================
# Treatment Detection
# ==========================================================

def _extract_treatment_agent(value):
    """
    Clean an explicitly captured treatment phrase.
    """

    value = _clean(value)

    if not value:
        return ""

    value = re.sub(
        r"\s+for\s+(?:\d+(?:\.\d+)?\s*)?(?:h|hours?|days?)\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s+at\s+day\s+\d+.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # Remove a trailing concentration clause from the treatment agent.
    # Match longer units first and prevent M from matching the m in mg/ml.
    value = re.sub(
        r"\s+at\s+\d+(?:\.\d+)?\s*"
        r"(?:(?:mg/ml|mg/l|ug/ml|µg/ml|μg/ml|ng/ml|ng/l|"
        r"g/l|ppm|ppb|nM|uM|µM|μM|mM|pM)\b|M(?![a-z])|%).*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # "stressor" describes the role of the intervention; it is
    # not part of the treatment agent itself.
    value = re.sub(
        r"^stressor\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return value.strip(" ,.;:-")


def _detect_treatment(title, protocol=""):
    """
    Detect an explicit treatment relationship.

    A treatment keyword alone is insufficient.

    The function recognizes treatment only when language establishes
    that experimental material received, was exposed to, was treated
    with, was inoculated with, or otherwise underwent an intervention.

    Protocol evidence has priority over title evidence.
    """

    texts = []

    if protocol:
        # Exclude treatment of extracted material while retaining other clauses.
        protocol = re.sub(
            r"\b(?:RNAs?|DNAs?|cDNAs?|libraries|lysates?|extracts?)\s+"
            r"(?:(?:were|was|are|is)\s+)?treated\s+with\b[^.;\n]*",
            " ", protocol, flags=re.IGNORECASE,
        )
        texts.append(("protocol", protocol))

    if title:
        texts.append(("title", title))

    patterns = [
        # treated with X
        r"\btreated\s+with\s+(.+?)(?=\.(?!\d)|[,;:\n]|$)",

        # treatment with X
        r"\btreatment\s+with\s+([^,.;:\n]+?)(?=\s+was\s+(?:performed|applied|administered)\b|[,.;:\n]|$)",

        # exposed to X
        r"\bexposed\s+to\s+([^,.;:\n]+)",

        # exposure to X
        r"\bexposure\s+to\s+([^,.;:\n]+)",

        # X exposure in cells/samples/cultures/plants/etc.
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"\s+exposure\s+in\s+"
        r"(?:cultured\s+)?(?:cells?|samples?|cultures?|organisms?|plants?|seedlings?)\b",

        # received X
        r"\b(?:animals?|mice|rats|subjects?|donors?|participants?|cells?|plants?|cultures?|seedlings?|samples?)\s+received\s+([^,.;:\n]+)",

        # X treatment was performed
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"\s+treatment\s+was\s+(?:performed|applied|administered)\b",

        # treatment was performed with X
        r"\btreatment\s+was\s+(?:performed|applied|administered)"
        r"\s+(?:with|using)\s+([^,.;:\n]+)",

        # X treatment was given
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"\s+treatment\s+was\s+given\b",

        # inoculated with X
        r"\binoculated\s+with\s+([^,.;:\n]+)",

        # inoculation with X
        r"\binoculation\s+with\s+([^,.;:\n]+)",

        # X-treated cells/samples/plants/etc.
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"[-\s]treated\s+"
        r"(?:cells?|samples?|cultures?|organisms?|plants?|seedlings?)\b",

        # X-inoculated
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"[-\s]inoculated\s+"
        r"(?:cells?|samples?|cultures?|organisms?|plants?|seedlings?)\b",

        # X-inoculated as an experiment label
        r"\b([A-Za-z0-9_/-]+)-inoculated\b",
    ]

    for source, text in texts:

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            if source == "protocol" and re.search(
                r"\b(?:RNase\s+[AH]|DNase\s+I|dsDNA\s+Fragmentase|primary antibodies)\b",
                match.group(0), re.I
            ):
                # Only exclude a reagent in a library-preparation context.
                start = max(text.rfind(".", 0, match.start()), text.rfind(";", 0, match.start())) + 1
                clause = text[start:match.end()]
                if re.search(r"chromatin|elut(?:ed|ion)|bisulfite|coverslip|libraries|library", clause, re.I):
                    continue

            if match.lastindex:

                value = _extract_treatment_agent(
                    match.group(match.lastindex)
                )

                if value:

                    # Explicit inoculation relationship
                    if re.search(
                        r"inoculat",
                        match.group(0),
                        flags=re.IGNORECASE,
                    ):
                        return value + " inoculation"

                    return value

            matched = match.group(0).strip()

            if matched:
                return matched

    return ""


# ==========================================================
# Time Point Detection
# ==========================================================

def _detect_time_point(title, protocol=""):
    """
    Detect explicitly documented sampling time information.

    Unlike title-only detection, protocol evidence can establish
    day-based sampling schedules.

    Examples:

        6h
        24 hours
        day 3
        days 1, 2, 3
        post 1, 2, 3, 4, 5 day
        time point
    """

    texts = []
    if title:
        # Library preparation durations may appear beside a biological time point.
        title = re.sub(
            r"\b\d+(?:\.\d+)?\s*(?:hours?|h)\s+(?:adapter\s+)?ligation\b"
            r"|\b(?:adapter\s+)?ligation\s+(?:for\s+)?\d+(?:\.\d+)?\s*(?:hours?|h)\b",
            " ", title, flags=re.IGNORECASE,
        )
        texts.append(("title", title))
    if protocol:
        # Incubation and sequencing durations do not establish sampling times.
        sampling_phrase = re.compile(
            r"\b(?:sampling|harvested|collected|sampled)\s+(?:(?:at|on|after)\s+)?"
            r"(?:days?\s+[\d, -]+|\d+(?:\.\d+)?\s*(?:hours?|h|days?)\b)"
            r"|\bpost\s+[\d, -]+\s+days?\b", re.I
        )
        culture_time = re.search(
            r"\bat (\d+ days? in vitro)\b[^.;]{0,150}\b(?:collected|harvested)\b",
            protocol, re.I
        )
        if culture_time:
            texts.append(("protocol", culture_time.group(1)))
        for phrase in sampling_phrase.finditer(protocol):
            texts.append(("protocol", phrase.group()))

    # ------------------------------------------------------
    # Protocol: sampling after X days
    # ------------------------------------------------------

    for source, text in texts:

        match = re.search(
            r"\bpost\s+"
            r"((?:\d+(?:\s*,\s*|\s+and\s+|\s*-\s*)?)+)"
            r"\s*day(?:s)?\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:

            values = _clean(
                match.group(1)
            )

            if values:
                return "Post-treatment days " + values

        match = re.search(
            r"\bsampling\s+(?:at|on)\s+"
            r"((?:day|days)\s+[^.;\n]+)",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return _clean(match.group(1))

        match = re.search(
            r"\b(?:at|on)\s+day\s+(\d+(?:\s*[-,]\s*\d+)*)\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return "Day " + _clean(match.group(1))

        # --------------------------------------------------
        if source == "protocol" and "days in vitro" not in text.lower() and "day in vitro" not in text.lower():
            day = re.search(r"\b(?:day\s+(\d+)|(\d+)\s+days?)\b", text, re.I)
            if day:
                return "Day " + (day.group(1) or day.group(2))

        if source == "title":
            age_code = re.search(r"(?:^|:\s*|\bin\s+)((?:PN|E)\d+(?:\.\d+)?)\s+(?=[a-z])", text)
            if age_code:
                return age_code[1]
            stage = re.search(r"\b(\d+[- ]cell stage)\b", text, re.I)
            if stage:
                return stage.group(1)
            day = re.search(r"(?:^|[ _,;:-])(?:day\s*|D)(\d+)(?=$|[ _,;:-])", text, re.I)
            if day:
                return "Day " + day.group(1)
            developmental_time = re.search(r"\b(\d+dAE)\b", text, re.I)
            if developmental_time:
                return developmental_time.group(1)
        elif re.search(r"\bdays? in vitro\b", text, re.I):
            return text.strip()

        # Hour-based time points
        # --------------------------------------------------

        match = re.search(
            r"\b(\d+(?:\.\d+)?\s*h)\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        match = re.search(
            r"\b(\d+(?:\.\d+)?\s+hours?)\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        if re.search(
            r"\btime\s+point\b",
            text,
            flags=re.IGNORECASE,
        ):
            return "Time point mentioned"

    return ""


# ==========================================================
# Replicate Assessment
# ==========================================================


def _biosample_sample_design_values(metadata):
    """
    Return explicit sample-level treatment and time-point annotations.

    These values describe the inspected BioSample only; they do not
    establish study-level groups or the complete experimental design.
    """

    sample = _get_sample(metadata)
    if sample is None:
        return "", ""

    treatment = ""
    time_point = ""

    ambiguous_treatments = {
        "control",
        "none",
        "none (parental control)",
        "parental control",
        "not applicable",
        "not specified",
        "untreated",
        "unknown",
    }

    for attribute in getattr(sample, "attributes", []) or []:
        names = {
            str(getattr(attribute, field, "") or "").strip().lower()
            for field in ("name", "harmonized_name", "display_name")
        }
        value = _clean(getattr(attribute, "value", ""))

        if not value:
            continue

        if (
            not treatment
            and names.intersection({"treatment"})
            and value.casefold() not in ambiguous_treatments
            and not re.search(r"\b(?:no treatment|control)\b", value, re.I)
            and not re.search(
                r"\b(?:control group|control samples?|parental control)\b",
                value,
                flags=re.IGNORECASE,
            )
        ):
            treatment = value

        if (
            not time_point
            and names.intersection({"time", "timepoint", "time point", "time_point"})
            and re.fullmatch(
                r"(?:differentiation\s+)?(?:(?:day|week|month|hour|hr|h|d|wk)\s*[-_ ]?\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:minutes?|min|hours?|hrs?|h|days?|weeks?|wk|months?))",
                value,
                flags=re.IGNORECASE,
            )
        ):
            time_point = value

    if not time_point:
        days = _sample_attribute_values(metadata, {"days in vitro"})
        if len(days) == 1 and re.fullmatch(r"\d+(?:\.\d+)?", days[0]):
            time_point = days[0] + " days in vitro"
    if not time_point:
        injection = _sample_attribute_values(metadata, {"pre or post injection"})
        if len(injection) == 1 and injection[0].lower() in {"pre", "post"}:
            time_point = injection[0].lower() + "-injection"
    if not time_point and treatment:
        duration = re.search(r"\b(\d+(?:\.\d+)?\s*(?:hours?|hrs?|h))\s*\)?$", treatment, re.I)
        if duration:
            time_point = duration[1]
    return treatment, time_point


def _biosample_design_annotations(metadata):
    """
    Collect explicitly deposited experimental-design attributes
    from structured BioSample metadata.

    These values are observational evidence only. They are not used
    here to infer study-level treatment/control groups, contrasts,
    time-course structure, or statistical design formulas.
    """

    sample = _get_sample(metadata)

    if sample is None:
        return []

    attributes = getattr(
        sample,
        "attributes",
        [],
    )

    annotations = []

    recognized_names = {
        "condition": "Condition",
        "experimental condition": "Experimental condition",
        "experimental_condition": "Experimental condition",
        "treatment": "Treatment",
        "control": "Control",
        "time": "Time",
        "timepoint": "Time point",
        "time point": "Time point",
        "time_point": "Time point",
    }

    for attribute in attributes:
        names = [
            getattr(attribute, "name", ""),
            getattr(attribute, "harmonized_name", ""),
            getattr(attribute, "display_name", ""),
        ]

        normalized_names = {
            str(name).strip().lower()
            for name in names
            if name
        }

        label = ""

        for name, candidate_label in recognized_names.items():
            if name in normalized_names:
                label = candidate_label
                break

        if not label:
            continue

        value = _clean(
            getattr(
                attribute,
                "value",
                "",
            )
        )

        if not value:
            continue

        annotation = (
            "BioSample structured metadata explicitly reports "
            f"{label.lower()}: {value}"
        )

        _append_unique(
            annotations,
            annotation,
        )

    return annotations


def _sample_attribute_values(metadata, keys):
    """Collect distinct non-placeholder values for explicit sample attributes."""
    values = []
    for attribute in getattr(_get_sample(metadata), "attributes", []) or []:
        names = {str(getattr(attribute, k, "") or "").strip().lower().replace("_", " ")
                 for k in ("name", "display_name", "harmonized_name")}
        value = _clean(getattr(attribute, "value", ""))
        if names & keys and value and value.lower() not in {"unknown", "not collected", "not provided", "not applicable", "not specified", "none", "n/a", "n.a.", "na", "missing"} and not value.lower().startswith("missing:"):
            if value not in values:
                values.append(value)
    return values


def _sample_design_labels(metadata):
    """Recover accession-scoped labels; keep study-wide assignments separate."""
    condition = ""
    control = ""
    replicate = ""
    title = _clean(getattr(_get_experiment(metadata), "title", ""))
    # Prefer a deposited group or phenotype. If the title identifies a genotype,
    # preserve that identity separately from an intervention on the same sample.
    for keys in ({"condition", "experimental condition", "experimental group"},
                 {"disease state"}, {"injury"}):
        values = _sample_attribute_values(metadata, keys)
        if values:
            condition = values[0] if len(values) == 1 else ""
            break
    else:
        genotypes = _sample_attribute_values(metadata, {"genotype"})
        interventions = _sample_attribute_values(metadata, {"treatment"})
        if len(genotypes) == 1 and not interventions:
            condition = genotypes[0]
        for keys in ({"genotype"}, {"cell line"}, {"ecotype"}, {"dev stage", "developmental stage"}):
            if condition:
                break
            values = _sample_attribute_values(metadata, keys)
            if len(values) == 1:
                token = re.escape(values[0]).replace(r"\-", "[-_ ]?").replace(r"\ ", "[-_ ]+")
                if re.search(r"(?<![A-Za-z0-9])"+token+r"(?=$|[^A-Za-z]|\d)", title, re.I):
                    condition = values[0]
                    break
        if not condition:
            for keys in ({"treatment"}, {"genotype"}):
                values = _sample_attribute_values(metadata, keys)
                if values:
                    condition = values[0] if len(values) == 1 else ""
                    break
    injection = _sample_attribute_values(metadata, {"pre or post injection"})
    if len(injection) == 1 and injection[0].lower() in {"pre", "post"}:
        if condition in _sample_attribute_values(metadata, {"treatment"}):
            condition = injection[0].lower() + "-injection"

    roles = _sample_attribute_values(metadata, {"sample role", "experimental group", "treatment", "genotype", "disease state"})
    for role in roles:
        if re.fullmatch(r"sham[- ]operated", role, re.I):
            control = "sham-operated"
            break
        if re.fullmatch(r"(?:control|ctrl|no treatment\s*\(control\)|euthermic control(?:\s+\d+)?)", role, re.I):
            control = "control"

    if re.fullmatch(r"no treatment\s*\(control\)", condition, re.I):
        condition = "Control"
    role_labels = _sample_attribute_values(metadata, {"replicate", "replication"})
    if len(role_labels) == 1 and re.match(r"^control[-_]", role_labels[0], re.I):
        control = control or "control"
        condition = condition or "Control"

    for keys, prefix in (({"biological replicate"}, "Biological"), ({"technical replicate"}, "Technical"),
                         ({"replicate", "replication", "replicate number"}, "")):
        values = _sample_attribute_values(metadata, keys)
        if not values:
            continue
        if len(values) == 1:
            value = values[0]
            number = re.search(r"(?:^|[-_\s])(?:rep(?:licate|lication)?[._ -]*)?(\d+)$", value, re.I)
            # A numeric suffix on an opaque label is not itself a replicate number.
            if number and (value.isdigit() or re.search(r"rep(?:licate|lication)?[._ -]*\d+$", value, re.I)):
                replicate = (f"{prefix} replicate {number[1]}" if prefix
                             else f"Replicate {number[1]}; type unspecified")
            elif not prefix:
                replicate = f"Replicate label {value}; type unspecified"
            else:
                replicate = f"{prefix} replicate {value}"
        break
    if not replicate:
        for text in [title, *_sample_attribute_values(metadata, {"source name"})]:
            typed = re.search(r"(?:^|[\s,;:_-])(biol(?:ogical)?|tech(?:nical)?)\.?[ _-]+rep(?:licate)?[ ._-]*(\d+)\b", text, re.I)
            if typed:
                kind = "Biological" if typed[1].lower().startswith("biol") else "Technical"
                replicate = f"{kind} replicate {typed[2]}"
                break
    return condition, control, replicate


def _biosample_replicate_annotation(metadata):
    """
    Detect an explicitly deposited biological-replicate annotation
    from structured BioSample attributes.

    This is observational evidence only. It does not establish the
    complete study-level replicate structure.
    """

    sample = getattr(
        metadata,
        "sample",
        None,
    )

    if sample is None:
        return ""

    attributes = getattr(
        sample,
        "attributes",
        [],
    )

    for attribute in attributes:

        names = [
            getattr(
                attribute,
                "name",
                "",
            ),
            getattr(
                attribute,
                "harmonized_name",
                "",
            ),
            getattr(
                attribute,
                "display_name",
                "",
            ),
        ]

        normalized_names = {
            str(name).strip().lower()
            for name in names
            if name
        }

        value = str(
            getattr(
                attribute,
                "value",
                "",
            )
        ).strip()

        normalized_value = value.lower()

        name_is_biological = any(
            name in {
                "biological replicate",
                "biological_replicate",
                "biological-replicate",
            }
            for name in normalized_names
        )

        name_is_generic_replicate = any(
            name in {
                "replicate",
                "replicate number",
                "replicate_number",
            }
            for name in normalized_names
        )

        value_is_biological = bool(
            re.search(
                r"\bbiological\s+replicate\b",
                normalized_value,
                flags=re.IGNORECASE,
            )
        )

        if not (
            name_is_biological
            or (
                name_is_generic_replicate
                and value_is_biological
            )
        ):
            continue

        if value:
            return (
                f"Biological replicate annotation '{value}' "
                "is explicitly reported in the BioSample metadata. "
                "This provides partial replicate evidence; complete "
                "sample-level replicate structure is not established "
                "from the inspected accession alone."
            )

        return (
            "A biological replicate annotation is explicitly "
            "reported in the BioSample metadata; the replicate "
            "identifier/value is not specified."
        )

    return ""


def _assess_replicates(metadata):
    """
    Assess explicit replicate information.

    Priority:

    1. Construction protocol
    2. Experiment title
    3. Structured BioSample biological-replicate annotation
    4. Run metadata

    A sequencing run is never interpreted as a biological replicate.

    BioSample replicate annotations are treated as partial evidence
    unless the available metadata establishes the complete sample-level
    replicate structure.
    """

    experiment = _get_experiment(metadata)

    title = _clean(getattr(experiment, "title", ""))
    protocol = _protocol(metadata)

    # ------------------------------------------------------
    # Protocol: explicit biological replicates
    # ------------------------------------------------------

    if protocol:

        if re.search(r"\bpooled\s+(?:as|into)\s+(?:one|a single)\s+biological replicate\b", protocol, re.I):
            return "One pooled biological replicate per sample"

        patterns = [
            r"\b(\d+)\s+biological\s+replicates?\b",
            r"\bthree\s+biological\s+replicates?\b",
            r"\btwo\s+biological\s+replicates?\b",
            r"\bfour\s+biological\s+replicates?\b",
            r"\bfive\s+biological\s+replicates?\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                protocol,
                flags=re.IGNORECASE,
            )

            if match:

                phrase = match.group(0).strip()

                number_map = {
                    "two": "2",
                    "three": "3",
                    "four": "4",
                    "five": "5",
                }

                for word, number in number_map.items():

                    phrase = re.sub(
                        rf"\b{word}\b",
                        number,
                        phrase,
                        flags=re.IGNORECASE,
                    )

                return (
                    phrase.capitalize()
                    + " are explicitly documented in the "
                    "library construction protocol."
                )

        if re.search(
            r"\bbiological\s+replicate\b",
            protocol,
            flags=re.IGNORECASE,
        ):
            return (
                "Biological replicate information is explicitly "
                "documented in the library construction protocol."
            )

    # ------------------------------------------------------
    # Title: explicit biological replicate
    # ------------------------------------------------------

    biosample_replicate = _biosample_replicate_annotation(metadata)

    if title:

        # Token boundaries accommodate submitter separators, including underscores.
        compact = re.search(
            r"(?:^|[.\s_,;:-])(?:(biological|technical)[ _-]+)?"
            r"rep(?:licate)?[._ -]*(\d+)(?=$|[\s_,;:-])", title, re.I
        )
        if compact:
            kind, label = compact.groups()
            if kind:
                if kind.lower() == "technical":
                    return f"Technical replicate {label}; biological replicate status is not established."
                return f"Biological replicate {label} is explicitly identified in the experiment title."
            return biosample_replicate or f"Replicate {label}; type unspecified"

        match = re.search(
            r"\bbiological\s+replicate\s+([A-Za-z0-9_-]+)",
            title,
            flags=re.IGNORECASE,
        )

        if match:

            return (
                f"Biological replicate {match.group(1)} is explicitly "
                "identified in the experiment title."
            )

        match = re.search(
            r"\breplicate\s+([A-Za-z0-9_-]+)",
            title,
            flags=re.IGNORECASE,
        )

        if match:

            return (
                f"Replicate {match.group(1)} is explicitly identified "
                "in the experiment title; biological or technical "
                "replicate status is not established."
            )

    # ------------------------------------------------------
    # BioSample: structured biological replicate annotation
    # ------------------------------------------------------

    if biosample_replicate:
        return biosample_replicate
    labels = _sample_attribute_values(metadata, {"replicate", "replication", "replicate number"})
    if len(labels) == 1:
        identifier = labels[0]
        number = re.fullmatch(r"(?:rep(?:licate|lication)?[ ._:-]*)?(\d+)", identifier, re.I)
        if number:
            return f"Replicate {number.group(1)}; type unspecified"
        return f"Replicate label {identifier}; type unspecified"

    # Replication is meaningful for every assay. A run identifier alone
    # leaves biological replication unresolved regardless of library strategy.
    # ------------------------------------------------------
    # Run metadata
    # ------------------------------------------------------

    run = getattr(
        metadata,
        "run",
        None,
    )

    run_accession = ""

    if run is not None:
        run_accession = _clean(
            getattr(
                run,
                "accession",
                "",
            )
        )

    if run_accession:
        return (
            "One sequencing run is represented by the inspected "
            "accession; biological replicate status is not "
            "established by this information alone."
        )

    return (
        "Replicate structure could not be established from the "
        "available metadata."
    )


def _has_complex_design(metadata):
    """
    Identify protocol language indicating a multifactorial or
    sequential experimental design.

    This does not determine the experimental groups. It only prevents
    Scout from assigning the strongest confidence level when the
    available evidence indicates that the design is more complex than
    a simple single-factor treatment/control experiment.
    """

    protocol = _protocol(metadata)

    if not protocol:
        return False

    complexity_patterns = [
        r"\bfirst\s+stressor\b",
        r"\bsecond\s+stressor\b",
        r"\bmultiple\s+(?:stressors?|treatments?|pathogens?)\b",
        r"\bcombination\s+of\s+[^.\n]*pathogens?\b",
        r"\b(?:above|below)[-\s]ground\s+pathogens?\b",
        r"\bmock\s+treatment\b",
    ]

    for pattern in complexity_patterns:

        if re.search(
            pattern,
            protocol,
            flags=re.IGNORECASE,
        ):
            return True

    return False


# ==========================================================
# Design description
# ==========================================================

def _build_design_description(
    condition,
    control,
    treatment,
    time_point,
    replicate_information,
):
    """
    Build a conservative natural-language description.
    """

    established = []

    if condition:
        established.append("experimental context")

    if control:
        established.append("control information")

    if treatment:
        established.append("treatment information")

    if time_point:
        established.append("time-point information")

    if (
        replicate_information
        and "could not be established"
        not in replicate_information.lower()
        and "not established"
        not in replicate_information.lower()
        and "type unspecified" not in replicate_information.lower()
        and "one pooled biological replicate" not in replicate_information.lower()
    ):
        established.append("replicate information")

    if (
        condition
        and control
        and treatment
        and replicate_information
        and "could not be established"
        not in replicate_information.lower()
        and "not established"
        not in replicate_information.lower()
        and "type unspecified" not in replicate_information.lower()
        and "one pooled biological replicate" not in replicate_information.lower()
    ):
        return (
            "The available metadata explicitly document key elements "
            "of the experimental design, including experimental "
            "context, treatment/control information, and replicate "
            "structure."
        )

    if established:

        return (
            "The available metadata contain explicit experimental "
            "design information, but the complete experimental group "
            "structure cannot be established from the inspected "
            "accession alone."
        )

    return (
        "The available metadata do not provide enough information "
        "to establish the experimental design."
    )


# ==========================================================
# Main Layer 2 Function
# ==========================================================

def _add_study_biosample_patterns(insight, evidence):
    """Summarize explicit treatment/time attributes across BioSamples.

    These summaries are observed metadata patterns, not assignments
    of study-level groups or biological replicate structure.
    """
    if evidence is None:
        return

    retrieved = getattr(evidence, "retrieved_biosample_count", 0)
    unique = getattr(evidence, "unique_biosample_count", 0)

    _append_unique(
        insight.observed_features,
        f"Study BioSample metadata retrieved for {retrieved} of "
        f"{unique} unique BioSamples.",
    )

    attribute_values = getattr(evidence, "attribute_values", {}) or {}

    treatment_keys = {
        "treatment",
        "treatments",
        "experimental treatment",
        "experimental_treatment",
        "treatment group",
        "treatment_group",
    }
    time_keys = {
        "time",
        "time point",
        "time_point",
        "timepoint",
        "sampling time",
        "sampling_time",
        "collection time",
        "collection_time",
    }

    def normalize_key(value):
        return " ".join(
            str(value).strip().lower().replace("-", " ").split()
        )

    def summarize(keys, label):
        matched = []
        for key, values in attribute_values.items():
            normalized_key = normalize_key(key)
            normalized_key_underscore = normalized_key.replace(" ", "_")
            if (
                normalized_key not in keys
                and normalized_key_underscore not in keys
            ):
                continue

            if not isinstance(values, dict):
                continue

            entries = [
                (str(value).strip(), count)
                for value, count in values.items()
                if str(value).strip() and isinstance(count, int) and count > 0
            ]
            if entries:
                entries.sort(key=lambda item: item[0].lower())
                pattern = ", ".join(
                    f"{value} ({count} BioSample{'s' if count != 1 else ''})"
                    for value, count in entries
                )
                matched.append(f"{key}: {pattern}")

        if matched:
            _append_unique(
                insight.observed_features,
                f"Observed study BioSample {label} patterns — "
                + "; ".join(matched)
                + ". Counts represent BioSample records, not confirmed "
                  "independent biological replicates.",
            )

    summarize(treatment_keys, "treatment")
    summarize(time_keys, "time-point")

    for warning in getattr(evidence, "warnings", []) or []:
        if warning:
            _append_unique(
                insight.warnings,
                f"Study BioSample enrichment: {warning}",
            )


def generate_design_insight(metadata, study_biosample_evidence=None):
    """
    Generate an evidence-based experimental design interpretation.

    Construction protocol information is treated as observed evidence
    when it explicitly documents a design feature.
    """

    insight = ExperimentalDesignInsight()

    (
        insight.sample_treatment,
        insight.sample_time_point,
    ) = _biosample_sample_design_values(metadata)

    (insight.sample_condition, insight.sample_control,
     insight.sample_replicate_status) = _sample_design_labels(metadata)

    ages = _sample_attribute_values(metadata, {"age", "age at collection"})
    stages = _sample_attribute_values(metadata, {"dev stage", "developmental stage"})
    if len(ages) == 1:
        insight.sample_age = ages[0]
    if len(stages) == 1:
        insight.sample_developmental_stage = stages[0]

    _add_study_biosample_patterns(
        insight,
        study_biosample_evidence,
    )

    observed = _collect_observed_metadata(
        metadata
    )

    title = observed.get(
        "title",
        "",
    )

    protocol = observed.get(
        "construction_protocol",
        "",
    )

    # ------------------------------------------------------
    # Record basic observed metadata
    # ------------------------------------------------------

    if title:

        _append_unique(
            insight.observed_features,
            f"Experiment title: {title}",
        )

    if observed.get("library_strategy"):

        _append_unique(
            insight.observed_features,
            "Library strategy: "
            + observed["library_strategy"],
        )

    if observed.get("layout"):

        _append_unique(
            insight.observed_features,
            "Sequencing layout: "
            + observed["layout"],
        )

    if observed.get("platform"):

        _append_unique(
            insight.observed_features,
            "Sequencing platform: "
            + observed["platform"],
        )

    if observed.get("organism"):

        _append_unique(
            insight.observed_features,
            "Organism: "
            + observed["organism"],
        )

    if protocol:

        _append_unique(
            insight.observed_features,
            "Library construction protocol is available as an "
            "experimental-design evidence source.",
        )

    # ------------------------------------------------------
    # Structured BioSample experimental-design evidence
    # ------------------------------------------------------

    biosample_design_annotations = _biosample_design_annotations(
        metadata
    )

    for annotation in biosample_design_annotations:

        _append_unique(
            insight.observed_features,
            annotation,
        )

    # ------------------------------------------------------
    # Condition
    # ------------------------------------------------------

    condition = _detect_condition(
        title,
        protocol,
    )

    if condition:

        insight.condition = condition

        # If the protocol independently supports the biological
        # context, record the resulting interpretation as observed
        # evidence rather than treating it as title-only inference.
        protocol_support = False

        if protocol:

            if condition.lower() == "pathogen infection":

                protocol_support = bool(
                    re.search(
                        r"\b(?:pathogen|pathogens)\b|"
                        r"\binfect(?:ed|ion|ious)?\b|"
                        r"\bstressor\b",
                        protocol,
                        flags=re.IGNORECASE,
                    )
                )

            else:

                protocol_support = bool(
                    re.search(
                        re.escape(condition),
                        protocol,
                        flags=re.IGNORECASE,
                    )
                )

        if protocol_support:

            _append_unique(
                insight.observed_features,
                "Experimental context explicitly supported by "
                "the library construction protocol: "
                + condition,
            )

        else:

            _append_unique(
                insight.inferred_features,
                "The experiment title suggests an experimental "
                "condition or context: "
                + condition
                + ".",
            )

    # ------------------------------------------------------
    # Control
    # ------------------------------------------------------

    control = _detect_control(title, protocol)
    if not control and observed.get("library_strategy") == "CHIP_SEQ":
        if re.search(r"(?:^|[ _,;:(-])input(?=$|[ _,;:)-])", title or "", re.I):
            control = "input control"

    if control:

        insight.control = control

        if protocol and re.search(
            r"\bmock\s+(?:treatment|control)\b|"
            r"\bvehicle\s+control\b|"
            r"\buntreated\s+(?:control|samples?|cells?|plants?)\b",
            protocol,
            flags=re.IGNORECASE,
        ):
            _append_unique(
                insight.observed_features,
                "Control information explicitly documented in the "
                "library construction protocol: "
                + control,
            )

        else:

            _append_unique(
                insight.observed_features,
                "Control terminology explicitly present in the "
                "experiment title: "
                + control,
            )

    else:

        _append_unique(
            insight.warnings,
            "No explicit control group was identified from the "
            "available metadata.",
        )

        _append_unique(
            insight.missing_information,
            "Control-group annotation",
        )

    # ------------------------------------------------------
    # Treatment
    # ------------------------------------------------------

    treatment = _detect_treatment(
        title,
        protocol,
    )

    if treatment:

        insight.treatment = treatment

        if protocol:

            _append_unique(
                insight.observed_features,
                "Treatment/intervention relationship explicitly "
                "documented in the library construction protocol: "
                + treatment,
            )

        else:

            _append_unique(
                insight.observed_features,
                "Treatment relationship explicitly present in the "
                "experiment title: "
                + treatment,
            )

    else:

        _append_unique(
            insight.warnings,
            "No unambiguous treatment assignment was identified "
            "from the available metadata.",
        )

        _append_unique(
            insight.missing_information,
            "Treatment-group annotation, if applicable",
        )

    # ------------------------------------------------------
    # Time point
    # ------------------------------------------------------

    time_point = _detect_time_point(
        title,
        protocol,
    )

    if time_point:

        insight.time_point = time_point

        if not _detect_time_point(title):

            _append_unique(
                insight.observed_features,
                "Sampling time information explicitly documented "
                "in the library construction protocol: "
                + time_point,
            )

        else:

            _append_unique(
                insight.observed_features,
                "Time-point information explicitly present in the "
                "experiment title: "
                + time_point,
            )

    else:

        _append_unique(
            insight.missing_information,
            "Time-point information, if applicable",
        )

    # ------------------------------------------------------
    # Replicates
    # ------------------------------------------------------

    insight.replicate_information = _assess_replicates(
        metadata
    )

    replicate_text = insight.replicate_information.lower()

    has_partial_replicate_evidence = (
        "partial replicate evidence" in replicate_text
    )

    replicate_structure_unresolved = (
        "could not be established" in replicate_text
        or "type unspecified" in replicate_text
        or "not established" in replicate_text
    )

    if has_partial_replicate_evidence:

        _append_unique(
            insight.observed_features,
            "Partial biological replicate evidence explicitly "
            "documented in available BioSample metadata; complete "
            "sample-level replicate structure remains unresolved.",
        )

    elif not replicate_structure_unresolved:

        if protocol and "protocol" in replicate_text:

            _append_unique(
                insight.observed_features,
                "Biological replicate information explicitly "
                "documented in the library construction protocol.",
            )

        else:

            _append_unique(
                insight.observed_features,
                "Replicate information explicitly documented in "
                "available metadata.",
            )

    else:

        _append_unique(
            insight.missing_information,
            "Biological replicate annotation",
        )

    # ------------------------------------------------------
    # Conservative warning
    # ------------------------------------------------------

    if _has_complex_design(metadata):

        _append_unique(
            insight.warnings,
            "The available protocol indicates a multifactorial or "
            "sequential experimental design; complete sample-level "
            "group assignments are not established by this accession "
            "alone.",
        )

    if (
        condition
        or control
        or treatment
        or time_point
    ):

        _append_unique(
            insight.warnings,
            "Experimental relationships are interpreted from "
            "explicitly documented metadata; sample-level group "
            "assignments should be confirmed before downstream "
            "statistical analysis.",
        )

    # ------------------------------------------------------
    # Design confidence
    # ------------------------------------------------------

    established_count = 0

    if condition:
        established_count += 1

    if control:
        established_count += 1

    if treatment:
        established_count += 1

    if time_point:
        established_count += 1

    if (
        insight.replicate_information
        and "could not be established"
        not in insight.replicate_information.lower()
        and "not established"
        not in insight.replicate_information.lower()
        and "type unspecified" not in insight.replicate_information.lower()
        and "one pooled biological replicate" not in insight.replicate_information.lower()
    ):
        established_count += 1

    if protocol:

        # Rich protocol evidence is not equivalent to a completely
        # resolved sample-level experimental design. In particular,
        # unresolved treatment/control relationships should prevent
        # the strongest confidence label.

        complete_group_structure = (
            bool(treatment)
            and bool(control)
            and (
                insight.replicate_information
                and "could not be established"
                not in insight.replicate_information.lower()
                and "not established"
                not in insight.replicate_information.lower()
                and "type unspecified" not in insight.replicate_information.lower()
                and "one pooled biological replicate" not in insight.replicate_information.lower()
            )
        )

        complex_design = _has_complex_design(metadata)

        # A multifactorial/sequential protocol can contain strong
        # evidence while still lacking sample-level group mapping.
        # Do not call such a design "Well characterized" merely
        # because several metadata fields were detected.
        if (
            established_count >= 4
            and complete_group_structure
            and not complex_design
        ):

            insight.design_confidence = (
                "Well characterized"
            )

        elif established_count >= 3:

            insight.design_confidence = (
                "Substantially characterized"
            )

        elif established_count >= 2:

            insight.design_confidence = (
                "Partially characterized"
            )

        elif (
            insight.sample_treatment
            and insight.sample_time_point
        ):

            # Sample-level annotations support partial evidence only.
            # They do not establish study-level group assignments.
            insight.design_confidence = (
                "Partially characterized"
            )

        else:

            insight.design_confidence = (
                "Insufficient information"
            )

    else:

        if established_count >= 3:

            insight.design_confidence = (
                "Substantially characterized"
            )

        elif established_count >= 2:

            insight.design_confidence = (
                "Partially characterized"
            )

        elif (
            insight.sample_treatment
            and insight.sample_time_point
        ):

            # Explicit sample-level annotations support partial
            # evidence, but do not establish study-level assignments.
            insight.design_confidence = (
                "Partially characterized"
            )

        else:

            insight.design_confidence = (
                "Insufficient information"
            )

    # ------------------------------------------------------
    # Description
    # ------------------------------------------------------

    insight.design_description = _build_design_description(
        condition,
        control,
        treatment,
        time_point,
        insight.replicate_information,
    )

    # Explain the confidence decision without promoting sample-level
    # annotations into study-level assignments.
    if insight.design_confidence == "Well characterized":
        explanation = (
            "Multiple study-level design features are established, "
            "including treatment/control structure and replicate "
            "information. Confirm group assignments before analysis."
        )
    elif insight.design_confidence == "Substantially characterized":
        explanation = (
            "Several study-level design features are established, "
            "but some aspects of the experimental structure remain "
            "unresolved."
        )
    elif insight.design_confidence == "Partially characterized":
        explanation = (
            "Some design evidence is available, but the complete "
            "study-level experimental structure is not established."
        )
    else:
        explanation = (
            "Available metadata does not establish enough of the "
            "study-level experimental design for a stronger "
            "confidence assessment."
        )

    sample_evidence = []
    if insight.sample_condition:
        sample_evidence.append(f"BioSample condition observed: {insight.sample_condition}")
    if insight.sample_treatment:
        sample_evidence.append(
            f"BioSample treatment observed: {insight.sample_treatment}"
        )
    if insight.sample_time_point:
        sample_evidence.append(
            f"BioSample time point observed: {insight.sample_time_point}"
        )

    if sample_evidence:
        explanation += (
            " Sample-level evidence: "
            + "; ".join(sample_evidence)
            + ". These observations do not independently establish "
              "study-level treatment groups or the complete design."
        )

    unresolved = []
    if not control:
        unresolved.append("control/group structure")
    if not treatment:
        unresolved.append("study-level treatment assignment")
    if not time_point:
        unresolved.append("study-level time-point structure")
    if (
        not insight.replicate_information
        or "could not be established"
        in insight.replicate_information.lower()
        or "type unspecified" in insight.replicate_information.lower()
        or "not established"
        in insight.replicate_information.lower()
    ):
        unresolved.append("complete replicate structure")

    if unresolved:
        explanation += (
            " Not established from the available evidence: "
            + ", ".join(unresolved)
            + "."
        )

    insight.confidence_explanation = explanation

    return insight
