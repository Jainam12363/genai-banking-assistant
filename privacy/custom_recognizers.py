from presidio_analyzer import Pattern
from presidio_analyzer import PatternRecognizer


# ------------------------------------------------------------------
# ACCOUNT NUMBER
# ------------------------------------------------------------------

account_number_pattern = Pattern(
    name="account_number",
    regex=r"(?<!\d)\d{10}(?!\d)",
    score=0.85
)

account_number_recognizer = PatternRecognizer(
    supported_entity="ACCOUNT_NUMBER",
    patterns=[
        account_number_pattern
    ]
)


# ------------------------------------------------------------------
# PAN
# ------------------------------------------------------------------

pan_pattern = Pattern(
    name="pan",
    regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    score=0.95
)

pan_recognizer = PatternRecognizer(
    supported_entity="PAN",
    patterns=[
        pan_pattern
    ]
)


# ------------------------------------------------------------------
# CUSTOMER ID
# ------------------------------------------------------------------

customer_id_pattern = Pattern(
    name="customer_id",
    regex=r"\bCUST[-_]?\d{4,10}\b",
    score=0.90
)

customer_id_recognizer = PatternRecognizer(
    supported_entity="CUSTOMER_ID",
    patterns=[
        customer_id_pattern
    ]
)


# ------------------------------------------------------------------
# CONTEXT-AWARE PERSON NAME
# ------------------------------------------------------------------

person_name_patterns = [
    Pattern(
        name="name_after_my_name_is",
        regex=r"(?<=my name is )[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?=\s|[.,!?]|$)",
        score=0.95
    ),
    Pattern(
        name="name_after_customer_name",
        regex=r"(?<=customer name is )[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?=\s|[.,!?]|$)",
        score=0.95
    ),
    Pattern(
        name="name_after_contact",
        regex=r"(?<=contact )[A-Z][a-z]+(?=\s+(?:at|on|from)\b|[.,!?]|$)",
        score=0.90
    ),
    Pattern(
        name="name_after_send_money_to",
        regex=r"(?<=send money to )[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?=\s|[.,!?]|$)",
        score=0.90
    ),
    Pattern(
        name="name_after_mr",
        regex=r"(?<=Mr\. )[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?=\s|[.,!?]|$)",
        score=0.90
    ),
    Pattern(
        name="name_after_mrs",
        regex=r"(?<=Mrs\. )[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?=\s|[.,!?]|$)",
        score=0.90
    ),
    Pattern(
        name="name_after_ms",
        regex=r"(?<=Ms\. )[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?=\s|[.,!?]|$)",
        score=0.90
    )
]

person_name_recognizer = PatternRecognizer(
    supported_entity="PERSON",
    patterns=person_name_patterns
)


# ------------------------------------------------------------------
# GENERIC INDIAN PHONE NUMBER
# ------------------------------------------------------------------

generic_phone_pattern = Pattern(
    name="generic_indian_phone",
    regex=r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)",
    score=0.90
)

generic_phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER",
    patterns=[
        generic_phone_pattern
    ]
)

# ------------------------------------------------------------------
# ACCOUNT NUMBER CONTEXT
# ------------------------------------------------------------------

account_context_patterns = [
    Pattern(
        name="account_after_account",
        regex=r"(?<=account )\d{10}",
        score=1.0
    ),
    Pattern(
        name="account_after_account_number",
        regex=r"(?<=account number )\d{10}",
        score=1.0
    ),
    Pattern(
        name="account_after_account_no",
        regex=r"(?<=account no )\d{10}",
        score=1.0
    ),
    Pattern(
        name="account_after_account_number_is",
        regex=r"(?<=account number is )\d{10}",
        score=1.0
    )
]

account_context_recognizer = PatternRecognizer(
    supported_entity="ACCOUNT_NUMBER",
    patterns=account_context_patterns
)

# ------------------------------------------------------------------
# PHONE NUMBER CONTEXT
# ------------------------------------------------------------------

phone_context_patterns = [
    Pattern(
        name="phone_after_phone",
        regex=r"(?<=phone is )(?:\+91[-\s]?)?[6-9]\d{9}",
        score=1.0
    ),
    Pattern(
        name="phone_after_mobile",
        regex=r"(?<=mobile is )(?:\+91[-\s]?)?[6-9]\d{9}",
        score=1.0
    ),
    Pattern(
        name="phone_after_contact",
        regex=r"(?<=contact me at )(?:\+91[-\s]?)?[6-9]\d{9}",
        score=1.0
    ),
    Pattern(
        name="phone_after_call",
        regex=r"(?<=call )(?:\+91[-\s]?)?[6-9]\d{9}",
        score=1.0
    ),
    Pattern(
        name="phone_after_at",
        regex=r"(?<=at )(?:\+91[-\s]?)?[6-9]\d{9}",
        score=1.0
    )
]

phone_context_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER",
    patterns=phone_context_patterns
)