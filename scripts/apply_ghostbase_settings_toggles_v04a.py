from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_peer_metrics_v03c.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/SettingsUI/Sources").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
profile_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"

if not controller_p.exists():
    raise SystemExit(f"missing file: {controller_p}")
if not profile_p.exists():
    raise SystemExit(f"missing file: {profile_p}")

parts = []
parts.append(r'''import Foundation
import UIKit
import Display
import SwiftSignalKit
import TelegramCore
import TelegramPresentationData
import ItemListUI
import AccountContext

private enum GhostBaseKey {
    static let profileEnabled = "GhostBase.Profile.Enabled"
    static let showIds = "GhostBase.Profile.ShowIds"
    static let showDCs = "GhostBase.Profile.ShowDCs"
    static let showRegistration = "GhostBase.Profile.ShowRegistration"

    static let readMessages = "GhostBase.GhostMode.ReadMessages"
    static let typingActions = "GhostBase.GhostMode.TypingActions"
    static let presence = "GhostBase.GhostMode.Presence"
    static let scheduledSend = "GhostBase.GhostMode.ScheduledSend"
}

private func ghostBaseBool(_ key: String, defaultValue: Bool) -> Bool {
    if let value = UserDefaults.standard.object(forKey: key) as? Bool {
        return value
    }
    return defaultValue
}

private struct GhostBaseSettingsState: Equatable {
    var profileEnabled: Bool
    var showIds: Bool
    var showDCs: Bool
    var showRegistration: Bool

    var readMessages: Bool
    var typingActions: Bool
    var presence: Bool
    var scheduledSend: Bool

    static func load() -> GhostBaseSettingsState {
        return GhostBaseSettingsState(
            profileEnabled: ghostBaseBool(GhostBaseKey.profileEnabled, defaultValue: true),
            showIds: ghostBaseBool(GhostBaseKey.showIds, defaultValue: true),
            showDCs: ghostBaseBool(GhostBaseKey.showDCs, defaultValue: true),
            showRegistration: ghostBaseBool(GhostBaseKey.showRegistration, defaultValue: true),
            readMessages: ghostBaseBool(GhostBaseKey.readMessages, defaultValue: false),
            typingActions: ghostBaseBool(GhostBaseKey.typingActions, defaultValue: false),
            presence: ghostBaseBool(GhostBaseKey.presence, defaultValue: false),
            scheduledSend: ghostBaseBool(GhostBaseKey.scheduledSend, defaultValue: false)
        )
    }

    func save() {
        UserDefaults.standard.set(self.profileEnabled, forKey: GhostBaseKey.profileEnabled)
        UserDefaults.standard.set(self.showIds, forKey: GhostBaseKey.showIds)
        UserDefaults.standard.set(self.showDCs, forKey: GhostBaseKey.showDCs)
        UserDefaults.standard.set(self.showRegistration, forKey: GhostBaseKey.showRegistration)

        UserDefaults.standard.set(self.readMessages, forKey: GhostBaseKey.readMessages)
        UserDefaults.standard.set(self.typingActions, forKey: GhostBaseKey.typingActions)
        UserDefaults.standard.set(self.presence, forKey: GhostBaseKey.presence)
        UserDefaults.standard.set(self.scheduledSend, forKey: GhostBaseKey.scheduledSend)
    }
}

''')
parts.append(r'''private final class GhostBaseSettingsArguments {
    let updateBool: (String, Bool) -> Void

    init(updateBool: @escaping (String, Bool) -> Void) {
        self.updateBool = updateBool
    }
}

private enum GhostBaseSettingsSection: Int32 {
    case profileMetrics
    case ghostMode
    case debug
    case footer
}

private enum GhostBaseSettingsEntry: ItemListNodeEntry {
    case header(Int32, String)
    case toggle(Int32, Int32, String, String, Bool)
    case info(Int32, String)

    var section: ItemListSectionId {
        switch self {
        case let .header(section, _):
            return section
        case let .toggle(section, _, _, _, _):
            return section
        case let .info(section, _):
            return section
        }
    }

    var stableId: Int32 {
        switch self {
        case let .header(section, _):
            return section * 1000
        case let .toggle(section, index, _, _, _):
            return section * 1000 + index
        case let .info(section, _):
            return section * 1000 + 999
        }
    }

    static func ==(lhs: GhostBaseSettingsEntry, rhs: GhostBaseSettingsEntry) -> Bool {
        switch lhs {
        case let .header(ls, lt):
            if case let .header(rs, rt) = rhs {
                return ls == rs && lt == rt
            }
            return false
        case let .toggle(ls, li, lk, lt, lv):
            if case let .toggle(rs, ri, rk, rt, rv) = rhs {
                return ls == rs && li == ri && lk == rk && lt == rt && lv == rv
            }
            return false
        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {
                return ls == rs && lt == rt
            }
            return false
        }
    }

    static func <(lhs: GhostBaseSettingsEntry, rhs: GhostBaseSettingsEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! GhostBaseSettingsArguments

        switch self {
        case let .header(_, text):
            return ItemListSectionHeaderItem(presentationData: presentationData, text: text, sectionId: self.section)

        case let .toggle(_, _, key, title, value):
            return ItemListSwitchItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                value: value,
                sectionId: self.section,
                style: .blocks,
                updated: { updatedValue in
                    arguments.updateBool(key, updatedValue)
                }
            )

        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }
    }
}

''')
parts.append(r'''private func ghostBaseSettingsEntries(state: GhostBaseSettingsState, context: AccountContext) -> [GhostBaseSettingsEntry] {
    var entries: [GhostBaseSettingsEntry] = []

    let profile = GhostBaseSettingsSection.profileMetrics.rawValue
    let ghost = GhostBaseSettingsSection.ghostMode.rawValue
    let debug = GhostBaseSettingsSection.debug.rawValue
    let footer = GhostBaseSettingsSection.footer.rawValue

    entries.append(.header(profile, "Profile Metrics"))
    entries.append(.toggle(profile, 1, GhostBaseKey.profileEnabled, "Enable Profile Card", state.profileEnabled))
    entries.append(.toggle(profile, 2, GhostBaseKey.showIds, "Show IDs", state.showIds))
    entries.append(.toggle(profile, 3, GhostBaseKey.showDCs, "Show DCs", state.showDCs))
    entries.append(.toggle(profile, 4, GhostBaseKey.showRegistration, "Show Registration Date", state.showRegistration))

    entries.append(.header(ghost, "Ghost Mode"))
    entries.append(.toggle(ghost, 1, GhostBaseKey.readMessages, "Read Messages", state.readMessages))
    entries.append(.toggle(ghost, 2, GhostBaseKey.typingActions, "Typing Actions", state.typingActions))
    entries.append(.toggle(ghost, 3, GhostBaseKey.presence, "Presence", state.presence))
    entries.append(.toggle(ghost, 4, GhostBaseKey.scheduledSend, "Scheduled Send", state.scheduledSend))

    let telegramId = String(context.account.peerId.id._internalGetInt64Value())
    let bundleId = Bundle.main.bundleIdentifier ?? "unknown"

    entries.append(.header(debug, "Debug"))
    entries.append(.info(debug, """
Telegram ID: \(telegramId)
Bundle ID: \(bundleId)
AppGroup: group.4a348a9b186b700c.1
Base: Official Telegram 12.7
KeychainFix: sideloadKeychainFix.dylib
Version: v0.4A
"""))

    entries.append(.info(footer, "Profile Metrics affects the profile card after reopening a profile. Ghost Mode toggles are saved for upcoming runtime modules."))

    return entries
}

''')
parts.append(r'''public func ghostBaseSettingsController(context: AccountContext) -> ViewController {
    let initialState = GhostBaseSettingsState.load()
    let statePromise = ValuePromise(initialState, ignoreRepeated: true)
    let stateValue = Atomic(value: initialState)

    let updateState: ((GhostBaseSettingsState) -> GhostBaseSettingsState) -> Void = { f in
        let updated = stateValue.modify { current in
            var next = f(current)

            if !next.showIds && !next.showDCs && !next.showRegistration {
                next.profileEnabled = false
            } else if next.showIds || next.showDCs || next.showRegistration {
                if !current.showIds && !current.showDCs && !current.showRegistration {
                    next.profileEnabled = true
                }
            }

            next.save()
            return next
        }

        statePromise.set(updated)
    }

    let arguments = GhostBaseSettingsArguments(updateBool: { key, value in
        updateState { state in
            var updated = state

            switch key {
            case GhostBaseKey.profileEnabled:
                updated.profileEnabled = value
                if value && !updated.showIds && !updated.showDCs && !updated.showRegistration {
                    updated.showIds = true
                    updated.showDCs = true
                    updated.showRegistration = true
                }

            case GhostBaseKey.showIds:
                updated.showIds = value
                if value {
                    updated.profileEnabled = true
                }

            case GhostBaseKey.showDCs:
                updated.showDCs = value
                if value {
                    updated.profileEnabled = true
                }

            case GhostBaseKey.showRegistration:
                updated.showRegistration = value
                if value {
                    updated.profileEnabled = true
                }

            case GhostBaseKey.readMessages:
                updated.readMessages = value

            case GhostBaseKey.typingActions:
                updated.typingActions = value

            case GhostBaseKey.presence:
                updated.presence = value

            case GhostBaseKey.scheduledSend:
                updated.scheduledSend = value

            default:
                break
            }

            return updated
        }
    })

    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text("GhostBase"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
        )

        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: ghostBaseSettingsEntries(state: state, context: context),
            style: .blocks,
            animateChanges: false
        )

        return (controllerState, (listState, arguments))
    }

    return ItemListController(context: context, state: signal)
}
''')

