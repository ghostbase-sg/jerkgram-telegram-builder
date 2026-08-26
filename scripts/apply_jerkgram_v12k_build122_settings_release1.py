#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STARS = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramStarsEditorController.swift"
DATA = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift"
ARCHIVE_FLOW = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift"
TRANSACTION = ROOT / "submodules/JerkgramCore/Sources/JerkgramArchiveTransaction.swift"
TIME_MACHINE = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift"

MARKER = "// MARK: Jerkgram v1.2K BUILD122_SETTINGS_RELEASE1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build122 settings release] " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def block_bounds(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    require(start >= 0, "missing block: " + signature)
    brace = text.find("{", start)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
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
                return start, index + 1
    raise RuntimeError("[Build122 settings release] unbalanced block: " + signature)


def restore_root_menu(text: str) -> str:
    start, end = block_bounds(text, "if page == .root {")
    old = text[start:end]
    require(".valueDisclosure(" in old and '"Jerkgram"' in old, "root Jerkgram hero missing before correction")
    replacement = '''if page == .root {
        // MARK: Jerkgram v1.2K BUILD122_SETTINGS_RELEASE1
        // Keep the agreed Telegram-native destination list. Presentation work
        // belongs inside destinations, not in a new root hero card.
        return [
            .header(0, strings.features),
            .disclosure(0, 1, strings.basicFunctions, "Jerkgram/Settings/Airplane", .home),
            .disclosure(0, 2, strings.ghostMode, "Chat/Context Menu/Eye", .ghostMode),
            .disclosure(0, 3, strings.messages, "Chat/Context Menu/MessageBubble", .messages),
            .disclosure(0, 4, strings.protectedContent, "Premium/CopyProtection/NoForward", .protectedContent),
            .disclosure(0, 5, strings.mediaAndStories, "Item List/Icons/Stories", .mediaStories),
            .disclosure(0, 6, strings.appearance, "Chat/Context Menu/ApplyTheme", .appearance),
            .disclosure(0, 7, strings.debugResearch, "Chat/Context Menu/FormatCode", .debugResearch),
            .disclosure(0, 8, strings.dataAndBackup, "Item List/Icons/Stories", .dataAndBackup),
            .disclosure(0, 9, strings.about, "Chat/Context Menu/Info", .about)
        ]
    }'''
    require(replacement.count(".disclosure(") == 9, "root menu must keep nine destinations")
    require('"Jerkgram",' not in replacement, "root Jerkgram hero survived")
    return text[:start] + replacement + text[end:]


def patch_settings() -> None:
    text = SETTINGS.read_text(encoding="utf-8")
    if MARKER in text and "jerkgramStarsEditorController(context: context)" in text:
        return
    text = restore_root_menu(text)
    legacy_stars_write = "UserDefaults.standard.set(" + "ghostBaseSanitizeStarsAmount(updatedText), forKey: key)"
    legacy_stars_input = (
        "                textUpdated: { updatedText in\n"
        "                    " + legacy_stars_write + "\n"
        "                },"
    )
    text = replace_once(
        text,
        legacy_stars_input,
        '''                // BUILD122: legacy input is not a persistence owner. The
                // dedicated Stars editor keeps a local draft and commits on Save.
                textUpdated: { _ in },''',
        "remove per-keystroke Stars persistence",
    )
    require(legacy_stars_write not in text, "Stars input must not write UserDefaults")
    text = replace_once(
        text,
        '''        if selectedPage == .dataAndBackup {
            pushController?(jerkgramDataAndBackupController(context: context))
        } else {''',
        '''        if selectedPage == .dataAndBackup {
            pushController?(jerkgramDataAndBackupController(context: context))
        } else if selectedPage == .stars {
            pushController?(jerkgramStarsEditorController(context: context))
        } else {''',
        "route dedicated Stars editor",
    )
    SETTINGS.write_text(text, encoding="utf-8")


STARS_SOURCE = r'''import Foundation
import Display
import SwiftSignalKit
import TelegramPresentationData
import ItemListUI
import AccountContext

// MARK: Jerkgram v1.2K BUILD122_STARS_DRAFT_EDITOR1
private let jerkgramStarsEnabledKey = "jerkgram.Stars.LocalBalance.Enabled"
private let jerkgramStarsAmountKey = "jerkgram.Stars.LocalBalance.Amount"

private struct JerkgramStarsDraftState: Equatable {
    var enabled: Bool
    var amount: String
}

private final class JerkgramStarsEditorArguments {
    let setEnabled: (Bool) -> Void
    let setAmount: (String) -> Void
    let applyPreset: (Int64) -> Void

    init(setEnabled: @escaping (Bool) -> Void, setAmount: @escaping (String) -> Void, applyPreset: @escaping (Int64) -> Void) {
        self.setEnabled = setEnabled
        self.setAmount = setAmount
        self.applyPreset = applyPreset
    }
}

private enum JerkgramStarsEditorEntry: ItemListNodeEntry {
    case preview(Int32, String, String)
    case toggle(Int32, String, Bool)
    case input(Int32, String, String)
    case preset(Int32, String, Int64)
    case info(Int32, String)

    var section: ItemListSectionId {
        switch self {
        case .preview: return 0
        case .toggle, .input: return 1
        case .preset: return 2
        case .info: return 3
        }
    }

    var stableId: Int32 {
        switch self {
        case let .preview(id, _, _), let .toggle(id, _, _), let .input(id, _, _), let .preset(id, _, _), let .info(id, _): return id
        }
    }

    static func == (lhs: Self, rhs: Self) -> Bool {
        return lhs.stableId == rhs.stableId && String(describing: lhs) == String(describing: rhs)
    }
    static func < (lhs: Self, rhs: Self) -> Bool { lhs.stableId < rhs.stableId }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! JerkgramStarsEditorArguments
        switch self {
        case let .preview(_, amount, status):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: "⭐  \(amount)", label: status, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .none, action: nil
            )
        case let .toggle(_, title, value):
            return ItemListSwitchItem(
                presentationData: presentationData, title: title, value: value,
                sectionId: self.section, style: .blocks,
                updated: { arguments.setEnabled($0) }
            )
        case let .input(_, title, value):
            return ItemListSingleLineInputItem(
                presentationData: presentationData,
                title: NSAttributedString(string: title, textColor: presentationData.theme.list.itemPrimaryTextColor),
                text: value, placeholder: "0", type: .regular(capitalization: false, autocorrection: false),
                returnKeyType: .done, alignment: .right, spacing: 16.0,
                clearType: .onFocus, maxLength: 20, selectAllOnFocus: true,
                sectionId: self.section,
                textUpdated: { arguments.setAmount(jerkgramSanitizeStarsDraft($0)) },
                shouldUpdateText: { jerkgramIsValidStarsDraft($0) }, action: {}
            )
        case let .preset(_, title, value):
            return ItemListActionItem(
                presentationData: presentationData, title: title, kind: .generic,
                alignment: .center, sectionId: self.section, style: .blocks,
                action: { arguments.applyPreset(value) }
            )
        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }
    }
}

private func jerkgramIsValidStarsDraft(_ text: String) -> Bool {
    let value = text.replacingOccurrences(of: ",", with: ".")
    guard value.count <= 20, value.filter({ $0 == "." }).count <= 1 else { return false }
    return value.allSatisfy { $0.isNumber || $0 == "." || $0 == " " || $0 == "\u{00a0}" }
}

private func jerkgramSanitizeStarsDraft(_ text: String) -> String {
    let compact = text.replacingOccurrences(of: " ", with: "").replacingOccurrences(of: "\u{00a0}", with: "").replacingOccurrences(of: ",", with: ".")
    guard jerkgramIsValidStarsDraft(compact) else { return "0" }
    return compact.isEmpty ? "0" : compact
}

private func jerkgramStarsPreset(_ current: String, delta: Int64) -> String {
    let whole = current.split(separator: ".", maxSplits: 1).first.flatMap { Int64($0) } ?? 0
    return String(max(0, whole + delta))
}

private func jerkgramCommitStarsDraft(accountPeerId: Int64, state: JerkgramStarsDraftState) {
    let defaults = UserDefaults.standard
    let amount = jerkgramSanitizeStarsDraft(state.amount)
    defaults.set(state.enabled, forKey: jerkgramStarsEnabledKey)
    defaults.set(amount, forKey: jerkgramStarsAmountKey)
    defaults.set(state.enabled, forKey: "jerkgram.account.\(accountPeerId).setting.\(jerkgramStarsEnabledKey)")
    defaults.set(amount, forKey: "jerkgram.account.\(accountPeerId).setting.\(jerkgramStarsAmountKey)")
}

public func jerkgramStarsEditorController(context: AccountContext) -> ViewController {
    let accountPeerId = context.account.peerId.toInt64()
    let scopedEnabled = "jerkgram.account.\(accountPeerId).setting.\(jerkgramStarsEnabledKey)"
    let scopedAmount = "jerkgram.account.\(accountPeerId).setting.\(jerkgramStarsAmountKey)"
    let defaults = UserDefaults.standard
    let initial = JerkgramStarsDraftState(
        enabled: (defaults.object(forKey: scopedEnabled) as? Bool) ?? defaults.bool(forKey: jerkgramStarsEnabledKey),
        amount: (defaults.string(forKey: scopedAmount) ?? defaults.string(forKey: jerkgramStarsAmountKey)).map(jerkgramSanitizeStarsDraft) ?? "0"
    )
    let stateValue = Atomic(value: initial)
    let statePromise = ValuePromise(initial, ignoreRepeated: true)
    var controller: ItemListController?

    func update(_ transform: (inout JerkgramStarsDraftState) -> Void) {
        let value = stateValue.modify { current in
            var current = current
            transform(&current)
            return current
        }
        statePromise.set(value)
    }

    let arguments = JerkgramStarsEditorArguments(
        setEnabled: { value in update { $0.enabled = value } },
        setAmount: { value in update { $0.amount = value } },
        applyPreset: { value in update { $0.amount = jerkgramStarsPreset($0.amount, delta: value) } }
    )

    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let strings = presentationData.strings.jerkgram
        let amount = jerkgramSanitizeStarsDraft(state.amount)
        let status = strings.starsOverrideSummary(state.enabled, amount)
        let dirty = state != initial
        let leftNavigationButton = ItemListNavigationButton(content: .text(presentationData.strings.Common_Cancel), style: .regular, enabled: true, action: {
            let _ = (controller?.navigationController as? NavigationController)?.popViewController(animated: true)
        })
        let rightNavigationButton = ItemListNavigationButton(content: .text(presentationData.strings.Common_Save), style: .bold, enabled: dirty, action: {
            jerkgramCommitStarsDraft(accountPeerId: accountPeerId, state: stateValue.with { $0 })
            let _ = (controller?.navigationController as? NavigationController)?.popViewController(animated: true)
        })
        let entries: [JerkgramStarsEditorEntry] = [
            .preview(1, amount, status),
            .toggle(2, strings.localStarsBalance, state.enabled),
            .input(3, strings.starsBalance, state.amount),
            .preset(4, "+ 100 ⭐", 100),
            .preset(5, "+ 1 000 ⭐", 1000),
            .preset(6, "+ 10 000 ⭐", 10000),
            .info(7, strings.starsEditorHint)
        ]
        return (
            ItemListControllerState(
                presentationData: ItemListPresentationData(presentationData), title: .text(strings.starsBalance),
                leftNavigationButton: leftNavigationButton, rightNavigationButton: rightNavigationButton,
                backNavigationButton: nil
            ),
            (ItemListNodeState(
                presentationData: ItemListPresentationData(presentationData), entries: entries,
                style: .blocks, animateChanges: false
            ), arguments as Any)
        )
    }
    controller = ItemListController(context: context, state: signal)
    return controller!
}
'''


def patch_data_ui() -> None:
    text = DATA.read_text(encoding="utf-8")
    if "BUILD122_DATA_ACTIONS1" in text:
        return
    old = '''        case let .action(_, _, title, value, action):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .arrow, action: { arguments.action(action) }
            )'''
    new = '''        // MARK: Jerkgram v1.2K BUILD122_DATA_ACTIONS1
        case let .action(_, _, title, value, action):
            if action == "export" || action == "import" || action == "cleanup" {
                return ItemListActionItem(
                    presentationData: presentationData, title: title,
                    kind: .generic, alignment: .center,
                    sectionId: self.section, style: .blocks,
                    action: { arguments.action(action) }
                )
            }
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: action == "perChat" ? .arrow : .none,
                action: { arguments.action(action) }
            )'''
    text = replace_once(text, old, new, "Data action semantics")
    DATA.write_text(text, encoding="utf-8")


def patch_time_machine() -> None:
    text = TIME_MACHINE.read_text(encoding="utf-8")
    if "BUILD122_TIME_MACHINE_POLISH1" in text:
        return
    text = replace_once(
        text,
        '''        case let .filter(_, _, title, value, kind):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .arrow,
                action: { if let kind { arguments.toggleKind(kind) } else { arguments.selectSender() } }
            )''',
        '''        // MARK: Jerkgram v1.2K BUILD122_TIME_MACHINE_POLISH1
        case let .filter(_, _, title, value, kind):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .none,
                action: { if let kind { arguments.toggleKind(kind) } else { arguments.selectSender() } }
            )''',
        "Time Machine filter semantics",
    )
    text = replace_once(
        text,
        '''        case let .loadMore(_, title):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: "", labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .arrow, action: { arguments.loadMore() }
            )''',
        '''        case let .loadMore(_, title):
            return ItemListActionItem(
                presentationData: presentationData, title: title,
                kind: .generic, alignment: .center,
                sectionId: self.section, style: .blocks,
                action: { arguments.loadMore() }
            )''',
        "Time Machine load-more button",
    )
    TIME_MACHINE.write_text(text, encoding="utf-8")


def patch_transaction() -> None:
    text = TRANSACTION.read_text(encoding="utf-8")
    if "JerkgramRetentionConfigurationStore" in text:
        return
    text = replace_once(
        text,
        '''public protocol JerkgramSettingsSnapshotStore: AnyObject {
    func snapshot(accountPeerId: Int64) throws -> JerkgramSettingsSnapshot
    func replace(_ snapshot: JerkgramSettingsSnapshot) throws
}
''',
        '''public protocol JerkgramSettingsSnapshotStore: AnyObject {
    func snapshot(accountPeerId: Int64) throws -> JerkgramSettingsSnapshot
    func replace(_ snapshot: JerkgramSettingsSnapshot) throws
}

// MARK: Jerkgram v1.2K BUILD122_ARCHIVE_EXACT_ACCOUNTS1
public protocol JerkgramRetentionConfigurationStore: AnyObject {
    func configuration(accountPeerId: Int64) throws -> JerkgramRetentionConfiguration
    func replace(_ configuration: JerkgramRetentionConfiguration) throws
}
''',
        "retention transaction protocol",
    )
    text = replace_once(
        text,
        '''        confirmSettingsChanges: Bool,
        eventStore: JerkgramEventStore,
        settingsStore: JerkgramSettingsSnapshotStore
    ) throws {''',
        '''        confirmSettingsChanges: Bool,
        eventStore: JerkgramEventStore,
        settingsStore: JerkgramSettingsSnapshotStore,
        incomingRetention: [Int64: JerkgramRetentionConfiguration] = [:],
        retentionStore: JerkgramRetentionConfigurationStore? = nil
    ) throws {''',
        "transaction retention parameters",
    )
    text = replace_once(
        text,
        '''        var eventRollback: [Int64: [JerkgramCanonicalEvent]] = [:]
        var settingsRollback: [Int64: JerkgramSettingsSnapshot] = [:]
        do {''',
        '''        var eventRollback: [Int64: [JerkgramCanonicalEvent]] = [:]
        var settingsRollback: [Int64: JerkgramSettingsSnapshot] = [:]
        var retentionRollback: [Int64: JerkgramRetentionConfiguration] = [:]
        do {''',
        "retention rollback map",
    )
    text = replace_once(
        text,
        '''                settingsRollback[accountPeerId] = try settingsStore.snapshot(accountPeerId: accountPeerId)
                let existingById = Dictionary''',
        '''                settingsRollback[accountPeerId] = try settingsStore.snapshot(accountPeerId: accountPeerId)
                if incomingRetention[accountPeerId] != nil, let retentionStore {
                    retentionRollback[accountPeerId] = try retentionStore.configuration(accountPeerId: accountPeerId)
                }
                let existingById = Dictionary''',
        "capture retention rollback",
    )
    text = replace_once(
        text,
        '''                if let settings = incomingSettings[accountPeerId] {
                    try settingsStore.replace(settings)
                }
            }''',
        '''                if let settings = incomingSettings[accountPeerId] {
                    guard settings.accountPeerId == accountPeerId else {
                        throw JerkgramArchiveValidationError.unavailableAccount(settings.accountPeerId)
                    }
                    try settingsStore.replace(settings)
                }
                if let retention = incomingRetention[accountPeerId], let retentionStore {
                    guard retention.accountPeerId == accountPeerId else {
                        throw JerkgramArchiveValidationError.unavailableAccount(retention.accountPeerId)
                    }
                    try retentionStore.replace(retention)
                }
            }''',
        "apply exact retention",
    )
    text = replace_once(
        text,
        '''                if let settings = settingsRollback[accountPeerId] {
                    try? settingsStore.replace(settings)
                }
            }''',
        '''                if let settings = settingsRollback[accountPeerId] {
                    try? settingsStore.replace(settings)
                }
                if let retention = retentionRollback[accountPeerId], let retentionStore {
                    try? retentionStore.replace(retention)
                }
            }''',
        "rollback retention",
    )
    require(
        "selectedAccountPeerIds.isSubset(of: availableAccountPeerIds)" in text,
        "exact available-account gate disappeared",
    )
    TRANSACTION.write_text(text, encoding="utf-8")


def patch_archive_flow() -> None:
    text = ARCHIVE_FLOW.read_text(encoding="utf-8")
    old_snapshot_replace = '''    func replace(_ snapshot: JerkgramSettingsSnapshot) throws {
        for (key, value) in snapshot.toggles {'''
    new_snapshot_replace = r'''    func replace(_ snapshot: JerkgramSettingsSnapshot) throws {
        // Replacement is exact so a failed transaction can restore absence as
        // well as values; otherwise newly introduced keys would leak past rollback.
        for key in jerkgramPortableBooleanKeys + jerkgramPortableStringKeys + jerkgramPortableIntegerKeys {
            let scoped = "jerkgram.account.\(snapshot.accountPeerId).setting.\(key)"
            UserDefaults.standard.removeObject(forKey: scoped)
        }
        for (key, value) in snapshot.toggles {'''
    if "BUILD122_ARCHIVE_ACTIVE_ACCOUNTS1" in text:
        if "removeObject(forKey: scoped)" not in text:
            text = replace_once(text, old_snapshot_replace, new_snapshot_replace, "exact snapshot replacement")
            ARCHIVE_FLOW.write_text(text, encoding="utf-8")
        return
    text = replace_once(
        text,
        '''public func jerkgramPresentArchiveImport(
    context: AccountContext,
    controller: ViewController
) {
    let presentationData = context.sharedContext.currentPresentationData.with { $0 }''',
        '''// MARK: Jerkgram v1.2K BUILD122_ARCHIVE_ACTIVE_ACCOUNTS1
public func jerkgramPresentArchiveImport(
    context: AccountContext,
    controller: ViewController
) {
    let _ = (context.sharedContext.activeAccountContexts
    |> take(1)
    |> deliverOnMainQueue).start(next: { activeAccounts in
        let availableAccountPeerIds = Set(activeAccounts.accounts.map { $0.1.account.peerId.toInt64() })
        jerkgramPresentArchiveImportPicker(
            context: context,
            controller: controller,
            availableAccountPeerIds: availableAccountPeerIds
        )
    })
}

private func jerkgramPresentArchiveImportPicker(
    context: AccountContext,
    controller: ViewController,
    availableAccountPeerIds: Set<Int64>
) {
    let presentationData = context.sharedContext.currentPresentationData.with { $0 }''',
        "active account import wrapper",
    )
    old_start = r'''                let accountPeerId = context.account.peerId.toInt64()
                guard let account = manifest.accounts.first(where: { $0.accountPeerId == accountPeerId }) else {
                    throw JerkgramArchiveValidationError.unavailableAccount(accountPeerId)
                }
                var payloads: [String: Data] = [:]
                for descriptor in account.payloads {
                    payloads[descriptor.relativePath] = try Data(contentsOf: workURL.appendingPathComponent(descriptor.relativePath))
                }
                try JerkgramArchiveV2.validateExtractedPayloads(
                    manifest: JerkgramArchiveManifestV2(createdAtMs: manifest.createdAtMs, accounts: [account]),
                    payloads: payloads
                )
                let base = "accounts/\(accountPeerId)"
                guard let settingsData = payloads["\(base)/settings.json"],
                      let retentionData = payloads["\(base)/retention.json"],
                      let eventsData = payloads["\(base)/events.json"] else {
                    throw JerkgramArchiveValidationError.missingPayload(base)
                }
                let settings = try decoder.decode(JerkgramSettingsSnapshot.self, from: settingsData)
                let retention = try decoder.decode(JerkgramRetentionConfiguration.self, from: retentionData)
                let events = try decoder.decode([JerkgramCanonicalEvent].self, from: eventsData)
                let strings = presentationData.strings.jerkgram'''
    new_start = r'''                var payloads: [String: Data] = [:]
                for descriptor in manifest.accounts.flatMap(\.payloads) {
                    payloads[descriptor.relativePath] = try Data(contentsOf: workURL.appendingPathComponent(descriptor.relativePath))
                }
                try JerkgramArchiveV2.validateExtractedPayloads(manifest: manifest, payloads: payloads)

                let matchingAccounts = manifest.accounts.filter { availableAccountPeerIds.contains($0.accountPeerId) }
                guard !matchingAccounts.isEmpty else {
                    throw JerkgramArchiveValidationError.unavailableAccount(manifest.accounts.first?.accountPeerId ?? 0)
                }
                let selectedAccountPeerIds = Set(matchingAccounts.map(\.accountPeerId))
                let disconnected = manifest.accounts.map(\.accountPeerId).filter { !availableAccountPeerIds.contains($0) }.sorted()
                var incomingSettings: [Int64: JerkgramSettingsSnapshot] = [:]
                var incomingRetention: [Int64: JerkgramRetentionConfiguration] = [:]
                var incomingEvents: [Int64: [JerkgramCanonicalEvent]] = [:]
                for account in matchingAccounts {
                    let accountPeerId = account.accountPeerId
                    let base = "accounts/\(accountPeerId)"
                    guard let settingsData = payloads["\(base)/settings.json"],
                          let retentionData = payloads["\(base)/retention.json"],
                          let eventsData = payloads["\(base)/events.json"] else {
                        throw JerkgramArchiveValidationError.missingPayload(base)
                    }
                    let settings = try decoder.decode(JerkgramSettingsSnapshot.self, from: settingsData)
                    let retention = try decoder.decode(JerkgramRetentionConfiguration.self, from: retentionData)
                    let events = try decoder.decode([JerkgramCanonicalEvent].self, from: eventsData)
                    guard settings.accountPeerId == accountPeerId, retention.accountPeerId == accountPeerId,
                          events.allSatisfy({ $0.accountPeerId == accountPeerId }) else {
                        throw JerkgramArchiveValidationError.unavailableAccount(accountPeerId)
                    }
                    incomingSettings[accountPeerId] = settings
                    incomingRetention[accountPeerId] = retention
                    incomingEvents[accountPeerId] = events
                }
                let strings = presentationData.strings.jerkgram
                let connectedLines = selectedAccountPeerIds.sorted().map { "✓ Telegram ID \($0)" }
                let disconnectedSuffix = strings.languageCode == "ru" ? "не подключён — пропущен" : "not connected — skipped"
                let disconnectedLines = disconnected.map { "— Telegram ID \($0) (\(disconnectedSuffix))" }
                let importPreview = (connectedLines + disconnectedLines).joined(separator: "\\n")'''
    text = replace_once(text, old_start, new_start, "multi-account archive decode")
    text = replace_once(
        text,
        '''                    text: strings.importSettingsConfirmation(accountPeerId),''',
        '''                    text: importPreview,''',
        "archive account preview",
    )
    legacy_single_account_argument = "availableAccountPeerIds: [" + "context.account.peerId.toInt64()]"
    legacy_transaction_call = '''                            try? JerkgramArchiveTransaction.apply(
                                selectedAccountPeerIds: [accountPeerId],
                                LEGACY_AVAILABLE_ACCOUNT_ARGUMENT,
                                incomingEvents: [accountPeerId: events],
                                incomingSettings: [accountPeerId: settings],
                                confirmSettingsChanges: true,
                                eventStore: eventStore,
                                settingsStore: settingsStore
                            )
                            try? JerkgramRetentionRuntime.save(retention)'''.replace(
        "LEGACY_AVAILABLE_ACCOUNT_ARGUMENT", legacy_single_account_argument
    )
    text = replace_once(
        text,
        legacy_transaction_call,
        '''                            // MARK: Jerkgram v1.2K BUILD122_ARCHIVE_RESULT_FEEDBACK1
                            let retentionStore = JerkgramRuntimeRetentionStore()
                            do {
                                try JerkgramArchiveTransaction.apply(
                                    selectedAccountPeerIds: selectedAccountPeerIds,
                                    availableAccountPeerIds: availableAccountPeerIds,
                                    incomingEvents: incomingEvents,
                                    incomingSettings: incomingSettings,
                                    confirmSettingsChanges: true,
                                    eventStore: eventStore,
                                    settingsStore: settingsStore,
                                    incomingRetention: incomingRetention,
                                    retentionStore: retentionStore
                                )
                                let result = textAlertController(
                                    context: context,
                                    title: strings.importArchive,
                                    text: strings.languageCode == "ru" ? "Импорт завершён." : "Import completed.",
                                    actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})]
                                )
                                controller.present(result, in: .window(.root), with: nil)
                            } catch {
                                let result = textAlertController(
                                    context: context,
                                    title: strings.importArchive,
                                    text: String(describing: error),
                                    actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})]
                                )
                                controller.present(result, in: .window(.root), with: nil)
                            }''',
        "exact account transaction call",
    )
    text = replace_once(
        text,
        '''private final class JerkgramUserDefaultsSnapshotStore: JerkgramSettingsSnapshotStore {''',
        '''private final class JerkgramRuntimeRetentionStore: JerkgramRetentionConfigurationStore {
    func configuration(accountPeerId: Int64) throws -> JerkgramRetentionConfiguration {
        return JerkgramRetentionRuntime.configuration(accountPeerId: accountPeerId)
    }

    func replace(_ configuration: JerkgramRetentionConfiguration) throws {
        try JerkgramRetentionRuntime.save(configuration)
    }
}

private final class JerkgramUserDefaultsSnapshotStore: JerkgramSettingsSnapshotStore {''',
        "runtime retention store",
    )
    text = replace_once(text, old_snapshot_replace, new_snapshot_replace, "exact snapshot replacement")
    require(legacy_single_account_argument not in text, "single-account import fallback survived")
    ARCHIVE_FLOW.write_text(text, encoding="utf-8")


def main() -> None:
    for path in (SETTINGS, DATA, ARCHIVE_FLOW, TRANSACTION, TIME_MACHINE):
        require(path.is_file(), "missing materialized owner: " + str(path))
    patch_settings()
    STARS.parent.mkdir(parents=True, exist_ok=True)
    STARS.write_text(STARS_SOURCE, encoding="utf-8")
    patch_data_ui()
    patch_time_machine()
    patch_transaction()
    patch_archive_flow()
    print("[Build122 settings release] GREEN")
    print("[Build122 settings release] root restored; Stars draft editor; exact-account transactional import; action semantics polished")


if __name__ == "__main__":
    main()
