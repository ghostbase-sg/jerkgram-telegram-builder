import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply_jerkgram_v13a1_build139_reconcile_compile_fix1.py"
spec = importlib.util.spec_from_file_location("build139_reconcile_fix", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def make_source(account_block: str, present_prefix: str, duplicate_reconcile_guard: bool = False) -> str:
    reconcile_guards = module.GUARD + (module.GUARD if duplicate_reconcile_guard else "")
    return (
        "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool {\n"
        + module.GUARD
        + account_block
        + "                    let chooseAccount = UIAlertController()\n"
        + "                    "
        + present_prefix
        + "chooseAccount, animated: true)\n"
        + "                    let startFailed = UIAlertController()\n"
        + "                    "
        + present_prefix
        + "startFailed, animated: true)\n"
        + "                    let alert = UIAlertController()\n"
        + "                    "
        + present_prefix
        + "alert, animated: true)\n"
        + "                    let done = UIAlertController()\n"
        + "                    "
        + present_prefix
        + "done, animated: true)\n"
        + "}\n"
        + "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool {\n"
        + reconcile_guards
        + "        let done = UIAlertController()\n"
        + "        "
        + present_prefix
        + "done, animated: true)\n"
        + "}\n"
    )


class Build139ReconcileCompileFixTests(unittest.TestCase):
    def test_duplicate_reconcile_guard_is_collapsed(self):
        source = make_source(
            module.OLD_ACCOUNT_LABEL_BLOCK,
            module.OLD_PRESENT_PREFIX,
            duplicate_reconcile_guard=True,
        )

        result = module.normalize_text(source)
        self.assertEqual(result.count(module.GUARD), 2)
        self.assertNotIn(module.DUPLICATE_GUARD, result)

    def test_compile_incompatible_account_and_present_patterns_are_normalized(self):
        source = make_source(module.OLD_ACCOUNT_LABEL_BLOCK, module.OLD_PRESENT_PREFIX)

        result = module.normalize_text(source)

        self.assertNotIn("transaction { transaction -> TelegramUser? in", result)
        self.assertIn("transaction { transaction -> String in", result)
        self.assertIn("start(next: { [weak self] accountLabel in", result)
        self.assertNotIn("user?.username", result)
        self.assertNotIn("else if let user", result)
        self.assertNotIn(module.OLD_PRESENT_PREFIX, result)
        self.assertEqual(result.count(module.NEW_PRESENT_PREFIX), 5)

    def test_clean_source_is_idempotent(self):
        source = make_source(module.NEW_ACCOUNT_LABEL_BLOCK, module.NEW_PRESENT_PREFIX)
        self.assertEqual(module.normalize_text(source), source)

    def test_unexpected_guard_count_fails_closed(self):
        source = make_source(module.NEW_ACCOUNT_LABEL_BLOCK, module.NEW_PRESENT_PREFIX)
        source = source.replace(module.GUARD, "", 1)
        with self.assertRaises(RuntimeError):
            module.normalize_text(source)

    def test_account_label_source_drift_fails_closed(self):
        source = make_source(module.NEW_ACCOUNT_LABEL_BLOCK, module.NEW_PRESENT_PREFIX)
        source = source.replace("transaction { transaction -> String in", "transaction { transaction -> Int in", 1)
        with self.assertRaises(RuntimeError):
            module.normalize_text(source)

    def test_presentation_source_drift_fails_closed(self):
        source = make_source(module.NEW_ACCOUNT_LABEL_BLOCK, module.NEW_PRESENT_PREFIX)
        source = source.replace(module.NEW_PRESENT_PREFIX, "differentPresenter(", 1)
        with self.assertRaises(RuntimeError):
            module.normalize_text(source)


if __name__ == "__main__":
    unittest.main()
