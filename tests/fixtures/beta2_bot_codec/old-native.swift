import Foundation

func marker(_ value: String) { FileHandle.standardError.write(Data((value + "\n").utf8)) }
var progress = BotBridgeHistoryProgress(owner: 0x123456789abcdef, peer: 0x23456789abcdef0, testing: true, generation: "retained-build178-authorization")
marker("OLD_INITIAL_INT_WRITE")
let entry = PreferencesEntry(progress)!
if CommandLine.arguments.count == 3 && CommandLine.arguments[1] == "save" {
    try entry.data.write(to: URL(fileURLWithPath: CommandLine.arguments[2]))
}
guard entry.get(BotBridgeHistoryProgress.self) == nil else { fatalError("old Int unexpectedly decoded") }
marker("OLD_INT_DECODE_NIL")
if CommandLine.arguments.last == "terminal" {
    var fallback = BotBridgeHistoryProgress(owner: 42, peer: 43, testing: false, generation: "fallback")
    fallback.terminal = .corrupt
    marker("OLD_TERMINAL_WRITE")
    _ = PreferencesEntry(fallback)
    fatalError("old terminal unexpectedly encoded")
}
print("PASS old optimized Int read fails")
