"""Client configuration and environment resolution.

Resolution order for every setting is: explicit argument -> environment
variable -> built-in default. Keeping this in one place makes the sync and
async clients behave identically and makes the eventual JS port a 1:1 map.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .exceptions import ConfigurationError

DEFAULT_BASE_URL = "https://api.hirebase.org"
DEFAULT_TIMEOUT = 30.0

ENV_API_KEY = "HIREBASE_API_KEY"
# ``HIREBASE_API_URL`` is accepted as a fallback for parity with the CLI.
ENV_BASE_URL = "HIREBASE_BASE_URL"
ENV_BASE_URL_LEGACY = "HIREBASE_API_URL"


@dataclass
class Settings:
    """Resolved, immutable client settings."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT

    @classmethod
    def resolve(
        cls,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> "Settings":
        key = api_key or os.getenv(ENV_API_KEY)
        if not key:
            raise ConfigurationError(
                "No API key provided. Pass api_key=... or set the "
                f"{ENV_API_KEY} environment variable."
            )

        url = (
            base_url
            or os.getenv(ENV_BASE_URL)
            or os.getenv(ENV_BASE_URL_LEGACY)
            or DEFAULT_BASE_URL
        )
        url = url.rstrip("/")

        return cls(
            api_key=key,
            base_url=url,
            timeout=DEFAULT_TIMEOUT if timeout is None else timeout,
        )

    @property
    def headers(self) -> dict:
        """Default headers for every request.

        ``Content-Type`` is intentionally omitted here so multipart uploads
        (resume file fields) get the correct ``multipart/form-data`` boundary.
        JSON bodies set ``application/json`` per request in the client layer.
        """
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }
