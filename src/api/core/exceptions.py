"""Custom exception classes for the Qlik Sense API."""

from typing import Any


class QlikSenseAPIException(Exception):
    """Base exception for all Qlik Sense API errors."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(QlikSenseAPIException):
    """Raised when there is a configuration error."""

    def __init__(self, message: str = "Configuration error", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=500, details=details)


class CertificateError(QlikSenseAPIException):
    """Raised when there is an issue with SSL certificates."""

    def __init__(
        self, message: str = "Certificate error", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, status_code=500, details=details)


class QlikConnectionError(QlikSenseAPIException):
    """Raised when connection to Qlik Sense fails."""

    def __init__(
        self,
        message: str = "Failed to connect to Qlik Sense",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=503, details=details)


class QlikAuthenticationError(QlikSenseAPIException):
    """Raised when authentication with Qlik Sense fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=401, details=details)


class QlikResourceNotFoundError(QlikSenseAPIException):
    """Raised when a requested Qlik resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=404, details=details)


class QlikEngineError(QlikSenseAPIException):
    """Raised when Qlik Engine API returns an error."""

    def __init__(
        self,
        message: str = "Qlik Engine error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=500, details=details)


class QlikRepositoryError(QlikSenseAPIException):
    """Raised when Qlik Repository API returns an error."""

    def __init__(
        self,
        message: str = "Qlik Repository error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=500, details=details)


class ValidationError(QlikSenseAPIException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=422, details=details)


class RateLimitError(QlikSenseAPIException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=429, details=details)


class TimeoutError(QlikSenseAPIException):
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=504, details=details)


class DataExtractionError(QlikSenseAPIException):
    """Raised when data extraction from Qlik fails."""

    def __init__(
        self,
        message: str = "Data extraction failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, status_code=500, details=details)


class AppNotFoundException(QlikSenseAPIException):
    """Raised when a Qlik Sense app is not found."""

    def __init__(
        self,
        app_name: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        message = f"Application '{app_name}' not found"
        super().__init__(message=message, status_code=404, details=details)


class TableNotFoundException(QlikSenseAPIException):
    """Raised when a table is not found in a Qlik Sense app."""

    def __init__(
        self,
        table_name: str,
        app_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if app_name:
            message = f"Table '{table_name}' not found in app '{app_name}'"
        else:
            message = f"Table '{table_name}' not found"
        super().__init__(message=message, status_code=404, details=details)
