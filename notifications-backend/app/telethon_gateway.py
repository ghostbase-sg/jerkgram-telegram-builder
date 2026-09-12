from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession

from .config import Settings
from .telegram_gateway import LoginChallenge


@dataclass(slots=True)
class _Attempt:
    client: TelegramClient
    qr: object


class TelethonGateway:
    """Test-only in-memory Telegram login-token gateway.

    No Telegram session string is written to disk or logs. An approved client
    remains connected in memory until shutdown so the next PoC milestone can
    attach update handling to the same independent authorization.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._attempts: dict[str, _Attempt] = {}

    @property
    def configured(self) -> bool:
        return self._settings.telegram_configured

    async def start_login(self, pair_id: str) -> LoginChallenge:
        if not self.configured:
            raise RuntimeError("telegram_not_configured")
        if pair_id in self._attempts:
            raise RuntimeError("pair_already_started")

        assert self._settings.telegram_api_id is not None
        assert self._settings.telegram_api_hash is not None
        client = TelegramClient(
            StringSession(),
            self._settings.telegram_api_id,
            self._settings.telegram_api_hash,
            device_model="Jerkgram Notifications",
            system_version="Jerkgram Backend PoC",
            app_version=self._settings.app_version,
            lang_code="en",
            system_lang_code="en",
            sequential_updates=True,
        )
        try:
            await client.connect()
            qr = await client.qr_login()
        except Exception:
            await client.disconnect()
            raise

        expires_at = _utc(qr.expires)
        self._attempts[pair_id] = _Attempt(client=client, qr=qr)
        return LoginChallenge(token=bytes(qr.token), expires_at=expires_at)

    async def wait_for_login(self, pair_id: str) -> None:
        attempt = self._attempts[pair_id]
        now = datetime.now(timezone.utc)
        remaining = max(0.0, (_utc(attempt.qr.expires) - now).total_seconds())
        if remaining <= 0:
            raise TimeoutError
        await attempt.qr.wait(timeout=remaining)

    async def close_login(self, pair_id: str) -> None:
        attempt = self._attempts.pop(pair_id, None)
        if attempt is not None:
            await attempt.client.disconnect()


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
