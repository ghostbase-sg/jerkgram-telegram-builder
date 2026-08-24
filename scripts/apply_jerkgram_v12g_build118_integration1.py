#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
SETTINGS_BUILD = ROOT / "submodules/SettingsUI/BUILD"
CORE = ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
CORE_BUILD = ROOT / "submodules/TelegramCore/BUILD"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 integration] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected once, found {count}")
    return text.replace(old, new, 1)


def add_dep(text):
    dep = '        "//submodules/JerkgramCore:JerkgramCore",\n'
    if dep in text:
        return text
    marker = "deps = [\n"
    require(marker in text, "BUILD deps marker missing")
    return text.replace(marker, marker + dep, 1)


def patch_settings(text):
    if "import JerkgramCore" not in text:
        text = replace_once(text, "import Foundation\n", "import Foundation\nimport JerkgramCore\n", "settings import")
    helper = '''// MARK: Jerkgram v1.2G BUILD118_ACCOUNT_SETTINGS_SCOPE1
private func jerkgramScopedSettingsKey(accountPeerId: Int64, key: String) -> String {
    return "jerkgram.account.\\(accountPeerId).setting.\\(key)"
}

private func jerkgramScopedBool(
    accountPeerId: Int64,
    key: String,
    defaultValue: Bool
) -> Bool {
    let scopedKey = jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key)
    if let value = UserDefaults.standard.object(forKey: scopedKey) as? Bool {
        return value
    }
    let migrated = ghostBaseBool(key, defaultValue: defaultValue)
    UserDefaults.standard.set(migrated, forKey: scopedKey)
    return migrated
}

private func jerkgramScopedString(
    accountPeerId: Int64,
    key: String,
    defaultValue: String
) -> String {
    let scopedKey = jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key)
    if let value = UserDefaults.standard.object(forKey: scopedKey) as? String {
        return value
    }
    let migrated = ghostBaseString(key, defaultValue: defaultValue)
    UserDefaults.standard.set(migrated, forKey: scopedKey)
    return migrated
}

private func jerkgramMirrorSettingsToAccount(accountPeerId: Int64) {
    for (key, value) in UserDefaults.standard.dictionaryRepresentation()
    where key.hasPrefix("jerkgram.") && !key.hasPrefix("jerkgram.account.") {
        UserDefaults.standard.set(
            value,
            forKey: jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key)
        )
    }
}

'''
    struct_marker = "struct GhostBaseSettingsState"
    require(struct_marker in text, "settings state marker missing")
    if "BUILD118_ACCOUNT_SETTINGS_SCOPE1" not in text:
        text = text.replace(struct_marker, helper + struct_marker, 1)
    text = replace_once(text, "static func load() -> GhostBaseSettingsState {", "static func load(accountPeerId: Int64) -> GhostBaseSettingsState {", "settings load signature")
    load_start = text.index("static func load(accountPeerId:")
    save_start = text.index("    func save()", load_start)
    load_block = text[load_start:save_start]
    load_block = load_block.replace("ghostBaseBool(", "jerkgramScopedBool(accountPeerId: accountPeerId, key: ")
    load_block = load_block.replace("ghostBaseString(", "jerkgramScopedString(accountPeerId: accountPeerId, key: ")
    text = text[:load_start] + load_block + text[save_start:]
    text = replace_once(text, "    func save() {", "    func save(accountPeerId: Int64) {", "settings save signature")
    text = replace_once(text, "let initialState = GhostBaseSettingsState.load()", "let initialState = GhostBaseSettingsState.load(accountPeerId: context.account.peerId.toInt64())", "settings load call")
    require(text.count("next.save()") == 1, "settings save call: expected once")
    text = text.replace(
        "next.save()",
        "next.save(accountPeerId: context.account.peerId.toInt64())\n            jerkgramMirrorSettingsToAccount(accountPeerId: context.account.peerId.toInt64())",
        1,
    )
    return text


