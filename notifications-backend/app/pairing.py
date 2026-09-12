from __future__ import annotations

import asyncio
import base64
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from urllib.parse import urlencode

from .telegram_gateway import TelegramGateway


class PairStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXPIRED = "expired"
    FAILED = "failed"


_TERMINAL = {PairStatus.APPROVED, PairStatus.EXPIRED, PairStatus.FAILED}


@dataclass(frozen=True, slots=True)
class PairRecord:
    pair_id: str
    status: PairStatus
    created_at: datetime
    expires_at: datetime
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PairStartSnapshot:
    pair_id: str
    status: PairStatus
    created_at: datetime
    expires_at: datetime
    authorize_url: str


class PairingStore:
    def __init__(self, *, clock=None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._records: dict[str, PairRecord] = {}

    def create(self, *, expires_at: datetime, pair_id: str | None = None) -> PairRecord:
        pair_id = pair_id or self._new_pair_id()
        if pair_id in self._records:
            raise ValueError("pair_id_collision")
        record = PairRecord(
            pair_id=pair_id,
            status=PairStatus.PENDING,
            created_at=self._clock(),
            expires_at=_as_utc(expires_at),
        )
        self._records[pair_id] = record
        return record

    def get(self, pair_id: str) -> PairRecord | None:
        record = self._records.get(pair_id)
        if record is None:
            return None
        if record.status is PairStatus.PENDING and self._clock() >= record.expires_at:
            record = replace(record, status=PairStatus.EXPIRED)
            self._records[pair_id] = record
        return record

    def transition(self, pair_id: str, status: PairStatus, *, error: str | None = None) -> PairRecord:
        record = self._records[pair_id]
        if record.status in _TERMINAL:
            return record
        if status is PairStatus.PENDING:
            return record
        updated = replace(record, status=status, error=error)
        self._records[pair_id] = updated
        return updated

    @staticmethod
    def _new_pair_id() -> str:
        return secrets.token_urlsafe(32)


def build_authorize_url(pair_id: str, token: bytes) -> str:
    encoded_token = base64.urlsafe_b64encode(token).decode("ascii").rstrip("=")
    query = urlencode({"pair": pair_id, "token": encoded_token})
    return f"jerkgram://push/authorize?{query}"


class PairingService:
    def __init__(self, gateway: TelegramGateway, *, store: PairingStore | None = None) -> None:
        self.gateway = gateway
        self.store = store or PairingStore()
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._active_pair_ids: set[str] = set()

    async def start(self) -> PairStartSnapshot:
        pair_id = PairingStore._new_pair_id()
        challenge = await self.gateway.start_login(pair_id)
        record = self.store.create(pair_id=pair_id, expires_at=challenge.expires_at)
        snapshot = PairStartSnapshot(
            pair_id=record.pair_id,
            status=record.status,
            created_at=record.created_at,
            expires_at=record.expires_at,
            authorize_url=build_authorize_url(record.pair_id, challenge.token),
        )
        self._active_pair_ids.add(pair_id)
        self._tasks[pair_id] = asyncio.create_task(self._watch(pair_id), name=f"pair:{pair_id}")
        # qr_login.wait() must already be running before the token is accepted.
        await asyncio.sleep(0)
        return snapshot

    def get(self, pair_id: str) -> PairRecord | None:
        return self.store.get(pair_id)

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for pair_id in list(self._active_pair_ids):
            await self.gateway.close_login(pair_id)
        self._active_pair_ids.clear()

    async def _watch(self, pair_id: str) -> None:
        try:
            await self.gateway.wait_for_login(pair_id)
            self.store.transition(pair_id, PairStatus.APPROVED)
        except asyncio.TimeoutError:
            self.store.transition(pair_id, PairStatus.EXPIRED)
            await self.gateway.close_login(pair_id)
            self._active_pair_ids.discard(pair_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Intentionally do not expose or log Telegram/session details.
            self.store.transition(pair_id, PairStatus.FAILED, error="telegram_login_failed")
            await self.gateway.close_login(pair_id)
            self._active_pair_ids.discard(pair_id)
        finally:
            self._tasks.pop(pair_id, None)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
