#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

SOURCE_ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()
OFFICIAL_ROOT = Path(os.environ.get(
    "GHOSTBASE_OFFICIAL_ROOT",
    "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official",
)).resolve()
BUILDER_ROOT = Path(os.environ.get(
    "GHOSTBASE_BUILDER_ROOT",
    "/root/gb_builder",
)).resolve()

PEER = Path("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources")
PATHS = {
    "header": PEER / "PeerInfoHeaderNode.swift",
    "screen": PEER / "PeerInfoScreen.swift",
    "section": PEER / "PeerInfoScreenItemSectionContainerNode.swift",
    "profile": PEER / "PeerInfoProfileItems.swift",
    "background": PEER / "GhostBaseProfileFullscreenBackground.swift",
    "report": PEER / "GhostBaseProfileReportPaneNode.swift",
    "data": PEER / "PeerInfoData.swift",
    "container": PEER / "PeerInfoPaneContainerNode.swift",
    "pane": Path("submodules/TelegramUI/Components/PeerInfo/PeerInfoPaneNode/Sources/PeerInfoPaneNode.swift"),
    "account": Path("submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"),
    "presence": Path("submodules/TelegramCore/Sources/UpdatePeers.swift"),
    "settings": Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"),
    "glass": Path("submodules/Display/Source/GhostBaseGlass.swift"),
}


def fail(message: str) -> None:
    raise SystemExit(f"[V11G VERIFY] {message}")


