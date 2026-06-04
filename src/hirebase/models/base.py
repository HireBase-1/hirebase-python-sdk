"""Shared pydantic base classes."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, PrivateAttr


class ResponseModel(BaseModel):
    """Base for every model parsed from an API response.

    ``extra="allow"`` keeps forward-compatibility: new API fields are retained
    on the instance instead of being dropped or raising.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        arbitrary_types_allowed=True,
    )


class BoundModel(ResponseModel):
    """A response model that holds a back-reference to its client.

    This is what powers ergonomic helpers like ``company.insights()`` -- the
    resource that created the object binds itself so the model can issue
    follow-up requests. The reference is private so it never serializes.
    """

    _client: Optional[Any] = PrivateAttr(default=None)

    def _bind(self, client: Any) -> "BoundModel":
        self._client = client
        return self

    def _require_client(self) -> Any:
        if self._client is None:
            raise RuntimeError(
                "This object is not bound to a client. Fetch it through a "
                "client method (e.g. client.companies.get(...)) to use this "
                "helper."
            )
        return self._client
