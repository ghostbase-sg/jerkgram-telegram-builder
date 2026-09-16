import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
SHELL = REPO / "webpush-companion/apply_webk_jerkgram_companion_shell_v02.py"
TYPECHECK = REPO / "webpush-companion/apply_webk_jerkgram_shell_typecheck_v04.py"
REPAIR = REPO / "webpush-companion/apply_webk_jerkgram_repair_v06.py"


def load(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"missing patcher: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WebKJerkgramRepairV06Tests(unittest.TestCase):
    def test_repair_uses_webk_push_owner_without_exposing_subscription_credentials(self):
        shell = load(SHELL, "shell_v02")
        typecheck = load(TYPECHECK, "typecheck_v04")
        repair = load(REPAIR, "repair_v06")

        source = typecheck.patch_shell_text(shell.SHELL_SOURCE)
        patched = repair.patch_shell_text(source)

        for token in (
            "uiNotificationsManager.onPushConditionsChange()",
            "Repair Notifications",
            "Repairing…",
            "subscription === 'missing'",
            "permission === 'granted'",
            "await refresh()",
        ):
            self.assertIn(token, patched)

        for forbidden in (
            "pushManager.subscribe(",
            "applicationServerKey",
            "endpoint=",
            "p256dh=",
            "auth=",
            "jerkgram://push/register",
            "jerkgram://push/unregister",
        ):
            self.assertNotIn(forbidden, patched)

    def test_repair_patch_is_idempotent(self):
        shell = load(SHELL, "shell_v02_idempotent")
        typecheck = load(TYPECHECK, "typecheck_v04_idempotent")
        repair = load(REPAIR, "repair_v06_idempotent")
        source = typecheck.patch_shell_text(shell.SHELL_SOURCE)
        once = repair.patch_shell_text(source)
        twice = repair.patch_shell_text(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
