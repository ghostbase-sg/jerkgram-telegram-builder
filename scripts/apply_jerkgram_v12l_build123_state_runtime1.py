#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
MARKER = "// MARK: Jerkgram v1.2L BUILD123_ACCOUNT_SETTINGS_OWNER1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build123 state/runtime] " + message)


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
    raise RuntimeError("[Build123 state/runtime] unbalanced block: " + signature)


OWNER_SOURCE = r'''// MARK: Jerkgram v1.2L BUILD123_ACCOUNT_SETTINGS_OWNER1
private enum JerkgramSettingValue: Equatable {
    case bool(Bool)
    case string(String)

    func write(to defaults: UserDefaults, key: String) {
        switch self {
        case let .bool(value): defaults.set(value, forKey: key)
        case let .string(value): defaults.set(value, forKey: key)
        }
    }
}

private enum JerkgramSettingsCommitQueue {
    private static let queue = Queue(name: "JerkgramSettingsCommitQueue", qos: .utility)
    static func enqueue(_ work: @escaping () -> Void) {
        self.queue.async(work)
    }
}

private func jerkgramStateValues(_ state: GhostBaseSettingsState) -> [String: JerkgramSettingValue] {
    return [
        GhostBaseKey.profileEnabled: .bool(state.profileEnabled),
        GhostBaseKey.showIds: .bool(state.showIds),
        GhostBaseKey.showDCs: .bool(state.showDCs),
        GhostBaseKey.showRegistration: .bool(state.showRegistration),
        GhostBaseKey.glassEnabled: .bool(state.glassEnabled),
        GhostBaseKey.profileAvatarBlur: .bool(state.profileAvatarBlur),
        GhostBaseKey.profileAnimatedBackground: .bool(state.profileAnimatedBackground),
        GhostBaseKey.profileBlurTint: .bool(state.profileBlurTint),
        GhostBaseKey.profileBlurReduced: .bool(state.profileBlurReduced),
        GhostBaseKey.readMessages: .bool(state.readMessages),
        GhostBaseKey.typingActions: .bool(state.typingActions),
        GhostBaseKey.recordingActions: .bool(state.recordingActions),
        GhostBaseKey.uploadingActions: .bool(state.uploadingActions),
        GhostBaseKey.stickerActivity: .bool(state.stickerActivity),
        GhostBaseKey.gameActivity: .bool(state.gameActivity),
        GhostBaseKey.emojiActivity: .bool(state.emojiActivity),
        GhostBaseKey.presence: .bool(state.presence),
        GhostBaseKey.scheduledSend: .bool(state.scheduledSend),
        GhostBaseKey.saveDeleted: .bool(state.saveDeleted),
        GhostBaseKey.showDeleted: .bool(state.showDeleted),
        GhostBaseKey.saveEditHistory: .bool(state.saveEditHistory),
        GhostBaseKey.showEditHistory: .bool(state.showEditHistory),
        ghostBaseSendTextStyleKey: .string(state.sendTextStyle),
        GhostBaseKey.deletedPortableReplies: .bool(state.deletedPortableReplies),
        GhostBaseKey.preserveDeletedMedia: .bool(state.preserveDeletedMedia),
        GhostBaseKey.showRamUnderClock: .bool(state.showRamUnderClock),
        GhostBaseKey.messageSeconds: .bool(state.messageSeconds),
        GhostBaseKey.hideOwnPhone: .bool(state.hideOwnPhone),
        GhostBaseKey.protectedEnabled: .bool(state.protectedEnabled),
        GhostBaseKey.protectedGalleryShare: .bool(state.protectedGalleryShare),
        GhostBaseKey.protectedGallerySave: .bool(state.protectedGallerySave),
        GhostBaseKey.protectedGalleryCopy: .bool(state.protectedGalleryCopy),
        GhostBaseKey.chatSave: .bool(state.chatSave),
        GhostBaseKey.chatCopy: .bool(state.chatCopy),
        GhostBaseKey.chatForward: .bool(state.chatForward),
        GhostBaseKey.allowScreenshots: .bool(state.allowScreenshots),
        GhostBaseKey.allowScreenRecording: .bool(state.allowScreenRecording),
        GhostBaseKey.oneTimeScreenshots: .bool(state.oneTimeScreenshots),
        GhostBaseKey.oneTimeScreenRecording: .bool(state.oneTimeScreenRecording),
        GhostBaseKey.oneTimeSave: .bool(state.oneTimeSave),
        GhostBaseKey.storySave: .bool(state.storySave),
        GhostBaseKey.localStarsEnabled: .bool(state.localStarsEnabled),
        GhostBaseKey.localStarsAmount: .string(state.localStarsAmount),
        GhostBaseKey.localStarsBaseAmount: .string(state.localStarsBaseAmount)
    ]
}

private func jerkgramPersistChangedSettings(
    accountPeerId: Int64,
    previous: GhostBaseSettingsState?,
    current: GhostBaseSettingsState
) {
    let oldValues = previous.map(jerkgramStateValues) ?? [:]
    let newValues = jerkgramStateValues(current)
    let changes = newValues.filter { oldValues[$0.key] != $0.value }
    guard !changes.isEmpty else { return }

    JerkgramSettingsCommitQueue.enqueue {
        let defaults = UserDefaults.standard
        for (key, value) in changes {
            value.write(to: defaults, key: jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key))
            // Legacy Telegram and extension consumers use this active-account projection.
            value.write(to: defaults, key: key)
            if key == GhostBaseKey.scheduledSend {
                value.write(to: UserDefaults(suiteName: "group.4a348a9b186b700c.1") ?? defaults, key: key)
            }
        }
    }
}

private func jerkgramProjectActiveSettings(accountPeerId: Int64, state: GhostBaseSettingsState) {
    jerkgramPersistChangedSettings(accountPeerId: accountPeerId, previous: nil, current: state)
}

// Regression sentinel: bulk defaults enumeration must never return here.
'''


