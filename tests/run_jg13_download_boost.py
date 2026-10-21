"""Run the real policy, scoped settings cache and stock request alignment on macOS."""
import os
from pathlib import Path
import subprocess
import tempfile
from run_jg13_deleted_reply import block

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
policy = (SOURCE / 'submodules/TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift').read_text()
fetch = (SOURCE / 'submodules/TelegramCore/Sources/Network/FetchV2.swift').read_text()
alignment = block(fetch, 'private func alignPartFetchRange(')
lengths = fetch.split('private let possiblePartLengths:', 1)[1].split('\n', 1)[0]
fixture = r'''
var count = 0
let sizes: [Int64?] = [nil, 0, 512 * 1024, 1024 * 1024, 1024 * 1024 + 1, 100 * 1024 * 1024]
for mode in JerkgramDownloadBoostMode.allCases {
    for size in sizes {
        for fast in [false, true] {
            for story in [false, true] {
                for encrypted in [false, true] {
                    for cdn in [false, true] {
                        let p = JerkgramDownloadBoostPolicy.parameters(mode: mode, size: size, isStory: story, fastDownloads: fast, encrypted: encrypted, isCdn: cdn)
                        let eligible = !cdn && !encrypted && (size ?? 0) > 1024 * 1024 && mode != .off
                        if !eligible {
                            precondition(p.mode == .off)
                            precondition(p.partSize == (cdn ? 128 * 1024 : (story ? 512 * 1024 : 128 * 1024)))
                            precondition(p.maxPendingParts == (fast ? (cdn ? 32 : 16) : 6))
                            precondition(p.initialWindow == 6 && p.adaptiveLargePartSize == 512 * 1024)
                        } else {
                            precondition(p.partSize == (mode == .medium ? 512 * 1024 : 1024 * 1024))
                            precondition(p.maxPendingParts == (fast ? 16 : (mode == .medium ? 8 : 12)))
                            precondition(p.initialWindow == (fast ? (mode == .medium ? 8 : 12) : 6))
                            precondition(p.adaptiveLargePartSize == p.partSize)
                        }
                        precondition(p.partSize <= 1024 * 1024 && p.maxPendingParts <= 32)
                        count += 1
                    }
                }
            }
        }
    }
}
for fast in [false, true] {
    let medium = JerkgramDownloadBoostPolicy.parameters(mode: .medium, size: 10_000_000, isStory: false, fastDownloads: fast, encrypted: false)
    let maximum = JerkgramDownloadBoostPolicy.parameters(mode: .maximum, size: 10_000_000, isStory: false, fastDownloads: fast, encrypted: false)
    precondition(maximum.partSize > medium.partSize)
    precondition(fast ? maximum.initialWindow > medium.initialWindow : maximum.maxPendingParts > medium.maxPendingParts)
}
let alignmentLengths: [Int64] = [128 * 1024, 512 * 1024, 1024 * 1024]
let alignmentOffsets: [Int64] = [0, 4095, 4096, 131071, 1048575, 1048576, 4_294_967_297]
for length in alignmentLengths {
    for offset in alignmentOffsets {
        let r = alignPartFetchRange(partRange: offset ..< offset + length, minPartSize: 4096, maxPartSize: 1024 * 1024, alignment: 4096, boundaryLimit: 1024 * 1024)
        precondition(r.fetchRange.lowerBound % 4096 == 0)
        precondition(r.fetchRange.count <= 1024 * 1024)
        precondition(r.fetchRange.lowerBound / (1024 * 1024) == (r.fetchRange.upperBound - 1) / (1024 * 1024))
        precondition(r.fetchRange.lowerBound <= r.partRange.lowerBound && r.fetchRange.upperBound >= r.partRange.upperBound)
    }
}
let account: Int64 = -8_651_650
let other: Int64 = -8_651_651
let key = JerkgramDownloadBoostSettings.scopedKey(accountPeerId: account)
let otherKey = JerkgramDownloadBoostSettings.scopedKey(accountPeerId: other)
let defaults = UserDefaults.standard
let globalKey = JerkgramDownloadBoostSettings.preferenceKey
let oldGlobal = defaults.object(forKey: globalKey)
let old = defaults.object(forKey: key), oldOther = defaults.object(forKey: otherKey)
defer {
    if let oldGlobal { defaults.set(oldGlobal, forKey: globalKey) } else { defaults.removeObject(forKey: globalKey) }
    if let old { defaults.set(old, forKey: key) } else { defaults.removeObject(forKey: key) }
    if let oldOther { defaults.set(oldOther, forKey: otherKey) } else { defaults.removeObject(forKey: otherKey) }
}
defaults.removeObject(forKey: key); defaults.removeObject(forKey: otherKey)
defaults.set("maximum", forKey: globalKey)
precondition(JerkgramDownloadBoostSettings.readStoredMode(accountPeerId: account) == .off)
precondition(JerkgramDownloadBoostSettings.readStoredMode(accountPeerId: other) == .off)
precondition(JerkgramDownloadBoostSettings.mode(accountPeerId: account) == .off)
precondition(JerkgramDownloadBoostSettings.mode(accountPeerId: other) == .off)
JerkgramDownloadBoostSettings.update(accountPeerId: account, rawValue: "medium")
let active = JerkgramDownloadBoostPolicy.parameters(mode: JerkgramDownloadBoostSettings.mode(accountPeerId: account), size: 10_000_000, isStory: false, fastDownloads: false, encrypted: false)
JerkgramDownloadBoostSettings.update(accountPeerId: account, rawValue: "maximum")
precondition(active.maxPendingParts == 8 && active.partSize == 512 * 1024)
precondition(JerkgramDownloadBoostSettings.mode(accountPeerId: account) == .maximum)
precondition(JerkgramDownloadBoostSettings.mode(accountPeerId: other) == .off)
JerkgramDownloadBoostSettings.update(accountPeerId: account, rawValue: "invalid")
precondition(JerkgramDownloadBoostSettings.mode(accountPeerId: account) == .off)
for _ in 0 ..< 32 { precondition(JerkgramDownloadBoostSettings.takeDebugLogSlot()) }
precondition(!JerkgramDownloadBoostSettings.takeDebugLogSlot())
print("PASS: real Download Boost policy", count, "cases; stock Off/CDN/encrypted/small/unknown, bounded modes, >4GiB alignment, account isolation, immutable active snapshot, log budget 32")
'''
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / 'main.swift'
    path.write_text(policy + '\nprivate let possiblePartLengths:' + lengths + '\n' + alignment + '\n' + fixture)
    subprocess.run(['xcrun', 'swift', str(path)], check=True)
