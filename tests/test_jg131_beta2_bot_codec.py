"""Recovery codec source guards and actual pinned Postbox native regression.

Run this file directly. JG_BETA2_REQUIRE_NATIVE=1 makes missing Swift a failure.
JG_BETA2_CODEC_OWNER may point to the final staged owner for the Task 3 gate.
"""
import os
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/beta2_bot_codec'
OWNER = Path(os.environ.get('JG_BETA2_CODEC_OWNER', str(
    ROOT.parent / 'jerkgram-next/beta2/recovery/source/submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift')))
COUNTERS = ('schema', 'reservedPages', 'committedPages', 'examined', 'inserted',
            'insertedPeers', 'insertedUsers', 'insertedChats', 'deleteIdsObserved',
            'skipped', 'unsupported', 'deletions', 'missingReferences')


def declaration(source, anchor):
    start = source.index(anchor)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def policy(source):
    return source.split('// BEGIN BOTBRIDGE POLICY\n')[1].split('// END BOTBRIDGE POLICY')[0]


def compile_fixture(folder, optimization, old=False):
    """Full pinned codec, exact supporting declaration, real ObjC hash module."""
    official = FIXTURE / 'official/submodules'
    includes = folder / 'include'
    header_dir = includes / 'MurMurHash32'
    header_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(official / 'MurMurHash32/PublicHeaders/MurMurHash32/MurMurHash32.h', header_dir / 'MurMurHash32.h')
    (includes / 'module.modulemap').write_text(
        'module MurMurHash32 { header "MurMurHash32/MurMurHash32.h" export * }\n')
    obj = folder / 'MurMurHash32.o'
    clang = subprocess.run(['xcrun', 'clang', '-fobjc-arc', '-I', str(includes), '-c',
        str(official / 'MurMurHash32/Sources/MurMurHash32.m'), '-o', str(obj)],
        capture_output=True, text=True, timeout=60)
    if clang.returncode:
        raise AssertionError(clang.stdout + clang.stderr)
    # This support type is copied verbatim, rather than pulling unrelated media,
    # peer, message and cache subsystems into a standalone codec executable.
    media = (official / 'Postbox/Sources/MediaResource.swift').read_text()
    (folder / 'MediaResourceId.swift').write_text('import Foundation\n' + declaration(media, 'public struct MediaResourceId:'))
    source = OWNER.read_text()
    if old:
        main = 'import Foundation\n' + (FIXTURE / 'old-policy.swift').read_text() + (FIXTURE / 'old-native.swift').read_text()
    else:
        storage = '\n'.join(declaration(source, anchor) for anchor in [
            'private func botBridgeValidatedAccount(', 'private func botBridgeReadProgress(',
            'func jerkgramPrepareBotBridgeHistory(', 'private func botBridgeWriteProgress('])
        main = 'import Foundation\n' + policy(source) + (FIXTURE / 'native.swift').read_text().replace('/* REAL_STORAGE_BOUNDARY */', storage)
    (folder / 'main.swift').write_text(main)
    sources = sorted((official / 'Postbox/Sources').rglob('*.swift'))
    sources = [p for p in sources if p.name != 'MediaResource.swift']
    executable = folder / 'codec'
    command = [shutil.which('swiftc'), '-swift-version', '5', optimization, '-I', str(includes),
               *map(str, sources), str(folder / 'MediaResourceId.swift'), str(folder / 'main.swift'),
               str(obj), '-framework', 'Foundation', '-o', str(executable)]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if compiled.returncode:
        raise AssertionError(compiled.stdout + compiled.stderr)
    return executable


