from privacy.errors import (
    PrivacyValidationError
)

def resolve_token(
    value: str,
    token_mapping: dict[str, str]
) -> str:
    """
    Resolve a privacy token to its original value.
    Supports tokens with or without square brackets.
    """

    if not value:
        raise PrivacyValidationError(
            "Privacy token cannot be empty."
        )

    if value in token_mapping:
        return token_mapping[value]

    bracketed_value = f"[{value}]"

    if bracketed_value in token_mapping:
        return token_mapping[bracketed_value]

    return value