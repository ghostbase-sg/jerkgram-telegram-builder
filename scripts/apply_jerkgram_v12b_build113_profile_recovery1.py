#!/usr/bin/env python3
from __future__ import annotations

import os
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

MARK_BLUR = "Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1"
MARK_GROUPS = "Jerkgram v1.2B BUILD113_COMMON_GROUPS_OWNER1"

def require(v: bool, msg: str) -> None:
    if not v:
        raise RuntimeError("[Build113 profile recovery] " + msg)

for p in (BG, GROUPS, PEER_ITEM):
    require(p.is_file(), f"missing source: {p}")

bg = BG.read_text(encoding="utf-8")
groups = GROUPS.read_text(encoding="utf-8")
peer_item = PEER_ITEM.read_text(encoding="utf-8")

if MARK_BLUR in bg and MARK_GROUPS in groups:
    print("[Build113 profile recovery] already materialized")
    raise SystemExit(0)

old_blur = '''            // MARK: GhostBase v1.1U BUILD106_STATIC_AVATAR_BLUR1
            // Build105 runtime proved that lowering UIVisualEffectView.alpha
            // does not lower blur intensity: it exposes the sharp stretched
            // image beneath it. Keep the persistent blur owner fully opaque.
            //
            // Reduced mode still affects the existing tint/cost policy; it
            // must not turn the scene back into an almost-unblurred avatar.
            self.blurView.alpha = 1.0
'''

new_blur = '''            // MARK: Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1
            // Keep the later decoded-avatar/cache/reopen pipeline, but restore
            // the Build97 visual owner for static avatars. Do not lower the
            // UIVisualEffectView alpha: that reveals the sharp image below it.
            //
            // Static profile photos always use the normal systemMaterial
            // family so Low Power / reduced-cost policy cannot silently turn
            // the fullscreen profile into an almost-sharp stretched avatar.
            if animatedSource == nil {
                self.blurView.effect = UIBlurEffect(
                    style: isDark
                        ? .systemMaterialDark
                        : .systemMaterialLight
                )
            } else {
                self.blurView.effect = UIBlurEffect(style: effectStyle)
            }
            self.blurView.alpha = 1.0
'''

require(
    old_blur in bg or MARK_BLUR in bg,
    "Build106 static-avatar blur owner missing",
)
if MARK_BLUR not in bg:
    bg = bg.replace(old_blur, new_blur, 1)

old_groups_tint = '''            // MARK: GhostBase v1.1T COMMON_GROUPS_NO_BLACK1
            self.ghostBaseGlassTintView.backgroundColor = isDark
                ? UIColor.white.withAlphaComponent(0.055)
                : UIColor.black.withAlphaComponent(0.045)
'''

new_groups_tint = '''            // MARK: Jerkgram v1.2B BUILD113_COMMON_GROUPS_OWNER1
            // The fullscreen profile scene owns blur/tone. Common Groups must
            // not stack a second material/tint plate over it.
            self.backgroundColor = .clear
            self.view.backgroundColor = .clear
            self.listNode.backgroundColor = .clear
            self.listNode.view.backgroundColor = .clear

            self.ghostBaseGlassEffectView.effect = nil
            self.ghostBaseGlassEffectView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.contentView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.isHidden = true
            self.ghostBaseGlassTintView.backgroundColor = .clear

            self.listBackgroundView.isHidden = true
            self.listBackgroundView.alpha = 0.0
            self.listMaskView.isHidden = true
            self.listMaskView.alpha = 0.0
'''

require(
    old_groups_tint in groups or MARK_GROUPS in groups,
    "Build105 Common Groups tint owner missing",
)
if MARK_GROUPS not in groups:
    groups = groups.replace(old_groups_tint, new_groups_tint, 1)

require(
    "systemStyle: .legacy" in groups,
    "Common Groups legacy row renderer missing",
)
require(
    "displayBackground: !ghostBaseGlassEnabled" in groups,
    "Common Groups backgroundless-row configuration missing",
)
require(
    "GhostBase v1.1U BUILD106_COMMON_GROUPS_OWNER1" in peer_item,
    "Build106 ItemListPeerItem background owner missing",
)
require(
    "!item.displayDecorations || !item.displayBackground" in peer_item,
    "ItemListPeerItem does not respect displayBackground",
)

BG.write_text(bg, encoding="utf-8")
GROUPS.write_text(groups, encoding="utf-8")

print("[Build113 profile recovery] static avatar: Build97-style systemMaterial owner installed")
print("[Build113 profile recovery] static avatar: Build105/106 cache/reopen pipeline preserved")
print("[Build113 profile recovery] Common Groups: pane material/tint removed; parent profile scene owns backdrop")
print("[Build113 profile recovery] Common Groups: Build106 transparent row owner preserved")
