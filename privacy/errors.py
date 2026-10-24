class PrivacyError(Exception):
    """
    Base exception for privacy-layer errors.
    """

    def __init__(
        self,
        code: str,
        message: str
    ):
        self.code = code
        self.message = message

        super().__init__(
            message
        )


class PrivacyValidationError(PrivacyError):
    """
    Raised when privacy-token validation fails.
    """

    def __init__(
        self,
        message: str = "Privacy token validation failed."
    ):
        super().__init__(
            code="PRIVACY_VALIDATION_FAILED",
            message=message
        )


class PrivacyDeAnonymizationError(PrivacyError):
    """
    Raised when de-anonymization cannot be completed safely.
    """

    def __init__(
        self,
        message: str = "Privacy de-anonymization failed."
    ):
        super().__init__(
            code="PRIVACY_DEANONYMIZATION_FAILED",
            message=message
        )