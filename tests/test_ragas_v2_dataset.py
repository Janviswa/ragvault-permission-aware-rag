from difflib import SequenceMatcher
import json
from pathlib import Path
import re
from unittest.mock import Mock

import pytest

from evaluation.knowledge_base import KNOWLEDGE_BASE_DOCUMENTS
from evaluation.generate_ragas_report_v2 import metric_status
from backend.evaluation.generate_ragas_report import metric_status as metric_status_v3
from evaluation.ragas_dataset_v2 import EVALUATION_DATASET
from backend.evaluation.ragas_dataset import EVALUATION_DATASET as EVALUATION_DATASET_V3
from evaluation import run_ragas
from evaluation.run_ragas import rate_limit_retry_delay, update_saved_sample
from evaluation.seed_knowledge_base import materialize_source


def test_ragas_v2_dataset_has_25_distinct_complete_samples():
    assert len(EVALUATION_DATASET) == 25
    required_fields = {"user_input", "response", "reference"}
    questions = []
    for sample in EVALUATION_DATASET:
        assert required_fields <= sample.keys()
        assert all(sample[field].strip() for field in required_fields)
        questions.append(sample["user_input"].casefold())

    assert len(set(questions)) == 25
    for index, question in enumerate(questions):
        for other in questions[index + 1 :]:
            assert SequenceMatcher(None, question, other).ratio() < 0.8


def test_ragas_v3_preserves_v2_and_corrects_verified_evaluation_facts():
    assert len(EVALUATION_DATASET_V3) == 25
    assert all(
        set(sample) == {"user_input", "reference"}
        and sample["user_input"].strip()
        and sample["reference"].strip()
        for sample in EVALUATION_DATASET_V3
    )
    engineering_architecture = next(
        document
        for document in KNOWLEDGE_BASE_DOCUMENTS
        if document["title"] == "RAGVault Engineering Architecture"
    )
    assert "limit three" not in engineering_architecture["content"]
    assert "The RAGAS evaluation runner also defaults to five" in (
        engineering_architecture["content"]
    )
    engineering_document_file = (
        Path(__file__).parents[1]
        / "evaluation"
        / "knowledge_base_files"
        / "ragvault-engineering-architecture-expanded.txt"
    )
    assert "RAGAS evaluation runner intentionally sets limit three" not in (
        engineering_document_file.read_text(encoding="utf-8")
    )
    assert any(
        "60-test" in " ".join(sample.values())
        for sample in EVALUATION_DATASET
    )
    assert not any(
        "60-test" in " ".join(sample.values())
        for sample in EVALUATION_DATASET_V3
    )
    assert "test_qdrant_query_uses_tenant_and_user_role_acl_filters" in (
        EVALUATION_DATASET_V3[23]["reference"]
    )
    assert "test_unauthorized_retrieval_never_reaches_llm_and_is_audited" in (
        EVALUATION_DATASET_V3[23]["reference"]
    )


def test_live_answer_evaluation_uses_the_secure_context_for_generation(monkeypatch):
    assert run_ragas.EVALUATOR_MODEL_V3 == "openai/gpt-oss-20b"
    assert run_ragas.PRODUCTION_MODEL_NAME == "openai/gpt-oss-120b"

    result = type(
        "RetrievedResult",
        (),
        {
            "payload": {
                "text": "Only authorized policy text",
                "document_id": "doc-1",
                "title": "Access Control Policy",
                "file_name": "access-control.txt",
                "chunk_index": 0,
            }
        },
    )()
    database = Mock()
    monkeypatch.setattr(run_ragas, "SessionLocal", lambda: database)
    monkeypatch.setattr(run_ragas, "get_admin_user", lambda db: "admin")
    monkeypatch.setattr(
        run_ragas,
        "retrieve_secure_context",
        lambda **kwargs: ("Only authorized policy text", [result]),
    )
    generated_answers = []

    def generate_answer(question, context):
        generated_answers.append((question, context))
        return "Generated from authorized context"

    monkeypatch.setattr(run_ragas, "generate_answer", generate_answer)
    retrieval_configuration = {
        "top_k": 5,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "permission_aware": True,
        "answer_generation_mode": "production_llm",
        "production_model": run_ragas.PRODUCTION_MODEL_NAME,
    }

    sample = run_ragas.build_evaluation_data(
        dataset=EVALUATION_DATASET_V3,
        sample_index=1,
        answer_generation_mode="production_llm",
        saved_results={},
        retrieval_configuration=retrieval_configuration,
    )[0]

    assert sample["response"] == "Generated from authorized context"
    assert sample["retrieved_contexts"] == ["Only authorized policy text"]
    assert generated_answers == [
        (EVALUATION_DATASET_V3[0]["user_input"], "Only authorized policy text")
    ]
    database.close.assert_called_once()


