"""Generate a report from saved live-answer RAGAS v3 results."""

from datetime import date
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from evaluation.evaluation_metadata import RAGAS_VERSION
from evaluation.knowledge_base import KNOWLEDGE_BASE_DOCUMENTS
from evaluation.ragas_dataset_v3 import EVALUATION_DATASET
from evaluation.run_ragas import EVALUATOR_MODEL_V3, PRODUCTION_MODEL_NAME


EVALUATION_DIR = Path(__file__).parent
RESULTS_FILE = EVALUATION_DIR / "ragas_results_v3.json"
V2_RESULTS_FILE = EVALUATION_DIR / "ragas_results_v2_20b.json"
BASELINE_FILE = EVALUATION_DIR / "ragas_baseline.json"
THRESHOLDS_FILE = EVALUATION_DIR / "ragas_thresholds_v3.json"
SECURITY_INVENTORY = (
    EVALUATION_DIR / "knowledge_base_files" / "security-test-inventory.txt"
)
REPORT_FILE = (
    EVALUATION_DIR / "reports" / "ragvault_ragas_live_evaluation_report_v3.pdf"
)

METRICS = (
    ("faithfulness", "Faithfulness", "higher"),
    ("answer_relevancy", "Answer Relevancy", "higher"),
    ("context_precision", "Context Precision", "higher"),
    ("context_recall", "Context Recall", "higher"),
    ("context_entity_recall", "Context Entity Recall", "higher"),
    ("noise_sensitivity", "Noise Sensitivity", "lower"),
)


def _read_json(path):
    with path.open("r", encoding="utf-8") as source:
        return json.load(source)


def metric_status(metric_name, score, thresholds):
    if metric_name == "noise_sensitivity":
        threshold = thresholds["noise_sensitivity_threshold"]
        return threshold, "PASS" if score <= threshold else "NEEDS IMPROVEMENT"
    threshold = thresholds["higher_is_better_threshold"]
    return threshold, "PASS" if score >= threshold else "NEEDS IMPROVEMENT"


def _valid_score(score):
    return (
        isinstance(score, (int, float))
        and not isinstance(score, bool)
        and math.isfinite(score)
        and 0 <= score <= 1
    )


def load_results(results_file=RESULTS_FILE):
    results = _read_json(results_file)
    if not isinstance(results, dict) or len(results) != 25:
        raise ValueError("RAGAS v3 requires exactly 25 saved sample records")

    metric_names = {name for name, _, _ in METRICS}
    validated = []
    for index, expected in enumerate(EVALUATION_DATASET, start=1):
        sample = results.get(str(index))
        if not isinstance(sample, dict):
            raise ValueError(f"Missing RAGAS v3 sample {index}")
        if (
            sample.get("user_input") != expected["user_input"]
            or sample.get("reference") != expected["reference"]
            or sample.get("answer_generation_mode") != "production_llm"
            or sample.get("retrieval_configuration", {}).get("production_model")
            != PRODUCTION_MODEL_NAME
            or sample.get("retrieval_configuration", {}).get("top_k") != 5
            or sample.get("retrieval_configuration", {}).get("chunk_size") != 500
            or sample.get("retrieval_configuration", {}).get("chunk_overlap") != 50
            or sample.get("retrieval_configuration", {}).get("permission_aware")
            is not True
        ):
            raise ValueError(f"Sample {index} does not match live-answer v3 inputs")
        scores = sample.get("scores")
        if not isinstance(scores, dict) or set(scores) != metric_names:
            raise ValueError(f"Sample {index} does not have all six metric scores")
        if not all(_valid_score(score) for score in scores.values()):
            raise ValueError(f"Sample {index} contains an invalid metric score")
        models = sample.get("metric_models")
        if not isinstance(models, dict) or any(
            models.get(name) != EVALUATOR_MODEL_V3 for name in metric_names
        ):
            raise ValueError(
                f"Sample {index} does not consistently use {EVALUATOR_MODEL_V3}"
            )
        if not isinstance(sample.get("retrieved_contexts"), list) or not isinstance(
            sample.get("retrieved_sources"), list
        ):
            raise ValueError(f"Sample {index} is missing retrieval evidence")
        if not all(
            isinstance(context, str) for context in sample["retrieved_contexts"]
        ) or not all(
            isinstance(source, dict) for source in sample["retrieved_sources"]
        ):
            raise ValueError(f"Sample {index} contains malformed retrieval evidence")
        if not isinstance(sample.get("response"), str) or not sample["response"].strip():
            raise ValueError(f"Sample {index} is missing its generated answer")
        validated.append((index, expected, sample))
    return validated


def _paragraph(text, style):
    return Paragraph(xml_escape(str(text)), style)


def _table(rows, widths, font_size=7):
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12304A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F1F5F9")],
                ),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="V3Title",
            parent=styles["Title"],
            fontSize=23,
            leading=28,
            textColor=colors.HexColor("#12304A"),
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="V3Heading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#12304A"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="V3Small",
            parent=styles["BodyText"],
            fontSize=7,
            leading=9,
        )
    )
    return styles


def _average(rows, metric):
    values = [sample["scores"][metric] for _, _, sample in rows]
    return sum(values) / len(values)


