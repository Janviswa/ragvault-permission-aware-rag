from fastapi import HTTPException, status


ALLOWED_CLASSIFICATIONS = {
    "Public",
    "Internal",
    "Confidential",
    "Restricted",
}


def validate_classification(classification: str) -> None:
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document classification",
        )