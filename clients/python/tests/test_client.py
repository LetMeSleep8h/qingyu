"""Mocked-server tests: pagination, auth header, read-only surface."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".." / "contracts" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qingyu_client import QingyuClient

BASE = "https://gw.example.test"
OBS = {
    "conversation_observation_id": "00000000-0000-4000-8000-000000000001",
    "import_batch_commit_id": "00000000-0000-4000-8000-000000000002",
    "conversation_id": "00000000-0000-4000-8000-000000000003",
    "source_account_id": "00000000-0000-4000-8000-000000000004",
    "archive_object_id": "00000000-0000-4000-8000-000000000005",
    "source_platform": "chatgpt",
    "parser_name": "chatgpt",
    "parser_contract_version": "1",
    "committed_at": "2026-10-01T00:00:00Z",
    "observed_at": "2026-09-30T00:00:00Z",
    "observed_title": "A talk",
    "normalized_created_at": None,
    "normalized_updated_at": None,
    "create_time_parse_status": "absent",
    "update_time_parse_status": "absent",
    "current_conversation_node_id": None,
    "current_node_status": "leaf",
    "source_observation_fingerprint": "f" * 64,
    "canonical_fragment_fingerprint": "c" * 64,
    "fragment_fingerprint_version": "v1",
}


def _page(items: list[dict], next_cursor: str | None) -> dict:
    return {
        "contract_version": "evidence-query-v1",
        "meaning": "gateway_recorded_historical_evidence",
        "consistency": "bounded_high_water_enumeration_v1",
        "items": items,
        "next_cursor": next_cursor,
        "limit": len(items) or 1,
    }


def _client(handler) -> QingyuClient:
    transport = httpx.MockTransport(handler)
    c = QingyuClient.__new__(QingyuClient)
    c._http = httpx.Client(base_url=BASE, headers={"Authorization": "Bearer tok"}, transport=transport)
    return c


def test_sends_bearer_token_and_returns_first_page():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization")
        seen["path"] = request.url.path
        return httpx.Response(200, json=_page([OBS], None))

    with _client(handler) as c:
        page = c.conversation_observations(limit=1)

    assert seen["auth"] == "Bearer tok"
    assert seen["path"] == "/api/v1/evidence/conversation-observations"
    assert page.items[0].observed_title == "A talk"


def test_iter_follows_signed_cursors_until_none():
    calls: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.params.get("cursor"))
        first = calls[-1] is None
        return httpx.Response(200, json=_page([OBS], None if not first else "signed-1"))

    with _client(handler) as c:
        titles = [o.observed_title for o in c.iter_conversation_observations()]

    assert calls == [None, "signed-1"]
    assert titles == ["A talk", "A talk"]


def test_client_exposes_no_write_methods():
    methods = {m for m in dir(QingyuClient) if not m.startswith("_")}
    assert not any(m in methods for m in ("post", "put", "patch", "delete", "create", "upload"))


def test_http_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "no"})

    with _client(handler) as c:
        with pytest.raises(httpx.HTTPStatusError):
            c.conversation_observations()
