"""Exception hierarchy for the Hirebase SDK.

Kept deliberately small and flat so it is trivial to mirror in the future
JavaScript SDK. Every error raised by the SDK is a subclass of
``HirebaseError``.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


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
    """429 - too many requests (100 requests / 60 s per key).

    ``retry_after`` carries the server's ``Retry-After`` seconds when present.
    """

    def __init__(self, *args: Any, retry_after: Optional[int] = None, usage: Any = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after
        self.usage = usage


class QuotaExceededError(RateLimitError):
    """429 with ``X-Billing-Code: limit_exceeded`` - the plan's included
    allowance for this meter is used up (block-mode plans). Backing off will
    not help; lower ``limit`` to fit the remaining units or upgrade.

    ``usage`` is a :class:`hirebase.UsageSnapshot` built from the response
    headers, so ``err.usage.included_remaining`` tells you what is left.
    Subclasses :class:`RateLimitError` so existing ``except RateLimitError``
    handlers keep working.
    """


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


def error_from_response(
    status_code: int, body: Any, headers: Optional[Mapping[str, Any]] = None
) -> APIError:
    """Map an HTTP status + decoded body (+ headers) onto the right exception."""
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
        from .models.usage import UsageSnapshot  # local: avoid import cycle

        usage = UsageSnapshot.from_headers(headers)
        retry_after = _retry_after(headers)
        if usage is not None and usage.is_blocked:
            return QuotaExceededError(
                message, status_code=status_code, body=body, retry_after=retry_after, usage=usage
            )
        return RateLimitError(
            message, status_code=status_code, body=body, retry_after=retry_after, usage=usage
        )
    if status_code >= 500:
        return ServerError(message, status_code=status_code, body=body)
    return APIError(message, status_code=status_code, body=body)


def _retry_after(headers: Optional[Mapping[str, Any]]) -> Optional[int]:
    if not headers:
        return None
    for key, value in headers.items():
        if str(key).lower() == "retry-after":
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


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
