from privacy.anonymizer import (
    anonymize_text
)

from privacy.deanonymizer import (
    deanonymize_text
)

from privacy.detector import (
    detect_pii
)

from privacy.errors import (
    PrivacyValidationError
)

from privacy.models import (
    PrivacyResult
)

from privacy.token_validator import (
    validate_tokens
)


def process_text(
    text: str
) -> PrivacyResult:
    """
    Detect and anonymize PII in user input.
    """

    entities = detect_pii(
        text
    )

    return anonymize_text(
        text,
        entities
    )


def validate_agent_response(
    response: str,
    token_mapping: dict[str, str]
) -> dict:
    """
    Validate privacy tokens present in an agent response.
    """

    validation_result = validate_tokens(
        response,
        token_mapping
    )

    if not validation_result["valid"]:

        raise PrivacyValidationError(
            "The agent response contains an unknown privacy token."
        )

    return validation_result


def process_agent_response(
    response: str,
    token_mapping: dict[str, str]
) -> str:
    """
    Validate and de-anonymize an agent response safely.
    """

    validate_agent_response(
        response,
        token_mapping
    )

    return deanonymize_text(
        response,
        token_mapping
    )