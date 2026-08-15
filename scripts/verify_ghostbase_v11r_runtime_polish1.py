#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src")).resolve()

files = {
    "media": ROOT / "submodules/MediaPlayer/Sources/MediaPlayerNode.swift",
    "chunk": ROOT / "submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift",
    "bg": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift",
    "cover": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoCoverComponent/Sources/PeerInfoCoverComponent.swift",
    "groups": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift",
    "gift": ROOT / "submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift",
    "music_controller": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift",
    "music_controls": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControlsNode.swift",
    "report": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift",
    "quote": ROOT / "submodules/TextFormat/Sources/ChatInputContentConversion.swift",
    "settings": ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift",
    "root": ROOT / "submodules/TelegramUI/Sources/TelegramRootController.swift",
}

for name, path in files.items():
    if not path.is_file():
        raise RuntimeError(f"[V11R VERIFY] missing {name}: {path}")

s = {name: path.read_text(encoding="utf-8") for name, path in files.items()}


def require(ok: bool, label: str):
    if not ok:
        raise RuntimeError(f"[V11R VERIFY] FAIL: {label}")

# Video: exact watchdog owner removed only from the GhostBase secondary path.
add_start = s["media"].find("public func addSecondaryVideoLayer")
add_end = s["media"].find("public func removeSecondaryVideoLayer", add_start)
require(add_start >= 0 and add_end > add_start, "secondary layer method region")
secondary_region = s["media"][add_start:add_end]
require("SECONDARY_VIDEO_LIFECYCLE1" in secondary_region, "secondary lifecycle marker")
require("layer.preventsCapture = self.captureProtected" not in secondary_region, "no secondary preventsCapture assignment")
require("requiresFlushToResumeDecoding" in s["media"], "legacy secondary flush recovery")
require("SECONDARY_VIDEO_RECOVERY1" in s["chunk"], "chunk recovery marker")
require("ghostBaseRecoverSecondaryVideoRenderers" in s["chunk"], "chunk recovery function")
require("requiresFlushToResumeDecoding" in s["chunk"], "chunk requires-flush gate")

# Static blur / reopen. Wallpaper and animated code remains; only static avatar becomes direct resource.
av_start = s["bg"].find("private func avatarEntrySignal")
av_end = s["bg"].find("private func resourceEntrySignal", av_start)
require(av_start >= 0 and av_end > av_start, "avatar pipeline region")
av = s["bg"][av_start:av_end]
require("STATIC_AVATAR_DIRECT_RESOURCE1" in s["bg"], "static avatar marker")
require("representation.resource" in av, "static avatar MediaBox resource")
require("alwaysSampleTint: true" in av, "static avatar fresh tint")
require("peerAvatarImage(" not in av, "no 360x360 peerAvatarImage background")
require("BUILD97_NEUTRAL_REOPEN1" in s["bg"], "Build97 neutral reopen preserved")
require("case let .placeholder" in s["bg"], "no-avatar path preserved")
require("case let .wallpaper" in s["bg"], "personal wallpaper path preserved")

# Premium.
require("PREMIUM_PATTERN_RESTORE1" in s["cover"], "Premium marker")
require("avatarBackgroundPatternContentsLayer.opacity = 1.0" in s["cover"], "avatar Premium pattern native opacity")
require("backgroundPatternContainer.alpha = patternFraction" in s["cover"], "Premium pattern transition preserved")

# Common Groups exactly follows one pane-level material architecture; old Official surfaces remain for OFF.
require("COMMON_GROUPS_GLASS1" in s["groups"], "Common Groups marker")
require("UIVisualEffectView" in s["groups"] and "systemUltraThinMaterialDark" in s["groups"], "Common Groups pane material")
require("listBackgroundView.isHidden = true" in s["groups"], "Common Groups old background hidden ON")
require("listBackgroundView.isHidden = false" in s["groups"], "Common Groups old background restored OFF")
require("systemStyle: ghostBaseGlassEnabled ? .glass : .legacy" in s["groups"], "Common Groups rows preserve conditional style")

# Gift.
require("GIFT_READABLE_GLASS1" in s["gift"], "Gift marker")
require("? 0.56" in s["gift"] and ": 0.64" in s["gift"], "Gift readable alpha")
require("style: .glass" in s["gift"], "Gift remains glass sheet")

# Music: real profile V11P preserved, actual controls + header now own glass.
require("MUSIC_REAL_PROFILE_GLASS1" in s["music_controller"], "V11P real-profile music preserved")
require("MUSIC_HEADER_GLASS2" in s["music_controller"], "music header marker")
require("ghostBaseHeaderGlassView" in s["music_controller"], "music header surface")
require("MUSIC_CONTROLS_GLASS2" in s["music_controls"], "music controls marker")
require("ghostBaseGlassBackgroundEnabled" in s["music_controls"], "music controls conditional glass")
require("backgroundNode.isHidden = self.ghostBaseGlassBackgroundEnabled" in s["music_controls"], "opaque controls background hidden only for GhostBase saved music")

# History: persistence and physical viewport markers retained; presentation becomes cards.
require("HISTORY_CARDS1" in s["report"], "History cards marker")
require("GhostBaseProfileReportCardNode" in s["report"], "History card node")
require("renderedReportSections" in s["report"], "History section renderer")
require("HISTORY_CLIP_HARDENING1" in s["report"], "History physical clipping preserved")
require("HISTORYSTATICHEADER1" in s["report"], "History static tabs preserved")
require("afterPendingWrites" in s["report"], "History pending-write ordering preserved")
require("previous.topMessageId.map(\n                            previous.topMessageId.map(" not in s["report"], "History local duplicate map normalized")

# Quote conversion: one consecutive quote group can contain multiple paragraph blocks.
require("MULTILINE_QUOTE1" in s["quote"], "Quote marker")
require("pendingQuoteParagraphs" in s["quote"], "Quote paragraph accumulator")
require("content: ChatInputContent(blocks: pendingQuoteParagraphs)" in s["quote"], "single structured blockQuote content")
require("Each quote\n                // paragraph" not in s["quote"], "old per-paragraph quote conversion removed")

# RAM setting + global root overlay.
require("RAM_SETTING1" in s["settings"], "RAM setting marker")
require('GhostBase.Appearance.ShowRamUnderClock' in s["settings"], "RAM defaults key")
require("var showRamUnderClock: Bool" in s["settings"], "RAM settings state")
require('"Показывать RAM под часами"' in s["settings"], "RAM toggle title")
require("defaultValue: false" in s["settings"], "RAM default off")
require("RAM_OVERLAY1" in s["root"], "RAM root marker")
require("task_vm_info_data_t" in s["root"] and "info.phys_footprint" in s["root"], "RAM process phys_footprint")
require("Foundation.Timer(timeInterval: 1.0" in s["root"], "RAM one-second timer")
require("UIApplication.willResignActiveNotification" in s["root"], "RAM timer app lifecycle")
require('label.text = "RAM \\(megabytes) MB"' in s["root"], "RAM label format")

print("[V11R VERIFY] GREEN")
print("[V11R VERIFY] watchdog/freeze secondary-video recovery: GREEN")
print("[V11R VERIFY] static-avatar direct resource + fresh reopen tint: GREEN")
print("[V11R VERIFY] Premium / Common Groups / Gift / saved-music glass: GREEN")
print("[V11R VERIFY] History cards + multiline quote grouping: GREEN")
print("[V11R VERIFY] RAM-under-clock process footprint + OFF lifecycle: GREEN")
