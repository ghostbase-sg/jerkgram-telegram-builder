#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

SETTINGS = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STATE = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
HISTORY = SRC / "submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift"
CTX = SRC / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

def require(condition, message):
    if not condition:
        raise RuntimeError(f"[v1.0S] {message}")

def replace_once(text, old, new, label):
    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

for path in (SETTINGS, STATE, HISTORY, CTX):
    require(path.is_file(), f"missing source: {path}")

settings = SETTINGS.read_text(encoding="utf-8")
state = STATE.read_text(encoding="utf-8")
history = HISTORY.read_text(encoding="utf-8")
ctx = CTX.read_text(encoding="utf-8")

# Keys and state
if "static let saveDeleted" not in settings:
    settings = replace_once(
        settings,
        '''    static let scheduledSend = "GhostBase.GhostMode.ScheduledSend"
''',
        '''    static let scheduledSend = "GhostBase.GhostMode.ScheduledSend"

    static let saveDeleted = "GhostBase.Messages.SaveDeleted"
    static let showDeleted = "GhostBase.Messages.ShowDeleted"
    static let saveEditHistory = "GhostBase.Messages.SaveEditHistory"
    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"
''',
        "message keys"
    )

    settings = replace_once(
        settings,
        '''    var scheduledSend: Bool

    var protectedEnabled: Bool
''',
        '''    var scheduledSend: Bool

    var saveDeleted: Bool
    var showDeleted: Bool
    var saveEditHistory: Bool
    var showEditHistory: Bool

    var protectedEnabled: Bool
''',
        "message state properties"
    )

    settings = replace_once(
        settings,
        '''            scheduledSend: ghostBaseBool(GhostBaseKey.scheduledSend, defaultValue: false),
            protectedEnabled:''',
        '''            scheduledSend: ghostBaseBool(GhostBaseKey.scheduledSend, defaultValue: false),

            saveDeleted: ghostBaseBool(GhostBaseKey.saveDeleted, defaultValue: true),
            showDeleted: ghostBaseBool(GhostBaseKey.showDeleted, defaultValue: true),
            saveEditHistory: ghostBaseBool(GhostBaseKey.saveEditHistory, defaultValue: true),
            showEditHistory: ghostBaseBool(GhostBaseKey.showEditHistory, defaultValue: true),

            protectedEnabled:''',
        "message state load"
    )

    settings = replace_once(
        settings,
        '''        UserDefaults.standard.set(self.scheduledSend, forKey: GhostBaseKey.scheduledSend)

        UserDefaults.standard.set(self.protectedEnabled''',
        '''        UserDefaults.standard.set(self.scheduledSend, forKey: GhostBaseKey.scheduledSend)

        UserDefaults.standard.set(self.saveDeleted, forKey: GhostBaseKey.saveDeleted)
        UserDefaults.standard.set(self.showDeleted, forKey: GhostBaseKey.showDeleted)
        UserDefaults.standard.set(self.saveEditHistory, forKey: GhostBaseKey.saveEditHistory)
        UserDefaults.standard.set(self.showEditHistory, forKey: GhostBaseKey.showEditHistory)

        UserDefaults.standard.set(self.protectedEnabled''',
        "message state save"
    )

# Toggle actions
if "case GhostBaseKey.saveDeleted:" not in settings:
    settings = replace_once(
        settings,
        '''            case GhostBaseKey.chatSave:
                updated.chatSave = value
''',
        '''            case GhostBaseKey.saveDeleted:
                updated.saveDeleted = value
            case GhostBaseKey.showDeleted:
                updated.showDeleted = value
            case GhostBaseKey.saveEditHistory:
                updated.saveEditHistory = value
            case GhostBaseKey.showEditHistory:
                updated.showEditHistory = value

            case GhostBaseKey.chatSave:
                updated.chatSave = value
''',
        "message toggle actions"
    )

settings = settings.replace(
    '"Read Ghost"',
    '"Не отмечать прочитанным"',
    1
)

