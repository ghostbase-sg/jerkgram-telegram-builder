#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

PATHS = {
    "media": ROOT / "submodules/MediaPlayer/Sources/MediaPlayerNode.swift",
    "chunk": ROOT / "submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift",
    "bg": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift",
    "groups": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift",
    "music_controls": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControlsNode.swift",
    "music_controller": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift",
}

MARKER = "GhostBase v1.1S RUNTIME_RECOVERY1"

for name, path in PATHS.items():
    if not path.is_file():
        raise RuntimeError(f"[V11S] missing required source {name}: {path}")

sources = {name: path.read_text(encoding="utf-8") for name, path in PATHS.items()}

if MARKER in sources["bg"]:
    print("[V11S] RUNTIME_RECOVERY1 already materialized")
    raise SystemExit(0)

required_v11r = {
    "media": "GhostBase v1.1R SECONDARY_VIDEO_LIFECYCLE1",
    "chunk": "GhostBase v1.1R SECONDARY_VIDEO_RECOVERY1",
    "bg": "GhostBase v1.1R STATIC_AVATAR_DIRECT_RESOURCE1",
    "groups": "GhostBase v1.1R COMMON_GROUPS_GLASS1",
    "music_controls": "GhostBase v1.1R MUSIC_CONTROLS_GLASS2",
    "music_controller": "GhostBase v1.1R MUSIC_HEADER_GLASS2",
}
for name, marker in required_v11r.items():
    if marker not in sources[name]:
        raise RuntimeError(f"[V11S] missing V11R prerequisite in {name}: {marker}")

backups = dict(sources)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"[V11S] {label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def replace_region(text: str, start_token: str, end_token: str, replacement: str, label: str) -> str:
    start = text.find(start_token)
    if start < 0:
        raise RuntimeError(f"[V11S] {label}: start token missing")
    end = text.find(end_token, start)
    if end < 0:
        raise RuntimeError(f"[V11S] {label}: end token missing")
    return text[:start] + replacement + text[end:]


