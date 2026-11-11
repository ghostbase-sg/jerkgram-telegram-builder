"""Compile exact production storage with pinned protocol/codecs and SQLite adapter."""
from pathlib import Path
import hashlib, json, shutil, subprocess, tempfile


def declaration(source, anchor):
    start = source.index(anchor)
    opening = source.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def verify_fixture(root):
    """Portable integrity proof for every pinned input used by the compiler."""
    import re
    fixture = root/'tests/fixtures/beta2_saved_tags'
    for directory in (fixture, root/'tests/fixtures/beta2_bot_codec'):
        manifest = json.loads((directory/'PROVENANCE.json').read_text())
        assert manifest.get('upstream', manifest.get('ref')) == '279f89e4d4f63f17227bf877dc3d8990f22ecd58'
        for row in manifest['files']:
            data = (directory/'official'/row['path']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
            expected = row.get('git_blob_sha1', row.get('sha'))
            assert hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest() == expected, row['path']
    protocol = (fixture/'official/submodules/Postbox/Sources/ValueBox.swift').read_text().split('public protocol ValueBox {')[1]
    adapter = (fixture/'SQLiteValueBox.swift').read_text()
    # Every protocol operation exists verbatim in the adapter. Unsupported
    # operations trap; they cannot quietly substitute a fake implementation.
    for line in protocol.splitlines():
        line = line.strip()
        if line.startswith('func '):
            compact = lambda value: re.sub(r'\s+', '', value)
            assert compact(line) in compact(adapter), line


def assemble(root, source, folder):
    """Assemble exact sources without executing or claiming a native build."""
    fixture = root/'tests/fixtures/beta2_saved_tags'
    official = root/'tests/fixtures/beta2_bot_codec/official/submodules'
    support = fixture/'official/submodules/Postbox/Sources'
    extracted = '\n'.join(declaration((support/name).read_text(), anchor) for name, anchor in (
        ('Peer.swift','public struct PeerId:'), ('Message.swift','public struct MessageId:')))
    extracted += '\n'+declaration((official/'Postbox/Sources/MediaResource.swift').read_text(), 'public struct MediaResourceId:')
    (folder/'Identity.swift').write_text('import Foundation\n'+extracted)
    postbox = (source/'submodules/Postbox/Sources/Postbox.swift').read_text()
    assert postbox.count('// BEGIN LOCAL SAVED TAGS TRANSACTION API') == 1
    api = postbox.split('// BEGIN LOCAL SAVED TAGS TRANSACTION API')[1].split('// END LOCAL SAVED TAGS TRANSACTION API')[0]
    # Sink is the real PostboxImpl method, including its exact operation field.
    sink = declaration(postbox, 'fileprivate func setPreferencesEntry(key: ValueBoxKey, value: PreferencesEntry?)')
    boundary = (fixture/'TransactionBoundary.swift').read_text().replace('/* EXACT_TRANSACTION_API */', api).replace('/* EXACT_PREFERENCES_SINK */', sink)
    (folder/'Boundary.swift').write_text(boundary)
    (folder/'main.swift').write_text((fixture/'native.swift').read_text())
    sources = [p for p in sorted((official/'Postbox/Sources').rglob('*.swift')) if p.name != 'MediaResource.swift']
    sources += [support/name for name in ('Table.swift','ValueBox.swift','ValueBoxKey.swift','PreferencesTable.swift')]
    return sources + [source/'submodules/Postbox/Sources/LocalSavedTagsTable.swift',fixture/'SQLiteValueBox.swift',folder/'Identity.swift',folder/'Boundary.swift',folder/'main.swift']


def run_native(root, source, assembler=assemble, expected=None):
    verify_fixture(root)
    official = root/'tests/fixtures/beta2_bot_codec/official/submodules'
    for opt in ('-Onone', '-O'):
        with tempfile.TemporaryDirectory(prefix='saved-tags-native-') as tmp:
            folder = Path(tmp)
            include = folder/'include'; headers = include/'MurMurHash32'; headers.mkdir(parents=True)
            shutil.copyfile(official/'MurMurHash32/PublicHeaders/MurMurHash32/MurMurHash32.h', headers/'MurMurHash32.h')
            (include/'module.modulemap').write_text('module MurMurHash32 { header "MurMurHash32/MurMurHash32.h" export * }\n')
            obj = folder/'hash.o'
            subprocess.run(['xcrun','clang','-fobjc-arc','-I',str(include),'-c',str(official/'MurMurHash32/Sources/MurMurHash32.m'),'-o',str(obj)],check=True,timeout=60)
            sources = assembler(root, source, folder)
            exe = folder/'store'
            subprocess.run(['xcrun','swiftc','-swift-version','5',opt,'-I',str(include),*map(str,sources),str(obj),'-framework','Foundation','-lsqlite3','-o',str(exe)],check=True,timeout=180)
            result = subprocess.run([str(exe),str(folder)],capture_output=True,text=True,timeout=600)
            print(result.stdout, end='')
            assert result.returncode == 0, result.stdout+result.stderr
            assert (expected or 'PASS actual production Saved Tags table with SQLite storage') in result.stdout
            reopened = subprocess.run([str(exe),str(folder),'--reopen-process'],capture_output=True,text=True,timeout=30)
            print(reopened.stdout, end='')
            assert reopened.returncode == 0, reopened.stdout+reopened.stderr
            assert 'PASS fresh-process SQLite reopen' in reopened.stdout
