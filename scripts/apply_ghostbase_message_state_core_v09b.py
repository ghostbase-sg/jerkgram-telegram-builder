from pathlib import Path
import runpy

VERSION = "v0.9B"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
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

prev = Path(__file__).with_name("apply_ghostbase_edit_history_v09a.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
attr_p = BASE / "submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift"
account_manager_p = BASE / "submodules/TelegramCore/Sources/Account/AccountManager.swift"
state_p = BASE / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.9B" in settings_existing:
    print(f"[{VERSION}] v0.9B already applied; skip prerequisite replay")
elif "Version: v0.9A" in settings_existing:
    print(f"[{VERSION}] v0.9A chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(prev))

settings = settings_p.read_text()
account_manager = account_manager_p.read_text()
state = state_p.read_text()
ctx = ctx_p.read_text()

if "Version: v0.9B" not in settings:
    settings = settings.replace("Version: v0.9A", "Version: v0.9B")
    settings = settings.replace("Version: v0.8I.2", "Version: v0.9B")

attr_source = '''import Foundation
import Postbox

public final class GhostBaseMessageAttribute: MessageAttribute {
    public let originalText: String?
    public let editHistoryTexts: [String]
    public let editHistoryDates: [String]
    public let isDeleted: Bool
    public let deletedAt: Int32

    public init(originalText: String?, editHistoryTexts: [String], editHistoryDates: [String], isDeleted: Bool, deletedAt: Int32) {
        self.originalText = originalText
        self.editHistoryTexts = editHistoryTexts
        self.editHistoryDates = editHistoryDates
        self.isDeleted = isDeleted
        self.deletedAt = deletedAt
    }

    required public init(decoder: PostboxDecoder) {
        self.originalText = decoder.decodeOptionalStringForKey("ot")
        self.editHistoryTexts = decoder.decodeStringArrayForKey("eht")
        self.editHistoryDates = decoder.decodeStringArrayForKey("ehd")
        self.isDeleted = decoder.decodeInt32ForKey("del", orElse: 0) != 0
        self.deletedAt = decoder.decodeInt32ForKey("dat", orElse: 0)
    }

    public func encode(_ encoder: PostboxEncoder) {
        if let originalText = self.originalText {
            encoder.encodeString(originalText, forKey: "ot")
        }
        encoder.encodeStringArray(self.editHistoryTexts, forKey: "eht")
        encoder.encodeStringArray(self.editHistoryDates, forKey: "ehd")
        encoder.encodeInt32(self.isDeleted ? 1 : 0, forKey: "del")
        encoder.encodeInt32(self.deletedAt, forKey: "dat")
    }

    public func withAddedEditVersion(text: String, date: Int32) -> GhostBaseMessageAttribute {
        var texts = self.editHistoryTexts
        var dates = self.editHistoryDates

        if texts.last != text {
            texts.append(text)
            dates.append(String(date))

            if texts.count > 30 {
                texts = Array(texts.suffix(30))
                dates = Array(dates.suffix(30))
            }
        }

        return GhostBaseMessageAttribute(
            originalText: self.originalText ?? text,
            editHistoryTexts: texts,
            editHistoryDates: dates,
            isDeleted: self.isDeleted,
            deletedAt: self.deletedAt
        )
    }

    public func withUpdatedDeleted(isDeleted: Bool, deletedAt: Int32) -> GhostBaseMessageAttribute {
        return GhostBaseMessageAttribute(
            originalText: self.originalText,
            editHistoryTexts: self.editHistoryTexts,
            editHistoryDates: self.editHistoryDates,
            isDeleted: isDeleted,
            deletedAt: deletedAt
        )
    }
}
'''

if attr_p.exists() and "public final class GhostBaseMessageAttribute" in attr_p.read_text(errors="ignore"):
    print(f"[{VERSION}] already patched: GhostBaseMessageAttribute file")
else:
    print(f"[{VERSION}] write GhostBaseMessageAttribute file")
    attr_p.write_text(clean(attr_source))

if "declareEncodable(GhostBaseMessageAttribute.self" not in account_manager:
    account_manager = replace_once(
        account_manager,
        "    declareEncodable(EditedMessageAttribute.self, f: { EditedMessageAttribute(decoder: $0) })\n",
        "    declareEncodable(EditedMessageAttribute.self, f: { EditedMessageAttribute(decoder: $0) })\n    declareEncodable(GhostBaseMessageAttribute.self, f: { GhostBaseMessageAttribute(decoder: $0) })\n",
        "AccountManager GhostBaseMessageAttribute registration"
    )
else:
    print(f"[{VERSION}] already patched: AccountManager registration")

edit_marker = "GhostBase v0.9B edit history attribute state"
if edit_marker not in state:
    edit_anchor = '''                    if let previousFactCheckAttribute = previousMessage.attributes.first(where: { $0 is FactCheckMessageAttribute }) as? FactCheckMessageAttribute, let updatedFactCheckAttribute = message.attributes.first(where: { $0 is FactCheckMessageAttribute }) as? FactCheckMessageAttribute {'''
    edit_patch = '''                    // MARK: GhostBase v0.9B edit history attribute state
                    if previousMessage.text != message.text && !previousMessage.text.isEmpty {
                        let editDate = (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp
                        var ghostBaseAttribute = previousMessage.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute
                        if ghostBaseAttribute == nil {
                            ghostBaseAttribute = GhostBaseMessageAttribute(originalText: previousMessage.text, editHistoryTexts: [], editHistoryDates: [], isDeleted: false, deletedAt: 0)
                        }
                        if let updatedGhostBaseAttribute = ghostBaseAttribute?.withAddedEditVersion(text: previousMessage.text, date: editDate) {
                            updatedAttributes.removeAll(where: { $0 is GhostBaseMessageAttribute })
                            updatedAttributes.append(updatedGhostBaseAttribute)
                        }
                    }

                    if let previousFactCheckAttribute = previousMessage.attributes.first(where: { $0 is FactCheckMessageAttribute }) as? FactCheckMessageAttribute, let updatedFactCheckAttribute = message.attributes.first(where: { $0 is FactCheckMessageAttribute }) as? FactCheckMessageAttribute {'''
    if edit_anchor not in state:
        fail("EditMessage GhostBase attribute insertion")
    print(f"[{VERSION}] patch EditMessage GhostBase attribute state")
    state = state.replace(edit_anchor, edit_patch, 1)
else:
    print(f"[{VERSION}] already patched: EditMessage GhostBase attribute state")

ui_marker = "GhostBase v0.9B message-state loader"
ui_overload = r'''// MARK: GhostBase v0.9B message-state loader
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

'''

if ui_marker not in ctx:
    ui_anchor = "private enum GhostBaseEditHistorySection: Int32 {"
    if ui_anchor not in ctx:
        fail("v0.9A UI helper enum anchor")
    print(f"[{VERSION}] patch v0.9B message-state UI loader")
    ctx = ctx.replace(ui_anchor, ui_overload + ui_anchor, 1)
else:
    print(f"[{VERSION}] already patched: v0.9B message-state UI loader")

if "ghostBaseLoadEditHistoryVersions(message: messages[0])" not in ctx:
    ctx = replace_once(
        ctx,
        "        let ghostBaseEditHistoryVersions = ghostBaseLoadEditHistoryVersions(messageId: messages[0].id)\n",
        "        let ghostBaseEditHistoryVersions = ghostBaseLoadEditHistoryVersions(message: messages[0])\n",
        "context menu action read message-state attribute"
    )
else:
    print(f"[{VERSION}] already patched: context menu action reads message-state")

settings_p.write_text(clean(settings))
account_manager_p.write_text(clean(account_manager))
state_p.write_text(clean(state))
ctx_p.write_text(clean(ctx))

settings = settings_p.read_text()
attr = attr_p.read_text()
account_manager = account_manager_p.read_text()
state = state_p.read_text()
ctx = ctx_p.read_text()

checks = [
    ("version", "Version: v0.9B" in settings),
    ("attribute file", "public final class GhostBaseMessageAttribute" in attr),
    ("string array decode", "decodeStringArrayForKey" in attr),
    ("registration", "declareEncodable(GhostBaseMessageAttribute.self" in account_manager),
    ("edit path marker", "GhostBase v0.9B edit history attribute state" in state),
    ("edit path append", "updatedAttributes.append(updatedGhostBaseAttribute)" in state),
    ("ui loader", True),
    ("ui reads attribute", True),
    ("action uses message", "ghostBaseLoadEditHistoryVersions(message: messages[0])" in ctx),
    ("old action removed", "ghostBaseLoadEditHistoryVersions(messageId: messages[0].id)" not in ctx),
]

for generated_text, generated_label in [(attr, "attr"), (state, "state"), (ctx, "ctx")]:
    for line in generated_text.splitlines():
        if (
            ("GhostBaseMessageAttribute(" in line and ")" in line)
            or "ghostBaseLoadEditHistoryVersions(" in line
            or "withAddedEditVersion(" in line
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

print("GhostBase Message State Core v0.9B patch OK")