settings = settings.replace(
    '''            .toggle(0, 7, GhostBaseKey.emojiActivity, "Скрыть выбор эмодзи", state.emojiActivity),
            .toggle(0, 8, GhostBaseKey.presence, "Скрыть онлайн", state.presence)
''',
    '''            .toggle(0, 7, GhostBaseKey.emojiActivity, "Скрыть выбор эмодзи", state.emojiActivity),
            .toggle(0, 8, GhostBaseKey.presence, "Скрыть онлайн", state.presence),
            .toggle(0, 9, GhostBaseKey.scheduledSend, "Отложенная отправка", state.scheduledSend)
''',
    1
)

old_messages = '''    if page == .messages {
        return [
            .header(0, "Сообщения"),
            .toggle(0, 1, GhostBaseKey.scheduledSend, "Отложенная отправка", state.scheduledSend),
            .info(0, "История редактирования и сохранение удалённых сообщений доступны через меню сообщения.")
        ]
    }
'''

new_messages = '''    if page == .messages {
        return [
            .header(0, "Удалённые сообщения"),
            .toggle(0, 1, GhostBaseKey.saveDeleted, "Сохранять удалённые сообщения", state.saveDeleted),
            .toggle(0, 2, GhostBaseKey.showDeleted, "Показывать удалённые сообщения", state.showDeleted),

            .header(1, "История изменений"),
            .toggle(1, 3, GhostBaseKey.saveEditHistory, "Сохранять историю изменений", state.saveEditHistory),
            .toggle(1, 4, GhostBaseKey.showEditHistory, "Показывать историю изменений", state.showEditHistory),

            .info(1, "Выключение функций не удаляет уже сохранённые данные.")
        ]
    }
'''

if old_messages in settings:
    settings = settings.replace(
        old_messages,
        new_messages,
        1
    )

# SaveDeleted: global-id path
global_marker = "GhostBase v1.0S global deleted-message save gate"

if global_marker not in state:
    start = state.index(
        "            case let .DeleteMessagesWithGlobalIds(ids):"
    )
    end = state.index(
        "            case let .DeleteMessages(ids):",
        start
    )

    block = state[start:end]
    loop_start = block.index(
        "                for id in ghostBaseMessageIds {"
    )
    loop_end = block.index(
        "                deletedMessageIds.append(contentsOf: ids.map { .global($0) })"
    )

    loop = block[loop_start:loop_end]
    loop = "".join(
        "    " + line if line.strip() else line
        for line in loop.splitlines(keepends=True)
    )

    wrapped = (
        "                // MARK: " + global_marker + "\n"
        "                let ghostBaseSaveDeleted = "
        "((UserDefaults.standard.object(forKey: "
        "\"GhostBase.Messages.SaveDeleted\") as? Bool) ?? true)\n"
        "                if ghostBaseSaveDeleted {\n"
        + loop
        + "                }\n"
    )

    block = block[:loop_start] + wrapped + block[loop_end:]
    state = state[:start] + block + state[end:]


# SaveDeleted: ordinary message-id path
local_marker = "GhostBase v1.0S local deleted-message save gate"

if local_marker not in state:
    start = state.index(
        "            case let .DeleteMessages(ids):"
    )
    end = state.index(
        "            case let .UpdateMinAvailableMessage(id):",
        start
    )

    replacement = '''            case let .DeleteMessages(ids):
                // MARK: GhostBase v1.0S local deleted-message save gate
                let ghostBaseSaveDeleted = ((UserDefaults.standard.object(forKey: "GhostBase.Messages.SaveDeleted") as? Bool) ?? true)

                if ghostBaseSaveDeleted {
                    for id in ids {
                        if let currentMessage = transaction.getMessage(id) {
                            var updatedAttributes = currentMessage.attributes
                            let originalText: String? = currentMessage.text.isEmpty ? nil : currentMessage.text
                            let attribute = (updatedAttributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute) ?? GhostBaseMessageAttribute(originalText: originalText, editHistoryTexts: [], editHistoryDates: [], isDeleted: false, deletedAt: 0)
                            let updatedAttribute = attribute.withUpdatedDeleted(isDeleted: true, deletedAt: currentMessage.timestamp)

                            updatedAttributes.removeAll(where: { $0 is GhostBaseMessageAttribute })
                            updatedAttributes.append(updatedAttribute)

                            transaction.updateMessage(id, update: { currentMessage in
                                let forwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                                return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: forwardInfo, authorId: currentMessage.author?.id, text: currentMessage.text, attributes: updatedAttributes, media: currentMessage.media))
                            })
                        }
                    }
                } else {
                    _internal_deleteMessages(transaction: transaction, mediaBox: mediaBox, ids: ids, manualAddMessageThreadStatsDifference: { id, add, remove in
                        addMessageThreadStatsDifference(threadKey: id, remove: remove, addedMessagePeer: nil, addedMessageId: nil, isOutgoing: false)
                    })
                    deletedMessageIds.append(contentsOf: ids.map { .messageId($0) })
                }
'''

    state = state[:start] + replacement + state[end:]

