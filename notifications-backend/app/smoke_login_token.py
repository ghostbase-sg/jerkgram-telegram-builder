from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from .config import Settings
from .telethon_gateway import TelethonGateway


async def _run() -> None:
    settings = Settings.from_env()
    if not settings.telegram_configured:
        raise SystemExit("telegram-login-token-smoke: credentials are not configured")

    gateway = TelethonGateway(settings)
    pair_id = "ci-smoke-login-token"
    challenge = await gateway.start_login(pair_id)
    try:
        if not challenge.token:
            raise RuntimeError("empty_login_token")
        expires = challenge.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            raise RuntimeError("login_token_already_expired")
        # Never print the token, api_hash, or MTProto session material.
        print("telegram-login-token-smoke: PASS (token redacted)")
    finally:
        await gateway.close_login(pair_id)


if __name__ == "__main__":
    asyncio.run(_run())