try:
    # ------------------------------------------------------------------
    # 1. Video: keep the watchdog fix (secondary preventsCapture stays
    #    removed), but undo the aggressive per-frame/per-tick flush loop
    #    that regressed animated profile backgrounds in Build103.
    # ------------------------------------------------------------------
    media = sources["media"]
    media = replace_region(
        media,
        "    private static func enqueueSecondaryCopies(\n",
        "    private func startPolling() {\n",
        '''    // MARK: GhostBase v1.1S SECONDARY_VIDEO_STABLE1\n    private static func enqueueSecondaryCopies(\n        _ sampleBuffer: CMSampleBuffer,\n        layers: [AVSampleBufferDisplayLayer]\n    ) {\n        for layer in layers where layer.isReadyForMoreMediaData {\n            var copy: CMSampleBuffer?\n            if CMSampleBufferCreateCopy(\n                allocator: kCFAllocatorDefault,\n                sampleBuffer: sampleBuffer,\n                sampleBufferOut: &copy\n            ) == noErr, let copy {\n                layer.enqueue(copy)\n            }\n        }\n    }\n\n''',
        "secondary copy stable restore",
    )
    sources["media"] = media

    chunk = sources["chunk"]
    recovery_start = "    // MARK: GhostBase v1.1R SECONDARY_VIDEO_RECOVERY1\n"
    update_token = "    private func updateInternalState() {\n"
    start = chunk.find(recovery_start)
    if start < 0:
        raise RuntimeError("[V11S] Chunk recovery marker missing")
    update = chunk.find(update_token, start)
    if update < 0:
        raise RuntimeError("[V11S] Chunk updateInternalState boundary missing")
    body_start = update + len(update_token)
    injected = (
        "        // ChunkMediaPlayerV2 already ticks on the main run loop. Repair only\n"
        "        // secondary renderers that AVFoundation explicitly says need a flush.\n"
        "        self.ghostBaseRecoverSecondaryVideoRenderers()\n"
    )
    if not chunk.startswith(injected, body_start):
        raise RuntimeError("[V11S] Chunk V11R recovery call shape changed")
    chunk = (
        chunk[:start]
        + "    // MARK: GhostBase v1.1S SECONDARY_VIDEO_STABLE1\n"
        + "    // Build103 recovery was too aggressive: preserve the V11Q timeline\n"
        + "    // and let normal seek/reset paths flush renderers only when required.\n"
        + update_token
        + chunk[body_start + len(injected):]
    )
    sources["chunk"] = chunk

    # ------------------------------------------------------------------
    # 2. Avatar blur: the raw MediaBox resource path introduced by V11R
    #    is not a safe avatar decoder. Return to Telegram's avatar decoder,
    #    but request a larger presentation and allow synchronous cache hits.
    #    Reduce blur intensity only for static avatars. Wallpapers,
    #    placeholders and animated avatars keep their proven Build102 path.
    # ------------------------------------------------------------------
    bg = sources["bg"]
    bg = replace_region(
        bg,
        "    // MARK: GhostBase v1.1R STATIC_AVATAR_DIRECT_RESOURCE1\n",
        "    private func resourceEntrySignal(\n",
        '''    // MARK: GhostBase v1.1S STATIC_AVATAR_PIPELINE3\n    private func avatarEntrySignal(\n        peer: EnginePeer,\n        representation: TelegramMediaImageRepresentation,\n        identity: String,\n        fallback: UIColor\n    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError>? {\n        // Telegram's peerAvatarImage pipeline understands avatar resources and\n        // cache formats. Build103 bypassed it and produced grey fallback plates.\n        // Keep the native decoder, use a larger source than Build102, and allow\n        // an immediate cache hit on profile reopen.\n        guard let signal = peerAvatarImage(\n            account: self.context.account,\n            peerReference: PeerReference(peer),\n            authorOfMessage: nil,\n            representation: representation,\n            displayDimensions: CGSize(width: 720.0, height: 720.0),\n            clipStyle: .none,\n            blurred: false,\n            inset: 0.0,\n            emptyColor: nil,\n            synchronousLoad: true\n        ) else {\n            return nil\n        }\n\n        return signal\n        |> deliverOn(Queue.concurrentDefaultQueue())\n        |> map { versions -> GhostBaseProfileBackgroundCacheEntry? in\n            guard let image = versions?.0 else {\n                return nil\n            }\n\n            let tint = Self.sampledTint(\n                from: image,\n                fallback: fallback\n            )\n            Self.storePersistentTint(tint, identity: identity)\n\n            return GhostBaseProfileBackgroundCacheEntry(\n                image: image,\n                tint: tint\n            )\n        }\n    }\n\n''',
        "static avatar decoder restore",
    )

    blur_anchor = "        self.blurView.effect = UIBlurEffect(style: effectStyle)\n"
    if "GhostBase v1.1S STATIC_AVATAR_BLUR_INTENSITY1" not in bg:
        bg = replace_once(
            bg,
            blur_anchor,
            blur_anchor
            + "        // MARK: GhostBase v1.1S STATIC_AVATAR_BLUR_INTENSITY1\n"
            + "        // Reset for every source; only static avatars lower intensity.\n"
            + "        self.blurView.alpha = 1.0\n",
            "blur alpha reset",
        )

    avatar_case_anchor = '''        case let .avatar(\n            peer,\n            representation,\n            resourceId,\n            animatedSource\n        ):\n            self.usesCustomBackground = true\n'''
    avatar_case_new = '''        case let .avatar(\n            peer,\n            representation,\n            resourceId,\n            animatedSource\n        ):\n            self.usesCustomBackground = true\n\n            // Static photos were still over-blurred in Build102. Lower only\n            // this presentation layer. Animated avatars keep the proven alpha.\n            if animatedSource == nil {\n                self.blurView.alpha = reduced ? 0.38 : 0.60\n            } else {\n                self.blurView.alpha = 1.0\n            }\n'''
    bg = replace_once(bg, avatar_case_anchor, avatar_case_new, "static avatar blur intensity")

    # Marker for the whole V11S correction.
    bg = replace_once(
        bg,
        "final class GhostBaseProfileBackgroundView: UIView {\n",
        "final class GhostBaseProfileBackgroundView: UIView {\n"
        "    // MARK: GhostBase v1.1S RUNTIME_RECOVERY1\n",
        "V11S background marker",
    )
    sources["bg"] = bg

    # ------------------------------------------------------------------
    # 3. Common Groups: Build103's second UIVisualEffectView still rendered
    #    as a black sheet in this pane. The profile scene is already blurred;
    #    use a single translucent rounded backing with no extra blur and force
    #    every list backing surface transparent while GhostBase is enabled.
    # ------------------------------------------------------------------
    groups = sources["groups"]
    update_start = groups.find("        if self.ghostBaseGlassEnabled {", groups.find("func update(size:"))
    if update_start < 0:
        raise RuntimeError("[V11S] Common Groups glass branch missing")
    else_pos = groups.find("        } else {", update_start)
    if else_pos < 0:
        raise RuntimeError("[V11S] Common Groups else boundary missing")
    groups_branch = '''        if self.ghostBaseGlassEnabled {\n            let isDark = presentationData.theme.overallDarkAppearance\n\n            self.backgroundColor = .clear\n            self.view.backgroundColor = .clear\n            self.listNode.backgroundColor = .clear\n            self.listNode.view.backgroundColor = .clear\n\n            // MARK: GhostBase v1.1S COMMON_GROUPS_TRANSLUCENT1\n            // Do not stack another dark system material over the already\n            // blurred profile scene. Keep one light rounded translucent owner.\n            self.ghostBaseGlassIsDark = isDark\n            self.ghostBaseGlassEffectView.effect = nil\n            self.ghostBaseGlassEffectView.backgroundColor = .clear\n            self.ghostBaseGlassEffectView.contentView.backgroundColor = .clear\n            self.ghostBaseGlassEffectView.isHidden = false\n            self.ghostBaseGlassTintView.backgroundColor =\n                presentationData.theme.list.itemBlocksBackgroundColor\n                    .withAlphaComponent(isDark ? 0.22 : 0.32)\n\n            self.listBackgroundView.isHidden = true\n            self.listBackgroundView.alpha = 0.0\n            self.listMaskView.isHidden = true\n            self.listMaskView.alpha = 0.0\n'''
    groups = groups[:update_start] + groups_branch + groups[else_pos:]

    # Ensure OFF restores alpha as well as visibility.
    off_anchor = '''            self.listBackgroundView.isHidden = false\n            self.listMaskView.isHidden = false\n'''
    off_new = '''            self.listBackgroundView.isHidden = false\n            self.listBackgroundView.alpha = 1.0\n            self.listMaskView.isHidden = false\n            self.listMaskView.alpha = 1.0\n'''
    groups = replace_once(groups, off_anchor, off_new, "Common Groups OFF alpha restore")
    sources["groups"] = groups

    # ------------------------------------------------------------------
    # 4. Saved Music: keep the real live PeerInfo underneath, but Build103's
    #    full-strength material either erased the panel or blurred away the
    #    text behind it. Use a visibly bounded translucent sheet without a
    #    second blur pass, so the underlying profile remains readable.
    # ------------------------------------------------------------------
    controls = sources["music_controls"]
    helper_start = controls.find("    private func updateGhostBaseGlassBackground() {\n")
    helper_end = controls.find("    func updatePresentationData(_ presentationData: PresentationData) {\n", helper_start)
    if helper_start < 0 or helper_end < 0:
        raise RuntimeError("[V11S] music controls helper boundaries missing")
    helper = '''    // MARK: GhostBase v1.1S MUSIC_TRANSLUCENT_SHEET1\n    private func updateGhostBaseGlassBackground() {\n        let isDark = self.presentationData.theme.overallDarkAppearance\n        self.backgroundNode.isHidden = self.ghostBaseGlassBackgroundEnabled\n\n        if self.ghostBaseGlassBackgroundEnabled {\n            self.ghostBaseGlassIsDark = isDark\n            self.ghostBaseGlassEffectView.effect = nil\n            self.ghostBaseGlassEffectView.alpha = 1.0\n            self.ghostBaseGlassEffectView.isHidden = false\n            self.ghostBaseGlassEffectView.backgroundColor = .clear\n            self.ghostBaseGlassEffectView.contentView.backgroundColor = .clear\n            self.ghostBaseGlassEffectView.layer.borderWidth = UIScreenPixel\n            self.ghostBaseGlassEffectView.layer.borderColor = UIColor.white\n                .withAlphaComponent(isDark ? 0.12 : 0.20).cgColor\n            self.ghostBaseGlassTintView.backgroundColor =\n                self.presentationData.theme.list.itemBlocksBackgroundColor\n                    .withAlphaComponent(isDark ? 0.26 : 0.38)\n        } else {\n            self.ghostBaseGlassEffectView.isHidden = true\n            self.ghostBaseGlassEffectView.effect = nil\n            self.ghostBaseGlassEffectView.layer.borderWidth = 0.0\n            self.ghostBaseGlassEffectView.layer.borderColor = nil\n            self.ghostBaseGlassTintView.backgroundColor = .clear\n        }\n    }\n\n'''
    controls = controls[:helper_start] + helper + controls[helper_end:]
    sources["music_controls"] = controls

    controller = sources["music_controller"]
    old_header = '''        headerGlassView.effect = UIBlurEffect(\n            style: isDark\n                ? .systemUltraThinMaterialDark\n                : .systemUltraThinMaterialLight\n        )\n        headerGlassView.isHidden = false\n        headerTintView.backgroundColor = UIColor(\n            white: isDark ? 0.0 : 1.0,\n            alpha: isDark ? 0.08 : 0.11\n        )\n'''
    new_header = '''        // MARK: GhostBase v1.1S MUSIC_HEADER_TRANSLUCENT1\n        headerGlassView.effect = nil\n        headerGlassView.alpha = 1.0\n        headerGlassView.isHidden = false\n        headerGlassView.backgroundColor = .clear\n        headerGlassView.contentView.backgroundColor = .clear\n        headerGlassView.layer.borderWidth = UIScreenPixel\n        headerGlassView.layer.borderColor = UIColor.white\n            .withAlphaComponent(isDark ? 0.12 : 0.20).cgColor\n        headerTintView.backgroundColor =\n            self.presentationData.theme.list.itemBlocksBackgroundColor\n                .withAlphaComponent(isDark ? 0.22 : 0.34)\n'''
    controller = replace_once(controller, old_header, new_header, "music header translucency")

    inactive_anchor = '''            self.ghostBaseHeaderGlassView?.isHidden = true\n            self.ghostBaseHeaderGlassView?.effect = nil\n            self.ghostBaseHeaderGlassTintView?.backgroundColor = .clear\n'''
    inactive_new = '''            self.ghostBaseHeaderGlassView?.isHidden = true\n            self.ghostBaseHeaderGlassView?.effect = nil\n            self.ghostBaseHeaderGlassView?.layer.borderWidth = 0.0\n            self.ghostBaseHeaderGlassView?.layer.borderColor = nil\n            self.ghostBaseHeaderGlassTintView?.backgroundColor = .clear\n'''
    controller = replace_once(controller, inactive_anchor, inactive_new, "music header OFF restore")
    sources["music_controller"] = controller

    # Transactional write only after every transformation succeeded.
    for name, path in PATHS.items():
        path.write_text(sources[name], encoding="utf-8")

except Exception:
    for name, path in PATHS.items():
        try:
            path.write_text(backups[name], encoding="utf-8")
        except Exception:
            pass
    raise

print("[V11S] RUNTIME_RECOVERY1 materialized")
print("[V11S] video: V11Q stable fan-out restored; resume preventsCapture fix preserved")
print("[V11S] blur: Telegram avatar decoder restored at 720px + static-only lower blur")
print("[V11S] animated avatar: aggressive V11R flush loop removed")
print("[V11S] Common Groups: extra dark material removed; translucent pane backing installed")
print("[V11S] music: bounded translucent controls/header; live profile remains readable")
print("[V11S] quote / Premium / Gifts / History / RAM intentionally untouched")
