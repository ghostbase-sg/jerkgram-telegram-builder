#!/usr/bin/env python3
"""Run the actual production ping predicate with focused Swift value fixtures."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "work/swiftgram-src/submodules/TelegramCore/Sources/TelegramEngine/Messages/ChatList.swift").read_text()
needle = "private func jerkgramBuild133ActivityVisible("
assert source.count(needle) == 1
start = source.index(needle)
brace = source.index("{", start)
depth = 1
end = brace + 1
while depth:
    if source[end] == "{":
        depth += 1
    elif source[end] == "}":
        depth -= 1
    end += 1
predicate = source[start:end]
fixture = '''import Foundation
struct PeerId { let value: Int }
struct MessageTags: OptionSet {
    let rawValue: Int
    static let unseenPersonalMessage = MessageTags(rawValue: 1)
    static let unseenReaction = MessageTags(rawValue: 2)
}
struct Message { let tags: MessageTags; let filtered: Bool }
'''
cases = '''
let sampleAccount = PeerId(value: 1)
let ordinary = Message(tags: .unseenPersonalMessage, filtered: false)
let filtered = Message(tags: .unseenPersonalMessage, filtered: true)
let unrelated = Message(tags: .unseenReaction, filtered: true)
func check(_ name: String, stock: Bool = true, expected: Int, account: PeerId? = sampleAccount, messages: [Message], result: Bool) {
    let actual = jerkgramBuild133ActivityVisible(stock: stock, expectedCount: expected, accountPeerId: account, messages: messages, tag: .unseenPersonalMessage, hidden: { _, message in message.filtered })
    precondition(actual == result, name)
    print("PASS: " + name)
}
check("ordinary ping remains", expected: 1, messages: [ordinary], result: true)
check("hard-filtered ping is hidden", expected: 1, messages: [filtered], result: false)
check("mixed history keeps ordinary ping", expected: 2, messages: [filtered, ordinary], result: true)
check("incomplete evidence preserves summary", expected: 2, messages: [filtered], result: true)
check("unrelated tags do not erase ping", expected: 1, messages: [unrelated], result: true)
check("missing account preserves summary", expected: 1, account: nil, messages: [filtered], result: true)
check("no stock ping creates none", stock: false, expected: 1, messages: [ordinary], result: false)
'''
with tempfile.TemporaryDirectory(prefix="jg13-pings-") as tmp:
    p = Path(tmp) / "main.swift"
    p.write_text(fixture + predicate + cases)
    subprocess.run(["xcrun", "swift", str(p)], check=True)
