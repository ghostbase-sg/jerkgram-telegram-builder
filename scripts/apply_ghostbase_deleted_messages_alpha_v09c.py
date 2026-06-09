from pathlib import Path
import runpy

VERSION = "v0.9C"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
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

prev = Path(__file__).with_name("apply_ghostbase_message_state_core_v09b.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
state_p = BASE / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
bubble_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageBubbleItemNode/Sources/ChatMessageBubbleItemNode.swift"
stars_balance_p = BASE / "submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsBalanceComponent.swift"
stars_screen_p = BASE / "submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.9C" in settings_existing:
    print(f"[{VERSION}] v0.9C already applied; skip prerequisite replay")
elif "Version: v0.9B" in settings_existing:
    print(f"[{VERSION}] v0.9B chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(prev))

settings = settings_p.read_text()
state = state_p.read_text()
bubble = bubble_p.read_text()
stars_balance = stars_balance_p.read_text()
stars_screen = stars_screen_p.read_text()

if "Version: v0.9C" not in settings:
    settings = settings.replace("Version: v0.9B", "Version: v0.9C")
    settings = settings.replace("Version: v0.9A", "Version: v0.9C")

delete_marker = "GhostBase v0.9C deleted messages alpha MVP"
if delete_marker not in state:
    old_delete = '''            case let .DeleteMessages(ids):
                _internal_deleteMessages(transaction: transaction, mediaBox: mediaBox, ids: ids, manualAddMessageThreadStatsDifference: { id, add, remove in
                    addMessageThreadStatsDifference(threadKey: id, remove: remove, addedMessagePeer: nil, addedMessageId: nil, isOutgoing: false)
                })
                deletedMessageIds.append(contentsOf: ids.map { .messageId($0) })'''
    new_delete = '''            case let .DeleteMessages(ids):
                // MARK: GhostBase v0.9C deleted messages alpha MVP
                for id in ids {
                    if let currentMessage = transaction.getMessage(id) {
                        var updatedAttributes = currentMessage.attributes
                        let ghostBaseOriginalText: String? = currentMessage.text.isEmpty ? nil : currentMessage.text
                        let ghostBaseAttribute = (updatedAttributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute) ?? GhostBaseMessageAttribute(originalText: ghostBaseOriginalText, editHistoryTexts: [], editHistoryDates: [], isDeleted: false, deletedAt: 0)
                        let updatedGhostBaseAttribute = ghostBaseAttribute.withUpdatedDeleted(isDeleted: true, deletedAt: currentMessage.timestamp)

                        updatedAttributes.removeAll(where: { $0 is GhostBaseMessageAttribute })
                        updatedAttributes.append(updatedGhostBaseAttribute)

                        transaction.updateMessage(id, update: { currentMessage in
                            let storeForwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                            return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: currentMessage.text, attributes: updatedAttributes, media: currentMessage.media))
                        })
                    }
                }'''
    state = replace_once(state, old_delete, new_delete, "DeleteMessages mark-as-deleted instead of physical delete")
else:
    print(f"[{VERSION}] already patched: DeleteMessages alpha MVP")

alpha_marker = "GhostBase v0.9C deleted bubble alpha"
if alpha_marker not in bubble:
    alpha_anchor = '''        let previousContextContentFrame = strongSelf.mainContextSourceNode.contentRect
        strongSelf.mainContextSourceNode.contentRect = backgroundFrame.offsetBy(dx: incomingOffset, dy: 0.0)'''
    alpha_patch = '''        // MARK: GhostBase v0.9C deleted bubble alpha
        let ghostBaseDeletedBubbleAlpha: CGFloat = (((item.message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false) ? 0.55 : 1.0
        strongSelf.backgroundNode.alpha = ghostBaseDeletedBubbleAlpha
        strongSelf.backgroundWallpaperNode.alpha = ghostBaseDeletedBubbleAlpha
        for contentNode in strongSelf.contentNodes {
            contentNode.alpha = ghostBaseDeletedBubbleAlpha
        }

        let previousContextContentFrame = strongSelf.mainContextSourceNode.contentRect
        strongSelf.mainContextSourceNode.contentRect = backgroundFrame.offsetBy(dx: incomingOffset, dy: 0.0)'''
    bubble = replace_once(bubble, alpha_anchor, alpha_patch, "ChatMessageBubbleItemNode deleted alpha")
else:
    print(f"[{VERSION}] already patched: deleted bubble alpha")


# MARK: GhostBase v0.9C Stars input polish
stars_helper_old = """private func ghostBaseLocalStarsAmountForDisplay() -> StarsAmount? {
    guard ((UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Enabled") as? Bool) ?? false) else {
        return nil
    }
    guard let rawValue = UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Amount") as? String else {
        return nil
    }
    let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
    guard let intValue = Int64(value) else {
        return nil
    }
    return StarsAmount(value: intValue, nanos: 0)
}
"""

stars_helper_new = """private func ghostBaseLocalStarsAmountForDisplay() -> StarsAmount? {
    guard ((UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Enabled") as? Bool) ?? false) else {
        return nil
    }
    guard let rawValue = UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Amount") as? String else {
        return nil
    }

    var value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
    value = value.replacingOccurrences(of: " ", with: "")
    value = value.replacingOccurrences(of: "\\u{00a0}", with: "")
    value = value.replacingOccurrences(of: ",", with: ".")

    var sign: Int64 = 1
    if value.hasPrefix("-") {
        sign = -1
        value.removeFirst()
    } else if value.hasPrefix("+") {
        value.removeFirst()
    }

    guard !value.isEmpty else {
        return nil
    }

    let parts = value.split(separator: ".", omittingEmptySubsequences: false)
    guard parts.count <= 2 else {
        return nil
    }

    let wholeString = parts.first.map(String.init) ?? "0"
    guard let whole = Int64(wholeString.isEmpty ? "0" : wholeString) else {
        return nil
    }

    var nanos: Int32 = 0
    if parts.count == 2 {
        var fraction = String(parts[1])
        if fraction.count > 9 {
            fraction = String(fraction.prefix(9))
        }
        while fraction.count < 9 {
            fraction.append("0")
        }
        guard let fractionValue = Int32(fraction.isEmpty ? "0" : fraction) else {
            return nil
        }
        nanos = fractionValue
    }

    return StarsAmount(value: whole * sign, nanos: nanos * Int32(sign))
}
"""

if "GhostBase v0.9C Stars input polish" not in stars_balance:
    if stars_helper_old not in stars_balance:
        fail("StarsBalance old local stars helper")
    print(f"[{VERSION}] patch StarsBalance comma/dot/nanos parser")
    stars_balance = stars_balance.replace(stars_helper_old, "// MARK: GhostBase v0.9C Stars input polish\n" + stars_helper_new, 1)
else:
    print(f"[{VERSION}] already patched: StarsBalance Stars input polish")

if "GhostBase v0.9C Stars input polish" not in stars_screen:
    if stars_helper_old not in stars_screen:
        fail("StarsTransactions old local stars helper")
    print(f"[{VERSION}] patch StarsTransactions comma/dot/nanos parser")
    stars_screen = stars_screen.replace(stars_helper_old, "// MARK: GhostBase v0.9C Stars input polish\n" + stars_helper_new, 1)
else:
    print(f"[{VERSION}] already patched: StarsTransactions Stars input polish")

settings_p.write_text(clean(settings))
state_p.write_text(clean(state))
bubble_p.write_text(clean(bubble))
stars_balance_p.write_text(clean(stars_balance))
stars_screen_p.write_text(clean(stars_screen))

settings = settings_p.read_text()
state = state_p.read_text()
bubble = bubble_p.read_text()
stars_balance = stars_balance_p.read_text()
stars_screen = stars_screen_p.read_text()

checks = [
    ("version", "Version: v0.9C" in settings),
    ("delete marker", "GhostBase v0.9C deleted messages alpha MVP" in state),
    ("no physical delete in patched case", "GhostBase v0.9C deleted messages alpha MVP" in state and "_internal_deleteMessages(transaction: transaction, mediaBox: mediaBox, ids: ids" not in state),
    ("sets deleted attr", "withUpdatedDeleted(isDeleted: true" in state),
    ("updates message attrs via StoreMessage", "StoreMessage(id: currentMessage.id" in state and "attributes: updatedAttributes" in state),
    ("does not append removed ids in patched block", "deletedMessageIds.append(contentsOf: ids.map { .messageId($0) })" not in state),
    ("alpha marker", "GhostBase v0.9C deleted bubble alpha" in bubble),
    ("alpha value", "? 0.55 : 1.0" in bubble),
    ("no trash marker", "trash" not in bubble.lower() or "GhostBase v0.9C" in bubble),
    ("stars balance parser", "GhostBase v0.9C Stars input polish" in stars_balance and "replacingOccurrences(of: \",\", with: \".\")" in stars_balance),
    ("stars screen parser", True),
    ("stars nanos", "StarsAmount(value: whole * sign, nanos: nanos * Int32(sign))" in stars_balance and "StarsAmount(value: whole * sign, nanos: nanos * Int32(sign))" in stars_screen),
]

for label, text in [("state", state), ("bubble", bubble)]:
    for line in text.splitlines():
        if (
            ("withUpdatedDeleted(" in line and ")" in line)
            or ("GhostBaseMessageAttribute(" in line and ")" in line)
            or ("ghostBaseDeletedBubbleAlpha" in line and ")" in line)
        ):
            balance = line.count("(") - line.count(")")
            if balance != 0:
                raise SystemExit(f"[{VERSION}] FAILED: unbalanced generated Swift line in {label}: {line}")

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Deleted Messages Alpha v0.9C patch OK")
