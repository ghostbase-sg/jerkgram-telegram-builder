"""Execute actual cache owners with bounded models and real temporary files on macOS."""
import os
from pathlib import Path
import subprocess
import tempfile
from run_jg13_deleted_reply import block
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
FACADE = r'''
import Foundation
import Darwin
struct PeerId { let value: Int64; func toInt64() -> Int64 { value } }
struct MessageId { let peerId: PeerId; let namespace: Int32; let id: Int32 }
struct ResourceId { let stringRepresentation: String }
protocol MediaResource { var id: ResourceId { get } }
struct Resource: MediaResource { let id: ResourceId }
protocol Media {}
struct Representation { let resource: MediaResource }
struct TelegramMediaImage: Media { let representations: [Representation] }
func largestImageRepresentation(_ values: [Representation]) -> Representation? { values.last }
struct TelegramMediaFile: Media { let fileName: String?; let mimeType: String; let resource: MediaResource }
struct Message { let id: MessageId; let media: [Media] }
final class MediaBox {
    let basePath: String
    init(_ path: String) { basePath = path }
    func completedResourcePath(_ resource: MediaResource) -> String? {
        let path = basePath + "/" + resource.id.stringRepresentation
        return FileManager.default.fileExists(atPath: path) ? path : nil
    }
}
// Count persistent reads/writes without changing the extracted production owner.
final class UserDefaults {
    static let standard = UserDefaults()
    var storage: [String: Any] = [:]
    var reads = 0; var writes = 0
    func dictionary(forKey key: String) -> [String: Any]? { reads += 1; return storage[key] as? [String: Any] }
    func stringArray(forKey key: String) -> [String]? { reads += 1; return storage[key] as? [String] }
    func object(forKey key: String) -> Any? { storage[key] }
    func set(_ value: Any, forKey key: String) { writes += 1; storage[key] = value }
}
let ghostBasePreserveDeletedMediaKey = "preserve"
let ghostBaseDeletedMediaRetentionDaysKey = "retention"
let ghostBaseDeletedMediaCacheLimitKey = "quota"
func ghostBaseDeletedBool(_ key: String, defaultValue: Bool) -> Bool { defaultValue }
'''
CHECKS = r'''
let defaults = UserDefaults.standard
GhostBasePublicPeerNameStore.store(peerId: PeerId(value: 1), firstName: " Иван ", lastName: "Петров")
precondition(defaults.reads == 2 && defaults.writes == 2)
for _ in 0..<1000 {
    precondition(GhostBasePublicPeerNameStore.name(peerId: PeerId(value: 1)) == "Иван Петров")
    GhostBasePublicPeerNameStore.store(peerId: PeerId(value: 1), firstName: "Иван", lastName: "Петров")
}
precondition(defaults.reads == 2 && defaults.writes == 2)
GhostBasePublicPeerNameStore.store(peerId: PeerId(value: 2), firstName: "Two", lastName: "")
let writesBefore = defaults.writes
GhostBasePublicPeerNameStore.store(peerId: PeerId(value: 1), firstName: "Иван", lastName: "Петров")
precondition(defaults.writes == writesBefore + 1) // LRU change only, no dictionary rewrite.
for id in 3...300 { GhostBasePublicPeerNameStore.store(peerId: PeerId(value: Int64(id)), firstName: "Name", lastName: "") }
precondition(GhostBasePublicPeerNameStore.name(peerId: PeerId(value: 1)) == nil)
precondition((defaults.storage["jerkgram.PublicPeerNames.V11T"] as! [String: String]).count == 256)
precondition(defaults.reads == 2)
let fm = FileManager.default
let root = fm.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try fm.createDirectory(at: root, withIntermediateDirectories: true)
defer { try? fm.removeItem(at: root) }
let box = MediaBox(root.path)
let resource = Resource(id: ResourceId(stringRepresentation: "source"))
let payload = Data("original bytes".utf8)
try payload.write(to: root.appendingPathComponent("source"))
let media = TelegramMediaFile(fileName: "file.bin", mimeType: "application/octet-stream", resource: resource)
let messageId = MessageId(peerId: PeerId(value: 77), namespace: 0, id: 1)
let message = Message(id: messageId, media: [media])
let cacheRoot = GhostBaseDeletedMediaCache.root(mediaBox: box)
try fm.createDirectory(at: cacheRoot, withIntermediateDirectories: true)
for id in 0..<100 { try fm.createDirectory(at: cacheRoot.appendingPathComponent("empty-\(id)"), withIntermediateDirectories: true) }
let live = cacheRoot.appendingPathComponent("live")
try fm.createDirectory(at: live, withIntermediateDirectories: true)
try payload.write(to: live.appendingPathComponent("keep"))
let link = cacheRoot.appendingPathComponent("symlink")
try fm.createSymbolicLink(at: link, withDestinationURL: root)
GhostBaseDeletedMediaCache.preserve(mediaBox: box, message: message)
GhostBaseDeletedMediaCache.fixtureDrain()
let recovered = GhostBaseDeletedMediaCache.resolvePath(mediaBox: box, messageId: messageId, media: media)!
GhostBaseDeletedMediaCache.fixtureDrain()
let recoveredBytes = try Data(contentsOf: URL(fileURLWithPath: recovered))
precondition(recoveredBytes == payload)
let retainedBytes = try Data(contentsOf: live.appendingPathComponent("keep"))
precondition(retainedBytes == payload)
precondition(fm.fileExists(atPath: link.path))
for id in 0..<100 { precondition(!fm.fileExists(atPath: cacheRoot.appendingPathComponent("empty-\(id)").path)) }
// Exercise the already-on-cache-queue path: no recursive sync deadlock.
GhostBaseDeletedMediaCache.fixtureResolve(box: box, id: messageId, media: media)
print("Actual cache PASS: one-time reads, unchanged-write suppression, LRU/256 bound, byte preservation, empty-directory pruning, symlink safety and queue reentrancy")
'''
def main():
    text = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift').read_text()
    owners = '\n'.join(block(text, token) for token in (
        'private enum GhostBasePublicPeerNameStore',
        'private struct GhostBaseDeletedMediaResourceSpec',
        'private func ghostBasePruneEmptyDeletedMediaDirectories(',
        'private enum GhostBaseDeletedMediaCache',
    ))
    extra = '''extension GhostBaseDeletedMediaCache {
        static func fixtureDrain() { self.queue.sync {} }
        static func fixtureResolve(box: MediaBox, id: MessageId, media: Media) {
            self.queue.sync { precondition(self.resolvePath(mediaBox: box, messageId: id, media: media) != nil) }
        }
    }'''
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'main.swift'
        target.write_text(FACADE + '\n' + owners + '\n' + extra + '\n' + CHECKS)
        subprocess.run(['xcrun', 'swift', str(target)], check=True, timeout=60)
if __name__ == '__main__': main()
