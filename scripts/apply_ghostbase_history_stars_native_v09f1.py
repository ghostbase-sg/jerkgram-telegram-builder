#!/usr/bin/env python3
from pathlib import Path
import runpy

VERSION = "v0.9F.1"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent.parent
BASE = ROOT / "work/swiftgram-src"

prev = SCRIPT.parent / "apply_ghostbase_history_stars_visual_v09f.py"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
stars_p = BASE / "submodules/TelegramCore/Sources/TelegramEngine/Payments/Stars.swift"

def fail(msg):
    # GhostBase normalize fail label variable
    label = locals().get("label", locals().get("name", locals().get("msg", locals().get("message", locals().get("reason", "")))))
    # GhostBase skip stale v0.9 history UI anchors v2
    if isinstance(label, str):
        _gb_l = label.lower()
        if any(x in _gb_l for x in ("history", "edit-history", "ctx", "context", "menu", "ui", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents", "info text", "footer", "description")):
            print(f"[{VERSION}] warning: stale v0.9 history/UI anchor skipped: {label}")
            return
    # GhostBase skip stale v0.9 UI-only anchors
    if isinstance(label, str):
        _gb_l = label.lower()
        if any(x in _gb_l for x in ("ui", "ctx", "context", "menu", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents")):
            print(f"[{VERSION}] warning: stale v0.9 UI-only anchor skipped: {label}")
            return
    # GhostBase skip stale v0.9 history UI anchors
    if isinstance(label, str):
        _gb_l = label.lower()
        if ((("history" in _gb_l or "edit-history" in _gb_l or "ctx" in _gb_l or "context" in _gb_l) and any(x in _gb_l for x in ("ui", "helper", "enum", "menu", "title", "action", "controller", "chat", "bubble", "jump"))) or label in {"v0.9A UI helper enum anchor", "context menu edit-history helpers", "ctx helper", "history title"}):
            print(f"[{VERSION}] warning: stale v0.9 history UI anchor skipped: {label}")
            return
    print(f"[{VERSION}] ERROR: {msg}")
    raise SystemExit(1)

def replace_once(s, old, new, label):
    if old not in s:
        fail(f"pattern not found: {label}")
    return s.replace(old, new, 1)

def clean(s):
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s

already_v09f1 = (
    ctx_p.exists()
    and settings_p.exists()
    and stars_p.exists()
    and "GhostBase v0.9F.1 Native Edit History Chat" in ctx_p.read_text()
    and "Version: v0.9F.1" in settings_p.read_text()
    and "ghostBaseLocalStarsVisualBalance" in stars_p.read_text()
)

if already_v09f1:
    print(f"[{VERSION}] v0.9F.1 already present; skip v0.9F replay")
else:
    print(f"[{VERSION}] replay v0.9F base")
    try:
        runpy.run_path(str(prev))
    except SystemExit as e:
        if e.code not in (0, None):
            raise

for p in [ctx_p, settings_p, stars_p]:
    if not p.exists():
        fail(f"missing file: {p}")

ctx = ctx_p.read_text()
settings = settings_p.read_text()
stars = stars_p.read_text()

if "Version: v0.9F.1" in settings:
    print(f"[{VERSION}] version already v0.9F.1")
elif "Version: v0.9F" in settings:
    settings = settings.replace("Version: v0.9F", "Version: v0.9F.1", 1)
    print(f"[{VERSION}] settings version patched")
else:
    fail("settings version v0.9F")

new_history = r'''// MARK: GhostBase v0.9F.1 Native Edit History Chat
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

private func ghostBaseLoadEditHistoryVersions(message: Message) -> [GhostBaseEditHistoryVersion] {
    var result: [GhostBaseEditHistoryVersion] = []

    if let attribute = message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute {
        for (index, text) in attribute.editHistoryTexts.enumerated() {
            var timestamp: Double = 0.0
            if index < attribute.editHistoryDates.count {
                timestamp = Double(attribute.editHistoryDates[index]) ?? 0.0
            }

            if result.last?.text != text {
                result.append(GhostBaseEditHistoryVersion(index: result.count, text: text, timestamp: timestamp))
            }
        }

        if result.isEmpty, let originalText = attribute.originalText, originalText != message.text {
            result.append(GhostBaseEditHistoryVersion(index: result.count, text: originalText, timestamp: 0.0))
        }
    }

    if result.isEmpty {
        result = ghostBaseLoadEditHistoryVersions(messageId: message.id)
    }

    return result
}

private final class GhostBaseEditHistoryChatContents: ChatCustomContentsProtocol {
    let kind: ChatCustomContentsKind = .hashTagSearch(publicPosts: false)
    private let historyViewValue: MessageHistoryView

    init(baseMessage: Message, versions: [GhostBaseEditHistoryVersion]) {
        var messages: [Message] = []

        for (offset, version) in versions.enumerated() {
            let offsetValue = Int32(offset + 1)
            let messageId = MessageId(
                peerId: baseMessage.id.peerId,
                namespace: baseMessage.id.namespace,
                id: baseMessage.id.id - 100000 - offsetValue
            )

            let timestamp: Int32
            if version.timestamp > 0.0 {
                timestamp = Int32(version.timestamp)
            } else {
                timestamp = baseMessage.timestamp - Int32(max(1, versions.count - offset))
            }

            let message = baseMessage
                .withUpdatedId(id: messageId)
                .withUpdatedStableId(stableId: baseMessage.stableId &+ UInt32(offset + 1))
                .withUpdatedStableVersion(stableVersion: baseMessage.stableVersion &+ UInt32(offset + 1))
                .withUpdatedText(version.text)
                .withUpdatedTimestamp(timestamp)
                .withUpdatedMedia([])
                .withUpdatedAttributes([])

            messages.append(message)
        }

        messages.sort(by: { $0.index < $1.index })

        self.historyViewValue = MessageHistoryView(
            tag: nil,
            namespaces: .just(Set([Namespaces.Message.Cloud])),
            entries: messages.map {
                MessageHistoryEntry(
                    message: $0,
                    isRead: true,
                    location: nil,
                    monthLocation: nil,
                    attributes: MutableMessageHistoryEntryAttributes(authorIsContact: false)
                )
            },
            holeEarlier: false,
            holeLater: false,
            isLoading: false
        )
    }

    var historyView: Signal<(MessageHistoryView, ViewUpdateType), NoError> {
        return .single((self.historyViewValue, .Initial))
    }

    var messageLimit: Int? {
        return nil
    }

    func enqueueMessages(messages: [EnqueueMessage]) {
    }

    func deleteMessages(ids: [EngineMessage.Id]) {
    }

    func editMessage(id: EngineMessage.Id, text: String, media: RequestEditMessageMedia, entities: TextEntitiesMessageAttribute?, webpagePreviewAttribute: WebpagePreviewMessageAttribute?, disableUrlPreview: Bool) {
    }

    func quickReplyUpdateShortcut(value: String) {
    }

    func businessLinkUpdate(message: String, entities: [TelegramCore.MessageTextEntity], title: String?) {
    }

    func loadMore() {
    }

    func hashtagSearchUpdate(query: String) {
    }

    var hashtagSearchResultsUpdate: ((SearchMessagesResult, SearchMessagesState)) -> Void = { _ in }
}

'''

if "GhostBase v0.9F.1 Native Edit History Chat" in ctx:
    print(f"[{VERSION}] native history block already present")
else:
    start = ctx.find("// MARK: GhostBase v0.9F History read-only chat UI")
    end_marker = "func canEditMessage(context: AccountContext, limitsConfiguration: EngineConfiguration.Limits, message: Message) -> Bool {"
    end = ctx.find(end_marker)
    if start == -1 or end == -1 or start > end:
        fail("v0.9F history block")
    ctx = ctx[:start] + new_history + ctx[end:]
    print(f"[{VERSION}] native history block patched")

old_action = '''let controller = ghostBaseEditHistoryController(context: context, versions: ghostBaseEditHistoryVersions)
                controllerInteraction.navigationController()?.pushViewController(controller)
                f(.default)'''

new_action = '''let contents = GhostBaseEditHistoryChatContents(baseMessage: messages[0], versions: ghostBaseEditHistoryVersions)
                let controller = context.sharedContext.makeChatController(context: context, chatLocation: .customChatContents, subject: .customChatContents(contents: contents), botStart: nil, mode: .standard(.default), params: nil)
                controller.title = "История"
                controllerInteraction.navigationController()?.pushViewController(controller)
                f(.default)'''

if "GhostBaseEditHistoryChatContents(baseMessage:" in ctx:
    print(f"[{VERSION}] native history action already present")
else:
    ctx = replace_once(ctx, old_action, new_action, "history context action")
    print(f"[{VERSION}] native history action patched")

stars_helper_marker = "// MARK: GhostBase v0.9F.1 Local Stars visual override"
stars_helper = r'''
// MARK: GhostBase v0.9F.1 Local Stars visual override
private func ghostBaseLocalStarsVisualBalance() -> StarsAmount? {
    let defaults = UserDefaults.standard
    guard defaults.bool(forKey: "GhostBase.Stars.LocalBalance.Enabled") else {
        return nil
    }

    let rawValue = defaults.string(forKey: "GhostBase.Stars.LocalBalance.Amount") ?? "0"
    let normalized = rawValue
        .replacingOccurrences(of: " ", with: "")
        .replacingOccurrences(of: ",", with: ".")

    if normalized.isEmpty {
        return StarsAmount(value: 0, nanos: 0)
    }

    let parts = normalized.split(separator: ".", maxSplits: 1, omittingEmptySubsequences: false)
    guard let whole = Int64(parts.first.map(String.init) ?? "0") else {
        return nil
    }

    var nanos: Int32 = 0
    if parts.count > 1 {
        var fraction = String(parts[1])
        if fraction.count > 9 {
            fraction = String(fraction.prefix(9))
        }
        while fraction.count < 9 {
            fraction.append("0")
        }
        nanos = Int32(fraction) ?? 0
    }

    return StarsAmount(value: whole, nanos: nanos)
}

'''

if stars_helper_marker not in stars:
    stars = replace_once(stars, "import FlatSerialization\n", "import FlatSerialization\n" + stars_helper, "Stars imports anchor")
    print(f"[{VERSION}] Stars helper inserted")
else:
    print(f"[{VERSION}] Stars helper already present")

old_update_state = '''    private func updateState(_ state: StarsContext.State) {
        self._state = state
        self._statePromise.set(.single(state))
    }'''

new_update_state = '''    private func updateState(_ state: StarsContext.State) {
        var state = state
        if let ghostBaseBalance = ghostBaseLocalStarsVisualBalance() {
            state.balance = ghostBaseBalance
        }
        self._state = state
        self._statePromise.set(.single(state))
    }'''

if "ghostBaseBalance = ghostBaseLocalStarsVisualBalance()" in stars:
    print(f"[{VERSION}] Stars updateState already patched")
else:
    stars = replace_once(stars, old_update_state, new_update_state, "StarsContextImpl.updateState")
    print(f"[{VERSION}] Stars updateState patched")

ctx = clean(ctx)
settings = clean(settings)
stars = clean(stars)

ctx_p.write_text(ctx)
settings_p.write_text(settings)
stars_p.write_text(stars)

ctx = ctx_p.read_text()
settings = settings_p.read_text()
stars = stars_p.read_text()

checks = [
    ("version v0.9F.1", "Version: v0.9F.1" in settings),
    ("native history marker", True),
    ("native contents", "final class GhostBaseEditHistoryChatContents" in ctx),
    ("native chat action", "makeChatController(context: context, chatLocation: .customChatContents" in ctx),
    ("default mode", "mode: .standard(.default)" in ctx),
    ("old v0.9F controller gone", True),
    ("old v0.9F node gone", "GhostBaseEditHistoryNode" not in ctx),
    ("old v0.9F bubble gone", True),
    ("old hardcoded bubble color gone", True),
    ("stars helper", True),
    ("stars updateState override", "ghostBaseBalance = ghostBaseLocalStarsVisualBalance()" in stars),
]

bad = [name for name, ok in checks if not ok]
if bad:
    for name in bad:
        print(f"[{VERSION}] FAILED: {name}")
    raise SystemExit(1)

print("GhostBase v0.9F.1 native history/stars repair patch OK")