class CodecSourceContract(unittest.TestCase):
    maxDiff = 2000

    def test_pinned_official_codec_bytes_and_old_policy(self):
        manifest = json.loads((FIXTURE / 'PROVENANCE.json').read_text())
        self.assertEqual(manifest['ref'], '279f89e4d4f63f17227bf877dc3d8990f22ecd58')
        for row in manifest['files']:
            data = (FIXTURE / 'official' / row['path']).read_bytes()
            self.assertEqual(hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest(), row['sha'], row['path'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'], row['path'])
        old = (FIXTURE / 'old-policy.swift').read_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(), manifest['old_policy']['sha256'])
        self.assertNotIn('func encode(to encoder:', old.decode())
        self.assertIn('func singleValueContainer() -> SingleValueEncodingContainer {\n        preconditionFailure()',
            (FIXTURE / 'official/submodules/Postbox/Sources/Utils/Encoder/AdaptedPostboxEncoder.swift').read_text())

    def test_explicit_supported_progress_codec(self):
        source = OWNER.read_text()
        self.assertIn('init(from decoder: Decoder) throws', source)
        self.assertIn('func encode(to encoder: Encoder) throws', source)
        for key in COUNTERS:
            self.assertIn(f'Int(try container.decode(Int32.self, forKey: .{key}))', source)
            self.assertIn(f'try wireInt32({key}, key: .{key})', source)
        self.assertIn('container.encodeIfPresent(terminal?.rawValue, forKey: .terminal)', source)
        self.assertIn('container.decodeIfPresent(String.self, forKey: .terminal)', source)
        self.assertIn('Int32(exactly: value)', source)
        self.assertIn('PreferencesEntry(progress.validatedForStorage)', source)
        self.assertIn('key.setInt32(0, value: 0x4A470002)', source)

    def test_existing_policy_algorithms_are_unchanged(self):
        source = policy(OWNER.read_text())
        start = source.index('    // Postbox supports keyed Int32 primitives,')
        end = source.index('    var isValid: Bool {\n        guard schema == 1', start)
        self.assertEqual(source[:start] + source[end:], (FIXTURE / 'old-policy.swift').read_text())
        # The Encodable constructor is a single centralized, validated write.
        import re
        self.assertEqual(re.findall(r'(?<![A-Za-z])PreferencesEntry\(([^\n]*)', OWNER.read_text()),
                         ['progress.validatedForStorage) })'])


class ActualPostboxNative(unittest.TestCase):
    def test_actual_pinned_codec_both_optimizations(self):
        if not shutil.which('swiftc') or not shutil.which('xcrun'):
            if os.environ.get('JG_BETA2_REQUIRE_NATIVE') == '1':
                self.fail('Mandatory native gate requires macOS Swift/Clang; native remains pending')
            self.skipTest('No macOS Swift/Clang: actual Postbox native regression pending')
        release_bytes = None
        for optimization in ['-O', '-Onone']:
            with self.subTest(optimization=optimization), tempfile.TemporaryDirectory(prefix='beta2-codec-') as tmp:
                folder = Path(tmp)
                old = folder / 'old'; old.mkdir()
                executable = compile_fixture(old, optimization, old=True)
                legacy = folder / 'release178.bin'
                result = subprocess.run([str(executable), 'save', str(legacy)], capture_output=True, text=True, timeout=30)
                self.assertIn('OLD_INITIAL_INT_WRITE', result.stderr)
                if optimization == '-O':
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn('OLD_INT_DECODE_NIL', result.stderr)
                    release_bytes = legacy.read_bytes()
                    trapped = subprocess.run([str(executable), 'terminal'], capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(trapped.returncode, 0, 'Old optimized terminal must trap')
                    self.assertIn('OLD_TERMINAL_WRITE', trapped.stderr)
                    self.assertNotIn('old terminal unexpectedly encoded', trapped.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0, 'Old debug Int write must assert')
                    self.assertNotIn('OLD_INT_DECODE_NIL', result.stderr)
                    self.assertIsNotNone(release_bytes)
                    legacy.write_bytes(release_bytes)
                fixed = folder / 'fixed'; fixed.mkdir()
                executable = compile_fixture(fixed, optimization)
                command = [str(executable), str(legacy)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('PASS actual pinned PreferencesEntry/Postbox codec', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
