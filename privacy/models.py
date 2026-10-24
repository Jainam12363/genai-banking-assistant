from dataclasses import dataclass, field


@dataclass
class PIIEntity:
    """
    Represent one piece of detected PII.
    """

    pii_type: str
    value: str
    start: int
    end: int
    token: str = ""


@dataclass
class PrivacyResult:
    """
    Store the result of PII detection and anonymization.
    """

    original_text: str
    anonymized_text: str
    entities: list[PIIEntity] = field(
        default_factory=list
    )
    token_mapping: dict[str, str] = field(
        default_factory=dict
    )