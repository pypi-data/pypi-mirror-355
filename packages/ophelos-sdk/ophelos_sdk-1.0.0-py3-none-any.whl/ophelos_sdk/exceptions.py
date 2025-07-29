"""
Exception classes for the Ophelos SDK.
"""

from typing import Optional, Dict, Any


class OphelosError(Exception):
    """Base exception class for all Ophelos SDK errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class OphelosAPIError(OphelosError):
    """Exception raised for API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(OphelosAPIError):
    """Exception raised for authentication-related errors."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any):
        super().__init__(message, status_code=401, **kwargs)


class ValidationError(OphelosAPIError):
    """Exception raised for validation errors."""

    def __init__(self, message: str = "Validation failed", **kwargs: Any):
        super().__init__(message, status_code=422, **kwargs)


class NotFoundError(OphelosAPIError):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", **kwargs: Any):
        super().__init__(message, status_code=404, **kwargs)


class RateLimitError(OphelosAPIError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs: Any):
        super().__init__(message, status_code=429, **kwargs)


class ConflictError(OphelosAPIError):
    """Exception raised for conflict errors."""

    def __init__(self, message: str = "Resource conflict", **kwargs: Any):
        super().__init__(message, status_code=409, **kwargs)


class ForbiddenError(OphelosAPIError):
    """Exception raised for forbidden access errors."""

    def __init__(self, message: str = "Access forbidden", **kwargs: Any):
        super().__init__(message, status_code=403, **kwargs)


class ServerError(OphelosAPIError):
    """Exception raised for server errors."""

    def __init__(self, message: str = "Internal server error", **kwargs: Any):
        if "status_code" not in kwargs:
            kwargs["status_code"] = 500
        super().__init__(message, **kwargs)
