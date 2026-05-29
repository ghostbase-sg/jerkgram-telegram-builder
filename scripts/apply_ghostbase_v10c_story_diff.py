from pathlib import Path
import runpy
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

base = ROOT / "scripts/apply_ghostbase_v10b_history_diagnostics.py"
if not base.exists():
    raise SystemExit("[v1.0C] ERROR: missing v1.0B base patcher")

print("[v1.0C] replay v1.0B base")
runpy.run_path(str(base), run_name="__main__")

def read(path):
    return path.read_text()

def write(path, text):
    path.write_text(text)

def replace_once(text, old, new, label):
    if new in text:
        print(f"[v1.0C] already patched: {label}")
        return text
    if old not in text:
        raise SystemExit(f"[v1.0C] ERROR: pattern not found: {label}")
    return text.replace(old, new, 1)

def ensure_contains(text, needle, label):
    if needle not in text:
        raise SystemExit(f"[v1.0C] ERROR: missing proof: {label}")

asm_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
asm = read(asm_p)

if "// MARK: GhostBase v1.0C Difference Deep Probe" not in asm:
    helper = r'''
// MARK: GhostBase v1.0C Difference Deep Probe
private func ghostBaseV10CRecordCoreEvent(_ name: String, amount: Int = 1) {
    if amount <= 0 {
        return
    }

    let defaults = UserDefaults.standard
    let prefix = "GhostBase.V10C.Core."
    let countKey = prefix + name + ".Count"

    defaults.set(defaults.integer(forKey: countKey) + amount, forKey: countKey)
    defaults.set(defaults.integer(forKey: prefix + "Total") + amount, forKey: prefix + "Total")
    defaults.set(name, forKey: prefix + "Last")
    defaults.set(amount, forKey: prefix + "LastAmount")
    defaults.set(Int(Date().timeIntervalSince1970), forKey: prefix + "LastTime")
}

private func ghostBaseV10CRecordDifference(kind: String, messages: [Api.Message], encryptedMessages: [Api.EncryptedMessage], updates: [Api.Update], chats: [Api.Chat], users: [Api.User]) {
    let defaults = UserDefaults.standard
    let prefix = "GhostBase.V10C.Core."

    var deleteMessageIds = 0
    var deleteChannelMessageIds = 0
    var updateNewMessages = 0
    var updateNewChannelMessages = 0

    for update in updates {
        switch update {
        case let .updateDeleteMessages(data):
            deleteMessageIds += data.messages.count
        case let .updateDeleteChannelMessages(data):
            deleteChannelMessageIds += data.messages.count
        case .updateNewMessage(_):
            updateNewMessages += 1
        case .updateNewChannelMessage(_):
            updateNewChannelMessages += 1
        default:
            break
        }
    }

    defaults.set(kind, forKey: prefix + "LastDifferenceKind")
    defaults.set(messages.count, forKey: prefix + "LastDifferenceNewMessagesCount")
    defaults.set(encryptedMessages.count, forKey: prefix + "LastDifferenceEncryptedMessagesCount")
    defaults.set(updates.count, forKey: prefix + "LastDifferenceOtherUpdatesCount")
    defaults.set(chats.count, forKey: prefix + "LastDifferenceChatsCount")
    defaults.set(users.count, forKey: prefix + "LastDifferenceUsersCount")
    defaults.set(deleteMessageIds, forKey: prefix + "LastDifferenceDeleteMessageIdsCount")
    defaults.set(deleteChannelMessageIds, forKey: prefix + "LastDifferenceDeleteChannelMessageIdsCount")
    defaults.set(updateNewMessages, forKey: prefix + "LastDifferenceUpdateNewMessagesCount")
    defaults.set(updateNewChannelMessages, forKey: prefix + "LastDifferenceUpdateNewChannelMessagesCount")

    ghostBaseV10CRecordCoreEvent("differenceRuns")
    ghostBaseV10CRecordCoreEvent("differenceNewMessages", amount: messages.count)
    ghostBaseV10CRecordCoreEvent("differenceEncryptedMessages", amount: encryptedMessages.count)
    ghostBaseV10CRecordCoreEvent("differenceOtherUpdates", amount: updates.count)
    ghostBaseV10CRecordCoreEvent("differenceDeleteMessageIds", amount: deleteMessageIds)
    ghostBaseV10CRecordCoreEvent("differenceDeleteChannelMessageIds", amount: deleteChannelMessageIds)
    ghostBaseV10CRecordCoreEvent("differenceUpdateNewMessages", amount: updateNewMessages)
    ghostBaseV10CRecordCoreEvent("differenceUpdateNewChannelMessages", amount: updateNewChannelMessages)
}
'''
    asm = asm.replace("private func reactionGeneratedEvent", helper + "\nprivate func reactionGeneratedEvent", 1)