def test_live_answer_evaluation_reuses_saved_answer_and_context(monkeypatch):
    configuration = {
        "top_k": 5,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "permission_aware": True,
        "answer_generation_mode": "production_llm",
        "production_model": run_ragas.PRODUCTION_MODEL_NAME,
    }
    saved_sample = {
        "user_input": EVALUATION_DATASET_V3[0]["user_input"],
        "response": "Previously generated answer",
        "reference": EVALUATION_DATASET_V3[0]["reference"],
        "retrieved_contexts": ["Previously retrieved authorized context"],
        "retrieved_sources": [],
        "answer_generation_mode": "production_llm",
        "retrieval_configuration": configuration,
    }
    monkeypatch.setattr(
        run_ragas,
        "SessionLocal",
        lambda: pytest.fail("A resumed sample must not be retrieved again"),
    )
    monkeypatch.setattr(
        run_ragas,
        "generate_answer",
        lambda *_: pytest.fail("A resumed answer must not be regenerated"),
    )

    sample = run_ragas.build_evaluation_data(
        dataset=EVALUATION_DATASET_V3,
        sample_index=1,
        answer_generation_mode="production_llm",
        saved_results={"1": saved_sample},
        retrieval_configuration=configuration,
    )[0]

    assert sample["response"] == "Previously generated answer"
    assert sample["retrieved_contexts"] == [
        "Previously retrieved authorized context"
    ]


def test_enterprise_corpus_has_substantial_policy_and_format_sources():
    assert len(KNOWLEDGE_BASE_DOCUMENTS) == 35
    assert len({document["title"] for document in KNOWLEDGE_BASE_DOCUMENTS}) == 35
    assert len({document["file_name"] for document in KNOWLEDGE_BASE_DOCUMENTS}) == 35
    assert all(
        sum(bool(line.strip()) for line in materialize_source(document).splitlines())
        > 25
        for document in KNOWLEDGE_BASE_DOCUMENTS
    )
    formats = {Path(document["file_name"]).suffix for document in KNOWLEDGE_BASE_DOCUMENTS}
    assert {".txt", ".pdf", ".docx"} <= formats


def test_security_inventory_names_existing_test_functions_and_result_locations():
    inventory_path = (
        Path(__file__).parents[1]
        / "evaluation"
        / "knowledge_base_files"
        / "security-test-inventory.txt"
    )
    inventory = inventory_path.read_text(encoding="utf-8")
    entries = re.findall(
        r"^- (test_\w+) .+?Location: (backend/tests/[\w_]+\.py)\. Result: PASS\.",
        inventory,
        flags=re.MULTILINE,
    )
    assert len(entries) == 64
    assert "64 passed, 0 failed" in inventory
    for test_name, location in entries:
        test_file = Path(__file__).parents[1] / "tests" / Path(location).name
        assert test_file.is_file()
        assert re.search(rf"^def {re.escape(test_name)}\(", test_file.read_text(encoding="utf-8"), re.MULTILINE)


def test_groq_retry_delay_respects_provider_minute_and_millisecond_waits():
    minute_error = type(
        "RateLimit",
        (),
        {
            "response": type("Response", (), {"headers": {}})(),
            "body": {
                "error": {
                    "message": "Please try again in 5m46.032s."
                }
            },
        },
    )()
    millisecond_error = type(
        "RateLimit",
        (),
        {
            "response": type("Response", (), {"headers": {}})(),
            "body": {
                "error": {
                    "message": "Please try again in 37.5ms."
                }
            },
        },
    )()

    assert rate_limit_retry_delay(minute_error, 0) == 347.032
    assert round(rate_limit_retry_delay(millisecond_error, 0), 3) == 1.038


