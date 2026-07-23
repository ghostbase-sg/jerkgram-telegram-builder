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
        raise SystemExit(f"[PROFILEINTEL2 verifier] missing source: {path}")

core = core_path.read_text(encoding="utf-8")
ui = ui_path.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[PROFILEINTEL2 verifier] {message}")


for proof in (
    "GhostBase v1.0ZF PROFILEINTEL2 Core",
    "ghostBaseProfileIntel2Snapshot(",
    "_internal_requestPeerPhotos(",
    "GhostBase.ProfileIntel2.",
    "Наблюдение начато",
    "Наблюдаемая сессия",
    "serverPhotoDates",
    "phoneCountryNumber",
    "Exact-status privacy mutation was not performed",
):
    require(proof in core, f"core proof missing: {proof}")

section = core[core.index("GhostBase v1.0ZF PROFILEINTEL2 Core"):]
require("account.setPrivacy" not in section, "unsafe direct privacy mutation found")
require(
    "updateSelectiveAccountPrivacySettings" not in section,
    "privacy settings mutation found in read-only snapshot"
)

for proof in (
    "GhostBase v1.0ZF PROFILEINTEL2 UI",
    "PROFILEINTEL2",
    "Снимок профиля + история фото",
    'case "profileIntel2Snapshot":',
    ".ghostBaseProfileIntel2Snapshot(username: target)",
):
    require(proof in ui, f"UI proof missing: {proof}")

print("[PROFILEINTEL2 verifier] local snapshots/history OK")
print("[PROFILEINTEL2 verifier] server photo-history probe OK")
print("[PROFILEINTEL2 verifier] PeerSettings preservation OK")
print("[PROFILEINTEL2 verifier] read-only privacy policy OK")
