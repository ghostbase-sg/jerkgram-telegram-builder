import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import tracemalloc
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
package = importlib.import_module("package_jg13")


class PackageDigestTests(unittest.TestCase):
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
