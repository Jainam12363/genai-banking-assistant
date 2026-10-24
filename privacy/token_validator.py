import re


TOKEN_PATTERN = re.compile(
    r"\[[A-Z_]+_\d+\]"
)


def find_tokens(
    text: str
) -> list[str]:
    """
    Find privacy tokens present in text.
    """

    if not text:

        return []

    return TOKEN_PATTERN.findall(
        text
    )


def validate_tokens(
    text: str,
    token_mapping: dict[str, str]
) -> dict:
    """
    Validate that every privacy token in the text
    exists in the supplied token mapping.
    """

    tokens = find_tokens(
        text
    )

    if not tokens:

        return {
            "success": True,
            "valid": True,
            "tokens": [],
            "unknown_tokens": []
        }

    unknown_tokens = [
        token
        for token in tokens
        if token not in token_mapping
    ]

    if unknown_tokens:

        return {
            "success": False,
            "valid": False,
            "tokens": tokens,
            "unknown_tokens": unknown_tokens,
            "error": "Unknown privacy token detected."
        }

    return {
        "success": True,
        "valid": True,
        "tokens": tokens,
        "unknown_tokens": []
    }