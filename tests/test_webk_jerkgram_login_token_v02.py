import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCHER = REPO / "webpush-companion/apply_webk_jerkgram_login_token_v02.py"


def load_patcher():
    if not PATCHER.is_file():
        raise AssertionError(f"missing Build139 Web K login-token patcher: {PATCHER}")
    spec = importlib.util.spec_from_file_location("webk_login_token_v02", PATCHER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SIGN_QR_FIXTURE = r'''import {AuthApi} from '../../lib/mtproto/apiMethods/auth';
import rootScope from '../../lib/rootScope';
import {attachClickEvent} from '../../helpers/dom/clickEvent';
import {Middleware} from '../../helpers/middleware';
import {onMount, onCleanup, createSignal, Show, For, createEffect} from 'solid-js';
import {render} from 'solid-js/web';
import {i18n} from '../../lib/langPack';
import apiManager from '../../lib/mtproto/mtprotoworker';
import Button from '../../components/button';
import Icon from '../../components/icon';
import wrapQrCode from '../../helpers/qrCode';
import {IS_MOBILE} from '../../environment/userAgent';
import {IS_TOUCH_SUPPORTED} from '../../environment/touchSupport';
import {cancelEvent} from '../../helpers/dom/cancelEvent';
import LanguageChangeButton from '../../components/languageChangeButton';
import {useHotReloadGuard} from '../../lib/solidjs/hotReloadGuard';
import {QrCode} from '../../components/qrCode';
import {PASSKEYS_SUPPORTED} from '../../environment/passkeys';
import PasskeyLoginButton from '../../components/passkeyLoginButton';

export default function SignQRCard({onCancel, onFirstMount, onError, qrCode}: {
  onCancel: () => void,
  onFirstMount: () => void,
  onError: (error: Error) => void,
  qrCode: QrCode
}) {
  const hotReloadGuard = useHotReloadGuard();
  const [token, setToken] = createSignal<AuthApi.LoginToken.loginToken>();
  const [stopped, setStopped] = createSignal(false);
  const [loading, setLoading] = createSignal(false);
  let qrCode;

  const iterate = () => {
    if(stopped()) return;
    setLoading(true);
    return apiManager.invokeApi('auth.exportLoginToken', {
      api_id: apiManager.getApiId(),
      api_hash: apiManager.getApiHash(),
      except_ids: []
    }).then(async(loginToken) => {
      if(loginToken._ === 'auth.loginTokenMigrateTo') {
        await apiManager.migrateTo(loginToken.dc_id);
        return iterate();
      } else if(loginToken._ === 'auth.loginTokenSuccess') {
        const authorization = loginToken.authorization as AuthApi.Authorization.authorization;
        await rootScope.managers.appUsersManager.setUser(authorization.user);
        await apiManager.setUserAuth(authorization.user.id);
        rootScope.dispatchEvent('user_auth', authorization.user.id);
        setStopped(true);
        hotReloadGuard.navigate('im');
        return;
      }

      setToken(loginToken);
      setLoading(false);
    }).catch((error) => {
      if(error.type === 'SESSION_PASSWORD_NEEDED') {
        setStopped(true);
        hotReloadGuard.navigate('authPassword');
        return;
      }
      onError(error);
    });
  };

  onMount(() => {
    iterate();
  });

  return <div class="card auth-card">
    <LanguageChangeButton />
    <div class="qr-container"></div>
    <Button onClick={iterate}>Log in by QR Code</Button>
    <Show when={PASSKEYS_SUPPORTED}>
      <PasskeyLoginButton />
    </Show>
    <Button onClick={onCancel}>Log in by phone number</Button>
  </div>;
}
'''


class WebKJerkgramLoginTokenV02Tests(unittest.TestCase):
    def test_patch_uses_official_login_token_with_random_nonce_and_no_subscription_credentials(self):
        module = load_patcher()
        patched = module.patch_sign_qr_text(SIGN_QR_FIXTURE)

        for token in (
            "auth.exportLoginToken",
            "crypto.getRandomValues(new Uint8Array(24))",
            "jerkgram.notifications.pairing.v1",
            "jerkgram.notifications.installation.v1",
            "localStorage.setItem(JERKGRAM_PAIRING_KEY",
            "localStorage.setItem(INSTALLATION_ID_KEY",
            "jerkgram://push/authorize?v=1",
            "token=${encodeURIComponent(tokenValue)}",
            "nonce=${encodeURIComponent(nonce)}",
            "accountNumber: getCurrentAccount()",
        ):
            self.assertIn(token, patched)

        for forbidden in (
            "jerkgram://push/register",
            "jerkgram://push/unregister",
            "p256dh=",
            "auth=",
            "endpoint=",
        ):
            self.assertNotIn(forbidden, patched)

    def test_pairing_is_short_lived_and_survives_pwa_process_restart(self):
        module = load_patcher()
        patched = module.patch_sign_qr_text(SIGN_QR_FIXTURE)
        for token in (
            "PAIRING_LIFETIME_MS = 120_000",
            "Date.now() - parsed.createdAt > PAIRING_LIFETIME_MS",
            "localStorage.removeItem(JERKGRAM_PAIRING_KEY)",
            "pairing.accountNumber !== getCurrentAccount()",
            "telegramUserId?: string",
        ):
            self.assertIn(token, patched)
        self.assertNotIn("sessionStorage", patched)

    def test_setup_requires_home_screen_and_notification_permission_before_exporting_token(self):
        module = load_patcher()
        patched = module.patch_sign_qr_text(SIGN_QR_FIXTURE)
        for token in (
            "function isJerkgramStandalone()",
            "Add Jerkgram Notifications to the Home Screen first.",
            "Notification.requestPermission()",
            "Allow notifications in iOS Settings to continue.",
            "Web Push is not available in this browser.",
        ):
            self.assertIn(token, patched)

        self.assertLess(
            patched.index("Notification.requestPermission()"),
            patched.index("const loginToken = await exportOrImportLoginToken();"),
        )

    def test_success_reconciles_once_with_actual_webk_user(self):
        module = load_patcher()
        patched = module.patch_sign_qr_text(SIGN_QR_FIXTURE)

        for token in (
            "authorization.user.id",
            "String(authorization.user.id)",
            "storeAcceptedUserId(String(authorization.user.id))",
            "telegramUserId: userId",
            "jerkgram://push/reconcile?v=1",
            "reconcileWithJerkgram(String(authorization.user.id))",
            "Finishing setup in Jerkgram…",
            "await toIm()",
        ):
            self.assertIn(token, patched)

        for forbidden in (
            "RECONCILE_RETRY_DELAY_MS",
            "markReconcileAttempt(",
            "armPairingCleanupAfterNativeHandoff(",
            "setTimeout(() =>",
        ):
            self.assertNotIn(forbidden, patched)

        self.assertLess(
            patched.index("await managers.apiManager.setUser(authorization.user)"),
            patched.index("storeAcceptedUserId(String(authorization.user.id))"),
        )
        self.assertLess(
            patched.index("storeAcceptedUserId(String(authorization.user.id))"),
            patched.index("reconcileWithJerkgram(String(authorization.user.id))"),
        )

    def test_companion_exposes_only_continue_setup_and_never_phone_passkey_or_2fa_ui(self):
        module = load_patcher()
        patched = module.patch_sign_qr_text(SIGN_QR_FIXTURE)

        for token in (
            "Jerkgram Notifications",
            "Connect with Jerkgram",
            "Jerkgram will open and ask you to confirm the account.",
            "No phone number, QR code, or Telegram password is entered here.",
            "./assets/img/logo_filled_rounded.png",
            "Additional Telegram verification is required. Restart setup in Jerkgram.",
        ):
            self.assertIn(token, patched)

        for forbidden in (
            "LanguageChangeButton",
            "PasskeyLoginButton",
            "PASSKEYS_SUPPORTED",
            "Log in by phone number",
            "hotReloadGuard.navigate('authPassword')",
        ):
            self.assertNotIn(forbidden, patched)

    def test_patch_is_idempotent_and_targets_pinned_sign_qr_file(self):
        module = load_patcher()
        once = module.patch_sign_qr_text(SIGN_QR_FIXTURE)
        twice = module.patch_sign_qr_text(once)
        self.assertEqual(once, twice)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "src/pages/cards/SignQRCard.tsx"
            target.parent.mkdir(parents=True)
            target.write_text(SIGN_QR_FIXTURE, encoding="utf-8")
            module.patch_tree(root)
            self.assertEqual(target.read_text(encoding="utf-8"), once)


if __name__ == "__main__":
    unittest.main()
