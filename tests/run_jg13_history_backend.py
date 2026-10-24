"""Compile and execute the actual backend factory/selection with bounded model facades."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "work/swiftgram-src/submodules/TelegramUI/Sources/ChatHistoryListNode.swift"

def fixture():
    source = OWNER.read_text()
    start = source.index("    private static func makeListView(")
    brace = source.index("{", start)
    end, depth = brace + 1, 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    factory = source[start:end]
    start = source.index("        self.rotated = rotated", source.index("nextClientId += 1"))
    selection = source[start:source.index("        super.init()", start)]
    return r'''import Foundation
protocol ChatHistoryListViewBackend: AnyObject { var rotated: Bool { get set } }
final class CoreListChatHistoryBackend: ChatHistoryListViewBackend { var rotated = false }
final class ListViewImpl: ChatHistoryListViewBackend { var rotated = false }
struct Experimental { var coreListChatBackend: Bool }
struct Shared { var immediateExperimentalUISettings: Experimental }
struct Context {
    let sharedContext: Shared
    let kill: Bool
    func getAppConfigValue(_ key: String) -> Any? {
        precondition(key == "ios_killswitch_disable_corelist_chat_backend")
        return kill ? true : nil
    }
}
final class ChatHistoryListNodeImpl {
    let rotated: Bool
    let usesCoreListBackend: Bool
    let listView: ChatHistoryListViewBackend
''' + factory + r'''
    init(rotated: Bool, debug: Bool, kill: Bool) {
        let context = Context(sharedContext: Shared(immediateExperimentalUISettings: Experimental(coreListChatBackend: debug)), kill: kill)
''' + selection + r'''
    }
}
for rotated in [false, true] {
    for debug in [false, true] {
        for kill in [false, true] {
            let node = ChatHistoryListNodeImpl(rotated: rotated, debug: debug, kill: kill)
            let expected = debug && !kill
            precondition(node.usesCoreListBackend == expected)
            precondition((node.listView is CoreListChatHistoryBackend) == expected)
            precondition((node.listView is ListViewImpl) == !expected)
            precondition(node.listView.rotated == rotated)
        }
    }
}
print("PASS: 8 actual backend-selection cases; UIKit/device performance not tested")
'''

def main():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "main.swift"
        executable = Path(directory) / "backend"
        source.write_text(fixture())
        subprocess.run(["xcrun", "swiftc", str(source), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)

if __name__ == "__main__": main()
