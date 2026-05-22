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

                        transaction.updateMessage(id, update: { message in
                            return .update(message.withUpdatedAttributes(updatedAttributes))
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

settings_p.write_text(clean(settings))
state_p.write_text(clean(state))
bubble_p.write_text(clean(bubble))

settings = settings_p.read_text()
state = state_p.read_text()
bubble = bubble_p.read_text()

checks = [
    ("version", "Version: v0.9C" in settings),
    ("delete marker", "GhostBase v0.9C deleted messages alpha MVP" in state),
    ("no physical delete in patched case", "GhostBase v0.9C deleted messages alpha MVP" in state and "_internal_deleteMessages(transaction: transaction, mediaBox: mediaBox, ids: ids" not in state),
    ("sets deleted attr", "withUpdatedDeleted(isDeleted: true" in state),
    ("updates message attrs", "message.withUpdatedAttributes(updatedAttributes)" in state),
    ("does not append removed ids in patched block", "deletedMessageIds.append(contentsOf: ids.map { .messageId($0) })" not in state),
    ("alpha marker", "GhostBase v0.9C deleted bubble alpha" in bubble),
    ("alpha value", "? 0.55 : 1.0" in bubble),
    ("no trash marker", "trash" not in bubble.lower() or "GhostBase v0.9C" in bubble),
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
