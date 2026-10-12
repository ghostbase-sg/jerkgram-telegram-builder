"""Exact patch-chain fixtures; not transport or device behavior evidence."""
import importlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class PortableCopyStageTests(unittest.TestCase):
    def setUp(self):
        self.stage = importlib.import_module("materialize_jg13_portable_copy")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name)
        self.baseline = (ROOT / "work/reply158" / self.stage.ENQUEUE).exists()
        canonical = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
        for name in self.stage.OWNERS | {self.stage.ACCOUNT}:
            original = canonical / name
            if self.baseline:
                original = ROOT / ("work/reply158" if name in self.stage.CORE_PARENT_OWNERS | {self.stage.ACCOUNT} else "work/forward159-baseline") / name
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
        for name in self.stage.read_manifest()["regression_locks"]:
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile((ROOT / "work/final157" if self.baseline else canonical) / name, target)
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        if not self.baseline:
            self.stage.check(self.source, "after")
            subprocess.run(["git", "apply", "--reverse", str(self.stage.PATCH)], cwd=self.source, check=True)

    def test_parent_apply_final_hashes_and_repeat_refusal(self):
        self.stage.apply_portable_copy(self.source)
        self.stage.verify_portable_copy(self.source)
        with self.assertRaises(RuntimeError):
            self.stage.apply_portable_copy(self.source)

    def test_tampered_owner_does_not_partly_apply(self):
        target = self.source / self.stage.ENQUEUE
        target.write_bytes(target.read_bytes() + b"\n// tampered\n")
        before = {str(f): f.read_bytes() for f in self.source.rglob("*.swift")}
        with self.assertRaises(RuntimeError):
            self.stage.apply_portable_copy(self.source)
        self.assertEqual(before, {str(f): f.read_bytes() for f in self.source.rglob("*.swift")})

    def test_five_locks_each_reject_modification(self):
        for name in self.stage.read_manifest()["regression_locks"]:
            with self.subTest(name=name):
                target = self.source / name
                original = target.read_bytes()
                target.write_bytes(original + b"\n// changed\n")
                with self.assertRaises(RuntimeError):
                    self.stage.check(self.source, "before")
                target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
