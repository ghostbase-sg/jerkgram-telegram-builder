#!/usr/bin/env python3
"""Execute the real single-pass history fragment, not a copied implementation."""
import os
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG13_SOURCE',ROOT/'work/swiftgram-src'))
def production_fragment():
    s=(SOURCE/'submodules/TelegramUI/Sources/ChatHistoryListNode.swift').read_text()
    return s.split('// JG155 bounds begin',1)[1].split('\n',1)[1].split('// JG155 bounds end',1)[0]
FACADE=r'''
import Foundation
typealias MessageId = Int
typealias MessageIndex = Int
struct Message { let id: MessageId; let index: MessageIndex }
struct Entry { let message: Message }
struct OriginalView { let entries: [Entry] }
struct Previous { let originalView: OriginalView }
func actual(_ entries: [Entry]) -> (Set<MessageId>, MessageIndex?) {
    let previous = Previous(originalView: OriginalView(entries: entries))
'''
FIXTURE=r'''
    return (previousIds, previousLastIndex)
}
func verify(_ entries: [Entry]) {
    let expectedIds = Set(entries.map { $0.message.id })
    let expectedIndex = entries.map { $0.message.index }.max()
    let result = actual(entries)
    precondition(result.0 == expectedIds && result.1 == expectedIndex)
}
verify([])
verify([Entry(message: Message(id: 1, index: -5))])
verify([Entry(message: Message(id: 1, index: 4)), Entry(message: Message(id: 1, index: -2)), Entry(message: Message(id: 3, index: 9))])
var seed: UInt64 = 17
for count in 0..<512 {
    var entries: [Entry] = []
    for _ in 0..<count {
        seed = seed &* 6364136223846793005 &+ 1
        entries.append(Entry(message: Message(id: Int(seed % 31), index: Int((seed >> 8) % 10001) - 5000)))
    }
    verify(entries)
    verify(Array(entries.reversed()))
}
print("history-bounds component PASS: actual production fragment matches former ID-set/max-index algorithm for empty, negative, duplicate, unordered and 1024 deterministic varied cases; no message content")
'''
if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='jg13-history-bounds-') as directory:
        target=Path(directory)/'main.swift'
        target.write_text(FACADE+production_fragment()+FIXTURE)
        subprocess.run(['xcrun','swift',str(target)],check=True)
