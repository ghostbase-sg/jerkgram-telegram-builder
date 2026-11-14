from pathlib import Path
import importlib.util
import json
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('analytics_integration', ROOT / 'scripts/apply_jerkgram_analytics_v3.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class AnalyticsIntegrationTests(unittest.TestCase):
    def test_lifecycle_preserves_v1_bytes_and_initializes_before_legacy_writes(self):
        source = (ROOT / 'tests/fixtures/analytics_v3/app-parent.swift').read_text()
        result = module.patch_app(source)
        self.assertEqual(module.legacy_telemetry(source), module.legacy_telemetry(result))
        self.assertLess(result.index('JerkgramAnalyticsV3Bridge.shared.bootstrap'), result.index('JerkGramLegacyDefaultsMigration.run()'))
        self.assertLess(result.index('JerkGramLegacyDefaultsMigration.run()'), result.index('JerkgramAnalyticsV3Bridge.shared.synchronizeConsent()'))
        for method in ['didBecomeActive', 'didEnterBackground', 'didResignActive']:
            self.assertEqual(result.count('JerkgramAnalyticsV3Bridge.shared.' + method + '()'), 1)
        self.assertEqual(result.count('/v1/activity'), 1)
        self.assertNotIn('/v3/events', result)

    def test_anchor_drift_is_rejected(self):
        source = (ROOT / 'tests/fixtures/analytics_v3/app-parent.swift').read_text()
        with self.assertRaises(RuntimeError):
            module.patch_app(source.replace('JerkGramLegacyDefaultsMigration.run()', 'unsupported()'))
        with self.assertRaises(RuntimeError):
            module.patch_app(module.patch_app(source))

    def test_ru_en_description_discloses_pseudonymity_and_off(self):
        source = (ROOT / 'tests/fixtures/analytics_v3/strings-parent.swift').read_text()
        result = module.patch_strings(source)
        for text in ['псевдонимный ID установки', 'сессии', 'модель и регион', 'очередь событий очищается', 'pseudonymous installation ID', 'sessions', 'device model and region', 'clears queued events']:
            self.assertIn(text, result)
        self.assertNotIn('sharing anonymous usage statistics', result)

    def test_reviewed_payload_manifest_matches_production_sources(self):
        manifest = json.loads(module.MANIFEST.read_text())
        self.assertEqual(set(manifest["payloads"]), set(module.PAYLOADS))
        for name in module.PAYLOADS:
            self.assertEqual(module.digest((module.PAYLOAD_ROOT / name).read_bytes()), manifest["payloads"][name], name)

    def test_unknown_product_owner_is_refused_before_writes(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch)
            owner = source / module.APP
            owner.parent.mkdir(parents=True)
            owner.write_text("unexpected product owner")
            with patch.object(module, "verify_pin", return_value=source):
                with self.assertRaises(RuntimeError):
                    module.apply(source)
            self.assertEqual(owner.read_text(), "unexpected product owner")
            self.assertFalse((owner.parent / "JerkgramAnalyticsV3.swift").exists())

    def test_parent_manifest_is_exact_current_product_and_not_release_identity(self):
        manifest = json.loads(module.MANIFEST.read_text())
        self.assertEqual(manifest['upstream_sha'], '24638bc69bd083981b178dd1e7f921eebbf7fc46')
        self.assertFalse(manifest['production_v3_delivery'])
        self.assertEqual(set(manifest['owners']), {module.APP, module.STRINGS})
        self.assertEqual(manifest['owners'][module.APP]['before_sha256'], '925b72fbb80fa60c973326b67b30687c5055634d5dc3e3f590562047bec8ec87')


if __name__ == '__main__':
    unittest.main()
