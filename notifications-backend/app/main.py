from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import Settings
from .pairing import PairingService
from .telegram_gateway import TelegramGateway
from .telethon_gateway import TelethonGateway


def create_app(*, gateway: TelegramGateway | None = None, settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    gateway = gateway or TelethonGateway(settings)
    service = PairingService(gateway)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            await service.shutdown()

    app = FastAPI(title="Jerkgram Notifications Backend PoC", version="0.1.0", lifespan=lifespan)
    app.state.pairing_service = service

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {
            "status": "ok",
            "telegram_configured": gateway.configured,
            "mode": "test-account-poc",
        }

    @app.post("/pair/start", status_code=201)
    async def pair_start() -> dict[str, object]:
        if not gateway.configured:
            raise HTTPException(status_code=503, detail="telegram_not_configured")
        try:
            pair = await service.start()
        except RuntimeError as exc:
            if str(exc) == "telegram_not_configured":
                raise HTTPException(status_code=503, detail="telegram_not_configured") from None
            raise HTTPException(status_code=409, detail="pair_start_conflict") from None
        except Exception:
            # Keep Telegram/network/session details out of HTTP responses.
            raise HTTPException(status_code=502, detail="telegram_login_start_failed") from None
        return {
            "pair_id": pair.pair_id,
            "status": pair.status.value,
            "created_at": pair.created_at,
            "expires_at": pair.expires_at,
            "authorize_url": pair.authorize_url,
        }

    @app.get("/pair/{pair_id}")
    async def pair_status(pair_id: str) -> dict[str, object]:
        record = service.get(pair_id)
        if record is None:
            raise HTTPException(status_code=404, detail="pair_not_found")
        return {
            "pair_id": record.pair_id,
            "status": record.status.value,
            "created_at": record.created_at,
            "expires_at": record.expires_at,
            "error": record.error,
        }

    return app


app = create_app()
