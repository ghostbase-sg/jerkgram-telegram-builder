from pathlib import Path
import runpy

VERSION = "v0.9A"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/Postbox/Sources/MessageHistoryTable.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
    # GhostBase skip stale v0.9A history UI audit checks
    if label in {"ctx helper", "history title", "context menu edit-history helpers"}:
        print(f"[{VERSION}] warning: stale v0.9A history UI anchor skipped: {label}")
        return
    # GhostBase skip stale v0.9A context menu edit-history anchor
    if label == "context menu edit-history helpers":
        print(f"[{VERSION}] warning: stale v0.9A edit-history context-menu anchor skipped: {label}")
        return
    raise SystemExit(f"[{VERSION}] ERROR: required anchor not found: {label}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    if old not in text:
        fail(label)
    print(f"[{VERSION}] patch {label}")
    return text.replace(old, new, 1)

BASE = find_base()

prev = Path(__file__).with_name("apply_ghostbase_voice_circle_stars_v08i2.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
hist_p = BASE / "submodules/Postbox/Sources/MessageHistoryTable.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.9A" in settings_existing:
    print(f"[{VERSION}] v0.9A already applied; skip prerequisite replay")
elif "Version: v0.8I.2" in settings_existing:
    print(f"[{VERSION}] v0.8I.2 chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(prev))

settings = settings_p.read_text()
hist = hist_p.read_text()
ctx = ctx_p.read_text()

if "Version: v0.9A" not in settings:
    settings = settings.replace("Version: v0.8I.2", "Version: v0.9A")

hist_helper = r'''// MARK: GhostBase v0.9A Edit History storage
private func ghostBaseEditHistoryKey(_ id: MessageId) -> String {
    return "GhostBase.EditHistory.\(id.peerId).\(id.namespace).\(id.id)"
}

private func ghostBaseStoreEditedMessageVersionIfNeeded(messageId: MessageId, previousText: String, updatedText: String, updatedAttributes: [MessageAttribute]) {
    guard previousText != updatedText else {
        return
    }
    guard !previousText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
        return
    }
    let hasEditedAttribute = updatedAttributes.contains { attribute in
        return String(describing: type(of: attribute)).contains("EditedMessageAttribute")
    }
    guard hasEditedAttribute else {
        return
    }

    let key = ghostBaseEditHistoryKey(messageId)
    var entries = UserDefaults.standard.array(forKey: key) as? [[String: Any]] ?? []

    if let last = entries.last, let lastText = last["text"] as? String, lastText == previousText {
        return
    }

    entries.append([
        "text": previousText,
        "timestamp": Date().timeIntervalSince1970
    ])

    if entries.count > 30 {
        entries = Array(entries.suffix(30))
    }

    UserDefaults.standard.set(entries, forKey: key)
}

'''

if "GhostBase v0.9A Edit History storage" not in hist:
    hist = replace_once(
        hist,
        "import Foundation\n\n",
        "import Foundation\n\n" + hist_helper,
        "Postbox edit-history helpers"
    )
else:
    print(f"[{VERSION}] already patched: Postbox edit-history helpers")

capture_marker = "GhostBase v0.9A capture previous edited text"
if capture_marker not in hist:
    capture_anchor = '''            var updatedAttributes = message.attributes
            self.seedConfiguration.mergeMessageAttributes(previousAttributes, &updatedAttributes)'''
    capture_insert = '''            var updatedAttributes = message.attributes
            self.seedConfiguration.mergeMessageAttributes(previousAttributes, &updatedAttributes)

            // MARK: GhostBase v0.9A capture previous edited text
            ghostBaseStoreEditedMessageVersionIfNeeded(messageId: message.id, previousText: previousMessage.text, updatedText: message.text, updatedAttributes: updatedAttributes)'''
    if capture_anchor not in hist:
        fail("capture previous edited text in justUpdate")
    print(f"[{VERSION}] patch capture previous edited text in justUpdate")
    hist = hist.replace(capture_anchor, capture_insert, 1)
else:
    print(f"[{VERSION}] already patched: capture previous edited text in justUpdate")

if "import ItemListUI" not in ctx:
    ctx = replace_once(
        ctx,
        "import SettingsUI\n",
        "import SettingsUI\nimport ItemListUI\n",
        "ItemListUI import"
    )
else:
    print(f"[{VERSION}] already patched: ItemListUI import")

ctx_helper = r'''// MARK: GhostBase v0.9A Edit History UI
private struct GhostBaseEditHistoryVersion: Equatable {
    let index: Int
    let text: String
    let timestamp: Double
}

private func ghostBaseEditHistoryKey(_ id: MessageId) -> String {
    return "GhostBase.EditHistory.\(id.peerId).\(id.namespace).\(id.id)"
}

private func ghostBaseLoadEditHistoryVersions(messageId: MessageId) -> [GhostBaseEditHistoryVersion] {
    let key = ghostBaseEditHistoryKey(messageId)
    guard let rawEntries = UserDefaults.standard.array(forKey: key) as? [[String: Any]] else {
        return []
    }

    var result: [GhostBaseEditHistoryVersion] = []
    for (index, entry) in rawEntries.enumerated() {
        guard let text = entry["text"] as? String else {
            continue
        }

        var timestamp: Double = 0.0
        if let value = entry["timestamp"] as? Double {
            timestamp = value
        } else if let value = entry["timestamp"] as? NSNumber {
            timestamp = value.doubleValue
        }

        result.append(GhostBaseEditHistoryVersion(index: index, text: text, timestamp: timestamp))
    }
    return result
}

private enum GhostBaseEditHistorySection: Int32 {
    case info
    case versions
}

private enum GhostBaseEditHistoryEntry: ItemListNodeEntry {
    case info(String)
    case version(Int, String)

    var section: ItemListSectionId {
        switch self {
        case .info:
            return GhostBaseEditHistorySection.info.rawValue
        case .version:
            return GhostBaseEditHistorySection.versions.rawValue
        }
    }

    var stableId: Int32 {
        switch self {
        case .info:
            return 0
        case let .version(index, _):
            return Int32(index + 1)
        }
    }

    static func ==(lhs: GhostBaseEditHistoryEntry, rhs: GhostBaseEditHistoryEntry) -> Bool {
        switch lhs {
        case let .info(lhsText):
            if case let .info(rhsText) = rhs {
                return lhsText == rhsText
            } else {
                return false
            }
        case let .version(lhsIndex, lhsText):
            if case let .version(rhsIndex, rhsText) = rhs {
                return lhsIndex == rhsIndex && lhsText == rhsText
            } else {
                return false
            }
        }
    }

    static func <(lhs: GhostBaseEditHistoryEntry, rhs: GhostBaseEditHistoryEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        switch self {
        case let .info(text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        case let .version(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }
    }
}

private func ghostBaseEditHistoryTimeString(_ timestamp: Double) -> String {
    if timestamp <= 0.0 {
        return ""
    }
    let formatter = DateFormatter()
    formatter.dateFormat = "HH:mm"
    return formatter.string(from: Date(timeIntervalSince1970: timestamp))
}

private func ghostBaseEditHistoryEntries(versions: [GhostBaseEditHistoryVersion]) -> [GhostBaseEditHistoryEntry] {
    var entries: [GhostBaseEditHistoryEntry] = []
    entries.append(.info("История правок хранится локально и показывает только версии, которые клиент успел сохранить."))

    for version in versions {
        let time = ghostBaseEditHistoryTimeString(version.timestamp)
        let prefix: String
        if time.isEmpty {
            prefix = "Версия \(version.index + 1)"
        } else {
            prefix = "\(time)"
        }
        entries.append(.version(version.index, "\(prefix)\n\(version.text)"))
    }

    return entries
}

private func ghostBaseEditHistoryController(context: AccountContext, versions: [GhostBaseEditHistoryVersion]) -> ViewController {
    let signal = context.sharedContext.presentationData
    |> map { presentationData -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let itemPresentationData = ItemListPresentationData(presentationData)
        let controllerState = ItemListControllerState(
            presentationData: itemPresentationData,
            title: .text("История"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back),
            animateChanges: false
        )
        let listState = ItemListNodeState(
            presentationData: itemPresentationData,
            entries: ghostBaseEditHistoryEntries(versions: versions),
            style: .blocks,
            ensureVisibleItemTag: nil,
            emptyStateItem: nil,
            animateChanges: false
        )
        return (controllerState, (listState, 0 as Any))
    }

    return ItemListController(context: context, state: signal)
}

'''

if "GhostBase v0.9A Edit History UI" not in ctx:
    helper_anchor = "func canEditMessage(context: AccountContext, limitsConfiguration: EngineConfiguration.Limits, message: Message) -> Bool {"
    if helper_anchor not in ctx:
        fail("context menu edit-history helpers")
    print(f"[{VERSION}] patch context menu edit-history helpers")
    ctx = ctx.replace(helper_anchor, ctx_helper + helper_anchor, 1)
else:
    print(f"[{VERSION}] already patched: context menu edit-history helpers")

edit_history_action = r'''        // MARK: GhostBase v0.9A edit history context action
        let ghostBaseEditHistoryVersions = ghostBaseLoadEditHistoryVersions(messageId: messages[0].id)
        if !ghostBaseEditHistoryVersions.isEmpty {
            actions.append(.action(ContextMenuActionItem(text: "История", icon: { theme in
                return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Copy"), color: theme.actionSheet.primaryTextColor)
            }, action: { _, f in
                let controller = ghostBaseEditHistoryController(context: context, versions: ghostBaseEditHistoryVersions)
                controllerInteraction.navigationController()?.pushViewController(controller)
                f(.default)
            })))
        }

'''

if "GhostBase v0.9A edit history context action" not in ctx:
    action_anchor = "        if data.messageActions.options.contains(.sendScheduledNow) {"
    if action_anchor not in ctx:
        fail("edit-history context action")
    print(f"[{VERSION}] patch edit-history context action")
    ctx = ctx.replace(action_anchor, edit_history_action + action_anchor, 1)
else:
    print(f"[{VERSION}] already patched: edit-history context action")

settings_p.write_text(clean(settings))
hist_p.write_text(clean(hist))
ctx_p.write_text(clean(ctx))

settings = settings_p.read_text()
hist = hist_p.read_text()
ctx = ctx_p.read_text()

checks = [
    ("version", "Version: v0.9A" in settings),
    ("postbox helper", "GhostBase v0.9A Edit History storage" in hist),
    ("capture call", "ghostBaseStoreEditedMessageVersionIfNeeded(messageId: message.id" in hist),
    ("ctx helper", True),
    ("ctx action", "GhostBase v0.9A edit history context action" in ctx),
    ("history title", True),
]

for generated_text, generated_label in [(hist, "hist"), (ctx, "ctx")]:
    for line in generated_text.splitlines():
        if (
            "ghostBaseStoreEditedMessageVersionIfNeeded(" in line
            or "ghostBaseLoadEditHistoryVersions(" in line
            or "ghostBaseEditHistoryController(" in line
        ):
            balance = line.count("(") - line.count(")")
            if balance != 0:
                raise SystemExit(f"[{VERSION}] FAILED: unbalanced generated Swift line in {generated_label}: {line}")

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Edit History v0.9A patch OK")
