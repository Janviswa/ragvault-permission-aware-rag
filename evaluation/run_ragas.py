from openai import AsyncOpenAI
from openai import RateLimitError
import asyncio
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import tempfile

from ragas.llms import llm_factory
from ragas.metrics.collections import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    ContextEntityRecall,
    NoiseSensitivity,
)
from ragas.embeddings import HuggingFaceEmbeddings

from app.config import settings
from app.db import SessionLocal
from app.models.user import User
from app.rag.pipeline import retrieve_secure_context
from app.rag.llm import MODEL_NAME as PRODUCTION_MODEL_NAME, generate_answer

from evaluation.ragas_dataset import EVALUATION_DATASET as EVALUATION_DATASET_V1
from evaluation.ragas_dataset_v2 import EVALUATION_DATASET as EVALUATION_DATASET_V2
from backend.evaluation.ragas_dataset import EVALUATION_DATASET as EVALUATION_DATASET_V3
from evaluation.evaluation_metadata import MODEL_NAME, RAGAS_VERSION


RESULTS_FILE = Path(__file__).with_name("ragas_results.json")
RESULTS_FILE_V3 = Path(__file__).with_name("ragas_results_v3.json")
EVALUATOR_MODEL_V3 = "openai/gpt-oss-20b"

def get_admin_user(db):
    user = (
        db.query(User)
        .filter(User.email == "admin@ragvault.local")
        .first()
    )

    if not user:
        raise RuntimeError("Admin user not found")

    return user


def build_evaluation_data(
    dataset=EVALUATION_DATASET_V1,
    limit=5,
    sample_index=None,
    answer_generation_mode=None,
    saved_results=None,
    retrieval_configuration=None,
):
    saved_results = saved_results or {}
    rows = []

    for index, item in enumerate(dataset, start=1):
        if sample_index is not None and index != sample_index:
            continue
        question = item["user_input"]
        reference = item["reference"]
        saved_sample = saved_results.get(str(index))

        if answer_generation_mode is not None and saved_sample is not None:
            if (
                saved_sample.get("user_input") != question
                or saved_sample.get("reference") != reference
                or saved_sample.get("answer_generation_mode")
                != answer_generation_mode
                or saved_sample.get("retrieval_configuration")
                != retrieval_configuration
                or not isinstance(saved_sample.get("response"), str)
                or not saved_sample["response"].strip()
                or not isinstance(saved_sample.get("retrieved_contexts"), list)
                or not isinstance(saved_sample.get("retrieved_sources"), list)
            ):
                raise ValueError(
                    f"Saved live-answer sample {index} does not match the "
                    "current dataset or retrieval configuration"
                )
            rows.append(
                {
                    "user_input": question,
                    "retrieved_contexts": saved_sample["retrieved_contexts"],
                    "response": saved_sample["response"],
                    "reference": reference,
                    "retrieved_sources": saved_sample["retrieved_sources"],
                    "answer_generation_mode": answer_generation_mode,
                }
            )
            continue

        db = SessionLocal()
        try:
            current_user = get_admin_user(db)
            secure_context, results = retrieve_secure_context(
                db=db,
                current_user=current_user,
                query=question,
                limit=limit,
            )
            retrieved_contexts = [
                result.payload.get("text", "")
                for result in results
                if result.payload
            ]
            response = (
                generate_answer(question, secure_context)
                if answer_generation_mode is not None
                else item["response"]
            )
            rows.append(
                {
                    "user_input": question,
                    "retrieved_contexts": retrieved_contexts,
                    "response": response,
                    "reference": reference,
                    "retrieved_sources": [
                        {
                            "document_id": result.payload.get("document_id"),
                            "title": result.payload.get("title"),
                            "file_name": result.payload.get("file_name"),
                            "chunk_index": result.payload.get("chunk_index"),
                        }
                        for result in results
                        if result.payload
                    ],
                    "answer_generation_mode": answer_generation_mode,
                }
            )
        finally:
            db.close()

    return rows