controller_p.write_text("".join(parts))
print("patched", controller_p)

controller = controller_p.read_text()

checks = [
    ("controller v0.4A", "Version: v0.4A" in controller),
    ("profile metrics", "Profile Metrics" in controller),
    ("main switch", "Enable Profile Card" in controller),
    ("main key", "GhostBase.Profile.Enabled" in controller),
    ("show ids key", "GhostBase.Profile.ShowIds" in controller),
    ("show dcs key", "GhostBase.Profile.ShowDCs" in controller),
    ("show registration key", "GhostBase.Profile.ShowRegistration" in controller),
    ("ghost mode section", "Ghost Mode" in controller),
    ("switch item", "ItemListSwitchItem(" in controller),
    ("state promise", "ValuePromise(initialState" in controller),
    ("atomic state", "Atomic(value: initialState)" in controller),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Settings Toggles v0.4A controller patch OK")

profile = profile_p.read_text()

for marker in [
    "    // MARK: GhostBase v0.4A peer metrics card with toggles\n",
    "    // MARK: GhostBase v0.3C peer metrics card\n",
    "    // MARK: GhostBase v0.3B peer id card\n",
]:
    while marker in profile:
        start = profile.index(marker)
        end = profile.index("    let bioContextAction:", start)
        profile = profile[:start] + profile[end:]

peer_block = r'''
    // MARK: GhostBase v0.4A peer metrics card with toggles
    do {
        let ghostBaseProfileEnabled = (UserDefaults.standard.object(forKey: "GhostBase.Profile.Enabled") as? Bool) ?? true
        let ghostBaseShowIds = (UserDefaults.standard.object(forKey: "GhostBase.Profile.ShowIds") as? Bool) ?? true
        let ghostBaseShowDCs = (UserDefaults.standard.object(forKey: "GhostBase.Profile.ShowDCs") as? Bool) ?? true
        let ghostBaseShowRegistration = (UserDefaults.standard.object(forKey: "GhostBase.Profile.ShowRegistration") as? Bool) ?? true

        if ghostBaseProfileEnabled {
            var ghostBaseItemId = 990000
            var ghostBasePeerIdText = ""

            if let peer = data.peer {
                if case let .channel(channel) = peer {
                    ghostBasePeerIdText = "-100" + String(channel.id.id._internalGetInt64Value())
                } else {
                    ghostBasePeerIdText = String(peer.id.id._internalGetInt64Value())
                }
            }

            if ghostBaseShowIds && !ghostBasePeerIdText.isEmpty {
                items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: ghostBaseItemId, label: "id: \(ghostBasePeerIdText)", text: "", textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                    interaction.requestLayout(false)
                }))
                ghostBaseItemId += 1
            }

            if ghostBaseShowDCs, let peer = data.peer, let smallProfileImage = peer.smallProfileImage, let cloudResource = smallProfileImage.resource as? CloudPeerPhotoSizeMediaResource {
                let ghostBaseDcText = String(cloudResource.datacenterId)
                items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: ghostBaseItemId, label: "dc: \(ghostBaseDcText)", text: "", textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                    interaction.requestLayout(false)
                }))
                ghostBaseItemId += 1
            }

            var ghostBaseRegDateString = ""
            if let cachedData = data.cachedData as? CachedUserData, let registrationDate = cachedData.peerStatusSettings?.registrationDate {
                let components = registrationDate.components(separatedBy: ".")
                if components.count == 2, let first = Int32(components[0]), let second = Int32(components[1]) {
                    let month = first - 1
                    let year = second - 1900
                    ghostBaseRegDateString = stringForMonth(strings: presentationData.strings, month: month, ofYear: year)
                }
            }

            if ghostBaseShowRegistration && !ghostBaseRegDateString.isEmpty {
                items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: ghostBaseItemId, label: "registered:", text: ghostBaseRegDateString, textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                    interaction.requestLayout(false)
                }))
                ghostBaseItemId += 1
            }
        }
    }

'''

needle = '''    for section in InfoSection.allCases {
        items[section] = []
    }
'''

if needle not in profile:
    raise SystemExit("items init insertion point not found")

profile = profile.replace(needle, needle + peer_block, 1)
profile_p.write_text(profile)
print("patched", profile_p)

controller = controller_p.read_text()
profile = profile_p.read_text()

marker = "    // MARK: GhostBase v0.4A peer metrics card with toggles\n"
if marker not in profile:
    raise SystemExit("v0.4A PeerInfo block marker missing")

start = profile.index(marker)
end = profile.index("    let bioContextAction:", start)
block = profile[start:end]

for forbidden in [
    "data.channelCreationTimestamp",
    "data.regDate",
    "data.peer as? TelegramUser",
    "data.peer as? TelegramChannel",
    "data.peer as? TelegramGroup",
    "openPeerInfoContextMenu(.copy",
    'label: "created:"',
    'label: "id: \\\\(ghostBasePeerIdText)"',
    'label: "dc: \\\\(ghostBaseDcText)"',
]:
    if forbidden in block:
        raise SystemExit("FORBIDDEN in v0.4A block: " + forbidden)

checks = [
    ("controller v0.4A", "Version: v0.4A" in controller),
    ("profile metrics header", "Profile Metrics" in controller),
    ("main switch title", "Enable Profile Card" in controller),
    ("main key controller", "GhostBase.Profile.Enabled" in controller),
    ("main key block", "GhostBase.Profile.Enabled" in block),
    ("show ids key", "GhostBase.Profile.ShowIds" in controller and "GhostBase.Profile.ShowIds" in block),
    ("show dcs key", "GhostBase.Profile.ShowDCs" in controller and "GhostBase.Profile.ShowDCs" in block),
    ("show registration key", "GhostBase.Profile.ShowRegistration" in controller and "GhostBase.Profile.ShowRegistration" in block),
    ("ghost mode header", "Ghost Mode" in controller),
    ("switch item", "ItemListSwitchItem(" in controller),
    ("state promise", "ValuePromise(initialState" in controller),
    ("atomic state", "Atomic(value: initialState)" in controller),
    ("main guard", "if ghostBaseProfileEnabled {" in block),
    ("channel -100", '"-100" + String(channel.id.id._internalGetInt64Value())' in block),
    ("id interpolation", 'label: "id: \\(ghostBasePeerIdText)"' in block),
    ("dc interpolation", 'label: "dc: \\(ghostBaseDcText)"' in block),
    ("registered row", 'label: "registered:"' in block),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Settings Toggles v0.4A patch OK")
