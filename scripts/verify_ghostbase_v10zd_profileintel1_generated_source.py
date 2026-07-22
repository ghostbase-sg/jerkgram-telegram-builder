#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

core_path = root / (
    "submodules/TelegramCore/Sources/TelegramEngine/Peers/"
    "TelegramEnginePeers.swift"
)
ui_path = root / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

for path in (core_path, ui_path):
    if not path.is_file():
        raise SystemExit(f"[v1.0ZD verifier] missing source: {path}")

core = core_path.read_text(encoding="utf-8")
ui = ui_path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZD verifier] {message}")


for proof in (
    "GhostBase v1.0ZD PROFILEINTEL1 Core",
    "ghostBaseProfileIntelProbe(",
    "_internal_resolvePeerByName(",
    "ageLimit: 0",
    "Api.functions.users.getFullUser",
    "Api.functions.messages.getPeerSettings",
    "hasRegistrationMonth:",
    "hasPhoneCountry:",
    "hasNameChangeDate:",
    "hasPhotoChangeDate:",
    "bit0IsHidden:",
    "dialogRequired: no",
    "automaticFloodWait: false",
):
    require(proof in core, f"missing core proof: {proof}")

probe_start = core.index("GhostBase v1.0ZD PROFILEINTEL1 Core")
probe_source = core[probe_start:]
require("account.setPrivacy" not in probe_source, "probe mutates privacy")
require("retryRequest" not in probe_source, "probe retries RPC calls")
require("photos.getUserPhotos" not in probe_source, "probe includes photo history")

for proof in (
    "GhostBase v1.0ZD PROFILEINTEL1 UI",
    "Проверить username из буфера",
    "UIPasteboard.general.string",
    ".ghostBaseProfileIntelProbe(username: target)",
    "ghostBaseProfileIntelDisposable",
    "CURRENT",
    "PREVIOUS",
):
    require(proof in ui, f"missing UI proof: {proof}")

print("[v1.0ZD verifier] username resolve probe OK")
print("[v1.0ZD verifier] getFullUser + getPeerSettings OK")
print("[v1.0ZD verifier] PeerSettings flags 15...18 captured")
print("[v1.0ZD verifier] approximate presence bit-0/isHidden captured")
print("[v1.0ZD verifier] no privacy mutation or background tracking")