def test_v2_thresholds_apply_correct_direction_and_preserve_original_baseline():
    thresholds_path = Path(__file__).parents[1] / "evaluation" / "ragas_thresholds_v2.json"
    original_path = Path(__file__).parents[1] / "evaluation" / "ragas_baseline.json"
    v2_path = Path(__file__).parents[1] / "evaluation" / "ragas_baseline_v2.json"
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    original = json.loads(original_path.read_text(encoding="utf-8"))
    v2_baseline = json.loads(v2_path.read_text(encoding="utf-8"))

    assert metric_status("faithfulness", 0.8001, thresholds) == (0.8, "PASS")
    assert metric_status("faithfulness", 0.8, thresholds) == (
        0.8,
        "NEEDS IMPROVEMENT",
    )
    assert metric_status("faithfulness", 0.799, thresholds) == (
        0.8,
        "NEEDS IMPROVEMENT",
    )
    assert metric_status("noise_sensitivity", 0.2, thresholds) == (
        0.2,
        "PASS",
    )
    assert metric_status("noise_sensitivity", 0.201, thresholds) == (
        0.2,
        "NEEDS IMPROVEMENT",
    )
    assert v2_baseline["baseline"] == original["baseline"]


def test_v3_average_threshold_is_inclusive_and_noise_sensitivity_is_lower_is_better():
    thresholds_path = Path(__file__).parents[1] / "evaluation" / "ragas_thresholds_v3.json"
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))

    assert thresholds["threshold_applies_to"] == "metric_average"
    assert thresholds["higher_is_better_threshold"] == 0.7
    assert metric_status_v3("faithfulness", 0.7, thresholds) == (0.7, "PASS")
    assert metric_status_v3("faithfulness", 0.7001, thresholds) == (0.7, "PASS")
    assert metric_status_v3("faithfulness", 0.8, thresholds) == (
        0.7,
        "PASS",
    )
    assert metric_status_v3("faithfulness", 0.6999, thresholds) == (
        0.7,
        "NEEDS IMPROVEMENT",
    )
    assert metric_status_v3("noise_sensitivity", 0.2, thresholds) == (
        0.2,
        "PASS",
    )


@pytest.mark.parametrize(
    (
        "score",
        "rescore_zero_scores",
        "already_rescored",
        "retry_rescored_zero_scores",
        "expected",
    ),
    [
        (0.0, False, False, False, False),
        (0.0, True, False, False, True),
        (0.0, True, True, False, False),
        (0.0, True, True, True, True),
        (0.5, True, False, True, False),
        (None, False, False, False, True),
    ],
)
def test_zero_score_rescoring_targets_only_zeros_and_allows_explicit_retries(
    score,
    rescore_zero_scores,
    already_rescored,
    retry_rescored_zero_scores,
    expected,
):
    assert run_ragas.should_score_metric(
        score,
        rescore_zero_scores=rescore_zero_scores,
        already_rescored=already_rescored,
        retry_rescored_zero_scores=retry_rescored_zero_scores,
    ) is expected


def test_changed_evaluation_inputs_require_explicit_rescore_and_preserve_old_scores():
    sample = {
        "user_input": "Question",
        "response": "Answer",
        "reference": "Reference",
        "retrieved_contexts": ["old context"],
        "retrieved_sources": [{"title": "Old source"}],
    }
    configuration = {
        "top_k": 5,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "permission_aware": True,
    }
    result = {
        **sample,
        "retrieval_configuration": configuration,
        "scores": {"faithfulness": 0.75},
    }
    changed_sample = {**sample, "retrieved_contexts": ["new context"]}

    with pytest.raises(ValueError, match="--recompute-sample"):
        update_saved_sample(result, changed_sample, configuration)

    update_saved_sample(
        result,
        changed_sample,
        configuration,
        recompute=True,
    )
    assert result["scores"] == {}
    assert result["previous_evaluations"][0]["scores"] == {
        "faithfulness": 0.75
    }
    assert result["retrieved_contexts"] == ["new context"]
