"""Question and reference set for live-answer RAGVault evaluation v3."""

from evaluation.ragas_dataset_v2 import EVALUATION_DATASET as V2_DATASET


EVALUATION_DATASET = [
    {
        "user_input": sample["user_input"],
        "reference": sample["reference"],
    }
    for sample in V2_DATASET
]

EVALUATION_DATASET[14] = {
    "user_input": (
        "What chunk size, overlap, and top-k does the RAGVault Engineering "
        "Architecture specify for production and evaluation?"
    ),
    "reference": (
        "The architecture specifies 500-character chunks with 50-character "
        "overlap. Both the production pipeline and the RAGAS evaluation runner "
        "use a top-k limit of five."
    ),
}

EVALUATION_DATASET[23] = {
    "user_input": (
        "Which tests does the security test inventory list for Qdrant ACL "
        "filtering and excluding unauthorized content from the LLM context?"
    ),
    "reference": (
        "The inventory lists test_qdrant_query_uses_tenant_and_user_role_acl_filters "
        "for Qdrant ACL filtering and "
        "test_unauthorized_retrieval_never_reaches_llm_and_is_audited for "
        "unauthorized-context exclusion. Both entries are recorded as passing."
    ),
}