# SaveEditHistory
edit_marker = "GhostBase v1.0S edit-history save gate"

if edit_marker not in state:
    start = state.index(
        "                    // MARK: GhostBase v0.9B edit history attribute state"
    )
    end = state.index(
        "                    if let previousFactCheckAttribute",
        start
    )

    replacement = '''                    // MARK: GhostBase v1.0S edit-history save gate
                    let ghostBaseSaveEditHistory = ((UserDefaults.standard.object(forKey: "GhostBase.Messages.SaveEditHistory") as? Bool) ?? true)

                    if let previousAttribute = previousMessage.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute {
                        updatedAttributes.removeAll(where: { $0 is GhostBaseMessageAttribute })
                        updatedAttributes.append(previousAttribute)
                    }

                    if ghostBaseSaveEditHistory && previousMessage.text != message.text && !previousMessage.text.isEmpty {
                        let editDate = (message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp
                        var attribute = previousMessage.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute

                        if attribute == nil {
                            attribute = GhostBaseMessageAttribute(originalText: previousMessage.text, editHistoryTexts: [], editHistoryDates: [], isDeleted: false, deletedAt: 0)
                        }

                        if let updatedAttribute = attribute?.withAddedEditVersion(text: previousMessage.text, date: editDate) {
                            updatedAttributes.removeAll(where: { $0 is GhostBaseMessageAttribute })
                            updatedAttributes.append(updatedAttribute)
                        }
                    }

'''

    state = state[:start] + replacement + state[end:]


# ShowDeleted
if "GhostBase v1.0S deleted-message visibility gate" not in history:
    history = replace_once(
        history,
        '''        var contentTypeHint: ChatMessageEntryContentType = .generic
''',
        '''        // MARK: GhostBase v1.0S deleted-message visibility gate
        let ghostBaseShowDeleted = ((UserDefaults.standard.object(forKey: "GhostBase.Messages.ShowDeleted") as? Bool) ?? true)
        let ghostBaseIsDeleted = ((message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false

        if !ghostBaseShowDeleted && ghostBaseIsDeleted {
            continue loop
        }

        var contentTypeHint: ChatMessageEntryContentType = .generic
''',
        "deleted visibility"
    )


# ShowEditHistory
if "GhostBase v1.0S edit-history visibility gate" not in ctx:
    ctx = replace_once(
        ctx,
        '''        // MARK: GhostBase v0.9A edit history context action
        let ghostBaseEditHistoryVersions = ghostBaseLoadEditHistoryVersions(message: messages[0])
        if !ghostBaseEditHistoryVersions.isEmpty {
''',
        '''        // MARK: GhostBase v1.0S edit-history visibility gate
        let ghostBaseShowEditHistory = ((UserDefaults.standard.object(forKey: "GhostBase.Messages.ShowEditHistory") as? Bool) ?? true)
        let ghostBaseEditHistoryVersions = ghostBaseLoadEditHistoryVersions(message: messages[0])

        if ghostBaseShowEditHistory && !ghostBaseEditHistoryVersions.isEmpty {
''',
        "edit-history visibility"
    )

settings = settings.replace(
    "Version: v1.0R",
    "Version: v1.0S"
)