def _source_evidence(sample):
    titles = []
    for source in sample["retrieved_sources"]:
        title = source.get("title")
        if title and title not in titles:
            titles.append(title)
    return "; ".join(titles) if titles else "No source documents retrieved"


def build_report(results_file=RESULTS_FILE, report_file=REPORT_FILE):
    samples = load_results(results_file)
    thresholds = _read_json(THRESHOLDS_FILE)
    baseline = _read_json(BASELINE_FILE)["baseline"]
    v2_results = _read_json(V2_RESULTS_FILE)
    if not isinstance(v2_results, dict) or len(v2_results) != 25:
        raise ValueError("The preserved v2 result set is not a complete 25-sample run")
    if len({document["title"] for document in KNOWLEDGE_BASE_DOCUMENTS}) != 35:
        raise ValueError("The evaluation corpus does not contain 35 unique titles")

    inventory = SECURITY_INVENTORY.read_text(encoding="utf-8")
    summary = next(
        (
            line
            for line in inventory.splitlines()
            if line.startswith("Focused security-suite result:")
        ),
        "Focused security-suite result: not recorded in the inventory.",
    )
    styles = _styles()
    report_file.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(report_file),
        pagesize=landscape(letter),
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
        title="RAGVault Live-Answer RAGAS Evaluation v3",
        author="RAGVault",
    )
    story = [
        Paragraph("RAGVault", styles["V3Title"]),
        Paragraph(
            "Live-Answer RAGAS Evaluation v3",
            styles["Heading2"],
        ),
        Paragraph(f"Report date: {date.today().isoformat()}", styles["Normal"]),
        Spacer(1, 7),
        Paragraph("Methodology and evaluation scope", styles["V3Heading"]),
        _paragraph(
            "The 25 v3 questions use references from the versioned evaluation "
            "dataset. Answers are generated one sample at a time through the "
            "existing RAGVault production answer function; the production model "
            f"is {PRODUCTION_MODEL_NAME}. The runner retrieves permission-aware "
            "context with top-k=5 and the existing 500-character chunk size and "
            "50-character overlap, then passes the secure context to the answer "
            "function. Generated answers and retrieval evidence are persisted "
            "before scoring so interrupted runs reuse the same answer and context. "
            f"All metrics use {EVALUATOR_MODEL_V3}; RAGAS version {RAGAS_VERSION}.",
            styles["BodyText"],
        ),
        Paragraph("Metrics and thresholds", styles["V3Heading"]),
        _paragraph(
            "Faithfulness evaluates support from retrieved context; Answer "
            "Relevancy evaluates answer-question relevance; Context Precision "
            "evaluates retrieved-context relevance and ordering; Context Recall "
            "evaluates reference coverage; Context Entity Recall evaluates "
            "reference-entity coverage. The five higher-is-better metric "
            "averages PASS at or above 0.70. Noise Sensitivity is "
            "lower-is-better and passes at or below 0.20.",
            styles["BodyText"],
        ),
        Paragraph("Metric averages, status, and coverage", styles["V3Heading"]),
    ]

    average_rows = [["Metric", "Average", "Threshold", "Status", "Coverage"]]
    averages = {}
    for metric, label, direction in METRICS:
        average = _average(samples, metric)
        threshold, status = metric_status(metric, average, thresholds)
        averages[metric] = average
        threshold_label = (
            f"<= {threshold:.2f}" if direction == "lower" else f">= {threshold:.2f}"
        )
        average_rows.append(
            [label, f"{average:.3f}", threshold_label, status, "25/25"]
        )
    story.extend(
        [
            _table(average_rows, [2.0 * inch, 1.0 * inch, 1.1 * inch, 2.0 * inch, 0.9 * inch]),
            Spacer(1, 5),
            _paragraph(
                "Sample coverage is 25/25 and each metric has 25/25 scores. "
                "The overall target is met only if every higher-is-better average "
                "is at least 0.70 and Noise Sensitivity is at most 0.20.",
                styles["BodyText"],
            ),
            Paragraph("Knowledge base and security boundary", styles["V3Heading"]),
            _paragraph(
                "The evaluation corpus contains 35 uniquely titled enterprise "
                "policy, process, and RAGVault architecture documents. The "
                "corpus-validation test checks that all materialized sources have "
                "more than 25 meaningful lines. "
                + summary
                + " RAGAS measures retrieval and answer quality; it is not a "
                "security test and does not prove tenant isolation, authorization, "
                "or absence of data leakage. Those claims require dedicated "
                "security tests.",
                styles["BodyText"],
            ),
            PageBreak(),
            Paragraph("Original baseline and v2 comparison", styles["V3Heading"]),
        ]
    )

    comparison_rows = [[
        "Metric",
        "Original 10-sample baseline",
        "V2 25-sample average",
        "Live-answer v3 average",
        "Interpretation",
    ]]
    for metric, label, _ in METRICS:
        v2_values = [
            item["scores"][metric]
            for item in v2_results.values()
            if isinstance(item, dict)
            and isinstance(item.get("scores"), dict)
            and _valid_score(item["scores"].get(metric))
        ]
        if len(v2_values) != 25:
            raise ValueError(f"Preserved v2 has incomplete {metric} coverage")
        comparison_rows.append(
            [
                label,
                f"{baseline[metric]:.3f}",
                f"{sum(v2_values) / len(v2_values):.3f}",
                f"{averages[metric]:.3f}",
                "Descriptive only; different response-generation/evaluation inputs",
            ]
        )
    story.extend(
        [
            _table(
                comparison_rows,
                [1.5 * inch, 1.45 * inch, 1.35 * inch, 1.35 * inch, 3.0 * inch],
                font_size=6.5,
            ),
            Spacer(1, 6),
            _paragraph(
                "The original baseline is preserved and uses 10 historical samples. "
                "V2 used authored response strings; v3 uses production-generated "
                "answers and corrected two evaluation facts. Because the response "
                "source and some inputs differ, these deltas are not a controlled "
                "before/after experiment. No quality improvement or regression is "
                "claimed from this cross-version comparison.",
                styles["BodyText"],
            ),
            Paragraph("Per-sample results", styles["V3Heading"]),
        ]
    )

    sample_rows = [[
        "Sample",
        "Question",
        "Faithfulness",
        "Answer Relevancy",
        "Context Precision",
        "Context Recall",
        "Entity Recall",
        "Noise",
    ]]
    for index, expected, sample in samples:
        sample_rows.append(
            [
                str(index),
                _paragraph(expected["user_input"], styles["V3Small"]),
                *(f"{sample['scores'][metric]:.3f}" for metric, _, _ in METRICS),
            ]
        )
    story.append(
        _table(
            sample_rows,
            [0.45 * inch, 3.0 * inch, 0.85 * inch, 0.9 * inch, 0.9 * inch, 0.8 * inch, 0.8 * inch, 0.55 * inch],
            font_size=6.2,
        )
    )
    story.extend(
        [
            PageBreak(),
            Paragraph(
                "Below-threshold samples and evidence-based analysis",
                styles["V3Heading"],
            ),
            _paragraph(
                "A metric score identifies a result to investigate, not its root "
                "cause. The evidence table records the exact sample and retrieved "
                "source titles. A cause is not assigned unless source or answer "
                "evidence demonstrates it. A paired after-score is N/A unless the "
                "same sample, answer-generation mode, retrieval configuration, and "
                "evaluator are measured before and after an explicit change.",
                styles["BodyText"],
            ),
        ]
    )

    failure_rows = [[
        "Sample / metric",
        "Score",
        "Retrieved sources",
        "Cause / evidence",
        "Change and before/after",
    ]]
    for index, expected, sample in samples:
        for metric, label, _ in METRICS:
            score = sample["scores"][metric]
            _, status = metric_status(metric, score, thresholds)
            if status == "PASS":
                continue
            source_names = _source_evidence(sample)
            response_preview = sample["response"][:350]
            context_preview = " ".join(sample["retrieved_contexts"])[:450]
            failure_rows.append(
                [
                    f"{index}: {label}",
                    f"{score:.3f}",
                    _paragraph(source_names, styles["V3Small"]),
                    _paragraph(
                        "Cause not established from score alone. Saved answer: "
                        + response_preview
                        + " Evidence context: "
                        + context_preview,
                        styles["V3Small"],
                    ),
                    _paragraph(
                        "No production behavior change is justified by this score "
                        "alone. Review query-to-source coverage before intervening. "
                        "Before/after: not measured; no improvement claim.",
                        styles["V3Small"],
                    ),
                ]
            )
    if len(failure_rows) == 1:
        failure_rows.append(
            ["None", "-", "-", "All per-sample metric scores meet their direction-aware threshold.", "-"]
        )
    story.append(
        _table(
            failure_rows,
            [1.0 * inch, 0.55 * inch, 1.5 * inch, 3.3 * inch, 3.1 * inch],
            font_size=6.2,
        )
    )
    story.extend(
        [
            Spacer(1, 8),
            Paragraph("Evidence-backed changes and conclusion", styles["V3Heading"]),
            _paragraph(
                "The evaluation source now states the verified top-k configuration "
                "of five for production and evaluation. V3 corrects the corresponding "
                "architecture question/reference and removes a stale test-run count "
                "from its security-inventory question. These are factual evaluation "
                "input corrections, not evidence that production retrieval improved. "
                "Chunk size, overlap, top-k, ACL filtering, post-retrieval "
                "authorization, and production model behavior were not tuned to "
                "inflate scores.",
                styles["BodyText"],
            ),
            _paragraph(
                "Final conclusion: "
                + (
                    "all declared average thresholds are met."
                    if all(
                        metric_status(metric, averages[metric], thresholds)[1]
                        == "PASS"
                        for metric, _, _ in METRICS
                    )
                    else "one or more declared average thresholds are not met; "
                    "the metric and per-sample tables identify the remaining gaps."
                )
                + " RAGAS is a quality evaluation only and does not replace the "
                "project's security test suite.",
                styles["BodyText"],
            ),
        ]
    )
    document.build(story)
    return report_file


if __name__ == "__main__":
    print(build_report())