def main() -> None:
    text = SETTINGS.read_text(encoding="utf-8")
    if MARKER in text:
        print("[Build123 state/runtime] already applied")
        return

    start, end = block_bounds(text, "private func jerkgramMirrorSettingsToAccount(accountPeerId: Int64)")
    text = text[:start] + OWNER_SOURCE + text[end:]

    start, end = block_bounds(text, "    func save(accountPeerId: Int64)")
    text = text[:start] + '''    func save(accountPeerId: Int64) {
        jerkgramPersistChangedSettings(accountPeerId: accountPeerId, previous: nil, current: self)
    }''' + text[end:]

    old_projection = '''    UserDefaults(suiteName: "group.4a348a9b186b700c.1")?.set(
        initialState.scheduledSend,
        forKey: GhostBaseKey.scheduledSend
    )'''
    require(text.count(old_projection) == 1, "initial scheduled projection anchor")
    text = text.replace(old_projection, "    jerkgramProjectActiveSettings(accountPeerId: context.account.peerId.toInt64(), state: initialState)", 1)

    old_commit = '''            next.save(accountPeerId: context.account.peerId.toInt64())
            jerkgramMirrorSettingsToAccount(accountPeerId: context.account.peerId.toInt64())'''
    new_commit = '''            jerkgramPersistChangedSettings(
                accountPeerId: context.account.peerId.toInt64(),
                previous: current,
                current: next
            )'''
    require(text.count(old_commit) == 1, "toggle commit anchor")
    text = text.replace(old_commit, new_commit, 1)

    require("dictionaryRepresentation()" not in text, "dictionaryRepresentation() survived the toggle path")
    require("jerkgramMirrorSettingsToAccount" not in text, "legacy reverse mirror survived")
    SETTINGS.write_text(text, encoding="utf-8")
    print("[Build123 state/runtime] GREEN")
    print("[Build123 state/runtime] scoped owner + active projection; targeted commits off main queue")


if __name__ == "__main__":
    main()
