from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import (
    NlpEngineProvider
)

from privacy.models import PIIEntity

from privacy.custom_recognizers import (
    account_number_recognizer,
    pan_recognizer,
    customer_id_recognizer,
    person_name_recognizer,
    phone_context_recognizer,
    generic_phone_recognizer,
    account_context_recognizer
)


# Configure Presidio to use the installed spaCy model
nlp_configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {
            "lang_code": "en",
            "model_name": "en_core_web_sm"
        }
    ]
}

provider = NlpEngineProvider(
    nlp_configuration=nlp_configuration
)

nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    supported_languages=["en"]
)



analyzer.registry.add_recognizer(
    account_number_recognizer
)

analyzer.registry.add_recognizer(
    pan_recognizer
)

analyzer.registry.add_recognizer(
    customer_id_recognizer
)

analyzer.registry.add_recognizer(
    person_name_recognizer
)

analyzer.registry.add_recognizer(
    generic_phone_recognizer
)

analyzer.registry.add_recognizer(
    phone_context_recognizer
)

analyzer.registry.add_recognizer(
    account_context_recognizer
)

# Map Presidio entity names to our existing privacy entity names
ENTITY_MAPPING = {
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE_NUMBER",
    "PERSON": "PERSON",
    "LOCATION": "LOCATION",
    "IP_ADDRESS": "IP_ADDRESS",
    "CREDIT_CARD": "CARD_NUMBER",
    "ACCOUNT_NUMBER": "ACCOUNT_NUMBER",
    "PAN": "PAN",
    "CUSTOMER_ID": "CUSTOMER_ID",
}


def detect_pii(
    text: str
) -> list[PIIEntity]:
    """
    Detect sensitive information using Presidio.

    Presidio combines:
    - NLP/NER recognition
    - Built-in pattern recognizers
    - Custom pattern recognizers
    """

    if not text or not text.strip():
        return []

    results = analyzer.analyze(
        text=text,
        language="en"
    )

    entities = []

    for result in results:

        pii_type = ENTITY_MAPPING.get(
            result.entity_type
        )

        if not pii_type:
            continue

        value = text[
            result.start:result.end
        ]

        entities.append(
            PIIEntity(
                pii_type=pii_type,
                value=value,
                start=result.start,
                end=result.end
            )
        )

    # Sort by position and prefer longer entities
    entities.sort(
        key=lambda entity: (
            entity.start,
            -(entity.end - entity.start)
        )
    )

    # Remove overlapping entities
    filtered_entities = []

    for entity in entities:

        overlaps = False

        for existing in filtered_entities:

            if (
                entity.start < existing.end
                and entity.end > existing.start
            ):
                overlaps = True
                break

        if not overlaps:
            filtered_entities.append(
                entity
            )

    filtered_entities.sort(
        key=lambda entity: entity.start
    )

    return filtered_entities