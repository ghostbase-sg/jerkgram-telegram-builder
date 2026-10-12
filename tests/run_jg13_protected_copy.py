"""Compile the actual source-message link helper; no transport/UI claims."""
import os
from pathlib import Path
import subprocess
import tempfile
from run_jg13_deleted_reply import FACADE, block
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
def main():
    source = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift').read_text()
    helper = '\n'.join(block(source, name) for name in (
        'private func ghostBaseProtectedCopyFailureText(',
        'private func ghostBaseProtectedForwardAllowsTextFallback(',
        'private func ghostBaseProtectedSourceMessageLink(',
        'private func ghostBaseProtectedForwardEnabled(',
        'private func ghostBaseProtectedForwardText(',
        'private func ghostBaseShiftEntities(',
    ))
    budget = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/JerkgramDeletedReplyText.swift').read_text()
    checks = r'''
precondition(ghostBaseProtectedSourceMessageLink(username: "channel", channelId: 123, messageId: 456) == "https://t.me/channel/456")
precondition(ghostBaseProtectedSourceMessageLink(username: nil, channelId: 123, messageId: 456) == "https://t.me/c/123/456")
precondition(ghostBaseProtectedSourceMessageLink(username: "user", channelId: nil, messageId: 456) == nil)
precondition(ghostBaseProtectedSourceMessageLink(username: nil, channelId: nil, messageId: 456) == nil)
precondition(ghostBaseProtectedCopyFailureText(languageCode: "ru-RU").hasPrefix("Не удалось"))
precondition(ghostBaseProtectedCopyFailureText(languageCode: "ru_RU").hasPrefix("Не удалось"))
precondition(ghostBaseProtectedCopyFailureText(languageCode: "en").hasPrefix("Could not"))
let pollFallback = TelegramMediaPoll(text: "Poll", textEntities: [], options: [])
precondition(ghostBaseProtectedForwardAllowsTextFallback(pollFallback))
let todoFallback = TelegramMediaTodo(text: "Todo", textEntities: [], items: [], completions: [])
precondition(ghostBaseProtectedForwardAllowsTextFallback(todoFallback))
precondition(!ghostBaseProtectedForwardAllowsTextFallback(nil))
precondition(!ghostBaseProtectedForwardAllowsTextFallback("binary placeholder"))
for kind in 0..<5 {
    precondition(ghostBaseProtectedForwardEnabled(enabled: true, chatForward: true, messageProtected: kind == 0, peerProtected: kind == 1, dmProtected: kind == 2, myDmProtected: kind == 3, channelRestricted: kind == 4))
}
precondition(!ghostBaseProtectedForwardEnabled(enabled: false, chatForward: true, messageProtected: true, peerProtected: true, dmProtected: true, myDmProtected: true, channelRestricted: true))
precondition(!ghostBaseProtectedForwardEnabled(enabled: true, chatForward: false, messageProtected: true, peerProtected: true, dmProtected: true, myDmProtected: true, channelRestricted: true))
precondition(!ghostBaseProtectedForwardEnabled(enabled: true, chatForward: true, messageProtected: false, peerProtected: false, dmProtected: false, myDmProtected: false))
let body = "😀 caption"
let entities = [MessageTextEntity(range: 0..<2, type: .Bold)]
let normal = ghostBaseProtectedForwardText(title: "Channel", link: "https://t.me/channel/456", mentionPeerId: nil, body: body, bodyEntities: entities, hideNames: false, limit: 1024, languageCode: "en")
precondition(normal.text == "Channel\n😀 caption")
precondition(normal.entities.contains { $0.range == 8..<10 && $0.type == .Bold })
precondition(normal.entities.contains { $0.range == 0..<7 && $0.type == .TextUrl(url: "https://t.me/channel/456") })
let hidden = ghostBaseProtectedForwardText(title: "Channel", link: "https://t.me/channel/456", mentionPeerId: nil, body: body, bodyEntities: entities, hideNames: true, limit: 1024, languageCode: "en")
precondition(hidden.text == body && hidden.entities == entities)
let captionHidden = ghostBaseProtectedForwardText(title: "Channel", link: nil, mentionPeerId: 123, body: "", bodyEntities: [], hideNames: false, limit: 1024, languageCode: "en")
precondition(captionHidden.text == "Channel")
precondition(captionHidden.entities.contains { $0.type == .TextMention(peerId: 123) })
let large = "😀" + String(repeating: "x", count: 5000)
for limit in [1024, 2048, 4096] {
    let clipped = ghostBaseProtectedForwardText(title: "Channel", link: nil, mentionPeerId: nil, body: large, bodyEntities: [MessageTextEntity(range: 0..<5002, type: .Bold)], hideNames: false, limit: limit, languageCode: "en")
    precondition((clipped.text as NSString).length <= limit && !clipped.text.contains("�"))
    precondition(clipped.entities.allSatisfy { $0.range.upperBound <= (clipped.text as NSString).length })
}
print("actual protected helpers: source links, settings/protection gates, UTF-16 header/entities, hidden author/caption and regular/premium budgets passed")
'''
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        target = path / 'main.swift'
        target.write_text(FACADE + '\n' + budget + '\n' + helper + '\nprivate func fixture() {\n' + checks + '\n}\nfixture()\n')
        subprocess.run(['xcrun', 'swift', str(target)], check=True)
if __name__ == '__main__': main()
