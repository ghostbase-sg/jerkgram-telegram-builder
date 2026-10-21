"""Execute actual Core policy, actual CachedMessage guard and profile capture helper."""
import os
from pathlib import Path
import subprocess
import tempfile
from run_jg13_deleted_reply import block

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
core = SOURCE / 'submodules/TelegramCore/Sources'
policy = (core / 'Utils/JerkgramSponsoredContentPolicy.swift').read_text()
ads = (core / 'TelegramEngine/Messages/AdMessages.swift').read_text()
guard = ads.split('func toMessage(peerId: PeerId, transaction: Transaction, removeSponsored: Bool) -> Message? {', 1)[1].split('            var attributes:', 1)[0]
assert guard.count('guard JerkgramSponsoredContentPolicy.shouldDisplay') == 1
avatar = (SOURCE / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoAvatarTransformContainerNode.swift').read_text()
profile = block(avatar, 'enum JerkgramProfileCapturePolicy')
recreate = avatar.split('                    if videoContent.id != self.videoContent?.id ||', 1)[1].split(' {', 1)[0]
assert recreate.strip() == 'self.videoCaptureProtected != captureProtected'
recreate = 'videoContent.id != self.videoContent?.id ||' + recreate
identity_suffix = avatar.split('id: .profileVideo(videoId, ', 1)[1].split('), userLocation:', 1)[0]

fixture = r'''
struct Message {}
struct CachedFixture {
    enum MessageType { case sponsored, recommended }
    let messageType: MessageType
    func materialize(removeSponsored: Bool) -> Message? {
        ACTUAL_GUARD
        return Message()
    }
}
for remove in [false, true] {
    precondition((CachedFixture(messageType: .sponsored).materialize(removeSponsored: remove) != nil) == !remove)
    precondition(CachedFixture(messageType: .recommended).materialize(removeSponsored: remove) != nil)
    // Non-ad entities have no sponsored attribute and never enter this mapper.
    for _ in ["ordinary", "service", "pinned", "paid", "suggested", "recommended-channel"] {
        precondition(JerkgramSponsoredContentPolicy.shouldDisplay(isSponsored: false, removeSponsored: remove))
    }
}
let first: Int64 = -8_661_660
let second: Int64 = -8_661_661
let third: Int64 = -8_661_662
let accounts = [first, second, third]
let defaults = UserDefaults.standard
let keys = accounts.map { JerkgramSponsoredContentPolicy.scopedKey(accountPeerId: $0) }
let globalKey = JerkgramSponsoredContentPolicy.preferenceKey
let saved = (keys + [globalKey]).map { defaults.object(forKey: $0) }
defer {
    for (index, key) in (keys + [globalKey]).enumerated() {
        if let value = saved[index] { defaults.set(value, forKey: key) } else { defaults.removeObject(forKey: key) }
    }
}
for key in keys { defaults.removeObject(forKey: key) }
defaults.set(true, forKey: globalKey)
for account in accounts {
    precondition(!JerkgramSponsoredContentPolicy.readStoredValue(accountPeerId: account))
}
precondition(!JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: first))
precondition(!JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: second))
defaults.set(true, forKey: keys[2])
precondition(JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: third))
JerkgramSponsoredContentPolicy.update(accountPeerId: first, enabled: true)
let activeContextSnapshot = JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: first)
JerkgramSponsoredContentPolicy.update(accountPeerId: first, enabled: false)
precondition(activeContextSnapshot)
precondition(!JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: first))
precondition(!JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: second))
for id in Int64(-8_662_000) ..< -8_661_960 {
    JerkgramSponsoredContentPolicy.update(accountPeerId: id, enabled: true)
}
precondition(!JerkgramSponsoredContentPolicy.removeSponsored(accountPeerId: second))

enum JerkgramHotSettings {
    static var values: [String: Bool] = [:]
    static func object(forKey key: String) -> Any? { return values[key] }
}
let screenshotKey = "jerkgram.ProtectedContent.AllowScreenshots"
let recordingKey = "jerkgram.ProtectedContent.AllowScreenRecording"
let options: [Bool?] = [nil, false, true]
var cases = 0
for nativeProtected in [false, true] {
    for screenshot in options {
        for recording in options {
            JerkgramHotSettings.values = [:]
            JerkgramHotSettings.values[screenshotKey] = screenshot
            JerkgramHotSettings.values[recordingKey] = recording
            let expected = nativeProtected && !((screenshot ?? true) && (recording ?? true))
            precondition(JerkgramProfileCapturePolicy.isProtected(nativeProtected: nativeProtected) == expected)
            cases += 1
        }
    }
}
struct VideoContent { let id: Int }
struct Peer { let isCopyProtectionEnabled: Bool }
func avatarCaptureSuffix(peer: Peer, captureProtected: Bool) -> String? {
    return ACTUAL_IDENTITY_SUFFIX
}
precondition(avatarCaptureSuffix(peer: Peer(isCopyProtectionEnabled: true), captureProtected: true) == nil)
precondition(avatarCaptureSuffix(peer: Peer(isCopyProtectionEnabled: true), captureProtected: false) == "jerkgram-capture-allowed")
precondition(avatarCaptureSuffix(peer: Peer(isCopyProtectionEnabled: false), captureProtected: false) == nil)
struct AvatarCaptureDecision {
    let videoContent: VideoContent?
    let videoCaptureProtected: Bool
    func shouldRecreate(videoContent: VideoContent, captureProtected: Bool) -> Bool {
        return ACTUAL_RECREATE
    }
}
// Execute the actual constructor condition for same and changed video identities.
for previous in [false, true] {
    for current in [false, true] {
        let decision = AvatarCaptureDecision(videoContent: VideoContent(id: 7), videoCaptureProtected: previous)
        precondition(decision.shouldRecreate(videoContent: VideoContent(id: 7), captureProtected: current) == (previous != current))
        precondition(decision.shouldRecreate(videoContent: VideoContent(id: 8), captureProtected: current))
        precondition(AvatarCaptureDecision(videoContent: nil, videoCaptureProtected: previous).shouldRecreate(videoContent: VideoContent(id: 7), captureProtected: current))
    }
}
print("PASS: actual sponsored guard and policy; Off/On, recommended survival, per-account default Off/cache/isolation/eviction/snapshot; profile capture", cases, "native/paired-toggle cases")
'''
fixture = fixture.replace('ACTUAL_GUARD', guard)
fixture = fixture.replace('ACTUAL_RECREATE', recreate)
fixture = fixture.replace('ACTUAL_IDENTITY_SUFFIX', identity_suffix)
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'main.swift'
    path.write_text(policy + '\n' + profile + '\n' + fixture)
    subprocess.run(['xcrun', 'swift', str(path)], check=True)
