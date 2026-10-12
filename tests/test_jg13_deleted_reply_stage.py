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


class DeletedReplyStageTests(unittest.TestCase):
    def setUp(self):
        self.stage = importlib.import_module("materialize_jg13_deleted_reply")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name)
        final_source = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
        use_baseline = (ROOT / "work/reply158-base" / self.stage.ACCOUNT).exists()
        for name in self.stage.OWNERS:
            original = (ROOT / "work/reply158-base" if use_baseline else final_source) / name
            if original.exists():
                target = self.source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, target)
        for name in self.stage.read_manifest()["regression_locks"]:
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile((ROOT / "work/final157" if use_baseline else final_source) / name, target)
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        if not use_baseline:
            self.stage.check(self.source, "after")
            subprocess.run(["git", "apply", "--reverse", str(self.stage.PATCH)], cwd=self.source, check=True)

    def test_exact_application_and_repeat_refusal(self):
        self.stage.apply_deleted_reply(self.source)
        self.stage.check(self.source, "after")
        with self.assertRaises(RuntimeError):
            self.stage.apply_deleted_reply(self.source)

    def test_tampered_parent_leaves_all_files_unchanged(self):
        target = self.source / self.stage.ACCOUNT
        target.write_text(target.read_text() + "\n// changed\n")
        before = {str(f): f.read_bytes() for f in self.source.rglob("*.swift")}
        with self.assertRaises(RuntimeError):
            self.stage.apply_deleted_reply(self.source)
        self.assertEqual(before, {str(f): f.read_bytes() for f in self.source.rglob("*.swift")})

    def test_existing_helper_is_not_overwritten(self):
        target = self.source / self.stage.HELPER
        target.write_text("// user file\n")
        with self.assertRaises(RuntimeError):
            self.stage.apply_deleted_reply(self.source)
        self.assertEqual(target.read_text(), "// user file\n")

    def test_each_protected_file_remains_locked(self):
        for name in self.stage.read_manifest()["regression_locks"]:
            with self.subTest(name=name):
                target = self.source / name
                original = target.read_bytes()
                target.write_bytes(original + b"\n// modified\n")
                with self.assertRaises(RuntimeError):
                    self.stage.check(self.source, "before")
                target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
