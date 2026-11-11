"""Exact pinned algorithms with explicit Foundation boundary types, not UIKit."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

PANEL = 'submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift'
HISTORY = 'submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift'
MODEL = 'submodules/TelegramCore/Sources/ChatInputContent/ChatInputContentModel.swift'
CONVERSION = 'submodules/TextFormat/Sources/ChatInputContentConversion.swift'


def declaration(source, anchor):
    """Extract one complete Swift declaration, ignoring comment/string braces."""
    start = source.index(anchor)
    i = source.index('{', start)
    depth = 0
    while i < len(source):
        if source.startswith('//', i):
            i = source.index('\n', i) + 1
            continue
        if source.startswith('/*', i):
            level = 1
            i += 2
            while level:
                if source.startswith('/*', i):
                    level += 1
                    i += 2
                elif source.startswith('*/', i):
                    level -= 1
                    i += 2
                else:
                    i += 1
            continue
        if source[i] == '"':
            delimiter = '"""' if source.startswith('"""', i) else '"'
            i += len(delimiter)
            while not source.startswith(delimiter, i):
                i += 2 if source[i] == '\\' else 1
            i += len(delimiter)
            continue
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
        i += 1
    raise AssertionError('Unclosed declaration: ' + anchor)


def verify_fixture(root):
    fixture = root / 'tests/fixtures/wave2a1'
    values = json.loads((fixture / 'PROVENANCE.json').read_text())
    assert values['upstream'] == '279f89e4d4f63f17227bf877dc3d8990f22ecd58'
    assert {r['path'] for r in values['files']} == {MODEL, CONVERSION}
    for row in values['files']:
        data = (fixture / 'official' / row['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
        assert hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == row['git_blob_sha1'], row['path']


def literal(source):
    helper = declaration(source, 'private func consumeJerkgramSynchronousInputEcho(')
    match = re.search(r'configuration: configuration, literalText: \{ ([^\n]+?) \},', helper)
    assert match, 'Actual echo literal callback missing'
    return match.group(1)


def predicate(source):
    end = source.index('        var contentTypeHint: ChatMessageEntryContentType')
    start = source.rfind('        if !ghostBaseShowDeleted {', 0, end)
    if start < 0:
        start = source.rfind('        let ghostBaseIsDeleted =', 0, end)
    assert start >= 0
    return source[start:end].strip()


def assemble(root, source, before, directory):
    verify_fixture(root)
    fixture = root / 'tests/fixtures/wave2a1'
    model = (fixture / 'official' / MODEL).read_text()
    conversion = (fixture / 'official' / CONVERSION).read_text()
    anchors = [
        'public struct ChatInputRun:', 'public struct ChatInputInlineAttributes:',
        'public enum ChatInputInlineEntity:', 'public struct ChatInputParagraph:',
        'public enum ChatInputParagraphStyle:', 'public enum ChatInputListMarker:',
        'public struct ChatInputListMembership:', 'public struct ChatInputCode:',
        'public struct ChatInputPullQuote:', 'extension ChatInputPullQuote: Codable',
        'public struct ChatInputBlockQuote:', 'extension ChatInputBlockQuote: Codable',
        'public enum ChatInputBlock:'
    ]
    declarations = '\n\n'.join(declaration(model, anchor) for anchor in anchors)
    boundary = (fixture / 'Boundary.swift').read_text().replace(
        '/* EXACT_PLAIN_TEXT_GETTER */', declaration(model, 'public var plainText: String'))
    projector = declaration(conversion, 'public func attributedString(from content:')
    projector = projector.replace('public func attributedString(', 'func officialAttributedString(', 1)
    parts = ['import Foundation', boundary, declarations,
             declaration(conversion, 'private func listMarkerText('), projector]
    for name, tree in [('old', before), ('new', source)]:
        expression = literal((tree / PANEL).read_text())
        parts.append(f'func {name}Literal(_ state: InputState) -> String {{ return {expression} }}')
        body = predicate((tree / HISTORY).read_text()).replace('continue loop', 'return false')
        parts.append(f'func {name}Allows(_ ghostBaseShowDeleted: Bool, _ message: FixtureMessage) -> Bool {{\n{body}\nreturn true\n}}')
    parts.append((fixture / 'cases.swift').read_text())
    output = directory / 'main.swift'
    output.write_text('\n\n'.join(parts) + '\n')
    assert '/* EXACT_' not in output.read_text()
    return output


def run_native(root, source, before):
    if not shutil.which('xcrun') or not shutil.which('swiftc'):
        raise RuntimeError('Wave2A1 native verification requires macOS Swift/xcrun; no behavioral PASS available')
    for optimization in ('-Onone', '-O'):
        with tempfile.TemporaryDirectory(prefix='wave2a1-native-') as tmp:
            directory = Path(tmp)
            main = assemble(root, source, before, directory)
            executable = directory / 'wave2a1'
            subprocess.run(['xcrun', 'swiftc', '-swift-version', '5', optimization,
                            str(main), '-o', str(executable)], check=True, timeout=90)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
            print(result.stdout, end='')
            assert result.returncode == 0, result.stdout + result.stderr
            assert 'PASS actual pinned plainText/projection' in result.stdout
