import importlib.util
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
import zipfile


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
FINALIZER = SCRIPTS / "jerkgram_finalize_build130_identity.py"


class Build130IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SCRIPTS))

    def load_finalizer(self):
        self.assertTrue(FINALIZER.is_file(), "missing Build130 identity finalizer")
        spec = importlib.util.spec_from_file_location("build130_identity", FINALIZER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def write_info(path: Path, version: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(plistlib.dumps({
            "CFBundleIdentifier": "org.jerkgram.test",
            "CFBundleShortVersionString": version,
            "CFBundleVersion": "130",
        }))

    def test_stamps_public_version_for_main_app_and_extensions(self):
        module = self.load_finalizer()
        with tempfile.TemporaryDirectory(prefix="build130-identity-test-") as directory:
            root = Path(directory) / "root"
            self.write_info(root / "Payload/Jerkgram.app/Info.plist", "12.9.1")
            self.write_info(root / "Payload/Jerkgram.app/PlugIns/Share.appex/Info.plist", "12.9.1")
            ipa = Path(directory) / "Jerkgram.ipa"
            with zipfile.ZipFile(ipa, "w") as archive:
                for path in sorted(root.rglob("Info.plist")):
                    archive.write(path, path.relative_to(root))
            module.stamp_short_version(ipa)
            output = Path(directory) / "output"
            with zipfile.ZipFile(ipa, "r") as archive:
                archive.extractall(output)
            for path in (
                output / "Payload/Jerkgram.app/Info.plist",
                output / "Payload/Jerkgram.app/PlugIns/Share.appex/Info.plist",
            ):
                self.assertEqual(plistlib.loads(path.read_bytes())["CFBundleShortVersionString"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
