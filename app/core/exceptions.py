"""Custom exception hierarchy for GrocyScan."""

from typing import Any


class AppException(Exception):
    """Base exception for the application.

    All custom exceptions should inherit from this class.

    Args:
        message: Human-readable error message
        details: Additional context about the error
        error_code: Machine-readable error code
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details if self.details else None,
        }


class NotFoundError(AppException):
    """Resource not found.

    Raised when a requested resource (product, location, etc.) doesn't exist.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "NOT_FOUND")


class ValidationError(AppException):
    """Input validation failed.

    Raised when user input fails validation rules.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "VALIDATION_ERROR")


class AuthenticationError(AppException):
    """Authentication failed.

    Raised when authentication credentials are invalid or missing.
    """

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "AUTHENTICATION_ERROR")


class AuthorizationError(AppException):
    """Authorization failed.

    Raised when a user lacks permission for an action.
    """

    def __init__(
        self,
        message: str = "Permission denied",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "AUTHORIZATION_ERROR")


class ExternalServiceError(AppException):
    """External service call failed.

    Raised when communication with an external service fails.
    """

    def __init__(
        self,
        message: str = "External service error",
        details: dict[str, Any] | None = None,
        service_name: str | None = None,
    ) -> None:
        if service_name:
            details = details or {}
            details["service"] = service_name
        super().__init__(message, details, "EXTERNAL_SERVICE_ERROR")


class GrocyError(ExternalServiceError):
    """Grocy API error.

    Raised when the Grocy API returns an error or is unreachable.
    """

    def __init__(
        self,
        message: str = "Grocy API error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "grocy")
        self.error_code = "GROCY_ERROR"


class LookupError(ExternalServiceError):
    """Barcode lookup error.

    Raised when all lookup providers fail to find a barcode.
    """

    def __init__(
        self,
        message: str = "Barcode lookup failed",
        details: dict[str, Any] | None = None,
        provider: str | None = None,
    ) -> None:
        super().__init__(message, details, provider or "lookup")
        self.error_code = "LOOKUP_ERROR"


class LLMError(ExternalServiceError):
    """LLM service error.

    Raised when the LLM service fails.
    """

    def __init__(
        self,
        message: str = "LLM service error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "llm")
        self.error_code = "LLM_ERROR"


class CacheError(AppException):
    """Cache operation error.

    Raised when Redis cache operations fail.
    """

    def __init__(
        self,
        message: str = "Cache operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "CACHE_ERROR")


class QueueError(AppException):
    """Job queue error.

    Raised when job queue operations fail.
    """

    def __init__(
        self,
        message: str = "Job queue operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details, "QUEUE_ERROR")


class BarcodeValidationError(ValidationError):
    """Barcode validation error.

    Raised when a barcode fails format or checksum validation.
    """

    def __init__(
        self,
        message: str = "Invalid barcode",
        barcode: str | None = None,
        barcode_type: str | None = None,
    ) -> None:
        details = {}
        if barcode:
            details["barcode"] = barcode
        if barcode_type:
            details["expected_type"] = barcode_type
        super().__init__(message, details)
        self.error_code = "BARCODE_VALIDATION_ERROR"