def build_ragas_llm(model_name=MODEL_NAME):
    client = AsyncOpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    llm = llm_factory(
        model_name,
        client=client,
        max_tokens=2048,
    )

    async def patched_agenerate(prompt, response_model):
        for attempt in range(8):
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.01,
                    top_p=0.1,
                    max_tokens=2048,
                    reasoning_effort="low",
                )
                break
            except RateLimitError as exc:
                if attempt == 7:
                    raise
                delay = rate_limit_retry_delay(exc, attempt)
                print(
                    "Groq rate limit; retrying this metric request in "
                    f"{delay:.1f}s"
                )
                await asyncio.sleep(delay)

        return response_model.model_validate_json(
            response.choices[0].message.content
        )

    llm.agenerate = patched_agenerate
    return llm


def rate_limit_retry_delay(error, attempt):
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            return max(float(retry_after), 1.0)
        except ValueError:
            pass

    body = getattr(error, "body", None)
    if isinstance(body, dict):
        message = body.get("error", {}).get("message", "")
    else:
        message = str(error)
    match = re.search(
        r"try again in (?:(\d+(?:\.\d+)?)m)?\s*(\d+(?:\.\d+)?)(ms|s)",
        message,
        flags=re.IGNORECASE,
    )
    if match:
        minutes = float(match.group(1) or 0)
        amount = float(match.group(2))
        unit = match.group(3).lower()
        seconds = amount / 1000 if unit == "ms" else amount
        return max(minutes * 60 + seconds + 1, 1.0)

    return min(2**attempt, 60)


def build_ragas_metrics(model_name=MODEL_NAME):
    evaluator_llm = build_ragas_llm(model_name)

    evaluator_embeddings = HuggingFaceEmbeddings(
        model=settings.embedding_model,
        normalize_embeddings=True,
    )

    return [
        Faithfulness(llm=evaluator_llm),
        AnswerRelevancy(
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
            strictness=1,
        ),
        ContextPrecision(llm=evaluator_llm),
        ContextRecall(llm=evaluator_llm),
        ContextEntityRecall(llm=evaluator_llm),
        NoiseSensitivity(
            llm=evaluator_llm,
            mode="relevant",
        ),
    ]


def load_results(results_file=RESULTS_FILE):
    if not results_file.exists():
        return {}

    with results_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_results(results, results_file=RESULTS_FILE):
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=results_file.parent,
        prefix=f".{results_file.name}.",
        suffix=".tmp",
        delete=False,
    ) as f:
        temporary_path = Path(f.name)
        json.dump(results, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary_path, results_file)


def is_valid_saved_score(score):
    return (
        isinstance(score, (int, float))
        and not isinstance(score, bool)
        and math.isfinite(score)
        and 0 <= score <= 1
    )


def should_score_metric(
    score,
    *,
    rescore_zero_scores=False,
    already_rescored=False,
    retry_rescored_zero_scores=False,
):
    if not is_valid_saved_score(score):
        return True
    return (
        rescore_zero_scores
        and score == 0
        and (retry_rescored_zero_scores or not already_rescored)
    )


def update_saved_sample(result, sample, retrieval_configuration, recompute=False):
    changed_fields = {
        "user_input": sample["user_input"],
        "response": sample["response"],
        "reference": sample["reference"],
        "retrieved_contexts": sample["retrieved_contexts"],
        "retrieved_sources": sample["retrieved_sources"],
        "retrieval_configuration": retrieval_configuration,
    }
    if sample.get("answer_generation_mode") is not None:
        changed_fields["answer_generation_mode"] = sample[
            "answer_generation_mode"
        ]
    has_previous_snapshot = "retrieved_contexts" in result
    changed = has_previous_snapshot and any(
        result.get(field) != value for field, value in changed_fields.items()
    )
    if changed and not recompute:
        raise ValueError(
            "Saved evaluation inputs or retrieved context changed; use "
            "--recompute-sample to retain the old scores and explicitly rescore"
        )
    if recompute and not changed:
        raise ValueError(
            "--recompute-sample requires changed question, answer, reference, "
            "retrieved context, or retrieval configuration"
        )

    if changed:
        result.setdefault("previous_evaluations", []).append(
            {
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "user_input": result.get("user_input"),
                "response": result.get("response"),
                "reference": result.get("reference"),
                "scores": deepcopy(result.get("scores", {})),
                "metric_models": deepcopy(result.get("metric_models", {})),
                "retrieved_contexts": deepcopy(result.get("retrieved_contexts", [])),
                "retrieved_sources": deepcopy(result.get("retrieved_sources", [])),
                "zero_score_rescore_history": deepcopy(
                    result.get("zero_score_rescore_history", {})
                ),
                "answer_generation_mode": result.get("answer_generation_mode"),
                "retrieval_configuration": deepcopy(
                    result.get("retrieval_configuration", {})
                ),
            }
        )
        result["scores"] = {}
        result["metric_models"] = {}
        result.pop("zero_score_rescore_history", None)
    result.update(changed_fields)
    return result


