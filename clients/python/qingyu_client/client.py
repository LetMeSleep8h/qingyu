"""A small httpx wrapper around the GET-only Evidence Query API."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
import uuid

import httpx

from qingyu_contracts.evidence import (
    AttachmentObservationPage,
    ConversationObservationSummary,
    NodePage,
    ObservationPage,
)


class QingyuClient:
    """Talks to one Gateway's `/api/v1/evidence` surface with a read token.

    The token is sent as a Bearer credential on every request. Only the
    GET endpoints are wrapped; there is deliberately no method that could
    mutate anything.
    """

    def __init__(self, base_url: str, read_token: str, *, timeout: float = 10.0) -> None:
        # One client instance, one connection pool; reuse it for a session's reads.
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {read_token}"},
            timeout=timeout,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "QingyuClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- single endpoint wrappers ------------------------------------------------

    def conversation_observations(
        self,
        *,
        limit: int = 100,
        cursor: str | None = None,
        source_account_id: uuid.UUID | None = None,
        conversation_id: uuid.UUID | None = None,
    ) -> ObservationPage:
        """One page of conversation observations; `next_cursor` continues it."""
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        if source_account_id is not None:
            params["source_account_id"] = str(source_account_id)
        if conversation_id is not None:
            params["conversation_id"] = str(conversation_id)
        response = self._http.get("/api/v1/evidence/conversation-observations", params=params)
        response.raise_for_status()
        return ObservationPage.model_validate(response.json())

    def nodes(
        self,
        conversation_observation_id: uuid.UUID,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> NodePage:
        """One page of nodes for a conversation observation."""
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        response = self._http.get(
            f"/api/v1/evidence/conversation-observations/{conversation_observation_id}/nodes",
            params=params,
        )
        response.raise_for_status()
        return NodePage.model_validate(response.json())

    def attachment_observations(
        self,
        conversation_observation_id: uuid.UUID,
        attachment_id: uuid.UUID,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> AttachmentObservationPage:
        """One page of observations for one attachment of a conversation."""
        params: dict[str, Any] = {"limit": limit}
        if cursor is not None:
            params["cursor"] = cursor
        response = self._http.get(
            f"/api/v1/evidence/conversation-observations/{conversation_observation_id}"
            f"/attachments/{attachment_id}/observations",
            params=params,
        )
        response.raise_for_status()
        return AttachmentObservationPage.model_validate(response.json())

    # -- page walkers --------------------------------------------------------------

    def iter_conversation_observations(self, **kwargs: Any) -> Iterator[ConversationObservationSummary]:
        """Yields every observation, following the signed cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.conversation_observations(cursor=cursor, **kwargs)
            yield from page.items
            cursor = page.next_cursor
            if cursor is None:
                return
