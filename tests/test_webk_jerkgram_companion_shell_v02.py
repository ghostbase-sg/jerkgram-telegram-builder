import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCHER = REPO / "webpush-companion/apply_webk_jerkgram_companion_shell_v02.py"
RUNTIME_PATCHER = REPO / "webpush-companion/apply_webk_jerkgram_notification_runtime_v03.py"


def load_module(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"missing Build139 patcher: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_patcher():
    return load_module(PATCHER, "webk_companion_shell_v02")


def load_runtime_patcher():
    return load_module(RUNTIME_PATCHER, "webk_notification_runtime_v03")


MOUNT_AUTH_FIXTURE = r'''import {render} from 'solid-js/web';
import {AuthState} from '@types';
import AuthCardsHost from '@/pages/AuthCardsHost';
import {CardSpec, navigateAuth} from '@/pages/authFlow';
export type MountAuthFlowState = Exclude<AuthState, AuthState.signedIn>;
function authStateToCardSpec(authState: MountAuthFlowState): CardSpec {
  switch(authState._) {
    case 'authStateSignIn': return {name: 'signIn'};
    case 'authStateSignQr': return {name: 'signQR'};
    case 'authStateAuthCode': return {name: 'authCode', payload: authState.sentCode};
    case 'authStatePassword': return {name: 'password'};
    case 'authStateSignUp': return {name: 'signUp', payload: authState.authCode};
    case 'authStateSignImport': return {name: 'signImport', payload: authState.data};
    default: throw new Error('unknown');
  }
}
'''

BOOTSTRAP_FIXTURE = r'''import blurActiveElement from '@helpers/dom/blurActiveElement';
import rootScope from '@lib/rootScope';
import {disposeActiveAuthFlow} from '@/pages/mountAuthFlow';
let bootstrapped = false;
export async function bootstrapIm(): Promise<void> {
  if(bootstrapped) return;
  bootstrapped = true;
  await rootScope.managers.appStateManager.pushToState('authState', {_: 'authStateSignedIn'});
  const pageChatsEl = document.getElementById('page-chats');
  if(pageChatsEl) pageChatsEl.style.display = '';
  const [{default: appDialogsManager}] = await Promise.all([import('@lib/appDialogsManager')]);
  appDialogsManager.start();
  document.body.classList.remove('has-auth-pages');
  setTimeout(() => disposeActiveAuthFlow(), 1000);
}
export default bootstrapIm;
'''


class WebKJerkgramCompanionShellV02Tests(unittest.TestCase):
    def test_all_unauthorized_states_route_only_to_jerkgram_setup(self):
        module = load_patcher()
        patched = module.patch_mount_auth_text(MOUNT_AUTH_FIXTURE)
        self.assertIn("return {name: 'signQR'};", patched)
        for forbidden in ("name: 'signIn'", "name: 'authCode'", "name: 'password'", "name: 'signUp'", "name: 'signImport'"):
            self.assertNotIn(forbidden, patched)

    def test_signed_in_boot_keeps_only_push_runtime_and_hides_telegram_shell(self):
        module = load_runtime_patcher()
        patched = module.patch_bootstrap_text(BOOTSTRAP_FIXTURE)
        for token in (
            "uiNotificationsManager.constructAndStartAll()",
            "mountJerkgramNotificationsShell()",
            "pageChatsEl.style.display = 'none'",
            "disposeActiveAuthFlow()",
        ):
            self.assertIn(token, patched)
        self.assertNotIn("appDialogsManager.start()", patched)
        self.assertLess(patched.index("uiNotificationsManager.constructAndStartAll()"), patched.index("mountJerkgramNotificationsShell()"))

    def test_active_shell_is_telegram_like_and_management_stays_native(self):
        module = load_patcher()
        source = module.SHELL_SOURCE
        self.assertIn("import {getCurrentAccount} from '@lib/accounts/getCurrentAccount';", source)

        for token in (
            "Jerkgram Notifications",
            "Push ready",
            "Permission",
            "Session",
            "Push subscription",
            "Finish Setup in Jerkgram",
            "Manage in Jerkgram",
            "navigator.serviceWorker.ready",
            "pushManager.getSubscription()",
            "Notification.permission",
            "rootScope.managers.appUsersManager.getSelf()",
            "jerkgram://push",
            "prefers-color-scheme: dark",
        ):
            self.assertIn(token, source)

        self.assertIn("Native Jerkgram is the authority for binding ACTIVE after user-id reconcile.", source)
        self.assertNotIn("statePill.textContent = active ? 'Active'", source)

        for forbidden in (
            "Disconnect",
            "jerkgram://push/unregister",
            "jerkgram://push/register",
            "endpoint=",
            "p256dh=",
            "auth=",
        ):
            self.assertNotIn(forbidden, source)

    def test_signed_in_shell_finishes_reconcile_only_after_explicit_tap(self):
        module = load_patcher()
        source = module.SHELL_SOURCE
        for token in (
            "jerkgram.notifications.pairing.v1",
            "jerkgram.notifications.installation.v1",
            "PAIRING_LIFETIME_MS = 120_000",
            "telegramUserId?: string",
            "jerkgram://push/reconcile?v=1",
            "String(self.id)",
            "pairing.accountNumber !== getCurrentAccount()",
            "pairing.telegramUserId && pairing.telegramUserId !== userId",
            "Finish Setup in Jerkgram",
            "finishButton.addEventListener('click'",
            "buildPendingReconcileUrl(self)",
            "clearPairingAfterManualHandoff()",
            "document.visibilityState === 'hidden'",
            "window.addEventListener('pagehide', onPageHide, {once: true})",
        ):
            self.assertIn(token, source)

        for forbidden in (
            "recoverPendingReconcile(",
            "RECONCILE_RETRY_DELAY_MS",
            "Date.now() - pairing.reconcileAttemptedAt",
            "window.setTimeout(() => void refresh(), 800)",
            "window.setTimeout(() => void refresh(), 2500)",
        ):
            self.assertNotIn(forbidden, source)

    def test_tree_patch_is_idempotent(self):
        shell_module = load_patcher()
        runtime_module = load_runtime_patcher()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mount = root / "src/pages/mountAuthFlow.tsx"
            bootstrap = root / "src/pages/bootstrapIm.ts"
            mount.parent.mkdir(parents=True)
            mount.write_text(MOUNT_AUTH_FIXTURE, encoding="utf-8")
            bootstrap.write_text(BOOTSTRAP_FIXTURE, encoding="utf-8")

            shell_module.patch_tree(root)
            runtime_module.patch_tree(root)
            first_mount = mount.read_text(encoding="utf-8")
            first_bootstrap = bootstrap.read_text(encoding="utf-8")
            shell = root / "src/lib/jerkgramNotificationsShell.ts"
            first_shell = shell.read_text(encoding="utf-8")

            shell_module.patch_tree(root)
            runtime_module.patch_tree(root)
            self.assertEqual(first_mount, mount.read_text(encoding="utf-8"))
            self.assertEqual(first_bootstrap, bootstrap.read_text(encoding="utf-8"))
            self.assertEqual(first_shell, shell.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