def score_metric(metric, sample):
    if metric.name == "faithfulness":
        return metric.score(
            user_input=sample["user_input"],
            response=sample["response"],
            retrieved_contexts=sample["retrieved_contexts"],
        ).value

    if metric.name == "answer_relevancy":
        return metric.score(
            user_input=sample["user_input"],
            response=sample["response"],
        ).value

    if metric.name == "context_precision":
        return metric.score(
            user_input=sample["user_input"],
            reference=sample["reference"],
            retrieved_contexts=sample["retrieved_contexts"],
        ).value

    if metric.name == "context_recall":
        return metric.score(
            user_input=sample["user_input"],
            retrieved_contexts=sample["retrieved_contexts"],
            reference=sample["reference"],
        ).value

    if metric.name == "context_entity_recall":
        return metric.score(
            reference=sample["reference"],
            retrieved_contexts=sample["retrieved_contexts"],
        ).value

    if metric.name == "noise_sensitivity":
        return metric.score(
            user_input=sample["user_input"],
            response=sample["response"],
            reference=sample["reference"],
            retrieved_contexts=sample["retrieved_contexts"],
        ).value

    raise ValueError(f"Unknown metric: {metric.name}")


def main(
    sample_index=None,
    results_file=None,
    top_k=5,
    dataset_version="v1",
    recompute_sample=False,
    evaluator_model=None,
    rescore_zero_scores=False,
    retry_rescored_zero_scores=False,
):
    datasets = {
        "v1": EVALUATION_DATASET_V1,
        "v2": EVALUATION_DATASET_V2,
        "v3": EVALUATION_DATASET_V3,
    }
    dataset = datasets[dataset_version]
    answer_generation_mode = (
        "production_llm" if dataset_version == "v3" else None
    )
    if evaluator_model is None:
        evaluator_model = (
            EVALUATOR_MODEL_V3 if dataset_version == "v3" else MODEL_NAME
        )
    if results_file is None:
        results_file = RESULTS_FILE_V3 if dataset_version == "v3" else RESULTS_FILE
    if dataset_version == "v3" and evaluator_model != EVALUATOR_MODEL_V3:
        raise ValueError(
            f"RAGAS v3 requires the single evaluator model {EVALUATOR_MODEL_V3}"
        )

    if sample_index is not None and not 1 <= sample_index <= len(dataset):
        raise ValueError(
            f"Sample index must be between 1 and {len(dataset)}, got {sample_index}"
        )
    if top_k < 1:
        raise ValueError(f"top-k must be positive, got {top_k}")

    results = load_results(results_file=results_file)

    print(f"Evaluation samples: {len(dataset)}")
    print(f"\nInitializing RAGAS {RAGAS_VERSION} metrics...")

    metrics = build_ragas_metrics(evaluator_model)

    print("\nMetrics:")
    for metric in metrics:
        print(f"  - {metric.name}")

    print("\nRunning resumable RAGAS evaluation...\n")

    selected_indices = (
        [sample_index]
        if sample_index is not None
        else list(range(1, len(dataset) + 1))
    )
    retrieval_configuration = {
        "top_k": top_k,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "permission_aware": True,
    }
    if answer_generation_mode is not None:
        retrieval_configuration.update(
            {
                "answer_generation_mode": answer_generation_mode,
                "production_model": PRODUCTION_MODEL_NAME,
            }
        )

    for index in selected_indices:
        sample_key = str(index)
        sample = build_evaluation_data(
            dataset=dataset,
            limit=top_k,
            sample_index=index,
            answer_generation_mode=answer_generation_mode,
            saved_results=results,
            retrieval_configuration=retrieval_configuration,
        )[0]

        if sample_key not in results:
            results[sample_key] = {
                "user_input": sample["user_input"],
                "scores": {},
            }
        elif not isinstance(results[sample_key].get("scores"), dict):
            raise ValueError(f"Saved sample {sample_key} has invalid scores")
        if dataset_version == "v3":
            existing_scores = results[sample_key]["scores"]
            existing_models = results[sample_key].get("metric_models", {})
            if any(
                is_valid_saved_score(score)
                and existing_models.get(metric_name) != evaluator_model
                for metric_name, score in existing_scores.items()
            ):
                raise ValueError(
                    f"Saved sample {sample_key} contains scores from a different "
                    "or unknown evaluator; refusing to mix evaluator models"
                )

        update_saved_sample(
            results[sample_key],
            sample,
            retrieval_configuration,
            recompute=recompute_sample,
        )
        save_results(results, results_file=results_file)

        print(f"Evaluating sample {index}/{len(dataset)}...")

        for metric in metrics:
            metric_name = metric.name

            saved_score = results[sample_key]["scores"].get(metric_name)
            rescore_history = results[sample_key].get(
                "zero_score_rescore_history", {}
            )
            needs_score = should_score_metric(
                saved_score,
                rescore_zero_scores=rescore_zero_scores,
                already_rescored=metric_name in rescore_history,
                retry_rescored_zero_scores=retry_rescored_zero_scores,
            )
            if not needs_score:
                print(
                    f"  {metric_name}: "
                    f"{saved_score} "
                    f"(saved, skipping)"
                )
                continue

            print(f"  Running {metric_name}...")

            score = score_metric(metric, sample)

            results[sample_key]["scores"][metric_name] = score
            results[sample_key].setdefault("metric_models", {})[
                metric_name
            ] = evaluator_model
            if rescore_zero_scores and saved_score == 0:
                history = results[sample_key].setdefault(
                    "zero_score_rescore_history", {}
                )
                attempt = {
                    "previous_score": saved_score,
                    "rescored_score": score,
                    "evaluator_model": evaluator_model,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
                previous_attempts = history.get(metric_name)
                if previous_attempts is None:
                    history[metric_name] = attempt
                elif isinstance(previous_attempts, list):
                    previous_attempts.append(attempt)
                else:
                    history[metric_name] = [previous_attempts, attempt]
            save_results(results, results_file=results_file)

            result_note = " (rescored and saved)" if saved_score == 0 else " (saved)"
            print(f"  {metric_name}: {score}{result_note}")

        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample-index",
        type=int,
        help="Evaluate exactly one 1-based dataset sample and save its scores",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=None,
        help="Results JSON path (use a separate path for new evaluation versions)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of retrieved chunks; defaults to the production pipeline limit",
    )
    parser.add_argument(
        "--dataset-version",
        choices=("v1", "v2", "v3"),
        default="v1",
        help="Evaluation dataset version; v3 uses generated production answers",
    )
    parser.add_argument(
        "--recompute-sample",
        action="store_true",
        help="Preserve prior scores and recompute only after sample inputs/context changed",
    )
    parser.add_argument(
        "--rescore-zero-scores",
        action="store_true",
        help=(
            "Rescore saved zero-valued metrics once using the same saved answer "
            "and retrieval evidence; preserve all other saved scores"
        ),
    )
    parser.add_argument(
        "--retry-zero-scores",
        action="store_true",
        help=(
            "Retry every saved zero-valued metric, including metrics already "
            "rescored; retain each attempt in the rescore history"
        ),
    )
    parser.add_argument(
        "--evaluator-model",
        default=None,
        help="Model used only for RAGAS metric judgments; does not configure production RAG",
    )
    args = parser.parse_args()
    main(
        sample_index=args.sample_index,
        results_file=args.results_file,
        top_k=args.top_k,
        dataset_version=args.dataset_version,
        recompute_sample=args.recompute_sample,
        evaluator_model=args.evaluator_model,
        rescore_zero_scores=(
            args.rescore_zero_scores or args.retry_zero_scores
        ),
        retry_rescored_zero_scores=args.retry_zero_scores,
    )
