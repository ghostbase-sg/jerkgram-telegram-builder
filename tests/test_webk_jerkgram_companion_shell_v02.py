import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCHER = REPO / "webpush-companion/apply_webk_jerkgram_companion_shell_v02.py"


def load_patcher():
    if not PATCHER.is_file():
        raise AssertionError(f"missing Build139 companion shell patcher: {PATCHER}")
    spec = importlib.util.spec_from_file_location("webk_companion_shell_v02", PATCHER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
        module = load_patcher()
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
        for token in (
            "Jerkgram Notifications",
            "Active",
            "Permission",
            "Session",
            "Push subscription",
            "Manage in Jerkgram",
            "navigator.serviceWorker.ready",
            "pushManager.getSubscription()",
            "Notification.permission",
            "rootScope.managers.appUsersManager.getSelf()",
            "jerkgram://push",
            "prefers-color-scheme: dark",
        ):
            self.assertIn(token, source)

        for forbidden in (
            "Disconnect",
            "jerkgram://push/unregister",
            "jerkgram://push/register",
            "endpoint=",
            "p256dh=",
            "auth=",
        ):
            self.assertNotIn(forbidden, source)

    def test_signed_in_shell_can_finish_reconcile_after_pwa_process_restart(self):
        module = load_patcher()
        source = module.SHELL_SOURCE
        for token in (
            "jerkgram.notifications.pairing.v1",
            "jerkgram.notifications.installation.v1",
            "PAIRING_LIFETIME_MS = 120_000",
            "jerkgram://push/reconcile?v=1",
            "String(self.id)",
            "localStorage.removeItem(JERKGRAM_PAIRING_KEY)",
        ):
            self.assertIn(token, source)

    def test_tree_patch_is_idempotent(self):
        module = load_patcher()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mount = root / "src/pages/mountAuthFlow.tsx"
            bootstrap = root / "src/pages/bootstrapIm.ts"
            mount.parent.mkdir(parents=True)
            mount.write_text(MOUNT_AUTH_FIXTURE, encoding="utf-8")
            bootstrap.write_text(BOOTSTRAP_FIXTURE, encoding="utf-8")

            module.patch_tree(root)
            first_mount = mount.read_text(encoding="utf-8")
            first_bootstrap = bootstrap.read_text(encoding="utf-8")
            shell = root / "src/lib/jerkgramNotificationsShell.ts"
            first_shell = shell.read_text(encoding="utf-8")

            module.patch_tree(root)
            self.assertEqual(first_mount, mount.read_text(encoding="utf-8"))
            self.assertEqual(first_bootstrap, bootstrap.read_text(encoding="utf-8"))
            self.assertEqual(first_shell, shell.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