def read(relative: Path) -> str:
    path = SOURCE_ROOT / relative
    if not path.is_file():
        fail(f"missing materialized file: {path}")
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_once(text: str, proof: str, label: str) -> None:
    count = text.count(proof)
    require(count == 1, f"{label}: expected one proof, found {count}: {proof!r}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


files = {name: read(relative) for name, relative in PATHS.items()}
header = files["header"]
screen = files["screen"]
section = files["section"]
profile = files["profile"]
background = files["background"]
report = files["report"]
data = files["data"]
container = files["container"]
pane = files["pane"]
account = files["account"]
presence = files["presence"]
settings = files["settings"]
glass = files["glass"]

# 1. Old UI architecture must be physically absent from final materialization.
legacy_haystack = "\n".join([header, screen, section, profile, background, report, data, container])
for forbidden in (
    "PROFILEHUB2",
    "PROFILEHUB4",
    "GhostBaseProfileHubItem",
    "GhostBaseProfileBackdrop",
    "backgroundBackdropNode",
    "История и сведения",
):
    require(forbidden not in legacy_haystack, f"legacy profile UI returned: {forbidden}")

# 2. Fullscreen background ownership and stock Premium decorations.
require_once(screen, "// MARK: GhostBase v1.1G PROFILEFULLSCREEN1", "fullscreen screen marker")
for proof in (
    "private let ghostBaseProfileBackgroundView: GhostBaseProfileBackgroundView?",
    "self.view.insertSubview(ghostBaseProfileBackgroundView, at: 0)",
    "frame: CGRect(origin: .zero, size: layout.size)",
    "if !isSettings, let settings = GhostBaseProfileGlassRuntime.loadSettings()",
    "ghostBaseRecordObservedProfileV11G(",
    "ghostBaseRecordPersonalChannelObservationV11G(",
):
    require(proof in screen, f"fullscreen/observation proof missing: {proof}")
require("backgroundBannerView.addSubview(ghostBaseProfileBackgroundView)" not in screen,
        "fullscreen view was put back inside header banner")

require_once(header, "// MARK: GhostBase v1.1G PREMIUMDECORATIONS1", "Premium decoration marker")
for proof in (
    "PeerInfoCoverComponent.View",
    "Keep PeerInfoCoverComponent alive",
    "GhostBaseProfileGlassRuntime.shouldBlendStockCover(",
):
    require(proof in header, f"stock cover preservation proof missing: {proof}")
require("backgroundCoverView.alpha = 0.0" not in header,
        "stock Premium cover is hidden again")

# Action buttons remain the Official rounded-square implementation: v1.1G adds no custom button geometry.
for forbidden in (
    "ghostBaseCircularActionButton",
    "GhostBaseRoundAction",
    "cornerRadius = buttonSize.width * 0.5",
):
    require(forbidden not in header, f"action buttons were changed to circles: {forbidden}")

# 3. Exactly one reusable image, blur and tint view; no hot-layout processing.
for proof in (
    "self.imageView = UIImageView()",
    "self.blurView = UIVisualEffectView(effect: nil)",
    "self.tintView = UIView()",
    "private static let imageCache = NSCache",
    "avatar:\\(peer.id.toInt64()):\\(resourceId)",
):
    require_once(background, proof, "background reusable surface")
for forbidden in (
    "CIContext",
    "CIFilter",
    "UIGraphicsBeginImageContext",
    "averageColor",
):
    require(forbidden not in background, f"forbidden image work returned: {forbidden}")
layout_start = background.find("override func layoutSubviews()")
layout_end = background.find("    func update(", layout_start)
require(layout_start >= 0 and layout_end > layout_start, "background layout function not found")
layout_body = background[layout_start:layout_end]
for forbidden in ("generateImage", "sampledTint", "UserDefaults.standard", "start(", "resolveSource"):
    require(forbidden not in layout_body, f"hot layout work returned: {forbidden}")

priority = [
    "// 1) personal chat wallpaper",
    "// 2) user-selected global wallpaper",
    "// 3) Premium profile color",
    "// 4) avatar-derived blurred background",
    "// 5) untouched Telegram theme",
]
positions = [background.find(value) for value in priority]
require(all(value >= 0 for value in positions), "background priority proof is incomplete")
require(positions == sorted(positions), "background priority order is wrong")
require("GhostBaseProfileBlurSettings.loadEnabled()" in background,
        "main OFF gate is not construction-time")
require("static let settings" not in background,
        "profile settings were cached process-wide")

# 4. OFF retains Official surfaces; only enabled mode makes sections translucent.
for proof in (
    "init(ghostBaseGlassEnabled: Bool = false)",
    "if self.ghostBaseGlassEnabled",
    "presentationData.theme.list.itemBlocksBackgroundColor",
):
    require(proof in section, f"section OFF/material proof missing: {proof}")
require(screen.count("PeerInfoScreenItemSectionContainerNode(ghostBaseGlassEnabled:") == 2,
        "not all section constructors use the single screen state")
for proof in (
    "// MARK: GhostBase v1.1G PANEGLASS1",
    "private let ghostBaseGlassEnabled: Bool",
    "ghostBaseGlassEnabled: Bool = false",
    "if self.ghostBaseGlassEnabled {",
    "self.backgroundColor = .clear",
):
    require(proof in container, f"fullscreen pane glass proof missing: {proof}")
require("ghostBaseGlassEnabled: self.ghostBaseProfileBackgroundView != nil" in screen,
        "pane container does not receive the construction-time OFF state")

# 5. Compact metrics are preloaded once, not read from infoItems hot path.
for proof in (
    "struct GhostBaseProfileMetricsSettings",
    "case ghostBaseMetrics",
    "label: \"Telegram ID\"",
    "label: \"DC\"",
    "label: \"Дата регистрации\"",
):
    require(proof in profile, f"profile metric proof missing: {proof}")
info_start = profile.find("func infoItems(")
info_end = profile.find("func editingItems(", info_start)
require(info_start >= 0 and info_end > info_start, "infoItems span unavailable")
info_body = profile[info_start:info_end]
for forbidden in (
    "UserDefaults.standard",
    "JSONDecoder",
    "JSONSerialization",
    "Data(contentsOf:",
    ".write(to:",
):
    require(forbidden not in info_body, f"heavy/synchronous work in infoItems: {forbidden}")
require("self.ghostBaseProfileMetricsSettings = GhostBaseProfileMetricsSettings.load()" in screen,
        "metrics settings are not loaded once per screen")

# 6. Native lazy panes and bounded history stores.
for key in (
    "case ghostBaseProfileHistory",
    "case ghostBasePresence",
    "case ghostBaseGiftHistory",
    "case ghostBasePersonalChannel",
):
    require(key in pane, f"native pane key missing: {key}")
for proof in (
    "ghostBaseAppendingProfilePanes(",
    "PeerInfoPaneKey.ghostBaseProfileHistory",
    "PeerInfoPaneKey.ghostBasePresence",
):
    require(proof in data, f"native pane policy missing: {proof}")
for proof in (
    "GhostBaseProfileReportPaneNode(",
    'text: "История"',
    'text: "Присутствие"',
    'text: "Подарки · история"',
    'text: "Канал"',
):
    require(proof in container, f"native pane container proof missing: {proof}")
for proof in (
    "if visibleHeight > 0.0",
    "self.startLoadingIfNeeded()",
    "DispatchQueue.global(qos: .utility).async",
    "ghostBaseGiftHistoryReport(",
    "GhostBase.ProfileIntel2.",
    "GhostBase.ProfileIntel3.PersonalChannel.",
    "maximumEvents = 200",
    "private static var profileHistories:",
    "private static var personalChannelHistories:",
    "history.current.hasSameContent(as: snapshot)",
    "history.current.hasSameContent(as: observation)",
):
    require(proof in report, f"lazy/bounded report proof missing: {proof}")

# 7. Performance recovery: old delete research probes and network requests are gone.
for forbidden in (
    "RAWDIFF",
    "FETCHRACE",
    "HISTORYAROUND",
    "Pre-delete Shadow Trace",
    "PVerdict",
    "PDeleteEvents",
    "startStandalone",
    "GhostBase.V10Q",
):
    require(forbidden not in account, f"runaway delete probe remains: {forbidden}")
for proof in (
    "// MARK: GhostBase v1.1G BOUNDEDDIAGNOSTICS1",
    "private static let limit = 200",
    "eventsSinceFlush >= 20",
    "// MARK: GhostBase v1.1G DELETEDMESSAGES1 bounded global gate",
    "// MARK: GhostBase v1.1G DELETEDMESSAGES1 bounded local gate",
    "// MARK: GhostBase v1.1G EDITHISTORY1 bounded save gate",
):
    require(proof in account, f"bounded message functionality proof missing: {proof}")
# The V10ZC bot-account helper intentionally performs one bounded lookup.
# Exclude only this exact helper from the general hot-path UserDefaults budget.
bot_helper_start = account.find("// MARK: GhostBase v1.0ZC Bot account helper")
bot_helper_end = account.find(
    "private func peerIdsFromDifference(",
    bot_helper_start,
)
require(
    bot_helper_start >= 0 and bot_helper_end > bot_helper_start,
    "V10ZC bot-account helper span is unavailable",
)
bot_helper_body = account[bot_helper_start:bot_helper_end]
require(
    bot_helper_body.count("UserDefaults.standard") == 1,
    "V10ZC bot-account helper must contain exactly one UserDefaults lookup",
)
account_without_bot_helper = (
    account[:bot_helper_start] + account[bot_helper_end:]
)
require(
    account_without_bot_helper.count("UserDefaults.standard") <= 4,
    "too many UserDefaults hot-path references remain in AccountStateManagementUtils",
)

for proof in (
    "// MARK: GhostBase v1.1G PRESENCEBOUNDED1",
    "label: \"GhostBase.PresenceStore.V11G\"",
    "static let maximumEvents = 500",
    "static let maximumKnownUsers = 5000",
    "private static var histories:",
    "private static var knownUsers:",
    "self.queue.async",
):
    require(proof in presence, f"bounded presence proof missing: {proof}")
require(presence.count("ghostBaseRecordPresence(") >= 2,
        "presence call sites were lost")
require(presence.count("ghostBaseRegisterKnownUser(") >= 2,
        "known-user call sites were lost")

# 8. Settings and bounded Debug/Research.
for proof in (
    'static let profileEnabled = "GhostBase.Profile.Enabled"',
    'static let showIds = "GhostBase.Profile.ShowIds"',
    'static let showDCs = "GhostBase.Profile.ShowDCs"',
    'static let showRegistration = "GhostBase.Profile.ShowRegistration"',
    "// MARK: GhostBase v1.1G BOUNDEDDEBUG1",
    "runtimeLines.suffix(80)",
    "Буфер ограничен 200 строками",
):
    require(proof in settings, f"settings recovery proof missing: {proof}")
require(settings.count("Version: v1.1G-unified-recovery") == 2,
        "visible v1.1G version labels are not exactly two")
for proof in (
    'profileAvatarBlur',
    'profileBlurTint',
    'profileBlurReduced',
):
    require(proof in glass or proof in settings, f"profile blur setting missing: {proof}")

# 9. Canonical chain, when available, must materialize and verify v1.1G last.
canonical_path = BUILDER_ROOT / "scripts/bazel_build_probe_official.sh"
if canonical_path.is_file():
    canonical = canonical_path.read_text(encoding="utf-8")
    begin = canonical.find("# MARK: GhostBase v1.1G unified recovery")
    end = canonical.find("# END MARK: GhostBase v1.1G unified recovery")
    bazel = canonical.find('"$BAZEL_BIN" build')
    require(begin >= 0 and end > begin and bazel > end,
            "v1.1G canonical block is not final before Bazel")
    require(canonical.count("apply_ghostbase_v11g_unified_recovery1.py") == 1,
            "v1.1G apply count in canonical is not one")
    require(canonical.count("verify_ghostbase_v11g_unified_recovery1.py") == 1,
            "v1.1G verifier count in canonical is not one")
    require('echo "-- verify Version: v1.1G-unified-recovery --"' in canonical,
            "final IPA version gate is not v1.1G")
    require("Final IPA does not contain Version: v1.1G-unified-recovery" in canonical,
            "v1.1G final IPA failure gate missing")
    require("final IPA missing v1.0Q+SH2+OT2 markers" not in canonical,
            "obsolete research marker gate remains")
    require("Final IPA does not contain v1.0P marker" not in canonical,
            "obsolete v1.0P gate remains")
    require("Final IPA does not contain v1.0O SourcePeer marker" not in canonical,
            "obsolete v1.0O gate remains")

print("[V11G VERIFY] UNIFIEDRECOVERY1 materialized source OK")
print(f"[V11G VERIFY] source={SOURCE_ROOT}")
print(f"[V11G VERIFY] PeerInfoScreen sha256={sha256(SOURCE_ROOT / PATHS['screen'])}")
print(f"[V11G VERIFY] AccountState sha256={sha256(SOURCE_ROOT / PATHS['account'])}")
