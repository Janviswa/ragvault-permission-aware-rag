from pypdf import PdfReader

from evaluation.generate_ragas_report import build_report


def test_ragas_report_contains_metrics_and_explicit_coverage():
    report_path = build_report()

    assert report_path.is_file()
    assert report_path.read_bytes().startswith(b"%PDF-")
    text = " ".join(
        " ".join((page.extract_text() or "").split())
        for page in PdfReader(report_path).pages
    )

    for phrase in (
        "RAGVault",
        "Evaluation methodology",
        "Faithfulness",
        "Answer Relevancy",
        "Context Precision",
        "Context Recall",
        "Context Entity Recall",
        "Noise Sensitivity",
        "Per-sample results",
        "10 of 10",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "57 scores",
        "3 scores",
        "0.4.3",
        "0.927",
        "0.859",
        "0.909",
        "1.000",
        "0.600",
        "0.303",
        "not a replacement for security tests",
    ):
        assert phrase in text
