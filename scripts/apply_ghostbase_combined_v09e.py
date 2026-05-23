from pathlib import Path
import runpy
import re

VERSION = "v0.9E"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/TelegramEngine/Messages/DeleteMessagesInteractively.swift").exists():
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

def call_end(text: str, start: int) -> int:
    open_i = text.find("(", start)
    if open_i == -1:
        return -1

    depth = 0
    in_string = False
    escape = False

    for i in range(open_i, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    while end < len(text) and text[end] in " \t":
                        end += 1
                    if end < len(text) and text[end] == "\n":
                        end += 1
                    return end
    return -1

def collect_entry_calls(text: str) -> list[str]:
    calls = []
    pos = 0
    while True:
        start = text.find("entries.append(", pos)
        if start == -1:
            break
        end = call_end(text, start)
        if end == -1:
            break
        calls.append(text[start:end])
        pos = end
    return calls

def remove_entry_calls_containing(text: str, needle: str) -> tuple[str, int]:
    out = []
    pos = 0
    count = 0

    while True:
        start = text.find("entries.append(", pos)
        if start == -1:
            out.append(text[pos:])
            break

        end = call_end(text, start)
        if end == -1:
            out.append(text[pos:])
            break

        out.append(text[pos:start])
        call = text[start:end]

        if needle in call:
            count += 1
        else:
            out.append(call)

        pos = end

    return "".join(out), count

def relabel_entry_call(text: str, key: str, title: str) -> tuple[str, int]:
    out = []
    pos = 0
    count = 0

    while True:
        start = text.find("entries.append(", pos)
        if start == -1:
            out.append(text[pos:])
            break

        end = call_end(text, start)
        if end == -1:
            out.append(text[pos:])
            break

        out.append(text[pos:start])
        call = text[start:end]

        if key in call:
            new_call, n = re.subn(r'(' + re.escape(key) + r'\s*,\s*)"[^"]*"', r'\1"' + title + r'"', call, count=1)
            if n > 0:
                count += 1
                call = new_call

        out.append(call)
        pos = end

    return "".join(out), count

BASE = find_base()

prev = Path(__file__).with_name("apply_ghostbase_deleted_stars_recovery_v09d.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
delete_p = BASE / "submodules/TelegramCore/Sources/TelegramEngine/Messages/DeleteMessagesInteractively.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

# MARK: GhostBase v0.9E early full-skip
if settings_p.exists() and delete_p.exists() and ctx_p.exists():
    _settings0 = settings_p.read_text()
    _delete0 = delete_p.read_text()
    _ctx0 = ctx_p.read_text()
    if (
        "Version: v0.9E" in _settings0
        and "GhostBase v0.9E self-delete two-stage" in _delete0
        and "История изменений" in _ctx0
        and "Local Stars Balance" in _settings0
    ):
        print(f"[{VERSION}] v0.9E already fully applied; skip all replay")
        raise SystemExit(0)

if not settings_p.exists() or "Version: 0.9" not in settings_p.read_text():
    runpy.run_path(str(prev))
else:
    print(f"[{VERSION}] v0.9E already applied; skip prerequisite replay")

settings = settings_p.read_text()
delete_src = delete_p.read_text()
ctx = ctx_p.read_text()

if "Version: v0.9E" in settings:
    print(f"[{VERSION}] version already v0.9E")
elif "Version: v0.9D" in settings:
    print(f"[{VERSION}] patch settings version")
    settings = settings.replace("Version: v0.9D", "Version: v0.9E", 1)
else:
    fail("settings version")

old_call = "deleteMessagesInteractively(transaction: transaction, stateManager: account.stateManager, postbox: account.postbox, messageIds: messageIds, type: type, removeIfPossiblyDelivered: true)"
new_call = "deleteMessagesInteractively(transaction: transaction, stateManager: account.stateManager, postbox: account.postbox, messageIds: messageIds, type: type, removeIfPossiblyDelivered: true, accountPeerId: account.peerId)"
delete_src = replace_once(delete_src, old_call, new_call, "self-delete pass accountPeerId")

old_sig = "func deleteMessagesInteractively(transaction: Transaction, stateManager: AccountStateManager?, postbox: Postbox, messageIds initialMessageIds: [MessageId], type: InteractiveMessagesDeletionType, deleteAllInGroup: Bool = false, removeIfPossiblyDelivered: Bool) {"
new_sig = "func deleteMessagesInteractively(transaction: Transaction, stateManager: AccountStateManager?, postbox: Postbox, messageIds initialMessageIds: [MessageId], type: InteractiveMessagesDeletionType, deleteAllInGroup: Bool = false, removeIfPossiblyDelivered: Bool, accountPeerId: PeerId? = nil) {"
delete_src = replace_once(delete_src, old_sig, new_sig, "self-delete signature")

delete_src = clean(delete_src)

old_physical = r'''    _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: messageIds.map(\.messageId))

    stateManager?.notifyDeletedMessages(messageIds: messageIds.map(\.messageId))'''

new_physical = r'''    // MARK: GhostBase v0.9E self-delete two-stage
    var ghostBasePhysicalDeleteMessageIds: [MessageAndThreadId] = []
    for messageAndThreadId in messageIds {
        let messageId = messageAndThreadId.messageId
        if let accountPeerId = accountPeerId, let message = transaction.getMessage(messageId) {
            let isGhostBaseDeleted = ((message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false
            let isOwnMessage = (message.author?.id == accountPeerId) || !message.flags.contains(.Incoming)
            if isOwnMessage && !isGhostBaseDeleted {
                transaction.updateMessage(messageId, update: { currentMessage in
                    var updatedAttributes = currentMessage.attributes
                    if let existingIndex = updatedAttributes.firstIndex(where: { $0 is GhostBaseMessageAttribute }), let existingAttribute = updatedAttributes[existingIndex] as? GhostBaseMessageAttribute {
                        updatedAttributes[existingIndex] = existingAttribute.withUpdatedDeleted(isDeleted: true, deletedAt: currentMessage.timestamp)
                    } else {
                        updatedAttributes.append(GhostBaseMessageAttribute(originalText: currentMessage.text, editHistoryTexts: [], editHistoryDates: [], isDeleted: true, deletedAt: currentMessage.timestamp))
                    }

                    let storeForwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                    return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: currentMessage.text, attributes: updatedAttributes, media: currentMessage.media))
                })
                continue
            }
        }
        ghostBasePhysicalDeleteMessageIds.append(messageAndThreadId)
    }

    if !ghostBasePhysicalDeleteMessageIds.isEmpty {
        _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: ghostBasePhysicalDeleteMessageIds.map(\.messageId))
    }

    stateManager?.notifyDeletedMessages(messageIds: ghostBasePhysicalDeleteMessageIds.map(\.messageId))'''

if "GhostBase v0.9E self-delete two-stage" in delete_src:
    print(f"[{VERSION}] already patched: self-delete two-stage local physical delete filter")
else:
    delete_src = replace_once(delete_src, old_physical, new_physical, "self-delete two-stage local physical delete filter")

if 'title: .text("История изменений")' in ctx:
    print(f"[{VERSION}] already patched: edit-history title")
else:
    ctx = replace_once(ctx, 'title: .text("История")', 'title: .text("История изменений")', "edit-history title")

if "Ниже показаны старые версии сообщения" in ctx:
    print(f"[{VERSION}] already patched: edit-history info text")
else:
    ctx = replace_once(
        ctx,
        'entries.append(.info("История правок хранится локально и показывает только версии, которые клиент успел сохранить."))',
        'entries.append(.info("Ниже показаны старые версии сообщения, которые GhostBase успел сохранить локально."))',
        "edit-history info text"
    )

old_loop = '''    for version in versions {
        let time = ghostBaseEditHistoryTimeString(version.timestamp)
        let prefix: String
        if time.isEmpty {
            prefix = "Версия \\(version.index + 1)"
        } else {
            prefix = "\\(time)"
        }
        entries.append(.version(version.index, "\\(prefix)\\n\\(version.text)"))
    }'''

new_loop = '''    for version in versions {
        let time = ghostBaseEditHistoryTimeString(version.timestamp)
        let header: String
        if time.isEmpty {
            header = "Старая версия \\(version.index + 1)"
        } else {
            header = "Старая версия \\(version.index + 1) • \\(time)"
        }
        entries.append(.version(version.index, "\\(header)\\n\\n\\(version.text)"))
    }'''

if "Старая версия" in ctx:
    print(f"[{VERSION}] already patched: edit-history version cards")
else:
    ctx = replace_once(ctx, old_loop, new_loop, "edit-history version cards")

settings, removed_base = remove_entry_calls_containing(settings, "GhostBaseKey.localStarsBaseAmount")
settings, removed_preview = remove_entry_calls_containing(settings, "ghostBaseStarsTransactionPreview")
settings, relabeled_amount = relabel_entry_call(settings, "GhostBaseKey.localStarsAmount", "Local Stars Balance")

entry_calls = "\n".join(collect_entry_calls(settings))
if "GhostBaseKey.localStarsBaseAmount" in entry_calls:
    fail("Stars base amount input UI")
if "ghostBaseStarsTransactionPreview" in entry_calls:
    fail("Stars transaction preview UI")
if "Local Stars Balance" not in entry_calls:
    fail("Stars local amount input UI")

print(f"[{VERSION}] patch Stars one-field UI: removed_base={removed_base}, removed_preview={removed_preview}, relabeled_amount={relabeled_amount}")

settings_p.write_text(clean(settings))
delete_p.write_text(clean(delete_src))
ctx_p.write_text(clean(ctx))

settings = settings_p.read_text()
delete_src = delete_p.read_text()
ctx = ctx_p.read_text()
entry_calls = "\n".join(collect_entry_calls(settings))

checks = [
    ("version v0.9E", "Version: v0.9E" in settings),
    ("self-delete marker", "GhostBase v0.9E self-delete two-stage" in delete_src),
    ("accountPeerId signature", "accountPeerId: PeerId? = nil" in delete_src),
    ("accountPeerId call", "accountPeerId: account.peerId" in delete_src),
    ("physical delete filtered", "ghostBasePhysicalDeleteMessageIds" in delete_src),
    ("edit-history title", 'title: .text("История изменений")' in ctx),
    ("edit-history cards", "Старая версия" in ctx),
    ("stars one amount label", "Local Stars Balance" in entry_calls),
    ("stars base input UI removed", "GhostBaseKey.localStarsBaseAmount" not in entry_calls),
    ("stars preview UI removed", "ghostBaseStarsTransactionPreview" not in entry_calls),
]

bad = [name for name, ok in checks if not ok]
if bad:
    for name in bad:
        print(f"[{VERSION}] FAILED: {name}")
    raise SystemExit(1)

print("GhostBase Combined v0.9E patch OK")
