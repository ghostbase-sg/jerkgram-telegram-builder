from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LoginChallenge:
    token: bytes
    expires_at: datetime


class TelegramGateway(Protocol):
    @property
    def configured(self) -> bool: ...

    async def start_login(self, pair_id: str) -> LoginChallenge: ...

    async def wait_for_login(self, pair_id: str) -> None: ...

    async def close_login(self, pair_id: str) -> None: ...
