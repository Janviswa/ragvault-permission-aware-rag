from pypdf import PdfReader

from evaluation.generate_ragas_report_v2 import build_report
from evaluation.generate_interview_prep import build_report as build_interview_prep


def test_v2_report_reflects_full_coverage_thresholds_analysis_and_security_boundary():
    report_path = build_report()
    assert report_path.is_file()
    assert report_path.read_bytes().startswith(b"%PDF-")

    text = " ".join(
        " ".join((page.extract_text() or "").split())
        for page in PdfReader(report_path).pages
    )
    for phrase in (
        "RAGVault",
        "RAGAS v2",
        "25/25 samples",
        "Faithfulness",
        "Answer Relevancy",
        "Context Precision",
        "Context Recall",
        "Context Entity Recall",
        "Noise Sensitivity",
        "0.80",
        "threshold",
        "Below-threshold sample analysis and changes",
        "Before score",
        "After score",
        "Improvement",
        "Answer Relevancy coverage investigation",
        "V1 completion now has 10/10 Answer Relevancy scores",
        "RAGVault Security Architecture",
        "Vendor Security Assessment PDF",
        "Employee Access Lifecycle DOCX",
        "35 unique documents",
        "openai/gpt-oss-20b",
        "64 focused tests",
        "Context Entity Recall explicitly requires",
        "NEEDS IMPROVEMENT",
        "not evidence of tenant isolation",
        "NOT ESTABLISHED",
    ):
        assert phrase in text


def test_interview_preparation_pdf_uses_complete_v2_results_and_security_boundary():
    report_path = build_interview_prep()
    assert report_path.is_file()
    assert report_path.read_bytes().startswith(b"%PDF-")

    text = " ".join(
        " ".join((page.extract_text() or "").split())
        for page in PdfReader(report_path).pages
    )
    for phrase in (
        "RAGVault",
        "Project interview guide",
        "Authentication verifies identity",
        "Qdrant search applies a tenant filter",
        "post-retrieval authorization",
        "RAGAS evaluates retrieval and answer quality",
        "Context Entity Recall",
        "25 samples",
        "six metrics",
        "resumption coverage gap",
        "Likely interview questions",
        "Resume-ready project summary",
    ):
        assert phrase in text
