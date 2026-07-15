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

core_text = core.read_text(encoding="utf-8")
ui_text = ui.read_text(encoding="utf-8")

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(
            f"[v1.0ZB bot difference verifier] {message}"
        )

for proof in (
    "GhostBase v1.0ZB Bot getDifference Probe",
    "ghostBaseBotDifferenceProbe()",
    "Api.functions.updates.getDifference",
    "case let .difference(data)",
    "case let .differenceSlice(data)",
    "case let .differenceEmpty(data)",
    "case let .differenceTooLong(data)",
    "newMessages:",
    "newEncryptedMessages:",
    "otherUpdates:",
    'error.errorDescription ?? "nil"',
):
    require(proof in core_text, f"missing core proof: {proof}")

start = core_text.index(
    "// MARK: GhostBase v1.0ZB Bot getDifference Probe"
)
end = core_text.index(
    "// MARK: GhostBase v1.0ZA Bot Account Capability Probe",
    start
)

require(
    "retryRequest" not in core_text[start:end],
    "difference probe contains retryRequest"
)

for proof in (
    "GhostBase v1.0ZB Bot Difference UI",
    "Проверить updates.getDifference",
    'case "botDifferenceProbe":',
    ".ghostBaseBotDifferenceProbe()",
):
    require(proof in ui_text, f"missing UI proof: {proof}")

require(
    core_text.count("ghostBaseBotDifferenceProbe()") == 1,
    "core probe duplicated"
)

require(
    ui_text.count('case "botDifferenceProbe":') == 1,
    "UI action duplicated"
)

print("[v1.0ZB bot difference verifier] direct request OK")
print("[v1.0ZB bot difference verifier] all result cases OK")
print("[v1.0ZB bot difference verifier] no retry OK")
print("[v1.0ZB bot difference verifier] UI OK")
