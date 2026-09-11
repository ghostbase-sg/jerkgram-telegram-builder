from pathlib import Path
import subprocess
import sys


def make_fixture(root: Path):
    (root / "src/pages/cards").mkdir(parents=True)
    (root / "src/pages").mkdir(parents=True, exist_ok=True)
    (root / "src/lib").mkdir(parents=True)

    (root / "src/pages/mountAuthFlow.tsx").write_text("""function authStateToCardSpec(authState) {\n  switch(authState._) {\n    case 'authStateSignIn':\n      return {name: 'signIn'};\n    case 'authStateSignQr':\n      return {name: 'signQR'};\n    case 'authStateAuthCode':\n      return {name: 'authCode', payload: authState.sentCode};\n    case 'authStatePassword':\n      return {name: 'password'};\n    case 'authStateSignUp':\n      return {name: 'signUp', payload: authState.authCode};\n    case 'authStateSignImport':\n      return {name: 'signImport', payload: authState.data};\n  }\n}\n""")

    (root / "src/pages/cards/SignQRCard.tsx").write_text("""// old Web K QR owner\n// auth.exportLoginToken\n// auth.importLoginToken\n// auth.loginTokenSuccess\n// SESSION_PASSWORD_NEEDED\n// jerkgram://push/authorize\n// phone code PasswordCard\nexport default function SignQRCard() { return null; }\n""")

    (root / "src/pages/bootstrapIm.ts").write_text("""import rootScope from '@lib/rootScope';\nimport {disposeActiveAuthFlow} from '@/pages/mountAuthFlow';\nexport async function bootstrapIm(): Promise<void> {\n  await rootScope.managers.appStateManager.pushToState('authState', {_: 'authStateSignedIn'});\n  const [{default: appDialogsManager}] = await Promise.all([import('@lib/appDialogsManager')]);\n  appDialogsManager.start();\n  disposeActiveAuthFlow();\n}\n""")

    (root / "src/lib/appImManager.ts").write_text("""import mountJerkgramCompanionShell from '@lib/jerkgramCompanionShell';\nexport class AppImManager {\n  public construct() {\n    mountJerkgramCompanionShell();\n  }\n}\n""")


def test_companion_setup_is_passwordless_and_notification_only(tmp_path: Path):
    root = tmp_path / "tweb"
    make_fixture(root)
    patcher = Path(__file__).parents[1] / "webpush-companion/apply_webk_jerkgram_passwordless_binding_v01.py"
    result = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout

    auth = (root / "src/pages/mountAuthFlow.tsx").read_text()
    for state in (
        "authStateSignIn",
        "authStateSignQr",
        "authStateAuthCode",
        "authStatePassword",
        "authStateSignUp",
        "authStateSignImport",
    ):
        assert f"case '{state}':" in auth
    assert auth.count("return {name: 'signQR'};") == 6
    assert "{name: 'password'}" not in auth
    assert "{name: 'signIn'}" not in auth
    assert "{name: 'authCode'" not in auth
    assert "{name: 'signUp'" not in auth
    assert "{name: 'signImport'" not in auth

    qr = (root / "src/pages/cards/SignQRCard.tsx").read_text()
    binding = (root / "src/lib/jerkgramCompanionBinding.ts").read_text()
    pure = (root / "src/lib/jerkgramPushBinding.ts").read_text()
    shell = (root / "src/lib/jerkgramCompanionShell.ts").read_text()
    bootstrap = (root / "src/pages/bootstrapIm.ts").read_text()
    combined = "\n".join((qr, binding, pure, shell, bootstrap))

    assert "navigator.serviceWorker.ready" in binding
    assert "pushManager.getSubscription()" in binding
    assert "pushManager.subscribe" in binding
    assert "App.pushServerKey" in binding
    assert "crypto.randomUUID()" in binding
    assert "buildJerkgramBindingUrl(action" in binding
    assert "Notification.requestPermission()" in qr
    assert "Notification.requestPermission()" in shell
    assert "Connect with Jerkgram" in qr
    assert "Connect with Jerkgram" in shell
    assert "Disconnect" in shell
    assert "Approve in Jerkgram" in combined
    assert "Add Jerkgram Notifications to the Home Screen first" in qr

    assert "const INSTALLATION_ID_KEY = 'jerkgram.notifications.installation.v1'" in binding
    assert binding.count("localStorage.setItem(") == 1
    assert binding.count("localStorage.getItem(") == 1
    assert "subscription.unsubscribe()" not in combined

    for forbidden in (
        "apiManagerProxy.pushSingleManager.registerDevice",
        "apiManagerProxy.pushSingleManager.unregisterDevice",
        "apiManager.logOut",
        "apiManagerProxy.getUser",
        "Connected as",
        "auth.exportLoginToken",
        "auth.importLoginToken",
        "auth.loginTokenSuccess",
        "SESSION_PASSWORD_NEEDED",
        "jerkgram://push/authorize",
        "PasswordCard",
        "appDialogsManager",
    ):
        assert forbidden not in combined

    assert "jerkgram://push/register" in pure
    assert "jerkgram://push/unregister" in pure
    assert "user_id" not in pure
    assert "accountId" not in pure
    assert "authKey" not in pure

    for generated in (qr, binding, shell):
        assert "console.log" not in generated
        assert "console.error" not in generated

    app_im = (root / "src/lib/appImManager.ts").read_text()
    assert "mountJerkgramCompanionShell" not in app_im
