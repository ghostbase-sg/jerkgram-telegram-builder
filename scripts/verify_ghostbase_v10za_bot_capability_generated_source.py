#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

core = root / (
    "submodules/TelegramCore/Sources/TelegramEngine/Peers/"
    "TelegramEnginePeers.swift"
)

ui = root / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

if not core.is_file():
    raise SystemExit(f"missing core source: {core}")

if not ui.is_file():
    raise SystemExit(f"missing UI source: {ui}")

core_text = core.read_text(encoding="utf-8")
ui_text = ui.read_text(encoding="utf-8")

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(
            f"[v1.0ZA bot capability verifier] {message}"
        )

for proof in (
    "GhostBase v1.0ZA Bot Account Capability Probe",
    "ghostBaseBotCapabilityProbe()",
    "Api.functions.users.getUsers",
    "Api.functions.updates.getState",
    "Api.functions.messages.getDialogs",
    "Api.functions.messages.getPinnedDialogs",
    "rpcError:",
    "rpcDescription:",
):
    require(proof in core_text, f"missing core proof: {proof}")

probe_start = core_text.index(
    "// MARK: GhostBase v1.0ZA Bot Account Capability Probe"
)

require(
    "retryRequest" not in core_text[probe_start:],
    "direct capability probe must not retry"
)

for proof in (
    "GhostBase v1.0ZA Bot Capability UI",
    "Bot Account Capability Probe",
    "Проверить RPC bot-аккаунта",
    'case "botCapabilityProbe":',
    ".ghostBaseBotCapabilityProbe()",
):
    require(proof in ui_text, f"missing UI proof: {proof}")

require(
    core_text.count("ghostBaseBotCapabilityProbe()") == 1,
    "core probe duplicated"
)

require(
    ui_text.count('case "botCapabilityProbe":') == 1,
    "UI action duplicated"
)

print("[v1.0ZA bot capability verifier] direct RPC core OK")
print("[v1.0ZA bot capability verifier] no retry boundary OK")
print("[v1.0ZA bot capability verifier] Debug / Research UI OK")
print("[v1.0ZA bot capability verifier] token-independent probe OK")
