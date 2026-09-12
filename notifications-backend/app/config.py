from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_api_id: int | None
    telegram_api_hash: str | None
    app_version: str = "0.1.0-poc"

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_api_id and self.telegram_api_hash)

    @classmethod
    def from_env(cls) -> "Settings":
        raw_api_id = os.getenv("TELEGRAM_API_ID", "").strip()
        api_hash = os.getenv("TELEGRAM_API_HASH", "").strip() or None
        try:
            api_id = int(raw_api_id) if raw_api_id else None
        except ValueError:
            api_id = None
        return cls(telegram_api_id=api_id, telegram_api_hash=api_hash)
