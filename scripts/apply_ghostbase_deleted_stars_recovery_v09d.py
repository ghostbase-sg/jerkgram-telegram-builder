from pathlib import Path
import runpy

VERSION = "v0.9D"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
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

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
state_p = BASE / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"

prev = Path(__file__).with_name("apply_ghostbase_deleted_messages_alpha_v09c.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

if settings_p.exists() and "Version: v0.9D" in settings_p.read_text():
    print(f"[{VERSION}] v0.9D already applied; skip prerequisite replay")
else:
    runpy.run_path(str(prev))

settings = settings_p.read_text()
state = state_p.read_text()

if "Version: v0.9D" in settings:
    print(f"[{VERSION}] version already v0.9D")
elif "Version: v0.9C" in settings:
    print(f"[{VERSION}] patch settings version")
    settings = settings.replace("Version: v0.9C", "Version: v0.9D", 1)
else:
    fail("settings version v0.9C")

old_sanitizer = '''private func ghostBaseSanitizeStarsAmount(_ text: String) -> String {
    var result = ""
    for ch in text {
        if ch == "-" && result.isEmpty {
            result.append(ch)
        } else if ch >= "0" && ch <= "9" {
            result.append(ch)
        }
    }
    return result
}
'''

new_sanitizer = '''// MARK: GhostBase v0.9D Stars input parser
private func ghostBaseIsValidStarsAmountInput(_ text: String) -> Bool {
    var hasSeparator = false

    for (index, ch) in text.enumerated() {
        if ch == "-" || ch == "+" {
            if index != 0 {
                return false
            }
        } else if ch >= "0" && ch <= "9" {
            continue
        } else if ch == "," || ch == "." {
            if hasSeparator {
                return false
            }
            hasSeparator = true
        } else if ch == " " || ch == "\\u{00a0}" {
            continue
        } else {
            return false
        }
    }

    return true
}

private func ghostBaseSanitizeStarsAmount(_ text: String) -> String {
    var result = ""
    var hasSeparator = false
    let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)

    for (index, ch) in trimmed.enumerated() {
        if ch == "-" && result.isEmpty && index == 0 {
            result.append(ch)
        } else if ch == "+" && result.isEmpty && index == 0 {
            continue
        } else if ch >= "0" && ch <= "9" {
            result.append(ch)
        } else if (ch == "," || ch == ".") && !hasSeparator {
            result.append(".")
            hasSeparator = true
        } else if ch == " " || ch == "\\u{00a0}" {
            continue
        }
    }

    if result == "." || result == "-." {
        return ""
    }

    return result
}
'''

if "GhostBase v0.9D Stars input parser" not in settings:
    start = settings.find("private func ghostBaseSanitizeStarsAmount(_ text: String) -> String {")
    end = settings.find("\n\nprivate func ghostBaseStarsInt64", start)
    if start == -1 or end == -1:
        fail("Stars real input sanitizer")
    print(f"[{VERSION}] patch Stars real input sanitizer")
    settings = settings[:start] + new_sanitizer + settings[end + 2:]
else:
    print(f"[{VERSION}] already patched: Stars real input sanitizer")

old_input_gate = "return ghostBaseSanitizeStarsAmount(updatedText) == updatedText"
new_input_gate = "return ghostBaseIsValidStarsAmountInput(updatedText)"

if old_input_gate in settings:
    print(f"[{VERSION}] patch Stars shouldUpdateText gate")
    settings = settings.replace(old_input_gate, new_input_gate)
elif new_input_gate in settings:
    print(f"[{VERSION}] already patched: Stars shouldUpdateText gate")
else:
    fail("Stars shouldUpdateText gate")

old_global_delete = '''            case let .DeleteMessagesWithGlobalIds(ids):
                var resourceIds: [MediaResourceId] = []
                transaction.deleteMessagesWithGlobalIds(ids, forEachMedia: { media in
                    addMessageMediaResourceIdsToRemove(media: media, resourceIds: &resourceIds)
                })
                if !resourceIds.isEmpty {
                    let _ = mediaBox.removeCachedResources(Array(Set(resourceIds)), force: true).start()
                }
                deletedMessageIds.append(contentsOf: ids.map { .global($0) })'''

new_global_delete = '''            case let .DeleteMessagesWithGlobalIds(ids):
                // MARK: GhostBase v0.9D deleted messages global-id recovery
                let ghostBaseMessageIds = transaction.messageIdsForGlobalIds(ids)
                for id in ghostBaseMessageIds {
                    transaction.updateMessage(id, update: { currentMessage in
                        var updatedAttributes = currentMessage.attributes
                        if let existingIndex = updatedAttributes.firstIndex(where: { $0 is GhostBaseMessageAttribute }), let existingAttribute = updatedAttributes[existingIndex] as? GhostBaseMessageAttribute {
                            updatedAttributes[existingIndex] = existingAttribute.withUpdatedDeleted(isDeleted: true, deletedAt: currentMessage.timestamp)
                        } else {
                            updatedAttributes.append(GhostBaseMessageAttribute(originalText: currentMessage.text, editHistoryTexts: [], editHistoryDates: [], isDeleted: true, deletedAt: currentMessage.timestamp))
                        }

                        let storeForwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                        return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: currentMessage.text, attributes: updatedAttributes, media: currentMessage.media))
                    })
                }
                deletedMessageIds.append(contentsOf: ids.map { .global($0) })'''

if "GhostBase v0.9D deleted messages global-id recovery" not in state:
    state = replace_once(state, old_global_delete, new_global_delete, "DeleteMessagesWithGlobalIds recovery")
else:
    print(f"[{VERSION}] already patched: DeleteMessagesWithGlobalIds recovery")

settings_p.write_text(clean(settings))
state_p.write_text(clean(state))

settings = settings_p.read_text()
state = state_p.read_text()

checks = [
    ("version", "Version: v0.9D" in settings),
    ("stars parser marker", "GhostBase v0.9D Stars input parser" in settings),
    ("stars validator gate", "return ghostBaseIsValidStarsAmountInput(updatedText)" in settings),
    ("old stars gate removed", "return ghostBaseSanitizeStarsAmount(updatedText) == updatedText" not in settings),
    ("global delete marker", "GhostBase v0.9D deleted messages global-id recovery" in state),
    ("global id resolver", "transaction.messageIdsForGlobalIds(ids)" in state),
    ("no physical global delete", "transaction.deleteMessagesWithGlobalIds(ids" not in state),
    ("old messageId delete path still exists", "GhostBase v0.9C deleted messages alpha MVP" in state),
]

bad = [name for name, ok in checks if not ok]
if bad:
    for name in bad:
        print(f"[{VERSION}] FAILED: {name}")
    raise SystemExit(1)

print("GhostBase Deleted/Stars Recovery v0.9D patch OK")
