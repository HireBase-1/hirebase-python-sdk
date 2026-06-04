"""Exception hierarchy for the Hirebase SDK.

Kept deliberately small and flat so it is trivial to mirror in the future
JavaScript SDK. Every error raised by the SDK is a subclass of
``HirebaseError``.
"""

from __future__ import annotations

from typing import Any, Optional


class HirebaseError(Exception):
    """Base class for every error raised by the SDK."""


class ConfigurationError(HirebaseError):
    """Raised when the client is misconfigured (e.g. no API key)."""


class APIError(HirebaseError):
    """Raised when the API returns a non-2xx response.

    Attributes:
        status_code: HTTP status code returned by the API.
        message: Human readable error message (the API ``detail`` field
            when available).
        body: The decoded response body, if any.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Any = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.body = body
        prefix = f"[{status_code}] " if status_code is not None else ""
        super().__init__(f"{prefix}{message}")


class AuthenticationError(APIError):
    """401 - the API key is missing or invalid."""


class PermissionError_(APIError):
    """403 - the API key is valid but not allowed to access the resource."""


class PaymentRequiredError(APIError):
    """402 - the request requires an active plan / available credits."""


class NotFoundError(APIError):
    """404 - the requested resource does not exist."""


class RateLimitError(APIError):
    """429 - too many requests."""


class ServerError(APIError):
    """5xx - something went wrong on the Hirebase side."""


class TaskError(HirebaseError):
    """Raised when an async task fails or times out."""


class TaskFailed(TaskError):
    """The task finished in a failed/canceled state."""

    def __init__(self, message: str, *, task: Any = None) -> None:
        self.task = task
        super().__init__(message)


class TaskTimeout(TaskError):
    """The task did not finish within the allotted polling window."""

    def __init__(self, message: str, *, task: Any = None) -> None:
        self.task = task
        super().__init__(message)


def error_from_response(status_code: int, body: Any) -> APIError:
    """Map an HTTP status + decoded body onto the right exception type."""
    message = _extract_message(body) or f"HTTP {status_code}"

    if status_code == 401:
        return AuthenticationError(message, status_code=status_code, body=body)
    if status_code == 402:
        return PaymentRequiredError(message, status_code=status_code, body=body)
    if status_code == 403:
        return PermissionError_(message, status_code=status_code, body=body)
    if status_code == 404:
        return NotFoundError(message, status_code=status_code, body=body)
    if status_code == 429:
        return RateLimitError(message, status_code=status_code, body=body)
    if status_code >= 500:
        return ServerError(message, status_code=status_code, body=body)
    return APIError(message, status_code=status_code, body=body)


def _extract_message(body: Any) -> Optional[str]:
    if isinstance(body, dict):
        detail = body.get("detail", body.get("message"))
        if isinstance(detail, list):  # FastAPI validation errors
            try:
                return "; ".join(
                    f"{'.'.join(str(p) for p in d.get('loc', []))}: {d.get('msg')}"
                    for d in detail
                )
            except Exception:  # pragma: no cover - defensive
                return str(detail)
        if detail is not None:
            return str(detail)
    if isinstance(body, str) and body:
        return body
    return None
