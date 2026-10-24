from privacy.errors import (
    PrivacyDeAnonymizationError
)


def deanonymize_text(
    text: str,
    token_mapping: dict[str, str]
) -> str:
    """
    Replace valid privacy tokens with their original values.
    """

    if not text:

        return text

    if not token_mapping:

        return text

    try:

        deanonymized_text = text

        for token, original_value in token_mapping.items():

            deanonymized_text = (
                deanonymized_text.replace(
                    token,
                    original_value
                )
            )

        return deanonymized_text

    except Exception as exc:

        raise PrivacyDeAnonymizationError(
            "Unable to safely de-anonymize the response."
        ) from exc