SETTINGS.write_text(settings, encoding="utf-8")
STATE.write_text(state, encoding="utf-8")
HISTORY.write_text(history, encoding="utf-8")
CTX.write_text(ctx, encoding="utf-8")

require(
    "GhostBase.Messages.SaveDeleted" in settings,
    "SaveDeleted missing"
)
require(
    "GhostBase v1.0S local deleted-message save gate" in state,
    "local delete gate missing"
)
require(
    "GhostBase v1.0S edit-history save gate" in state,
    "edit gate missing"
)
require(
    "GhostBase v1.0S deleted-message visibility gate" in history,
    "deleted visibility missing"
)
require(
    "GhostBase v1.0S edit-history visibility gate" in ctx,
    "history visibility missing"
)

print("[v1.0S] message controls applied")

# Scheduled Send: synchronize the main app setting with Share Extension
shared_group = "group.4a348a9b186b700c.1"
shared_key = "GhostBase.GhostMode.ScheduledSend"

if "GhostBase v1.0S shared scheduled-send sync" not in settings:
    settings = replace_once(
        settings,
        '''        UserDefaults.standard.set(self.scheduledSend, forKey: GhostBaseKey.scheduledSend)
''',
        '''        UserDefaults.standard.set(self.scheduledSend, forKey: GhostBaseKey.scheduledSend)

        // MARK: GhostBase v1.0S shared scheduled-send sync
        UserDefaults(suiteName: "group.4a348a9b186b700c.1")?.set(
            self.scheduledSend,
            forKey: GhostBaseKey.scheduledSend
        )
''',
        "shared scheduled-send save"
    )

    load_anchor = '''    let initialState = GhostBaseSettingsState.load()
'''

    require(
        load_anchor in settings,
        "initial settings state anchor"
    )

    settings = settings.replace(
        load_anchor,
        load_anchor + '''
    UserDefaults(suiteName: "group.4a348a9b186b700c.1")?.set(
        initialState.scheduledSend,
        forKey: GhostBaseKey.scheduledSend
    )
''',
        1
    )


STANDALONE = (
    SRC
    / "submodules/TelegramCore/Sources/PendingMessages"
    / "StandaloneSendMessage.swift"
)

require(
    STANDALONE.is_file(),
    f"missing source: {STANDALONE}"
)

standalone = STANDALONE.read_text(encoding="utf-8")

if "GhostBase v1.0S Standalone Scheduled Send" not in standalone:
    start = standalone.index(
        "// MARK: GhostBase v1.0Q+SH2 Standalone Scheduled Send"
    )

    end = standalone.index(
        "public func standaloneSendEnqueueMessages(",
        start
    )

    helper = '''// MARK: GhostBase v1.0S Standalone Scheduled Send
private func ghostBaseV10SApplyStandaloneSchedule(
    peerId: PeerId,
    attributes: inout [MessageAttribute]
) {
    let standardDefaults = UserDefaults.standard
    let sharedDefaults = UserDefaults(
        suiteName: "group.4a348a9b186b700c.1"
    )

    let standardEnabled = (
        standardDefaults.object(
            forKey: "GhostBase.GhostMode.ScheduledSend"
        ) as? Bool
    ) ?? false

    let sharedEnabled = (
        sharedDefaults?.object(
            forKey: "GhostBase.GhostMode.ScheduledSend"
        ) as? Bool
    ) ?? false

    if !standardEnabled && !sharedEnabled {
        return
    }

    if attributes.contains(where: {
        $0 is OutgoingScheduleInfoMessageAttribute
    }) {
        return
    }

    let scheduleTime =
        Int32(Date().timeIntervalSince1970) + 12

    attributes.append(
        OutgoingScheduleInfoMessageAttribute(
            scheduleTime: scheduleTime,
            repeatPeriod: nil
        )
    )

    let counterKey =
        "GhostBase.SH2.StandaloneScheduledIntercept.Count"

    let nextCount = max(
        standardDefaults.integer(forKey: counterKey),
        sharedDefaults?.integer(forKey: counterKey) ?? 0
    ) + 1

    standardDefaults.set(nextCount, forKey: counterKey)
    sharedDefaults?.set(nextCount, forKey: counterKey)

    standardDefaults.set(
        "\\(peerId)",
        forKey: "GhostBase.SH2.LastStandalonePeerId"
    )

    standardDefaults.set(
        Int(scheduleTime),
        forKey: "GhostBase.SH2.LastStandaloneScheduleTime"
    )
}

'''

    standalone = (
        standalone[:start]
        + helper
        + standalone[end:]
    )

    standalone = standalone.replace(
        "ghostBaseSH2ApplyStandaloneSchedule("
        "peerId: peerId, attributes: &attributes)",
        "ghostBaseV10SApplyStandaloneSchedule("
        "peerId: peerId, attributes: &attributes)",
        1
    )

