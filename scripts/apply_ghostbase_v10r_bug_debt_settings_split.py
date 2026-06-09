#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import json
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

BASE = ROOT / "scripts/apply_ghostbase_v10q_sh2_ot2_combined.py"
ASSET_SRC = ROOT / "scripts/assets/ghostbase_settings_icons"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def die(msg):
    raise SystemExit("[v1.0R SettingsSplit] ERROR: " + msg)

def ensure(s, needle, label):
    if needle not in s:
        die(f"missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    die(f"pattern not found: {label}")

print("[v1.0R SettingsSplit] running base v1.0Q+SH2+OT2...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

if not SRC.exists():
    die(f"missing source dir: {SRC}")

if not ASSET_SRC.exists():
    die(f"missing icon asset source: {ASSET_SRC}")

settings_items_p = SRC / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoSettingsItems.swift"
settings_actions_p = SRC / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift"
settings_controller_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
resources_p = SRC / "submodules/TelegramPresentationData/Sources/Resources/PresentationResourcesSettings.swift"
xcassets_p = SRC / "Swiftgram/SGSettingsUI/Images.xcassets"

standalone_p = SRC / "submodules/TelegramCore/Sources/PendingMessages/StandaloneSendMessage.swift"
forward_p = SRC / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
history_entries_p = SRC / "submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift"
managed_autoremove_p = SRC / "submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift"
consume_p = SRC / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift"

for p in [
    settings_items_p,
    settings_actions_p,
    settings_controller_p,
    resources_p,
    standalone_p,
    forward_p,
    history_entries_p,
    managed_autoremove_p,
    consume_p,
]:
    if not p.exists():
        die(f"missing file: {p}")

icons = {
    "GhostBaseHome": "ghostbase_home",
    "GhostBaseGhostMode": "ghost_mode",
    "GhostBaseMessages": "messages",
    "GhostBaseProtectedContent": "protected_content",
    "GhostBaseMediaStories": "media_stories",
    "GhostBaseAppearance": "appearance",
    "GhostBaseDebugResearch": "debug_research",
    "GhostBaseAbout": "about",
}

for asset_name, file_base in icons.items():
    imageset = xcassets_p / f"{asset_name}.imageset"
    imageset.mkdir(parents=True, exist_ok=True)

    for suffix in ["", "@2x", "@3x"]:
        src = ASSET_SRC / f"{file_base}{suffix}.png"
        if not src.exists():
            die(f"missing prepared icon: {src}")
        shutil.copy2(src, imageset / src.name)

    contents = {
        "images": [
            {
                "idiom": "universal",
                "filename": f"{file_base}.png",
                "scale": "1x"
            },
            {
                "idiom": "universal",
                "filename": f"{file_base}@2x.png",
                "scale": "2x"
            },
            {
                "idiom": "universal",
                "filename": f"{file_base}@3x.png",
                "scale": "3x"
            }
        ],
        "info": {
            "author": "xcode",
            "version": 1
        }
    }

    (imageset / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")

print("[v1.0R SettingsSplit] assets copied")

resources = read(resources_p)

insert_resources = '''    public static let ghostBaseHome = renderSettingsIcon(name: "GhostBaseHome")
    public static let ghostBaseGhostMode = renderSettingsIcon(name: "GhostBaseGhostMode")
    public static let ghostBaseMessages = renderSettingsIcon(name: "GhostBaseMessages")
    public static let ghostBaseProtectedContent = renderSettingsIcon(name: "GhostBaseProtectedContent")
    public static let ghostBaseMediaStories = renderSettingsIcon(name: "GhostBaseMediaStories")
    public static let ghostBaseAppearance = renderSettingsIcon(name: "GhostBaseAppearance")
    public static let ghostBaseDebugResearch = renderSettingsIcon(name: "GhostBaseDebugResearch")
    public static let ghostBaseAbout = renderSettingsIcon(name: "GhostBaseAbout")
'''

if "ghostBaseHome" not in resources:
    resources = replace_once(
        resources,
        '    public static let swiftgramPro = renderSettingsIcon(name: "SwiftgramPro", scaleFactor: 30.0 / 256.0)\n',
        '    public static let swiftgramPro = renderSettingsIcon(name: "SwiftgramPro", scaleFactor: 30.0 / 256.0)\n' + insert_resources,
        "insert GhostBase PresentationResourcesSettings icons"
    )

write(resources_p, resources)

items = read(settings_items_p)

old_root = '''    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 0, text: "GhostBase", icon: PresentationResourcesSettings.security, action: {
        interaction.openSettings(.ghostbase)
    }))
'''

new_root = '''    // MARK: GhostBase v1.0R Settings Split
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 0, text: "GhostBase", icon: PresentationResourcesSettings.ghostBaseHome, action: {
        UserDefaults.standard.set("home", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 1, text: "Ghost Mode", icon: PresentationResourcesSettings.ghostBaseGhostMode, action: {
        UserDefaults.standard.set("ghost_mode", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 2, text: "Messages", icon: PresentationResourcesSettings.ghostBaseMessages, action: {
        UserDefaults.standard.set("messages", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 3, text: "Protected Content", icon: PresentationResourcesSettings.ghostBaseProtectedContent, action: {
        UserDefaults.standard.set("protected_content", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 4, text: "Media & Stories", icon: PresentationResourcesSettings.ghostBaseMediaStories, action: {
        UserDefaults.standard.set("media_stories", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 5, text: "Appearance", icon: PresentationResourcesSettings.ghostBaseAppearance, action: {
        UserDefaults.standard.set("appearance", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 6, text: "Debug / Research", icon: PresentationResourcesSettings.ghostBaseDebugResearch, action: {
        UserDefaults.standard.set("debug_research", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 7, text: "About", icon: PresentationResourcesSettings.ghostBaseAbout, action: {
        UserDefaults.standard.set("about", forKey: "GhostBase.Settings.InitialPage")
        interaction.openSettings(.ghostbase)
    }))
'''

items = replace_once(items, old_root, new_root, "replace single GhostBase root row with split block")
write(settings_items_p, items)

print("[v1.0R SettingsSplit] root Settings block patched")

settings = read(settings_controller_p)

settings = replace_once(
    settings,
    "private enum GhostBaseSettingsSection: Int32 {\n    case profileMetrics\n    case ghostMode\n    case protectedContent\n    case stars\n    case debug\n    case footer\n}\n",
    "private enum GhostBaseSettingsSection: Int32 {\n    case profileMetrics\n    case ghostMode\n    case protectedContent\n    case stars\n    case debug\n    case footer\n}\n\nprivate func ghostBaseSettingsTitle(_ page: String) -> String {\n    switch page {\n    case \"ghost_mode\":\n        return \"Ghost Mode\"\n    case \"messages\":\n        return \"Messages\"\n    case \"protected_content\":\n        return \"Protected Content\"\n    case \"media_stories\":\n        return \"Media & Stories\"\n    case \"appearance\":\n        return \"Appearance\"\n    case \"debug_research\":\n        return \"Debug / Research\"\n    case \"about\":\n        return \"About\"\n    default:\n        return \"GhostBase\"\n    }\n}\n",
    "insert GhostBase title helper"
)

split_helper = r'''
private func ghostBaseSettingsSplitEntries(page: String, state: GhostBaseSettingsState, context: AccountContext, profile: Int32, ghost: Int32, protected protectedSection: Int32, stars: Int32, debug: Int32, footer: Int32) -> [GhostBaseSettingsEntry]? {
    var entries: [GhostBaseSettingsEntry] = []

    switch page {
    case "home":
        entries.append(.header(profile, "GhostBase"))
        entries.append(.info(profile, """
Version: v1.0R Bug Debt Cleanup + Settings Split

Public lane:
Settings split enabled.
Failed SH/OT hooks disabled.

D lane:
Raw delete id research state kept in Debug / Research.
"""))
        entries.append(.header(footer, "Status"))
        entries.append(.info(footer, "This screen is the public control center. Detailed counters are moved to Debug / Research."))
        return entries

    case "ghost_mode":
        entries.append(.header(ghost, "Ghost Mode"))
        entries.append(.toggle(ghost, 1, GhostBaseKey.readMessages, "Read Ghost", state.readMessages))
        entries.append(.toggle(ghost, 2, GhostBaseKey.typingActions, "Hide Typing", state.typingActions))
        entries.append(.toggle(ghost, 3, GhostBaseKey.recordingActions, "Hide Recording", state.recordingActions))
        entries.append(.toggle(ghost, 4, GhostBaseKey.uploadingActions, "Hide Uploading", state.uploadingActions))
        entries.append(.toggle(ghost, 5, GhostBaseKey.stickerActivity, "Hide Sticker Activity", state.stickerActivity))
        entries.append(.toggle(ghost, 6, GhostBaseKey.gameActivity, "Hide Game Activity", state.gameActivity))
        entries.append(.toggle(ghost, 7, GhostBaseKey.emojiActivity, "Hide Emoji Activity", state.emojiActivity))
        entries.append(.toggle(ghost, 8, GhostBaseKey.presence, "Hide Online", state.presence))
        entries.append(.toggle(ghost, 9, GhostBaseKey.scheduledSend, "Scheduled Send", state.scheduledSend))
        return entries

    case "messages":
        entries.append(.header(ghost, "Messages"))
        entries.append(.toggle(ghost, 1, GhostBaseKey.readMessages, "Read Ghost", state.readMessages))
        entries.append(.toggle(ghost, 2, GhostBaseKey.scheduledSend, "Scheduled Send", state.scheduledSend))
        entries.append(.info(ghost, """
Deleted Messages: enabled by core patch.
Edit History: enabled by local history storage.
History viewer: available from message context menu.
"""))
        return entries

    case "protected_content":
        entries.append(.header(protectedSection, "Protected Content"))
        entries.append(.toggle(protectedSection, 1, GhostBaseKey.protectedEnabled, "Enable Protected Content Bypass", state.protectedEnabled))
        entries.append(.toggle(protectedSection, 2, GhostBaseKey.protectedGalleryShare, "Gallery Share", state.protectedGalleryShare))
        entries.append(.toggle(protectedSection, 3, GhostBaseKey.protectedGallerySave, "Gallery Save", state.protectedGallerySave))
        entries.append(.toggle(protectedSection, 4, GhostBaseKey.protectedGalleryCopy, "Gallery Copy", state.protectedGalleryCopy))
        entries.append(.toggle(protectedSection, 5, GhostBaseKey.chatSave, "Chat Save", state.chatSave))
        entries.append(.toggle(protectedSection, 6, GhostBaseKey.chatCopy, "Chat Copy", state.chatCopy))
        entries.append(.toggle(protectedSection, 7, GhostBaseKey.chatForward, "Chat Forward", state.chatForward))
        entries.append(.toggle(protectedSection, 8, GhostBaseKey.allowScreenshots, "Allow Screenshots", state.allowScreenshots))
        entries.append(.toggle(protectedSection, 9, GhostBaseKey.allowScreenRecording, "Allow Screen Recording", state.allowScreenRecording))
        return entries

    case "media_stories":
        entries.append(.header(protectedSection, "Media & Stories"))
        entries.append(.toggle(protectedSection, 1, GhostBaseKey.oneTimeScreenshots, "Allow One-Time Screenshots", state.oneTimeScreenshots))
        entries.append(.toggle(protectedSection, 2, GhostBaseKey.oneTimeScreenRecording, "Allow One-Time Screen Recording", state.oneTimeScreenRecording))
        entries.append(.toggle(protectedSection, 3, GhostBaseKey.oneTimeSave, "Allow One-Time Save", state.oneTimeSave))
        entries.append(.toggle(protectedSection, 4, GhostBaseKey.storySave, "Story Save", state.storySave))
        entries.append(.info(protectedSection, "Failed outgoing timer/QuickShare experiments are disabled in v1.0R and are not shown as public features."))
        return entries

    case "appearance":
        entries.append(.header(profile, "Profile Card"))
        entries.append(.toggle(profile, 1, GhostBaseKey.profileEnabled, "Enable Profile Card", state.profileEnabled))
        entries.append(.toggle(profile, 2, GhostBaseKey.showIds, "Show IDs", state.showIds))
        entries.append(.toggle(profile, 3, GhostBaseKey.showDCs, "Show DCs", state.showDCs))
        entries.append(.toggle(profile, 4, GhostBaseKey.showRegistration, "Show Registration Date", state.showRegistration))

        entries.append(.header(stars, "Stars"))
        entries.append(.toggle(stars, 1, GhostBaseKey.localStarsEnabled, "Enable Local Stars Balance", state.localStarsEnabled))
        let ghostBaseStarsDisplay = state.localStarsAmount.isEmpty ? "0" : state.localStarsAmount
        entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Local Stars Balance", state.localStarsAmount))
        entries.append(.info(stars, "Current visual balance: \(ghostBaseStarsDisplay) ⭐"))
        return entries

    case "debug_research":
        let ghostBaseRawPrefixV10F = "GhostBase.V10F.Raw."
        let ghostBaseRawDefaultsV10F = UserDefaults.standard

        entries.append(.header(debug, "Debug / Research"))
        entries.append(.info(debug, """
v1.0R Bug Debt Cleanup:
PublicLane: failed SH/OT hooks disabled
DLane: raw delete id kept, local mapping still zero
NextD: raw id + persisted peer

v1.0Q Raw Delete Mapping:
QRawDeleteEvents: \(UserDefaults.standard.integer(forKey: "GhostBase.V10Q.RawDeleteEvents"))
QLastRawDeleteSource: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.LastRawDeleteSource") ?? "none")
QLastRawDeleteIdCount: \(UserDefaults.standard.integer(forKey: "GhostBase.V10Q.LastRawDeleteIdCount"))
QLastMappedDeleteIdCount: \(UserDefaults.standard.integer(forKey: "GhostBase.V10Q.LastMappedDeleteIdCount"))
QLastRawDeleteIds: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.LastRawDeleteIds") ?? "none")
QLastMappedDeleteIds: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.LastMappedDeleteIds") ?? "none")
QVerdict: \(UserDefaults.standard.string(forKey: "GhostBase.V10Q.Verdict") ?? "none")

v1.0P Pre-delete Shadow Trace:
PDeleteEvents: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.DeleteEvents"))
PLastDeleteSource: \(UserDefaults.standard.string(forKey: "GhostBase.V10P.LastDeleteSource") ?? "none")
PLastDeleteIdCount: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.LastDeleteIdCount"))
PPreDeleteMessageHits: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.PreDeleteMessageHits"))
PPreDeleteTextHits: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.PreDeleteTextHits"))
PVerdict: \(UserDefaults.standard.string(forKey: "GhostBase.V10P.Verdict") ?? "none")

v1.0O Persistent SourcePeer:
OSourcePeerPersistedRaw: \(UserDefaults.standard.object(forKey: "GhostBase.V10O.Persistent.SourcePeerIdRaw") as? Int64 ?? 0)
OSourcePeerCandidateStatus: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "OSourcePeerCandidateStatus") ?? "none")
OSourcePeerUsedRaw: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "OSourcePeerUsedRaw") ?? "none")

Disabled / hidden from public:
SH QuickShare Scheduled: disabled
OT outgoing timer keep: disabled
OT2 visual keep: disabled
"""))
        return entries

    case "about":
        let telegramId = String(context.account.peerId.id._internalGetInt64Value())
        let bundleId = Bundle.main.bundleIdentifier ?? "unknown"

        entries.append(.header(profile, "About GhostBase"))
        entries.append(.info(profile, """
GhostBase
Version: v1.0R Bug Debt Cleanup + Settings Split
Base: Official Telegram 12.7
Bundle ID: \(bundleId)
Telegram ID: \(telegramId)
KeychainFix: sideloadKeychainFix.dylib
AppGroup: group.4a348a9b186b700c.1
"""))
        entries.append(.header(footer, "Transparency"))
        entries.append(.info(footer, "Public settings show stable user-facing features. Research counters live only in Debug / Research."))
        return entries

    default:
        return nil
    }
}

'''

if "ghostBaseSettingsSplitEntries(page:" not in settings:
    settings = settings.replace(
        "private func ghostBaseSettingsEntries(state: GhostBaseSettingsState, context: AccountContext) -> [GhostBaseSettingsEntry] {\n",
        split_helper + "\nprivate func ghostBaseSettingsEntries(state: GhostBaseSettingsState, context: AccountContext, page: String) -> [GhostBaseSettingsEntry] {\n",
        1
    )
else:
    settings = settings.replace(
        "private func ghostBaseSettingsEntries(state: GhostBaseSettingsState, context: AccountContext) -> [GhostBaseSettingsEntry] {\n",
        "private func ghostBaseSettingsEntries(state: GhostBaseSettingsState, context: AccountContext, page: String) -> [GhostBaseSettingsEntry] {\n",
        1
    )

insert_after_sections = '''    let profile = GhostBaseSettingsSection.profileMetrics.rawValue
    let ghost = GhostBaseSettingsSection.ghostMode.rawValue
    let protected = GhostBaseSettingsSection.protectedContent.rawValue
    let stars = GhostBaseSettingsSection.stars.rawValue
    let debug = GhostBaseSettingsSection.debug.rawValue
    let footer = GhostBaseSettingsSection.footer.rawValue

'''

if "ghostBaseSettingsSplitEntries(page: page" not in settings:
    settings = replace_once(
        settings,
        insert_after_sections,
        insert_after_sections + '''    if let splitEntries = ghostBaseSettingsSplitEntries(page: page, state: state, context: context, profile: profile, ghost: ghost, protected: protected, stars: stars, debug: debug, footer: footer) {
        return splitEntries
    }

''',
        "insert page split early return"
    )

if 'let page = UserDefaults.standard.string(forKey: "GhostBase.Settings.InitialPage") ?? "home"' not in settings:
    settings = replace_once(
        settings,
        "public func ghostBaseSettingsController(context: AccountContext) -> ViewController {\n    let initialState = GhostBaseSettingsState.load()\n",
        "public func ghostBaseSettingsController(context: AccountContext) -> ViewController {\n    let page = UserDefaults.standard.string(forKey: \"GhostBase.Settings.InitialPage\") ?? \"home\"\n    UserDefaults.standard.removeObject(forKey: \"GhostBase.Settings.InitialPage\")\n\n    let initialState = GhostBaseSettingsState.load()\n",
        "read initial page in controller"
    )

settings = settings.replace('title: .text("GhostBase")', 'title: .text(ghostBaseSettingsTitle(page))')
settings = settings.replace(
    "entries: ghostBaseSettingsEntries(state: state, context: context),",
    "entries: ghostBaseSettingsEntries(state: state, context: context, page: page),"
)

settings = settings.replace("Version: v1.0R Bug Debt Cleanup + Settings Split", "Version: v1.0R Bug Debt Cleanup + Settings Split")
settings = settings.replace("Version: v1.0R Bug Debt Cleanup", "Version: v1.0R Bug Debt Cleanup + Settings Split")

write(settings_controller_p, settings)

print("[v1.0R SettingsSplit] GhostBase controller split patched")

standalone = read(standalone_p)
if "GhostBase v1.0R: SH2 disabled" not in standalone:
    standalone = standalone.replace(
        '''private func ghostBaseSH2ApplyStandaloneSchedule(peerId: PeerId, attributes: inout [MessageAttribute]) {
    let d = UserDefaults.standard''',
        '''private func ghostBaseSH2ApplyStandaloneSchedule(peerId: PeerId, attributes: inout [MessageAttribute]) {
    // GhostBase v1.0R: SH2 disabled, failed runtime path.
    return
    let d = UserDefaults.standard'''
    )
write(standalone_p, standalone)

forward = read(forward_p)
forward = forward.replace(
    "if ghostBaseSH1ScheduledSendEnabled && !shouldDivert {",
    "if false && ghostBaseSH1ScheduledSendEnabled && !shouldDivert {"
)
write(forward_p, forward)

history_entries = read(history_entries_p)
history_entries = history_entries.replace(
    "let ghostBaseOT2KeepViewOnceVisible = (((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.Enabled\") as? Bool) ?? true)",
    "let ghostBaseOT2KeepViewOnceVisible = false && (((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.Enabled\") as? Bool) ?? true)"
)
write(history_entries_p, history_entries)

managed_autoremove = read(managed_autoremove_p)
managed_autoremove = managed_autoremove.replace(
    "let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.Enabled\") as? Bool) ?? true)",
    "let ghostBaseOT1KeepOutgoingTimerLocal = false && (((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.Enabled\") as? Bool) ?? true)"
)
write(managed_autoremove_p, managed_autoremove)

consume = read(consume_p)
consume = consume.replace(
    "let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.Enabled\") as? Bool) ?? true)",
    "let ghostBaseOT1KeepOutgoingTimerLocal = false && (((UserDefaults.standard.object(forKey: \"GhostBase.ProtectedContent.Enabled\") as? Bool) ?? true)"
)
write(consume_p, consume)

print("[v1.0R SettingsSplit] failed SH/OT hooks disabled")

settings = read(settings_controller_p)
items = read(settings_items_p)
resources = read(resources_p)
standalone = read(standalone_p)
forward = read(forward_p)
history_entries = read(history_entries_p)
managed_autoremove = read(managed_autoremove_p)
consume = read(consume_p)

for asset_name in icons:
    imageset = xcassets_p / f"{asset_name}.imageset"
    if not imageset.exists():
        die(f"missing imageset: {imageset}")
    if not (imageset / "Contents.json").exists():
        die(f"missing Contents.json: {imageset}")

for name in [
    "ghostBaseHome",
    "ghostBaseGhostMode",
    "ghostBaseMessages",
    "ghostBaseProtectedContent",
    "ghostBaseMediaStories",
    "ghostBaseAppearance",
    "ghostBaseDebugResearch",
    "ghostBaseAbout",
]:
    ensure(resources, name, f"resource {name}")

for row in [
    'text: "GhostBase", icon: PresentationResourcesSettings.ghostBaseHome',
    'text: "Ghost Mode", icon: PresentationResourcesSettings.ghostBaseGhostMode',
    'text: "Messages", icon: PresentationResourcesSettings.ghostBaseMessages',
    'text: "Protected Content", icon: PresentationResourcesSettings.ghostBaseProtectedContent',
    'text: "Media & Stories", icon: PresentationResourcesSettings.ghostBaseMediaStories',
    'text: "Appearance", icon: PresentationResourcesSettings.ghostBaseAppearance',
    'text: "Debug / Research", icon: PresentationResourcesSettings.ghostBaseDebugResearch',
    'text: "About", icon: PresentationResourcesSettings.ghostBaseAbout',
]:
    ensure(items, row, f"root row {row}")

if 'text: "GhostBase", icon: PresentationResourcesSettings.security' in items:
    die("old single GhostBase security row still exists")

ensure(settings, 'GhostBase.Settings.InitialPage', "initial page key")
ensure(settings, "ghostBaseSettingsSplitEntries(page:", "split entries helper")
ensure(settings, "Version: v1.0R Bug Debt Cleanup + Settings Split", "v1.0R Settings Split version")
ensure(settings, "Disabled / hidden from public:", "debug disabled note")

ensure(standalone, "GhostBase v1.0R: SH2 disabled", "SH2 disabled marker")
ensure(forward, "if false && ghostBaseSH1ScheduledSendEnabled && !shouldDivert", "SH1 disabled")
ensure(history_entries, "let ghostBaseOT2KeepViewOnceVisible = false &&", "OT2 disabled")
ensure(managed_autoremove, "let ghostBaseOT1KeepOutgoingTimerLocal = false &&", "OT1 managed disabled")
ensure(consume, "let ghostBaseOT1KeepOutgoingTimerLocal = false &&", "OT1 consume disabled")

print("[v1.0R SettingsSplit] patch OK")
