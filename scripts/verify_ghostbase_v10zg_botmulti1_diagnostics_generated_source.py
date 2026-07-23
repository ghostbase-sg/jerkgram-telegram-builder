#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
auth_path = root / "submodules/TelegramCore/Sources/Authorization.swift"
shared_path = root / "submodules/TelegramUI/Sources/SharedAccountContext.swift"
for path in (auth_path, shared_path):
    if not path.is_file():
        raise SystemExit(f"[V10ZG BOTMULTI1 verifier] missing: {path}")

auth = auth_path.read_text(encoding="utf-8")
shared = shared_path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[V10ZG BOTMULTI1 verifier] {message}")


for proof in (
    "GhostBase v1.0ZG BOTMULTI1 diagnostics",
    "GhostBase.BotMulti1 sendCode start",
    "GhostBase.BotMulti1 sendCode migrate",
    "GhostBase.BotMulti1 sendCode rpc",
    "GhostBase.BotMulti1 sendCode timeout",
    "GhostBase.BotMulti1 switch authorized begin",
    "GhostBase.BotMulti1 switch authorized completed",
):
    require(proof in auth, f"missing auth proof: {proof}")
require("alternate: .fail(.timeout)" not in auth, "opaque sendCode timeout remains")
require("GhostBase v1.0ZG BOTMULTI1 auth record" in shared, "createAuth marker missing")
require("let authId = transaction.createAuth" in shared, "auth id is not captured")
require("GhostBase.BotMulti1 createAuth" in shared, "createAuth log missing")
require("id=\\(String(describing: authId))" in shared, "optional auth id is not rendered explicitly")
require("id=\\(authId)" not in shared, "implicit optional auth id interpolation remains")
print("[V10ZG verifier] BOTMULTI1 diagnostics OK")