asm = replace_once(
    asm,
    """    updatedState.mergeChats(chats)
    updatedState.mergeUsers(users)

    let currentTime = Int32(CFAbsoluteTimeGetCurrent() + kCFAbsoluteTimeIntervalSince1970)
""",
    """    ghostBaseV10CRecordDifference(kind: "finalStateWithDifference", messages: messages, encryptedMessages: encryptedMessages, updates: updates, chats: chats, users: users)

    updatedState.mergeChats(chats)
    updatedState.mergeUsers(users)

    let currentTime = Int32(CFAbsoluteTimeGetCurrent() + kCFAbsoluteTimeIntervalSince1970)
""",
    "record finalStateWithDifference payload"
)

write(asm_p, asm)

asm = read(asm_p)

asm = replace_once(
    asm,
    '                ghostBaseV10BRecordCoreEvent("deleteChannelMessages")',
    '''                ghostBaseV10BRecordCoreEvent("deleteChannelMessages")
                ghostBaseV10CRecordCoreEvent("deleteChannelMessagesEvents")
                ghostBaseV10CRecordCoreEvent("deleteChannelMessageIds", amount: updateDeleteChannelMessagesData.messages.count)
                UserDefaults.standard.set(updateDeleteChannelMessagesData.messages.count, forKey: "GhostBase.V10C.Core.LastDeleteChannelIdsCount")''',
    "deleteChannelMessages ids counter"
)

asm = replace_once(
    asm,
    '                ghostBaseV10BRecordCoreEvent("deleteMessages")',
    '''                ghostBaseV10BRecordCoreEvent("deleteMessages")
                ghostBaseV10CRecordCoreEvent("deleteMessagesEvents")
                ghostBaseV10CRecordCoreEvent("deleteMessageIds", amount: updateDeleteMessagesData.messages.count)
                UserDefaults.standard.set(updateDeleteMessagesData.messages.count, forKey: "GhostBase.V10C.Core.LastDeleteIdsCount")''',
    "deleteMessages ids counter"
)

asm = replace_once(
    asm,
    '                ghostBaseV10BRecordCoreEvent("editMessage")',
    '''                ghostBaseV10BRecordCoreEvent("editMessage")
                ghostBaseV10CRecordCoreEvent("editMessageEvents")''',
    "editMessage v10c counter"
)

asm = replace_once(
    asm,
    '                ghostBaseV10BRecordCoreEvent("newChannelMessage")',
    '''                ghostBaseV10BRecordCoreEvent("newChannelMessage")
                ghostBaseV10CRecordCoreEvent("newChannelMessageEvents")''',
    "newChannelMessage v10c counter"
)

asm = replace_once(
    asm,
    '                ghostBaseV10BRecordCoreEvent("newMessage")',
    '''                ghostBaseV10BRecordCoreEvent("newMessage")
                ghostBaseV10CRecordCoreEvent("newMessageEvents")''',
    "newMessage v10c counter"
)

write(asm_p, asm)

settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
settings = read(settings_p)

settings = replace_once(
    settings,
    '    static let oneTimeSave = "GhostBase.ProtectedContent.OneTimeSave"',
    '''    static let oneTimeSave = "GhostBase.ProtectedContent.OneTimeSave"
    static let storySave = "GhostBase.Stories.Save"''',
    "settings storySave key"
)

settings = replace_once(
    settings,
    "    var oneTimeSave: Bool\n    var localStarsEnabled: Bool",
    "    var oneTimeSave: Bool\n    var storySave: Bool\n    var localStarsEnabled: Bool",
    "settings storySave state var"
)

settings = replace_once(
    settings,
    "            oneTimeSave: ghostBaseBool(GhostBaseKey.oneTimeSave, defaultValue: false),\n            localStarsEnabled:",
    "            oneTimeSave: ghostBaseBool(GhostBaseKey.oneTimeSave, defaultValue: false),\n            storySave: ghostBaseBool(GhostBaseKey.storySave, defaultValue: false),\n            localStarsEnabled:",
    "settings storySave load"
)

settings = replace_once(
    settings,
    "        UserDefaults.standard.set(self.oneTimeSave, forKey: GhostBaseKey.oneTimeSave)\n        UserDefaults.standard.set(self.localStarsEnabled, forKey: GhostBaseKey.localStarsEnabled)",
    "        UserDefaults.standard.set(self.oneTimeSave, forKey: GhostBaseKey.oneTimeSave)\n        UserDefaults.standard.set(self.storySave, forKey: GhostBaseKey.storySave)\n        UserDefaults.standard.set(self.localStarsEnabled, forKey: GhostBaseKey.localStarsEnabled)",
    "settings storySave save"
)

write(settings_p, settings)

settings = read(settings_p)

settings = replace_once(
    settings,
    '    entries.append(.toggle(protected, 12, GhostBaseKey.oneTimeSave, "Allow One-Time Save", state.oneTimeSave))',
    '''    entries.append(.toggle(protected, 12, GhostBaseKey.oneTimeSave, "Allow One-Time Save", state.oneTimeSave))
    entries.append(.toggle(protected, 13, GhostBaseKey.storySave, "Story Save", state.storySave))''',
    "settings storySave toggle"
)