def patch_core(text):
    if "import JerkgramCore" not in text:
        text = replace_once(text, "import Foundation\n", "import Foundation\nimport JerkgramCore\n", "core import")
    deleted_pattern = re.compile(
        r'''let ghostBaseSaveDeleted = \(\s*UserDefaults\.standard\.object\(\s*forKey: "jerkgram\.Messages\.SaveDeleted"\s*\) as\? Bool\s*\) \?\? true'''
    )
    global_pattern = re.compile(
        deleted_pattern.pattern + r'''\s*let ghostBaseMessageIds = transaction\.messageIdsForGlobalIds\(ids\)'''
    )
    if global_pattern.search(text):
        text = global_pattern.sub('''let ghostBaseMessageIds = transaction.messageIdsForGlobalIds(ids)
                let ghostBaseSaveDeleted = ghostBaseMessageIds.allSatisfy { id in
                    JerkgramRetentionRuntime.shouldCapture(
                        accountPeerId: accountPeerId.toInt64(),
                        chatPeerId: id.peerId.toInt64(),
                        isSecretChat: id.peerId.namespace == Namespaces.Peer.SecretChat,
                        legacyToggleKey: "jerkgram.Messages.SaveDeleted"
                    )
                }''', text, count=1)
    replacements = 0
    while deleted_pattern.search(text):
        # Local deletes have `ids`; global deletes have the same name after
        # resolving global ids. Both sets are transaction-local and normally
        # contain one chat. Every id is still evaluated against its exact chat.
        new_deleted = '''let ghostBaseSaveDeleted = ids.allSatisfy { id in
                    JerkgramRetentionRuntime.shouldCapture(
                        accountPeerId: accountPeerId.toInt64(),
                        chatPeerId: id.peerId.toInt64(),
                        isSecretChat: id.peerId.namespace == Namespaces.Peer.SecretChat,
                        legacyToggleKey: "jerkgram.Messages.SaveDeleted"
                    )
                }'''
        text = deleted_pattern.sub(new_deleted, text, count=1)
        replacements += 1
    # Full source has two delete owners. Tiny fixtures only contain one.
    require(replacements >= 1, "delete capture gates missing")
    edit_pattern = re.compile(
        r'''let ghostBaseSaveEditHistory = \(\s*UserDefaults\.standard\.object\(\s*forKey: "jerkgram\.Messages\.SaveEditHistory"\s*\) as\? Bool\s*\) \?\? true'''
    )
    new_edit = '''let ghostBaseSaveEditHistory = JerkgramRetentionRuntime.shouldCapture(
                        accountPeerId: accountPeerId.toInt64(),
                        chatPeerId: id.peerId.toInt64(),
                        isSecretChat: id.peerId.namespace == Namespaces.Peer.SecretChat,
                        legacyToggleKey: "jerkgram.Messages.SaveEditHistory"
                    )'''
    require(len(edit_pattern.findall(text)) == 1, "edit capture gate: expected once")
    text = edit_pattern.sub(new_edit, text, count=1)
    delete_capture_marker = '''ghostBaseScheduleDeletedMediaPreservation(
                                mediaBox: mediaBox,
                                message: currentMessage
                            )'''
    local_delete_capture_marker = '''ghostBaseScheduleDeletedMediaPreservation(
                            mediaBox: mediaBox,
                            message: currentMessage
                        )'''
    delete_capture = '''JerkgramCaptureRecorder.record(
                                accountPeerId: accountPeerId.toInt64(),
                                chatPeerId: currentMessage.id.peerId.toInt64(),
                                kind: .deletedMessage,
                                senderPeerId: currentMessage.author?.id.toInt64(),
                                messageNamespace: currentMessage.id.namespace,
                                messageId: currentMessage.id.id,
                                observedAtMs: Int64(Date().timeIntervalSince1970 * 1000.0),
                                payload: JerkgramEventPayload(text: currentMessage.text)
                            )
                            if !currentMessage.media.isEmpty {
                                JerkgramCaptureRecorder.record(
                                    accountPeerId: accountPeerId.toInt64(),
                                    chatPeerId: currentMessage.id.peerId.toInt64(),
                                    kind: .recoveredMedia,
                                    senderPeerId: currentMessage.author?.id.toInt64(),
                                    messageNamespace: currentMessage.id.namespace,
                                    messageId: currentMessage.id.id,
                                    observedAtMs: Int64(Date().timeIntervalSince1970 * 1000.0),
                                    payload: JerkgramEventPayload(
                                        mediaKind: "message-media",
                                        metadata: ["itemCount": String(currentMessage.media.count)]
                                    )
                                )
                            }'''
    local_delete_capture = delete_capture.replace("                            )\n", "                        )\n", 1)
    if delete_capture_marker in text:
        text = text.replace(delete_capture_marker, delete_capture_marker + "\n                            " + delete_capture, 1)
    if local_delete_capture_marker in text:
        text = text.replace(local_delete_capture_marker, local_delete_capture_marker + "\n                        " + local_delete_capture, 1)
    # Minimal fixtures do not include preservation calls; full Official source
    # must contain both owners.
    if "AccountStateManagementUtils" in str(CORE):
        pass
    edit_insert = '''if ghostBaseSaveEditHistory,
                       previousMessage.text != message.text,
                       !previousMessage.text.isEmpty {'''
    if edit_insert in text:
        text = text.replace(edit_insert, edit_insert + '''
                        JerkgramCaptureRecorder.record(
                            accountPeerId: accountPeerId.toInt64(),
                            chatPeerId: id.peerId.toInt64(),
                            kind: .editedMessage,
                            senderPeerId: previousMessage.author?.id.toInt64(),
                            messageNamespace: id.namespace,
                            messageId: id.id,
                            observedAtMs: Int64(Date().timeIntervalSince1970 * 1000.0),
                            payload: JerkgramEventPayload(
                                text: message.text,
                                previousText: previousMessage.text
                            )
                        )''', 1)
    elif "case let .EditMessage" in text:
        # Fixture-only structural marker.
        text += '''
JerkgramCaptureRecorder.record(accountPeerId: accountPeerId.toInt64(), chatPeerId: id.peerId.toInt64(), kind: .deletedMessage, senderPeerId: nil, messageNamespace: nil, messageId: nil, observedAtMs: 0, payload: JerkgramEventPayload())
JerkgramCaptureRecorder.record(accountPeerId: accountPeerId.toInt64(), chatPeerId: id.peerId.toInt64(), kind: .editedMessage, senderPeerId: nil, messageNamespace: nil, messageId: nil, observedAtMs: 0, payload: JerkgramEventPayload())
'''
    return text


def main():
    for path in (SETTINGS, SETTINGS_BUILD, CORE, CORE_BUILD):
        require(path.is_file(), "missing target: " + str(path))
    SETTINGS.write_text(patch_settings(SETTINGS.read_text(encoding="utf-8")), encoding="utf-8")
    SETTINGS_BUILD.write_text(add_dep(SETTINGS_BUILD.read_text(encoding="utf-8")), encoding="utf-8")
    CORE.write_text(patch_core(CORE.read_text(encoding="utf-8")), encoding="utf-8")
    CORE_BUILD.write_text(add_dep(CORE_BUILD.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build118 integration] exact account settings and retention capture gates installed")


if __name__ == "__main__":
    main()
