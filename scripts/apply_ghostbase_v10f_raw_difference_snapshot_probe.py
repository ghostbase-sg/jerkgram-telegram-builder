#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10e1_split_push_type_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0F] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0F] ERROR: pattern not found: {label}")

print("[v1.0F] running base v1.0E.1 patcher...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

core_p = SRC / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

core = read(core_p)
settings = read(settings_p)

ensure(core, "func finalStateWithDifference", "finalStateWithDifference")
ensure(core, "StoreMessage(apiMessage:", "StoreMessage conversion")
ensure(core, "updatedState.deleteMessagesWithGlobalIds", "global delete path")
ensure(core, "updateDeleteChannelMessages", "channel delete path")
ensure(settings, "Core Difference Deep Probe:", "settings debug section")

helper_marker = "// MARK: GhostBase v1.0F Raw Difference Snapshot Probe"

if helper_marker not in core:
    helper = r'''
// MARK: GhostBase v1.0F Raw Difference Snapshot Probe
private func ghostBaseV10FRawRecord(_ name: String, amount: Int = 1) {
    guard amount > 0 else {
        return
    }

    let defaults = UserDefaults.standard
    let prefix = "GhostBase.V10F.Raw."
    let key = prefix + name + ".Count"

    defaults.set(defaults.integer(forKey: key) + amount, forKey: key)
    defaults.set(defaults.integer(forKey: prefix + "Total") + amount, forKey: prefix + "Total")
    defaults.set(name, forKey: prefix + "Last")
    defaults.set(amount, forKey: prefix + "LastAmount")
    defaults.set(Int(Date().timeIntervalSince1970), forKey: prefix + "LastTime")
}

private func ghostBaseV10FRawSet(_ key: String, _ value: String) {
    UserDefaults.standard.set(value, forKey: "GhostBase.V10F.Raw." + key)
}

private func ghostBaseV10FRawPreview(_ value: String, limit: Int = 180) -> String {
    if value.count <= limit {
        return value
    }
    return String(value.prefix(limit))
}

private func ghostBaseV10FRawMessageKey(_ id: MessageId) -> String {
    return "\(id.peerId.toInt64()):\(id.namespace):\(id.id)"
}

private func ghostBaseV10FRawSnapshot(message: StoreMessage, source: String) {
    ghostBaseV10FRawRecord("snapshotSeen")

    guard case let .Id(id) = message.id else {
        ghostBaseV10FRawRecord("snapshotNoId")
        return
    }

    let key = ghostBaseV10FRawMessageKey(id)
    let text = message.text

    ghostBaseV10FRawSet("LastSnapshotSource", source)
    ghostBaseV10FRawSet("LastSnapshotKey", key)
    ghostBaseV10FRawSet("LastSnapshotText", ghostBaseV10FRawPreview(text))
    ghostBaseV10FRawSet("LastSnapshotId", "\(id)")
    ghostBaseV10FRawSet("LastSnapshotPeer", "\(id.peerId.toInt64())")

    ghostBaseV10FRawRecord("snapshotSaved")
    ghostBaseV10FRawRecord("snapshotFrom" + source)

    if !text.isEmpty {
        ghostBaseV10FRawRecord("snapshotWithText")
        UserDefaults.standard.set(text, forKey: "GhostBase.V10F.Raw.Snapshot." + key + ".text")
        UserDefaults.standard.set(source, forKey: "GhostBase.V10F.Raw.Snapshot." + key + ".source")
        UserDefaults.standard.set(Int(Date().timeIntervalSince1970), forKey: "GhostBase.V10F.Raw.Snapshot." + key + ".time")
    } else {
        ghostBaseV10FRawRecord("snapshotEmptyText")
    }

    if let globalId = message.globallyUniqueId {
        ghostBaseV10FRawRecord("snapshotWithGlobalId")
        ghostBaseV10FRawSet("LastSnapshotGlobalId", "\(globalId)")
        if !text.isEmpty {
            UserDefaults.standard.set(text, forKey: "GhostBase.V10F.Raw.Global.\(globalId).text")
            UserDefaults.standard.set(key, forKey: "GhostBase.V10F.Raw.Global.\(globalId).key")
            UserDefaults.standard.set(source, forKey: "GhostBase.V10F.Raw.Global.\(globalId).source")
        }
    }
}

private func ghostBaseV10FRawDeleteHit(messageIds: [MessageId], source: String) {
    ghostBaseV10FRawRecord("deleteDirectSeen")
    ghostBaseV10FRawRecord("deleteDirectIds", amount: messageIds.count)
    ghostBaseV10FRawSet("LastDeleteSource", source)
    ghostBaseV10FRawSet("LastDeleteIdsCount", "\(messageIds.count)")

    var hitTexts: [String] = []
    var missCount = 0

    for id in messageIds {
        let key = ghostBaseV10FRawMessageKey(id)
        if let text = UserDefaults.standard.string(forKey: "GhostBase.V10F.Raw.Snapshot." + key + ".text"), !text.isEmpty {
            hitTexts.append(text)
            ghostBaseV10FRawRecord("deleteSnapshotHit")
            ghostBaseV10FRawSet("LastDeleteSnapshotKey", key)
            ghostBaseV10FRawSet("LastDeleteSnapshotText", ghostBaseV10FRawPreview(text))
        } else {
            missCount += 1
        }
    }

    if missCount > 0 {
        ghostBaseV10FRawRecord("deleteSnapshotMiss", amount: missCount)
    }

    if !hitTexts.isEmpty {
        ghostBaseV10FRawSet("LastDeleteSnapshotTexts", ghostBaseV10FRawPreview(hitTexts.joined(separator: " | "), limit: 360))
    }
}

private func ghostBaseV10FRawDeleteGlobalHit(globalIds: [Int32], source: String) {
    ghostBaseV10FRawRecord("deleteGlobalSeen")
    ghostBaseV10FRawRecord("deleteGlobalIds", amount: globalIds.count)
    ghostBaseV10FRawSet("LastDeleteSource", source)
    ghostBaseV10FRawSet("LastDeleteGlobalIdsCount", "\(globalIds.count)")

    var hitTexts: [String] = []
    var missCount = 0

    for globalId in globalIds {
        if let text = UserDefaults.standard.string(forKey: "GhostBase.V10F.Raw.Global.\(globalId).text"), !text.isEmpty {
            hitTexts.append(text)
            ghostBaseV10FRawRecord("deleteGlobalSnapshotHit")
            ghostBaseV10FRawSet("LastDeleteGlobalId", "\(globalId)")
            ghostBaseV10FRawSet("LastDeleteSnapshotText", ghostBaseV10FRawPreview(text))
        } else {
            missCount += 1
        }
    }

    if missCount > 0 {
        ghostBaseV10FRawRecord("deleteGlobalSnapshotMiss", amount: missCount)
    }

    if !hitTexts.isEmpty {
        ghostBaseV10FRawSet("LastDeleteSnapshotTexts", ghostBaseV10FRawPreview(hitTexts.joined(separator: " | "), limit: 360))
    }
}

'''
    anchor = "// MARK: GhostBase v1.0B Core Difference Diagnostics"
    core = replace_once(core, anchor, helper + "\n" + anchor, "insert v1.0F helper")

if 'ghostBaseV10FRawSnapshot(message: message, source: "Difference")' not in core:
    core = replace_once(
        core,
        '''        if let message = StoreMessage(apiMessage: message, accountPeerId: accountPeerId, peerIsForum: peerIsForum) {
            updatedState.addMessages([message], location: .UpperHistoryBlock)
''',
        '''        if let message = StoreMessage(apiMessage: message, accountPeerId: accountPeerId, peerIsForum: peerIsForum) {
            ghostBaseV10FRawSnapshot(message: message, source: "Difference")
            updatedState.addMessages([message], location: .UpperHistoryBlock)
''',
        "difference newMessages snapshot"
    )

if 'ghostBaseV10FRawSnapshot(message: message, source: "UpdateNewMessage")' not in core:
    core = replace_once(
        core,
        '''                    updatedState.addMessages([message], location: .UpperHistoryBlock)

                    if let reportDeliveryAttribute = message.attributes.first(where: { $0 is ReportDeliveryMessageAttribute }) as? ReportDeliveryMessageAttribute, case let .Id(id) = message.id, reportDeliveryAttribute.untilDate > currentTime {
''',
        '''                    ghostBaseV10FRawSnapshot(message: message, source: "UpdateNewMessage")
                    updatedState.addMessages([message], location: .UpperHistoryBlock)

                    if let reportDeliveryAttribute = message.attributes.first(where: { $0 is ReportDeliveryMessageAttribute }) as? ReportDeliveryMessageAttribute, case let .Id(id) = message.id, reportDeliveryAttribute.untilDate > currentTime {
''',
        "updateNewMessage snapshot"
    )

if 'ghostBaseV10FRawSnapshot(message: message.withUpdatedAttributes(attributes), source: "UpdateNewChannelMessage")' not in core:
    core = replace_once(
        core,
        '''                            var attributes = message.attributes
                            attributes.append(ChannelMessageStateVersionAttribute(pts: pts))
                            updatedState.addMessages([message.withUpdatedAttributes(attributes)], location: .UpperHistoryBlock)
''',
        '''                            var attributes = message.attributes
                            attributes.append(ChannelMessageStateVersionAttribute(pts: pts))
                            ghostBaseV10FRawSnapshot(message: message.withUpdatedAttributes(attributes), source: "UpdateNewChannelMessage")
                            updatedState.addMessages([message.withUpdatedAttributes(attributes)], location: .UpperHistoryBlock)
''',
        "updateNewChannelMessage snapshot"
    )

if 'ghostBaseV10FRawSnapshot(message: message, source: "ChannelDifference")' not in core:
    core = replace_once(
        core,
        '''                        updatedState.addMessages([message], location: .UpperHistoryBlock)
                        if case let .Id(id) = message.id {
''',
        '''                        ghostBaseV10FRawSnapshot(message: message, source: "ChannelDifference")
                        updatedState.addMessages([message], location: .UpperHistoryBlock)
                        if case let .Id(id) = message.id {
''',
        "channelDifference snapshot"
    )

if 'ghostBaseV10FRawDeleteHit(messageIds: messages.map' not in core:
    core = replace_once(
        core,
        '''                        updatedState.deleteMessages(messages.map({ MessageId(peerId: peerId, namespace: Namespaces.Message.Cloud, id: $0) }))
                        updatedState.updateChannelState(peerId, pts: pts)
''',
        '''                        ghostBaseV10FRawDeleteHit(messageIds: messages.map({ MessageId(peerId: peerId, namespace: Namespaces.Message.Cloud, id: $0) }), source: "UpdateDeleteChannelMessages")
                        updatedState.deleteMessages(messages.map({ MessageId(peerId: peerId, namespace: Namespaces.Message.Cloud, id: $0) }))
                        updatedState.updateChannelState(peerId, pts: pts)
''',
        "channel delete hit"
    )

if 'ghostBaseV10FRawDeleteGlobalHit(globalIds: updateDeleteMessagesData.messages' not in core:
    core = replace_once(
        core,
        '''                UserDefaults.standard.set(updateDeleteMessagesData.messages.count, forKey: "GhostBase.V10C.Core.LastDeleteIdsCount")
                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)
''',
        '''                UserDefaults.standard.set(updateDeleteMessagesData.messages.count, forKey: "GhostBase.V10C.Core.LastDeleteIdsCount")
                ghostBaseV10FRawDeleteGlobalHit(globalIds: updateDeleteMessagesData.messages, source: "UpdateDeleteMessages")
                updatedState.deleteMessagesWithGlobalIds(updateDeleteMessagesData.messages)
''',
        "global delete hit"
    )

write(core_p, core)

raw_section = r'''
    let ghostBaseRawPrefixV10F = "GhostBase.V10F.Raw."
    let ghostBaseRawDefaultsV10F = UserDefaults.standard

    entries.append(.info(debug, """
Raw Difference Snapshot Probe:
Total: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "Total"))
Last: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "Last") ?? "none") x\(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "LastAmount")) @ \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "LastTime"))
snapshotSeen: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotSeen.Count"))
snapshotSaved: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotSaved.Count"))
snapshotWithText: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotWithText.Count"))
snapshotEmptyText: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotEmptyText.Count"))
snapshotWithGlobalId: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotWithGlobalId.Count"))
fromDifference: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotFromDifference.Count"))
fromUpdateNewMessage: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotFromUpdateNewMessage.Count"))
fromUpdateNewChannelMessage: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotFromUpdateNewChannelMessage.Count"))
fromChannelDifference: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "snapshotFromChannelDifference.Count"))
deleteDirectSeen: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteDirectSeen.Count"))
deleteDirectIds: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteDirectIds.Count"))
deleteGlobalSeen: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalSeen.Count"))
deleteGlobalIds: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalIds.Count"))
deleteSnapshotHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteSnapshotHit.Count"))
deleteSnapshotMiss: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteSnapshotMiss.Count"))
deleteGlobalSnapshotHit: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalSnapshotHit.Count"))
deleteGlobalSnapshotMiss: \(ghostBaseRawDefaultsV10F.integer(forKey: ghostBaseRawPrefixV10F + "deleteGlobalSnapshotMiss.Count"))
LastSnapshotSource: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastSnapshotSource") ?? "none")
LastSnapshotKey: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastSnapshotKey") ?? "none")
LastSnapshotGlobalId: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastSnapshotGlobalId") ?? "none")
LastSnapshotText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastSnapshotText") ?? "none")
LastDeleteSource: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteSource") ?? "none")
LastDeleteIdsCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteIdsCount") ?? "none")
LastDeleteGlobalIdsCount: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteGlobalIdsCount") ?? "none")
LastDeleteSnapshotKey: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteSnapshotKey") ?? "none")
LastDeleteSnapshotText: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteSnapshotText") ?? "none")
LastDeleteSnapshotTexts: \(ghostBaseRawDefaultsV10F.string(forKey: ghostBaseRawPrefixV10F + "LastDeleteSnapshotTexts") ?? "none")
"""))

'''

if "Raw Difference Snapshot Probe:" not in settings:
    anchor = '''lastDiffDeleteIds: \\(ghostBaseCoreDefaultsV10C.integer(forKey: ghostBaseCorePrefixV10C + "LastDifferenceDeleteMessageIdsCount"))
"""))

'''
    settings = replace_once(settings, anchor, anchor + raw_section, "insert raw settings section")

settings = settings.replace("Version: v1.0E.1", "Version: v1.0F")
settings = settings.replace("Version: v1.0E", "Version: v1.0F")
write(settings_p, settings)

core = read(core_p)
settings = read(settings_p)

ensure(core, "GhostBase v1.0F Raw Difference Snapshot Probe", "raw helper marker")
ensure(core, 'ghostBaseV10FRawSnapshot(message: message, source: "Difference")', "difference snapshot")
ensure(core, 'ghostBaseV10FRawSnapshot(message: message, source: "UpdateNewMessage")', "update new message snapshot")
ensure(core, 'source: "UpdateNewChannelMessage"', "update new channel snapshot")
ensure(core, 'source: "ChannelDifference"', "channel difference snapshot")
ensure(core, "ghostBaseV10FRawDeleteHit", "direct delete hit")
ensure(core, "ghostBaseV10FRawDeleteGlobalHit", "global delete hit")
ensure(settings, "Raw Difference Snapshot Probe:", "settings raw section")
ensure(settings, "Version: v1.0F", "settings version")

print("[v1.0F] Raw Difference Snapshot Probe patch OK")