CHAT_CONTROLLER = (
    SRC
    / "submodules/TelegramUI/Sources"
    / "ChatController.swift"
)

require(
    CHAT_CONTROLLER.is_file(),
    f"missing source: {CHAT_CONTROLLER}"
)

chat_controller = CHAT_CONTROLLER.read_text(
    encoding="utf-8"
)

inline_marker = (
    "GhostBase v1.0S inline-result scheduled send"
)

if inline_marker not in chat_controller:
    start = chat_controller.index(
        "    func enqueueChatContextResult("
    )

    end = chat_controller.find(
        "\n    func ",
        start + 10
    )

    require(
        end >= 0,
        "inline-result function end"
    )

    block = chat_controller[start:end]

    old = '''        let sendMessage: (Int32?) -> Void = { [weak self] scheduleTime in
            guard let self else {
                return
            }
            let replyMessageSubject = self.presentationInterfaceState.interfaceState.replyMessageSubject
'''

    new = '''        let sendMessage: (Int32?) -> Void = { [weak self] scheduleTime in
            guard let self else {
                return
            }

            // MARK: GhostBase v1.0S inline-result scheduled send
            let ghostBaseScheduledSend = (
                UserDefaults.standard.object(
                    forKey: "GhostBase.GhostMode.ScheduledSend"
                ) as? Bool
            ) ?? false

            let ghostBaseEffectiveScheduleTime: Int32?

            if let scheduleTime = scheduleTime {
                ghostBaseEffectiveScheduleTime = scheduleTime
            } else if ghostBaseScheduledSend {
                ghostBaseEffectiveScheduleTime =
                    Int32(Date().timeIntervalSince1970) + 12

                UserDefaults.standard.set(
                    UserDefaults.standard.integer(
                        forKey: "GhostBase.V10S.InlineScheduledIntercept.Count"
                    ) + 1,
                    forKey: "GhostBase.V10S.InlineScheduledIntercept.Count"
                )
            } else {
                ghostBaseEffectiveScheduleTime = nil
            }

            let replyMessageSubject = self.presentationInterfaceState.interfaceState.replyMessageSubject
'''

    require(
        old in block,
        "inline send closure anchor"
    )

    block = block.replace(old, new, 1)

    require(
        "scheduleTime: scheduleTime" in block,
        "inline scheduleTime argument"
    )

    block = block.replace(
        "scheduleTime: scheduleTime",
        "scheduleTime: ghostBaseEffectiveScheduleTime",
        1
    )

    chat_controller = (
        chat_controller[:start]
        + block
        + chat_controller[end:]
    )


SETTINGS.write_text(settings, encoding="utf-8")
STANDALONE.write_text(standalone, encoding="utf-8")
CHAT_CONTROLLER.write_text(
    chat_controller,
    encoding="utf-8"
)

require(
    "GhostBase v1.0S shared scheduled-send sync"
    in settings,
    "shared sync missing"
)

require(
    "GhostBase v1.0S Standalone Scheduled Send"
    in standalone,
    "standalone fix missing"
)

require(
    inline_marker in chat_controller,
    "inline fix missing"
)

print("[v1.0S] Quick Share scheduled send fixed")
print("[v1.0S] inline-result scheduled send fixed")
