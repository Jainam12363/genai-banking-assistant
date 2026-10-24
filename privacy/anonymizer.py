from privacy.models import PIIEntity, PrivacyResult


def anonymize_text(
    text: str,
    entities: list[PIIEntity]
) -> PrivacyResult:
    """
    Replace detected PII with deterministic tokens.
    """

    if not text:

        return PrivacyResult(
            original_text=text,
            anonymized_text=text
        )

    token_mapping = {}   #example: [EMAIL_1] → john@example.com, useful for deanonymization

    value_to_token = {}   #example: john@example.com → [EMAIL_1], useful for anonymization

    token_counters = {}   #Example: ACCOUNT_NUMBER_1, ACCOUNT_NUMBER_2, etc. keeps track of numbering

    replacements = []  #example: replace position 14–24 with [ACCOUNT_NUMBER_1]

    for entity in entities:

        if entity.value in value_to_token:

            token = value_to_token[
                entity.value
            ]

        else:

            count = token_counters.get(
                entity.pii_type,
                0
            ) + 1

            token_counters[
                entity.pii_type
            ] = count

            token = (
                f"[{entity.pii_type}_{count}]"
            )

            value_to_token[
                entity.value
            ] = token

            token_mapping[
                token
            ] = entity.value

        entity.token = token

        replacements.append(
            (
                entity.start,
                entity.end,
                token
            )
        )

    anonymized_text = text

    for start, end, token in reversed(
        replacements
    ):

        anonymized_text = (
            anonymized_text[:start]
            + token
            + anonymized_text[end:]
        )

    return PrivacyResult(
        original_text=text,
        anonymized_text=anonymized_text,
        entities=entities,
        token_mapping=token_mapping
    )


def anonymize_with_existing_mapping(
    text: str,
    token_mapping: dict[str, str]
) -> str:
    """
    Replace original PII values with their existing privacy tokens.

    This is used for tool results so that sensitive values returned
    by banking APIs are anonymized before they are sent back to the LLM.
    """

    if not text or not token_mapping:
        return text

    anonymized_text = text

    # Replace longer values first to avoid partial replacements.
    mappings = sorted(
        token_mapping.items(),
        key=lambda item: len(item[1]),
        reverse=True
    )

    for token, original_value in mappings:

        anonymized_text = (
            anonymized_text.replace(
                original_value,
                token
            )
        )

    return anonymized_text