settings = replace_once(
    settings,
    "            case GhostBaseKey.oneTimeSave:\n                updated.oneTimeSave = value\n            case GhostBaseKey.localStarsEnabled:",
    "            case GhostBaseKey.oneTimeSave:\n                updated.oneTimeSave = value\n            case GhostBaseKey.storySave:\n                updated.storySave = value\n            case GhostBaseKey.localStarsEnabled:",
    "settings storySave updateBool"
)

settings = replace_once(
    settings,
    "                updated.oneTimeSave = value\n            case GhostBaseKey.protectedGalleryShare:",
    "                updated.oneTimeSave = value\n                updated.storySave = value\n            case GhostBaseKey.protectedGalleryShare:",
    "settings protected master storySave cascade"
)

settings = settings.replace(
    "&& !updated.oneTimeScreenshots && !updated.oneTimeScreenRecording && !updated.oneTimeSave",
    "&& !updated.oneTimeScreenshots && !updated.oneTimeScreenRecording && !updated.oneTimeSave && !updated.storySave"
)
settings = settings.replace(
    "|| updated.oneTimeScreenshots || updated.oneTimeScreenRecording || updated.oneTimeSave",
    "|| updated.oneTimeScreenshots || updated.oneTimeScreenRecording || updated.oneTimeSave || updated.storySave"
)

insert_before = '    let ghostBaseCorePrefix = "GhostBase.V10B.Core."'
deep_debug = r'''    let ghostBaseCorePrefixV10C = "GhostBase.V10C.Core."
    let ghostBaseCoreDefaultsV10C = UserDefaults.standard

    entries.append(.info(debug, """
Core Difference Deep Probe:
Total: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "Total"))
Last: \(ghostBaseCoreDefaultsV10C.string(forKey: ghostBaseCorePrefixV10C + "Last") ?? "none") x\(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "LastAmount")) @ \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "LastTime"))
diffRuns: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "differenceRuns.Count"))
diffNewMessages: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "differenceNewMessages.Count"))
diffOtherUpdates: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "differenceOtherUpdates.Count"))
deleteEvents: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "deleteMessagesEvents.Count"))
deleteIds: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "deleteMessageIds.Count"))
lastDeleteIds: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "LastDeleteIdsCount"))
lastDiffNewMessages: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "LastDifferenceNewMessagesCount"))
lastDiffOtherUpdates: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "LastDifferenceOtherUpdatesCount"))
lastDiffDeleteIds: \(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "LastDifferenceDeleteMessageIdsCount"))
"""))

'''
settings = replace_once(settings, insert_before, deep_debug + insert_before, "settings v10c deep diagnostics UI")

settings = re.sub(r"Version: v[0-9A-Za-z.\-]+", "Version: v1.0C", settings, count=1)

write(settings_p, settings)

story_p = SRC / "submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemSetContainerComponent.swift"
story = read(story_p)

story = replace_once(
    story,
    "} else if !component.slice.item.storyItem.isForwardingDisabled {",
    "} else if !component.slice.item.storyItem.isForwardingDisabled || ((UserDefaults.standard.object(forKey: \"GhostBase.Stories.Save\") as? Bool) ?? false) {",
    "story save show item for forwarding-disabled stories"
)

story = replace_once(
    story,
    '''                            if accountUser.isPremium {
                                self.requestSave()
                            } else {
                                self.presentSaveUpgradeScreen()
                            }''',
    '''                            if accountUser.isPremium || ((UserDefaults.standard.object(forKey: "GhostBase.Stories.Save") as? Bool) ?? false) {
                                self.requestSave()
                            } else {
                                self.presentSaveUpgradeScreen()
                            }''',
    "story save bypass premium gate"
)

write(story_p, story)

asm = read(asm_p)
settings = read(settings_p)
story = read(story_p)

ensure_contains(asm, "GhostBase v1.0C Difference Deep Probe", "v1.0C ASM helper")
ensure_contains(asm, "ghostBaseV10CRecordDifference", "v1.0C difference recorder")
ensure_contains(asm, "differenceNewMessages", "v1.0C differenceNewMessages counter")
ensure_contains(asm, "deleteMessageIds", "v1.0C deleteMessageIds counter")

ensure_contains(settings, 'static let storySave = "GhostBase.Stories.Save"', "Story Save settings key")
ensure_contains(settings, 'Story Save", state.storySave', "Story Save settings toggle")
ensure_contains(settings, "Core Difference Deep Probe", "Deep Probe settings UI")
ensure_contains(settings, "Version: v1.0C", "v1.0C version")

ensure_contains(story, 'GhostBase.Stories.Save', "Story Save story viewer patch")
ensure_contains(story, "self.requestSave()", "Story requestSave still present")

print("[v1.0C] GhostBase Story Save + Difference Deep Probe patch OK")
