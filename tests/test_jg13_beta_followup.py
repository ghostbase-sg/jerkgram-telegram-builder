"""Bounded source contracts and real IPA metadata verifier (no app runtime claim)."""
import ast
import json
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src"
sys.path.insert(0, str(ROOT / "scripts"))
import package_jg13 as package

TM = "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift"
AVATAR = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift"


class FollowupTests(unittest.TestCase):
    def test_extracted_swift_blocks_have_declaration_separator(self):
        tree = ast.parse((ROOT / "tests/run_jg13_followup.py").read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "block")
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "fixture-helper", "exec"), namespace)
        text = "private func first() { return 1 }\nprivate func second() { return 2 }"
        first = namespace["block"](text, "private func first()")
        second = namespace["block"](text, "private func second()")
        self.assertIn("}\nprivate func second", first + second)

    def test_ipa_upstream_version_is_separate_from_product_version(self):
        config = dict(bundle_id="com.jerkgram.ios", build_number=143,
                      product_version="1.1.0", bundle_short_version="13.0")
        # Fixture is deliberately not an executable IPA; it exercises the production verifier.
        with tempfile.TemporaryDirectory() as tmp:
            ipa = Path(tmp) / "metadata-fixture.zip"
            with zipfile.ZipFile(ipa, "w") as z:
                main = dict(CFBundleIdentifier=config["bundle_id"], CFBundleDisplayName="Jerkgram",
                            CFBundleVersion="143", CFBundleShortVersionString="13.0",
                            CFBundleIcons={"CFBundlePrimaryIcon": {"CFBundleIconName": "JerkgramGlassReveal"}})
                z.writestr("Payload/Jerkgram.app/Info.plist", plistlib.dumps(main))
                for name, suffix in package.EXTENSIONS.items():
                    info = dict(main, CFBundleIdentifier=config["bundle_id"] + "." + suffix)
                    z.writestr("Payload/Jerkgram.app/PlugIns/" + name + "/Info.plist", plistlib.dumps(info))
                z.writestr("Payload/Jerkgram.app/Frameworks/sideloadKeychainFix.dylib", package.keychain.ASSET.read_bytes())
                z.writestr("Payload/Jerkgram.app/Frameworks/FilePickerFix.dylib", package.picker.FILE_PICKER_ASSET.read_bytes())
            package.verify(ipa, config)

    def test_bundle_metadata_owner_uses_explicit_bundle_version(self):
        self.assertIn('config["bundle_short_version"]', (ROOT / "scripts/configure_jg13.py").read_text())
        config = json.loads((ROOT / "jerkgram-migration.json").read_text())
        self.assertEqual(config.get("bundle_short_version"), "13.0")
        self.assertEqual(config["product_display_version"], "1.1.0 Beta 1")

    def test_one_formatter_per_list_rebuild(self):
        text = (SOURCE / TM).read_text()
        helper = text.split("private func jerkgramTimeMachineDateText", 1)[1].split("private func jerkgramTimeMachineRootURL", 1)[0]
        self.assertNotIn("DateFormatter()", helper)
        rebuild = text.split("|> map { presentationData, state, page", 1)[1]
        before_loop, loop = rebuild.split("for (index, event) in results.enumerated()", 1)
        self.assertEqual(before_loop.count("DateFormatter()"), 1)
        self.assertNotIn("DateFormatter()", loop)
        self.assertIn("formatter: dateFormatter", loop)

    def test_entry_equality_is_typed_and_payload_sensitive(self):
        text = (SOURCE / TM).read_text()
        equality = text.split("static func ==", 1)[1].split("static func <", 1)[0]
        self.assertNotIn("String(describing:", equality)
        for case in ("header", "summary", "filter", "result", "info", "loadMore"):
            self.assertIn("." + case + "(", equality)
        self.assertIn("le == re", equality)

    def test_both_chat_index_queries_use_existing_chat_partition(self):
        text = (SOURCE / "submodules/JerkgramCore/Sources/JerkgramStore.swift").read_text()
        queries = text.split("public func indexRecords(", 1)[1].split("private func filteredRecords(", 1)[0]
        self.assertEqual(queries.count("state.recordsByChat[chatPeerId] ?? []"), 2)
        self.assertNotIn("state.records,", queries)

    def test_avatar_dedup_validates_before_jpeg_and_preserves_lru(self):
        text = (SOURCE / AVATAR).read_text()
        store = text.split("private static func ghostBaseStoreAvatarDiskCache(", 1)[1].split("private static let persistentToneKey", 1)[0]
        self.assertIn("UIImage(contentsOfFile:", store, "Missing validated-cache deduplication")
        self.assertLess(store.index("ghostBaseTouchMatchingAvatarDiskCache(url:"), store.index("image.jpegData("))
        self.assertLess(store.index("ghostBaseAvatarDiskCacheLock.unlock()"), store.index("image.jpegData("))
        self.assertEqual(store.count("self.ghostBaseTouchMatchingAvatarDiskCache(url:"), 2)
        self.assertIn("cached.cgImage?.width == image.cgImage?.width", store)
        self.assertIn("cached.cgImage?.height == image.cgImage?.height", store)
        self.assertIn(".modificationDate: Date()", store)
        comparator = store.split(".sorted {", 1)[1].split("for old", 1)[0]
        self.assertNotIn("resourceValues(", comparator)
        self.assertIn("urls.map {", store)
        self.assertIn("at: old.url", store)
        self.assertIn("completeOnly: true", text)
        self.assertIn("blurred: false", text)

    def test_telemetry_diagnostics_do_not_log_payload_or_change_protocol(self):
        text = (SOURCE / "submodules/TelegramUI/Sources/AppDelegate.swift").read_text()
        sender = text.split("private final class JerkgramTelemetry {", 1)[1].split("final class JerkgramMemorySampler", 1)[0]
        self.assertIn('Logger.shared.log("JerkgramTelemetry",', sender)
        self.assertIn("http.statusCode", sender)
        self.assertIn("error.code", sender)
        self.assertIn("minimumInterval: TimeInterval = 4 * 60 * 60", sender)
        self.assertIn('"schema":1', sender)
        for line in sender.splitlines():
            if "Logger.shared.log" in line:
                for private in ("payload", "body", "receipt", "secret", "dayId", "localizedDescription"):
                    self.assertNotIn(private, line)


if __name__ == "__main__":
    unittest.main()
