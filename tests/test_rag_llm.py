from app.rag.llm import generate_answer


def test_generate_answer_without_context():

    answer = generate_answer(
        question="What is RAGVault?",
        context="",
    )

    assert "authorized" in answer.lower()