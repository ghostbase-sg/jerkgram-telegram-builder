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
        from jg132_baseline import enabled
        if enabled():
            self.set_up_132()
            return
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

    def set_up_132(self):
        from contextlib import ExitStack
        from jg132_baseline import source_boundary_view, TARGET
        from jg131_final_stages import source_view
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        canonical = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
        parent = self.stack.enter_context(source_boundary_view(canonical, 7))
        names = self.stage.OWNERS | {self.stage.ACCOUNT} | set(self.stage.read_manifest()["regression_locks"])
        replacements = {name:(parent/name).read_bytes() for name in names}
        self.source = source_view(parent,Path(self.tmp.name)/"source",replacements)
        # Full CI sources retain their genuine target commit. Local bounded
        # projections exercise exact parents/guards through explicit test mode.
        try:
            self.genuine_132 = subprocess.check_output(["git","rev-parse","HEAD"],cwd=canonical,stderr=subprocess.DEVNULL,text=True).strip()==TARGET
        except subprocess.CalledProcessError:
            self.genuine_132 = False

    def apply_fixture(self):
        from jg132_baseline import enabled,apply_stage
        if enabled():
            return apply_stage(self.source,"jg13-portable-copy",require_head=self.genuine_132)
        return self.stage.apply_portable_copy(self.source)

    def test_parent_apply_final_hashes_and_repeat_refusal(self):
        self.apply_fixture()
        self.stage.verify_portable_copy(self.source)
        from jg132_baseline import enabled
        if enabled():
            before = {str(f):f.read_bytes() for f in self.source.rglob("*.swift")}
            self.apply_fixture()
            self.assertEqual(before,{str(f):f.read_bytes() for f in self.source.rglob("*.swift")})
            result = subprocess.run(["git","apply","--check",str(self.stage.PATCH)],cwd=self.source,capture_output=True)
            self.assertNotEqual(result.returncode,0)
        else:
            with self.assertRaises(RuntimeError):self.apply_fixture()

    def test_tampered_owner_does_not_partly_apply(self):
        target = self.source / self.stage.ENQUEUE
        target.write_bytes(target.read_bytes() + b"\n// tampered\n")
        before = {str(f): f.read_bytes() for f in self.source.rglob("*.swift")}
        with self.assertRaises(RuntimeError):
            self.apply_fixture()
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
