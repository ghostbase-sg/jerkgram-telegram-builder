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
MAIN_INSTALL_NAME = "@executable_path/Frameworks/sideloadKeychainFix.dylib"
NSE_INSTALL_NAME = "@executable_path/../../Frameworks/sideloadKeychainFix.dylib"


def thin_arm64_macho_with_headerpad() -> bytes:
    header = struct.pack("<IiiIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0)
    return header + b"\0" * 4096


class NativePushNSEKeychainTests(unittest.TestCase):
    def load_packager(self):
        spec = importlib.util.spec_from_file_location("build126_keychain_package", PACKAGER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def make_ipa(self, root: Path) -> Path:
        app = root / "payload" / "Payload" / "Jerkgram.app"
        nse = app / "PlugIns" / "NotificationServiceExtensionv1.appex"
        widget = app / "PlugIns" / "WidgetExtension.appex"
        nse.mkdir(parents=True)
        widget.mkdir(parents=True)

        (app / "Jerkgram").write_bytes(thin_arm64_macho_with_headerpad())
        (app / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "Jerkgram",
            "CFBundleIdentifier": "com.jerkgram.ios",
        }))

        (nse / "NotificationServiceExtensionv1").write_bytes(thin_arm64_macho_with_headerpad())
        (nse / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "NotificationServiceExtensionv1",
            "CFBundleIdentifier": "com.jerkgram.ios.NotificationService",
            "NSExtension": {
                "NSExtensionPointIdentifier": "com.apple.usernotifications.service",
                "NSExtensionPrincipalClass": "NotificationService",
            },
        }))

        # A non-notification extension must not be modified by this targeted fix.
        (widget / "WidgetExtension").write_bytes(thin_arm64_macho_with_headerpad())
        (widget / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "WidgetExtension",
            "CFBundleIdentifier": "com.jerkgram.ios.Widget",
            "NSExtension": {"NSExtensionPointIdentifier": "com.apple.widgetkit-extension"},
        }))

        ipa = root / "input.ipa"
        with zipfile.ZipFile(ipa, "w") as archive:
            for path in sorted((root / "payload").rglob("*")):
                archive.write(path, path.relative_to(root / "payload"))
        return ipa

    def test_shared_sideload_fix_is_loaded_by_main_app_and_notification_service(self):
        module = self.load_packager()
        with tempfile.TemporaryDirectory() as directory:
            ipa = self.make_ipa(Path(directory))
            module.package_ipa(ipa, DYLIB)
            with zipfile.ZipFile(ipa) as archive:
                names = set(archive.namelist())
                self.assertIn("Payload/Jerkgram.app/Frameworks/sideloadKeychainFix.dylib", names)
                self.assertNotIn(
                    "Payload/Jerkgram.app/PlugIns/NotificationServiceExtensionv1.appex/Frameworks/sideloadKeychainFix.dylib",
                    names,
                )
                main = archive.read("Payload/Jerkgram.app/Jerkgram")
                nse = archive.read(
                    "Payload/Jerkgram.app/PlugIns/NotificationServiceExtensionv1.appex/NotificationServiceExtensionv1"
                )
                widget = archive.read("Payload/Jerkgram.app/PlugIns/WidgetExtension.appex/WidgetExtension")

            self.assertIn(MAIN_INSTALL_NAME, module.loaded_dylib_paths(main))
            self.assertIn(NSE_INSTALL_NAME, module.loaded_dylib_paths(nse))
            self.assertNotIn(NSE_INSTALL_NAME, module.loaded_dylib_paths(widget))

    def test_packaging_with_notification_service_remains_idempotent(self):
        module = self.load_packager()
        with tempfile.TemporaryDirectory() as directory:
            ipa = self.make_ipa(Path(directory))
            module.package_ipa(ipa, DYLIB)
            once = ipa.read_bytes()
            module.package_ipa(ipa, DYLIB)
            self.assertEqual(once, ipa.read_bytes())


if __name__ == "__main__":
    unittest.main()
