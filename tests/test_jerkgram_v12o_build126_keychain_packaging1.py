import hashlib
import importlib.util
from pathlib import Path
import plistlib
import struct
import tempfile
import unittest
import zipfile


REPO = Path(__file__).resolve().parents[1]
PACKAGER = REPO / "scripts" / "jerkgram_finalize_build126_keychain_package1.py"
DYLIB = REPO / "assets" / "sideloadKeychainFix.dylib"
INSTALL_NAME = "@executable_path/Frameworks/sideloadKeychainFix.dylib"
EXPECTED_SHA256 = "f8d81929c4de5799c9f5cb5b3e7d7410a7374224bef63afe88128f66fc351d79"


def thin_arm64_macho_with_headerpad() -> bytes:
    header = struct.pack("<IiiIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0)
    return header + b"\0" * 4096


class Build126KeychainPackagingTests(unittest.TestCase):
    def load_packager(self):
        self.assertTrue(PACKAGER.is_file(), "Build126 keychain packager is missing")
        spec = importlib.util.spec_from_file_location("build126_keychain_package", PACKAGER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def make_ipa(self, root: Path) -> Path:
        payload = root / "payload" / "Payload" / "Jerkgram.app"
        payload.mkdir(parents=True)
        (payload / "PlugIns" / "WidgetExtension.appex").mkdir(parents=True)
        (payload / "Jerkgram").write_bytes(thin_arm64_macho_with_headerpad())
        (payload / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "Jerkgram",
            "CFBundleIdentifier": "ph.telegra.Telegraph",
            "CFBundleVersion": "125",
        }))
        ipa = root / "input.ipa"
        with zipfile.ZipFile(ipa, "w") as archive:
            for path in sorted((root / "payload").rglob("*")):
                archive.write(path, path.relative_to(root / "payload"))
        return ipa

    def test_packager_inserts_only_approved_main_app_dylib_and_load_command(self):
        module = self.load_packager()
        self.assertTrue(DYLIB.is_file(), "approved dylib asset is missing")
        self.assertEqual(hashlib.sha256(DYLIB.read_bytes()).hexdigest(), EXPECTED_SHA256)
        with tempfile.TemporaryDirectory() as directory:
            ipa = self.make_ipa(Path(directory))
            module.package_ipa(ipa, DYLIB)
            with zipfile.ZipFile(ipa) as archive:
                names = archive.namelist()
                dylib_name = "Payload/Jerkgram.app/Frameworks/sideloadKeychainFix.dylib"
                self.assertIn(dylib_name, names)
                self.assertEqual(hashlib.sha256(archive.read(dylib_name)).hexdigest(), EXPECTED_SHA256)
                self.assertFalse(any(".appex/Frameworks/sideloadKeychainFix.dylib" in name for name in names))
                executable = archive.read("Payload/Jerkgram.app/Jerkgram")
            self.assertEqual(module.loaded_dylib_paths(executable), [INSTALL_NAME])

    def test_second_packaging_is_idempotent(self):
        module = self.load_packager()
        with tempfile.TemporaryDirectory() as directory:
            ipa = self.make_ipa(Path(directory))
            module.package_ipa(ipa, DYLIB)
            once = ipa.read_bytes()
            module.package_ipa(ipa, DYLIB)
            self.assertEqual(once, ipa.read_bytes())


if __name__ == "__main__":
    unittest.main()
