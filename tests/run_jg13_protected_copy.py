"""Compile the actual source-message link helper; no transport/UI claims."""
import os
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/recovery159'))
def main():
    source = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift').read_text()
    start = source.index('private func ghostBaseProtectedSourceMessageLink(')
    cursor = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[cursor] == '{') - (source[cursor] == '}')
        cursor += 1
    helper = source[start:cursor]
    checks = '''
precondition(ghostBaseProtectedSourceMessageLink(username: "channel", channelId: 123, messageId: 456) == "https://t.me/channel/456")
precondition(ghostBaseProtectedSourceMessageLink(username: nil, channelId: 123, messageId: 456) == "https://t.me/c/123/456")
precondition(ghostBaseProtectedSourceMessageLink(username: "user", channelId: nil, messageId: 456) == nil)
precondition(ghostBaseProtectedSourceMessageLink(username: nil, channelId: nil, messageId: 456) == nil)
print("protected source-message links: 4 passed")
'''
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        (path / 'main.swift').write_text('import Foundation\n' + helper + checks)
        subprocess.run(['swiftc', str(path / 'main.swift'), '-o', str(path / 'check')], check=True)
        subprocess.run([str(path / 'check')], check=True)
if __name__ == '__main__': main()
