#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE_ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src")).resolve()
OFFICIAL_ROOT = Path(
    os.environ.get(
        "GHOSTBASE_OFFICIAL_ROOT",
        "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official",
    )
).resolve()

PEER_REL = Path("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources")
PEER_SOURCE = SOURCE_ROOT / PEER_REL
PEER_OFFICIAL = OFFICIAL_ROOT / PEER_REL
HEADER = PEER_SOURCE / "PeerInfoHeaderNode.swift"
PROFILE_ITEMS = PEER_SOURCE / "PeerInfoProfileItems.swift"
SCREEN = PEER_SOURCE / "PeerInfoScreen.swift"
SECTION = PEER_SOURCE / "PeerInfoScreenItemSectionContainerNode.swift"
SETTINGS = SOURCE_ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
RUNTIME = SOURCE_ROOT / "submodules/Display/Source/GhostBaseGlass.swift"


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"[V11F PROFILE HEADER BLUR VERIFY] {message}")


def require(path: Path) -> str:
    if not path.is_file():
        fail(f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def official_bytes(relative: Path) -> bytes:
    external = OFFICIAL_ROOT / relative
    if external.is_file():
        return external.read_bytes()

    try:
        return subprocess.check_output(
            [
                "git",
                "-C",
                str(SOURCE_ROOT),
                "show",
                f"HEAD:{relative.as_posix()}",
            ],
            stderr=subprocess.PIPE, 
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip()
        fail(f"official reference unavailable for {relative}: {detail}")


def require_all(text: str, values: list[str], label: str) -> None:
    missing = [value for value in values if value not in text]
    if missing:
        fail(f"{label}: missing {missing}")


def forbid_all(text: str, values: list[str], label: str) -> None:
    found = [value for value in values if value in text]
    if found:
        fail(f"{label}: forbidden markers remain: {found}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def braced_region(text: str, marker: str, label: str) -> str:
    start = text.find(marker)
    if start < 0:
        fail(f"{label}: marker not found: {marker}")
    open_brace = text.find("{", start)
    if open_brace < 0:
        fail(f"{label}: opening brace not found")
    depth = 0
    in_string = False
    escaped = False
    for index in range(open_brace, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    fail(f"{label}: closing brace not found")


for path in (HEADER, PROFILE_ITEMS, SCREEN, SECTION, SETTINGS, RUNTIME):
    if not path.is_file():
        fail(f"missing required file: {path}")

for filename, current in (
    ("PeerInfoScreen.swift", SCREEN),
    ("PeerInfoScreenItemSectionContainerNode.swift", SECTION),
):
    relative = PEER_REL / filename
    official = official_bytes(relative)
    current_bytes = current.read_bytes()
    expected_bytes = official

    if filename == "PeerInfoScreen.swift":
        official_text = official.decode("utf-8")
        enum_anchor = "enum PeerInfoSettingsSection {\n"

        if official_text.count(enum_anchor) != 1:
            fail(
                "Official PeerInfoSettingsSection enum anchor "
                f"count={official_text.count(enum_anchor)}"
            )

        expected_text = official_text.replace(
            enum_anchor,
            enum_anchor + "    case ghostbase\n",
            1,
        )
        expected_bytes = expected_text.encode("utf-8")

    if current_bytes != expected_bytes:
        fail(
            f"{filename} differs from the permitted Official 12.9.2 "
            f"materialization "
            f"(current={hashlib.sha256(current_bytes).hexdigest()}, "
            f"expected={hashlib.sha256(expected_bytes).hexdigest()})"
        )

header = require(HEADER)
profile_items = require(PROFILE_ITEMS)
settings = require(SETTINGS)
runtime = require(RUNTIME)

require_all(
    header,
    [
        "// MARK: GhostBase v1.1F PROFILEHEADERBLUR1",
        "private final class GhostBaseProfileHeaderBackgroundView: UIView",
        "private static let imageCache = NSCache<NSString, GhostBaseProfileHeaderBackgroundCacheEntry>()",
        "private let imageView: UIImageView",
        "private let blurView: UIVisualEffectView",
        "private let tintView: UIView",
        "self.imageView = UIImageView()",
        "self.blurView = UIVisualEffectView(effect: nil)",
        "self.tintView = UIView()",
        "if let settings = GhostBaseProfileBlurSettings.loadEnabled()",
        "self.ghostBaseProfileHeaderBackgroundView = GhostBaseProfileHeaderBackgroundView(context: context, settings: settings)",
        "self.ghostBaseProfileHeaderBackgroundView = nil",
        "self.backgroundBannerView.insertSubview(ghostBaseProfileHeaderBackgroundView, at: 0)",
        "guard self.currentStateKey != stateKey else",
        "presentationData.chatWallpaper != presentationData.theme.chat.defaultWallpaper",
        "case premiumProfile",
        "case avatar(EnginePeer, TelegramMediaImageRepresentation, String)",
        'let cacheKey = "avatar:\\(peer.id.toInt64()):\\(resourceId)" as NSString',
        "blurred: true",
        "synchronousLoad: false",
        "deliverOn(Queue.concurrentDefaultQueue())",
        "runOn(Queue.concurrentDefaultQueue())",
        "backgroundCoverView.alpha = self.ghostBaseProfileHeaderBackgroundView?.usesCustomBackground == true ? 0.0 : 1.0",
        "transition.updateFrame(view: ghostBaseProfileHeaderBackgroundView, frame: frame)",
    ],
    "PeerInfoHeaderNode integration",
)

for value, expected in (
    ("private let imageView: UIImageView", 1),
    ("private let blurView: UIVisualEffectView", 1),
    ("private let tintView: UIView", 1),
    ("self.imageView = UIImageView()", 1),
    ("self.blurView = UIVisualEffectView(effect: nil)", 1),
    ("self.tintView = UIView()", 1),
    ("GhostBaseProfileBlurSettings.loadEnabled()", 1),
):
    actual = header.count(value)
    if actual != expected:
        fail(f"PeerInfoHeaderNode count mismatch for {value!r}: {actual}, expected {expected}")

# The OFF branch must be a construction gate, not an alpha/effect-only branch.
gate = """        if let settings = GhostBaseProfileBlurSettings.loadEnabled() {
            self.ghostBaseProfileHeaderBackgroundView = GhostBaseProfileHeaderBackgroundView(context: context, settings: settings)
        } else {
            self.ghostBaseProfileHeaderBackgroundView = nil
        }
"""
if gate not in header:
    fail("absolute OFF construction gate is missing or changed")

# Verify source precedence by code order inside resolveSource().
priority_needles = [
    "cachedData as? CachedUserData",
    "presentationData.chatWallpaper != presentationData.theme.chat.defaultWallpaper",
    "return .premiumProfile",
    "self.settings.avatarBlurInProfile",
    "return .telegramTheme",
]
priority_positions = [header.find(value) for value in priority_needles]
if any(position < 0 for position in priority_positions) or priority_positions != sorted(priority_positions):
    fail(f"background source priority is not personal → global → Premium → avatar → theme: {priority_positions}")

# layoutSubviews is frame-only.
helper_class_start = header.find("private final class GhostBaseProfileHeaderBackgroundView: UIView")
layout_start = header.find("    override func layoutSubviews() {", helper_class_start)
layout_end = header.find("\n    func update(", layout_start)
if layout_start < 0 or layout_end < 0:
    fail("could not isolate GhostBase layoutSubviews")
layout_body = "\n".join(
    line.split("//", 1)[0] for line in header[layout_start:layout_end].splitlines()
)
forbidden_layout = [
    "UserDefaults",
    "peerAvatarImage",
    "resourceData",
    "fetchedResource",
    "sampledTint",
    "generatedWallpaperImage",
    "CIImage",
    "CIFilter",
    "UIGraphics",
    "averageColor",
    "Signal<",
]
forbid_all(layout_body, forbidden_layout, "GhostBase layout hot path")

# update()/apply() may select and schedule a source, but they must not decode,
# render, sample or create image pixels on the profile update path.
update_start = header.find("    func update(\n", helper_class_start)
apply_tint_start = header.find("    private func applyTint(", update_start)
if update_start < 0 or apply_tint_start < 0:
    fail("could not isolate GhostBase update/apply hot path")
hot_update_body = "\n".join(
    line.split("//", 1)[0] for line in header[update_start:apply_tint_start].splitlines()
)
forbid_all(
    hot_update_body,
    [
        "hasCoverColor = true",
        "generatedWallpaperImage(",
        "sampledTint(",
        "UIImage(contentsOfFile:",
        "generateImage(",
        "CGContext(",
        "CIImage",
        "CIFilter",
        "UIGraphics",
        "averageColor",
    ],
    "GhostBase update/apply hot path",
)

forbid_all(
    header,
    [
        "NotificationCenter",
        "ghostBaseGlassTintDidChange",
        "NSProcessInfoPowerStateDidChange",
        "WallpaperBackgroundNode",
        "createWallpaperBackgroundNode",
        "GhostBaseProfilePalette",
        "GhostBaseProfileBackdropNode",
        "GhostBaseColdGlassSectionView",
        "GhostBaseProfileHubItem",
        "PROFILEHUB2",
        "PROFILEHUB4",
        "PROFILEBACKDROP",
        "PROFILEGLASS1",
        "PROFILESELECTOR2",
        "PROFILEHUBNATIVE3",
        "CIImage",
        "CIFilter",
        "UIGraphicsBeginImageContext",
        "averageColor(",
    ],
    "PeerInfoHeaderNode forbidden architecture",
)

forbid_all(
    profile_items,
    [
        "GhostBaseProfileHubItem",
        "GhostBaseProfileHubTab",
        "ghostBaseProfileHub",
        "GhostBasePersonalChannelObservation",
        "GhostBasePersonalChannelHistory",
        "ghostBasePersonalChannelReport(",
        "ghostBaseGiftHistoryReport(",
        "ghostBasePresenceHistoryReport(",
        "ghostBaseHiddenGiftHistoryReport(",
        "PROFILEHUB2",
        "PROFILEHUB4",
        "PROFILEGLASS1",
        "PROFILESELECTOR2",
        "PROFILEHUBNATIVE3",
        "UIVisualEffectView",
        "UIBlurEffect",
        "JSONEncoder()",
        "JSONDecoder()",
    ],
    "PeerInfoProfileItems legacy/hot work",
)
info_items_body = braced_region(profile_items, "func infoItems(", "PeerInfoProfileItems.infoItems")
forbid_all(
    info_items_body,
    [
        "UserDefaults.standard.data(",
        "GhostBase.ProfileHub2.",
        'UserDefaults.standard.object(forKey: "GhostBase.Glass.Enabled")',
        "JSONEncoder",
        "JSONDecoder",
        "FileManager",
        "Data(contentsOf:",
        "ghostBasePersonalChannelReport",
        "ghostBaseGiftHistoryReport",
        "ghostBasePresenceHistoryReport",
        "ghostBaseHiddenGiftHistoryReport",
    ],
    "PeerInfoProfileItems.infoItems synchronous/history work",
)

require_all(
    profile_items,
    [
        "GhostBase v1.0U hide own phone profile",
        "GhostBase v1.0ZG PRIVATELINK1 cached exported invite",
        "func infoItems(",
    ],
    "PeerInfoProfileItems preserved unrelated features",
)

for legacy_name in (
    "GhostBaseProfileHubItem.swift",
    "GhostBaseProfileBackdropNode.swift",
    "GhostBaseColdGlassSectionView.swift",
):
    if (PEER_SOURCE / legacy_name).exists():
        fail(f"legacy file still exists: {PEER_SOURCE / legacy_name}")

require_all(
    runtime,
    [
        "// MARK: GhostBase v1.1F PROFILEBLURSETTINGS1",
        'public static let enabledKey = "GhostBase.Glass.Enabled"',
        'public static let avatarBlurKey = "GhostBase.ProfileBlur.Avatar"',
        'public static let tintKey = "GhostBase.ProfileBlur.Tint"',
        'public static let reducedKey = "GhostBase.ProfileBlur.Reduced"',
        "public static func loadEnabled() -> GhostBaseProfileBlurSettings?",
        "guard GhostBaseGlassStyle.isEnabled else",
        "return nil",
        "public static func lightweightFillColor(_ base: UIColor) -> UIColor",
        "public static func lightweightTintColor(_ base: UIColor) -> UIColor",
        "public static func borderColor(_ base: UIColor) -> UIColor",
        "public static func activeTintColor(fallback: UIColor) -> UIColor",
        "return fallback",
    ],
    "GhostBaseGlass runtime",
)
forbid_all(
    runtime,
    [
        "NotificationCenter",
        "addObserver",
        "post(name:",
        "GhostBaseProfilePalette",
        "UIImage",
        "CIImage",
        "CIFilter",
        "averageColor",
        "ActiveTint",
        "PeerTint",
        "setActiveTintColor",
    ],
    "GhostBaseGlass runtime forbidden work",
)

load_body = braced_region(runtime, "public static func loadEnabled()", "GhostBaseProfileBlurSettings.loadEnabled")
main_gate_position = load_body.find("guard GhostBaseGlassStyle.isEnabled else")
child_read_positions = [
    load_body.find("self.avatarBlurKey"),
    load_body.find("self.tintKey"),
    load_body.find("self.reducedKey"),
]
if main_gate_position < 0 or any(position <= main_gate_position for position in child_read_positions):
    fail("profile child settings are read before the absolute main OFF gate")

# Static API compatibility gate for all still-materialized non-profile Glass
# callers. Unknown tokens usually mean an older runtime/palette API survived.
supported_glass_api = {
    "enabledKey",
    "isEnabled",
    "usesReducedEffects",
    "setEnabled",
    "backdropOverlayAlpha",
    "coldSurfaceAlpha",
    "lightweightSurfaceAlpha",
    "borderAlpha",
    "compactCornerRadius",
    "cardCornerRadius",
    "coldFillColor",
    "lightweightFillColor",
    "lightweightTintColor",
    "borderColor",
    "activeTintColor",
}
used_glass_api: set[str] = set()
scan_roots = [
    SOURCE_ROOT / "submodules/TelegramUI",
    SOURCE_ROOT / "submodules/SettingsUI",
    SOURCE_ROOT / "submodules/Display",
]
for scan_root in scan_roots:
    if not scan_root.is_dir():
        continue
    for swift_path in scan_root.rglob("*.swift"):
        if swift_path == RUNTIME:
            continue
        try:
            swift_text = swift_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        used_glass_api.update(re.findall(r"GhostBaseGlassStyle\.([A-Za-z_][A-Za-z0-9_]*)", swift_text))
        if "GhostBaseProfilePalette" in swift_text:
            fail(f"process-global profile palette reference survives in {swift_path}")
unknown_glass_api = sorted(used_glass_api - supported_glass_api)
if unknown_glass_api:
    fail(f"unsupported/legacy GhostBaseGlassStyle API remains in materialized source: {unknown_glass_api}")

require_all(
    settings,
    [
        'static let glassEnabled = "GhostBase.Glass.Enabled"',
        'static let profileAvatarBlur = "GhostBase.ProfileBlur.Avatar"',
        'static let profileBlurTint = "GhostBase.ProfileBlur.Tint"',
        'static let profileBlurReduced = "GhostBase.ProfileBlur.Reduced"',
        '"Эффект фона профиля"',
        '"Размывать аватар в профиле"',
        '"Цветовой tint"',
        '"Облегчённое размытие"',
        "case GhostBaseKey.profileAvatarBlur:",
        "case GhostBaseKey.profileBlurTint:",
        "case GhostBaseKey.profileBlurReduced:",
        "Version: v1.1F-profile-header",
        "Base: Official Telegram 12.9.2",
    ],
    "settings controls",
)
forbid_all(
    settings,
    [
        'GhostBase.Profile.Enabled',
        'GhostBase.Profile.ShowIds',
        'GhostBase.Profile.ShowDCs',
        'GhostBase.Profile.ShowRegistration',
        "Карточка профиля",
        "Profile Metrics",
        "Enable Profile Card",
        "v1.1F-ui-rebuild",
    ],
    "settings old profile card",
)

# Parse-only syntax gate when swift-format is available. It does not need the
# iOS modules and catches malformed Swift before Bazel starts.
swift_format = shutil.which("swift-format")
if swift_format:
    for path in (HEADER, PROFILE_ITEMS, SETTINGS, RUNTIME):
        result = subprocess.run(
            [swift_format, "lint", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        errors = [line for line in result.stdout.splitlines() if " error:" in line]
        if errors:
            fail(f"Swift parse errors in {path}:\n" + "\n".join(errors[:20]))

print("[V11F VERIFY] PROFILEHEADERBLUR1 materialized source OK")
print(f"[V11F VERIFY] source={SOURCE_ROOT}")
print(f"[V11F VERIFY] official={OFFICIAL_ROOT}")
print(f"[V11F VERIFY] PeerInfoScreen sha256={sha256(SCREEN)}")
print(f"[V11F VERIFY] SectionContainer sha256={sha256(SECTION)}")
