import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build116FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load_script("apply_jerkgram_v12e_build116_foundation1.py")

    def test_settings_source_is_versioned_atomic_and_typed(self):
        source = self.overlay.settings_source()
        for token in (
            "JerkgramSettingsV1: Codable, Equatable",
            "schemaVersion: Int = 1",
            "JerkgramSendStyleV1: String, Codable, CaseIterable",
            "func load() throws -> JerkgramSettingsV1",
            "func save(_ value: JerkgramSettingsV1) throws",
            ".atomic",
            "unsupportedSchemaVersion",
        ):
            self.assertIn(token, source)

    def test_archive_source_has_safe_bounded_v1_schema(self):
        source = self.overlay.archive_source()
        for token in (
            "JerkgramArchiveManifestV1: Codable, Equatable",
            "JerkgramArchiveEventV1: Codable, Equatable",
            "JerkgramArchiveV1: Codable, Equatable",
            "schemaVersion: Int = 1",
            "maximumEventCount = 100_000",
            "accountPeerId",
            "peerId",
            "messageId",
            "eventTimestamp",
            "kind",
            "JSONEncoder.OutputFormatting.sortedKeys",
            "unsupportedSchemaVersion",
        ):
            self.assertIn(token, source)
        for forbidden in ("authKey", "accessToken", "sessionToken", "mobileprovision", "signingCertificate"):
            self.assertNotIn(forbidden, source)

    def test_reference_merge_deduplicates_and_sorts_deterministically(self):
        first = {
            "accountPeerId": 2, "peerId": 20, "messageId": 9,
            "eventTimestamp": 100, "kind": "edit", "payload": "old",
        }
        duplicate = dict(first, payload="new")
        earlier = {
            "accountPeerId": 1, "peerId": 10, "messageId": 3,
            "eventTimestamp": 50, "kind": "delete", "payload": "x",
        }
        merged = self.overlay.merge_events([first], [duplicate, earlier])
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0], earlier)
        self.assertEqual(merged[1]["payload"], "new")

    def test_materializer_creates_only_two_foundation_files(self):
        files = self.overlay.materialized_files()
        self.assertEqual(
            set(files),
            {
                "submodules/SettingsUI/Sources/Jerkgram/JerkgramSettingsStore.swift",
                "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchive.swift",
            },
        )


if __name__ == "__main__":
    unittest.main()
