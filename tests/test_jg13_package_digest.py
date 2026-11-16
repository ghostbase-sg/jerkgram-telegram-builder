import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
package = importlib.import_module("package_jg13")


class PackageDigestTests(unittest.TestCase):
    def test_read_only_bazel_archive_can_be_preserved_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            source = out / 'compiled.ipa'
            source.write_bytes(b'unchanged compiled archive')
            source.chmod(0o444)
            raw = package.preserve_raw_ipa(source, out, 'test', {})
            first = raw.read_bytes()
            self.assertEqual(package.preserve_raw_ipa(source, out, 'test', {}), raw)
            self.assertEqual(package.preserve_raw_ipa(raw, out, 'test', {}), raw)
            self.assertEqual(raw.read_bytes(), first)

    def test_packaging_gets_writable_copy_of_read_only_raw(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'jerkgram-migration.json').write_text((ROOT / 'jerkgram-migration.json').read_text())
            source = root / 'compiled.ipa'
            source.write_bytes(b'untouched raw archive')
            source.chmod(0o444)
            def mutate(candidate):
                self.assertTrue(candidate.stat().st_mode & 0o200, 'candidate must be owner-writable')
                with candidate.open('ab') as output:
                    output.write(b'packaging mutation')
                raise RuntimeError('stop after successful candidate mutation')
            with patch.object(package, 'ROOT', root), patch.object(sys, 'argv', ['package', str(source)]), patch.object(package.keychain, 'package_ipa', side_effect=mutate):
                with self.assertRaisesRegex(RuntimeError, 'stop after successful candidate mutation'):
                    package.main()
            raw = next((root / 'artifacts').glob('*-RAW-UNVERIFIED.ipa'))
            self.assertEqual(raw.read_bytes(), source.read_bytes())

    def test_different_raw_archive_cannot_overwrite_first(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            source = out / 'compiled.ipa'
            source.write_bytes(b'first')
            raw = package.preserve_raw_ipa(source, out, 'test', {})
            source.write_bytes(b'second')
            with self.assertRaisesRegex(RuntimeError, 'different'):
                package.preserve_raw_ipa(source, out, 'test', {})
            self.assertEqual(raw.read_bytes(), b'first')

    def test_large_archive_digest_has_bounded_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.ipa"
            chunk = bytes(range(256)) * 4096
            expected = hashlib.sha256()
            with path.open("wb") as target:
                for _ in range(12):
                    target.write(chunk)
                    expected.update(chunk)
            tracemalloc.start()
            try:
                digest = package.sha256_file(path)
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            self.assertEqual(digest, expected.hexdigest())
            self.assertLess(peak, 3 * 1024 * 1024)

    def test_empty_archive_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty"
            path.touch()
            self.assertEqual(package.sha256_file(path), hashlib.sha256(b"").hexdigest())


if __name__ == "__main__":
    unittest.main()
