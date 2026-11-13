// This executable uses the real pinned Postbox preferences encoder/decoder.
func check(_ value: @autoclosure () -> Bool) { precondition(value()) }
func oldWire(_ version: Int32?) -> PreferencesEntry {
    let encoder = PostboxEncoder()
    encoder.encodeInt32(1, forKey: "schema")
    encoder.encodeInt64(7, forKey: "owner"); encoder.encodeInt64(1, forKey: "peer")
    encoder.encodeBool(false, forKey: "testing"); encoder.encodeString("build181", forKey: "generation")
    encoder.encodeInt32(2, forKey: "historyPolicyVersion")
    encoder.encodeBool(false, forKey: "reservedState")
    encoder.encodeString("completed", forKey: "terminal")
    for key in ["reservedPages", "committedPages", "examined", "inserted", "insertedPeers", "insertedUsers", "insertedChats", "deleteIdsObserved", "skipped", "unsupported", "deletions", "missingReferences"] { encoder.encodeInt32(0, forKey: key) }
    if let version { encoder.encodeInt32(version, forKey: "peerMetadataRepairVersion") }
    let root = PostboxEncoder()
    root.encodeInnerObjectDataWithHeader(typeHash: postboxEncodableTypeHash(BotBridgeHistoryProgress.self), data: encoder.makeData(), valueType: .Object, forKey: "_")
    return PreferencesEntry(data: root.makeData())
}
let old = oldWire(nil).get(BotBridgeHistoryProgress.self)!
check(old.terminal == .completed)
let retained = JerkgramBotReplayPolicy.upgrade(old, owner: 7, peer: 1, testing: false, now: 1000)
check(retained == old) // Build181 progress remains durable; no metadata-only replay.
let entry = PreferencesEntry(retained)!
let decoded = PreferencesEntry(data: entry.data).get(BotBridgeHistoryProgress.self)!
check(decoded == retained)
check(JerkgramBotReplayPolicy.upgrade(old, owner: 8, peer: 1, testing: false) == old)
check(JerkgramBotReplayPolicy.upgrade(old, owner: 7, peer: 2, testing: false) == old)
check(JerkgramBotReplayPolicy.upgrade(old, owner: 7, peer: 1, testing: true) == old)
print("PASS Stable182 actual Postbox retained history codec")
