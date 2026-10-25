"""Execute the actual picker callback under the same nested-capture shape on Swift 27."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / 'work/swiftgram-src/submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift'

def fixture():
    source = OWNER.read_text()
    start = source.index('            picker.peerSelected = {')
    brace = source.index('{', start)
    end, depth = brace + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    callback = source[start:end]
    return '''import Foundation
struct Context {}
struct PeerId { let value: Int64; func toInt64() -> Int64 { value } }
struct Peer { let id: PeerId }
class ItemListController {
    var pushes = 0
    func push(_ controller: ItemListController) { self.pushes += 1 }
}
final class PeerSelectionController: ItemListController {
    var peerSelected: ((Peer, Bool) -> Void)?
    var dismissals = 0
    func dismiss() { self.dismissals += 1 }
}
func jerkgramChatRetentionController(context: Context, chatPeerId: Int64) -> ItemListController {
    precondition(chatPeerId == 42)
    return ItemListController()
}
func run() {
    let context = Context()
    var controller: ItemListController?
    let action = { () -> PeerSelectionController in
        let picker = PeerSelectionController()
''' + callback + '''
        controller?.push(picker)
        return picker
    }
    controller = ItemListController()
    let picker = action()
    precondition(controller?.pushes == 1)
    picker.peerSelected?(Peer(id: PeerId(value: 42)), false)
    precondition(controller?.pushes == 2)
    precondition(picker.dismissals == 1)
    weak let releasedController = controller
    controller = nil
    precondition(releasedController == nil)
    picker.peerSelected?(Peer(id: PeerId(value: 42)), false)
    precondition(picker.dismissals == 2)
    _ = action
}
run()
print("PASS: actual weak picker callback navigates and does not retain its controller; full app compile still required")
'''

def main():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / 'main.swift'
        executable = Path(directory) / 'capture'
        source.write_text(fixture())
        subprocess.run(['xcrun', 'swiftc', '-warnings-as-errors', str(source), '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True)

if __name__ == '__main__': main()
