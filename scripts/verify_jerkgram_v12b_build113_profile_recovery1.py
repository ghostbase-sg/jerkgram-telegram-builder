#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

BG = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/"
    "PeerInfoScreen/Sources/"
    "GhostBaseProfileFullscreenBackground.swift"
)

GROUPS = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/"
    "PeerInfoScreen/Sources/Panes/"
    "PeerInfoGroupsInCommonPaneNode.swift"
)

PEER_ITEM = ROOT / (
    "submodules/ItemListPeerItem/Sources/"
    "ItemListPeerItem.swift"
)

def require(v: bool, msg: str) -> None:
    if not v:
        raise RuntimeError("[verify Build113 profile recovery] " + msg)

for p in (BG, GROUPS, PEER_ITEM):
    require(p.is_file(), f"missing source: {p}")

bg = BG.read_text(encoding="utf-8")
groups = GROUPS.read_text(encoding="utf-8")
peer_item = PEER_ITEM.read_text(encoding="utf-8")

require(
    "Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1" in bg,
    "Build113 static-avatar blur marker missing",
)
require(
    ".systemMaterialDark" in bg and ".systemMaterialLight" in bg,
    "normal systemMaterial static-avatar owner missing",
)
require(
    "if animatedSource == nil" in bg,
    "static/animated avatar split missing",
)
require(
    "self.blurView.alpha = 1.0" in bg,
    "persistent blur must remain fully opaque",
)
require(
    "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1" in bg,
    "Build105 360px native avatar pipeline missing",
)
require(
    "GhostBase v1.1T BUILD97_STATIC_AVATAR_CACHE1" in bg,
    "Build105 persistent avatar cache missing",
)

require(
    "Jerkgram v1.2B BUILD113_COMMON_GROUPS_OWNER1" in groups,
    "Build113 Common Groups marker missing",
)
for token in (
    "self.backgroundColor = .clear",
    "self.view.backgroundColor = .clear",
    "self.listNode.backgroundColor = .clear",
    "self.listNode.view.backgroundColor = .clear",
    "self.ghostBaseGlassEffectView.effect = nil",
    "self.ghostBaseGlassEffectView.isHidden = true",
    "self.ghostBaseGlassTintView.backgroundColor = .clear",
    "self.listBackgroundView.isHidden = true",
    "self.listBackgroundView.alpha = 0.0",
    "self.listMaskView.isHidden = true",
    "self.listMaskView.alpha = 0.0",
    "systemStyle: .legacy",
    "displayBackground: !ghostBaseGlassEnabled",
):
    require(token in groups, f"Common Groups owner missing token: {token}")

require(
    "GhostBase v1.1U BUILD106_COMMON_GROUPS_OWNER1" in peer_item,
    "Build106 row owner missing",
)
require(
    re.search(
        r"backgroundNode\.isHidden\s*=\s*"
        r"!item\.displayDecorations\s*\|\|\s*!item\.displayBackground",
        peer_item,
    ) is not None,
    "late ItemListPeerItem background pass can still re-enable opaque rows",
)

print("[verify Build113 profile recovery] GREEN")
print("[verify Build113 profile recovery] static-avatar blur owner coherent")
print("[verify Build113 profile recovery] Common Groups has no pane-level black/material owner")
