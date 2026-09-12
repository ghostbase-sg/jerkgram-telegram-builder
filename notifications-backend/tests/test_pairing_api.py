from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.pairing import PairStatus, PairingStore, build_authorize_url
from app.telegram_gateway import LoginChallenge


class FakeGateway:
    def __init__(self, *, configured: bool = True) -> None:
        self.configured = configured
        self.started: list[str] = []

    async def start_login(self, pair_id: str) -> LoginChallenge:
        if not self.configured:
            raise RuntimeError("telegram_not_configured")
        self.started.append(pair_id)
        return LoginChallenge(
            token=b"\xfb\xef\xff\x00jerkgram-test-token",
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=30),
        )

    async def wait_for_login(self, pair_id: str) -> None:
        return None

    async def close_login(self, pair_id: str) -> None:
        return None


def test_pairing_store_generates_distinct_high_entropy_ids() -> None:
    store = PairingStore()
    expires = datetime.now(timezone.utc) + timedelta(seconds=30)

    first = store.create(expires_at=expires)
    second = store.create(expires_at=expires)

    assert first.pair_id != second.pair_id
    assert len(first.pair_id) >= 32
    assert first.status is PairStatus.PENDING


def test_terminal_pair_state_cannot_regress() -> None:
    store = PairingStore()
    record = store.create(expires_at=datetime.now(timezone.utc) + timedelta(seconds=30))

    approved = store.transition(record.pair_id, PairStatus.APPROVED)
    ignored = store.transition(record.pair_id, PairStatus.PENDING)

    assert approved.status is PairStatus.APPROVED
    assert ignored.status is PairStatus.APPROVED


def test_pending_pair_expires_on_read() -> None:
    now = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
    store = PairingStore(clock=lambda: now)
    record = store.create(expires_at=now + timedelta(seconds=5))

    now = now + timedelta(seconds=6)
    fetched = store.get(record.pair_id)

    assert fetched is not None
    assert fetched.status is PairStatus.EXPIRED


def test_authorize_url_uses_unpadded_base64url() -> None:
    url = build_authorize_url("pair-123", b"\xfb\xef\xff")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "jerkgram"
    assert parsed.netloc == "push"
    assert parsed.path == "/authorize"
    assert query["pair"] == ["pair-123"]
    assert query["token"] == ["--__"]
    assert "=" not in query["token"][0]


def test_health_does_not_require_telegram_credentials() -> None:
    app = create_app(gateway=FakeGateway(configured=False))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["telegram_configured"] is False


def test_pair_start_returns_short_lived_native_deep_link() -> None:
    gateway = FakeGateway()
    app = create_app(gateway=gateway)
    client = TestClient(app)

    response = client.post("/pair/start")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert len(body["pair_id"]) >= 32
    assert body["authorize_url"].startswith("jerkgram://push/authorize?")
    parsed = urlparse(body["authorize_url"])
    query = parse_qs(parsed.query)
    assert query["pair"] == [body["pair_id"]]
    assert "=" not in query["token"][0]
    assert gateway.started == [body["pair_id"]]


def test_pair_status_returns_404_for_unknown_pair() -> None:
    app = create_app(gateway=FakeGateway())
    client = TestClient(app)

    response = client.get("/pair/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "pair_not_found"


def test_pair_start_returns_503_when_telegram_is_not_configured() -> None:
    app = create_app(gateway=FakeGateway(configured=False))
    client = TestClient(app)

    response = client.post("/pair/start")

    assert response.status_code == 503
    assert response.json()["detail"] == "telegram_not_configured"
