import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply_jerkgram_v13a1_build139_reconcile_compile_fix1.py"
spec = importlib.util.spec_from_file_location("build139_reconcile_fix", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class Build139ReconcileCompileFixTests(unittest.TestCase):
    def test_duplicate_reconcile_guard_is_collapsed(self):
        guard = module.GUARD
        source = (
            "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool {\n"
            + guard
            + "              let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return true }\n"
            + "}\n"
            + "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool {\n"
            + guard
            + guard
            + "              let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return true }\n"
            + "}\n"
        )

        result = module.normalize_text(source)
        self.assertEqual(result.count(guard), 2)
        self.assertNotIn(module.DUPLICATE_GUARD, result)

    def test_clean_source_is_idempotent(self):
        guard = module.GUARD
        source = (
            "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool {\n"
            + guard
            + "}\n"
            + "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool {\n"
            + guard
            + "}\n"
        )
        self.assertEqual(module.normalize_text(source), source)

    def test_unexpected_guard_count_fails_closed(self):
        source = (
            "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool {}\n"
            "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool {}\n"
        )
        with self.assertRaises(RuntimeError):
            module.normalize_text(source)


if __name__ == "__main__":
    unittest.main()
