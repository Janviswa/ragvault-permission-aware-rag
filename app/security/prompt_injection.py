"""Prompt-injection detection boundary.

This is intentionally conservative: the primary defense remains authorization and
keeping untrusted document text inside a clearly delimited context supplied to the LLM.
"""

PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "reveal hidden instructions",
    "developer message",
)

def contains_prompt_injection(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in PATTERNS)
