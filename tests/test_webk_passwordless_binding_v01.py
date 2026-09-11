from pathlib import Path
import subprocess
import sys


def make_fixture(root: Path):
    (root / "src/pages/cards").mkdir(parents=True)
    (root / "src/pages").mkdir(parents=True, exist_ok=True)
    (root / "src/lib").mkdir(parents=True)

    (root / "src/pages/mountAuthFlow.tsx").write_text("""function authStateToCardSpec(authState) {\n  switch(authState._) {\n    case 'authStateSignIn': return {name: 'signIn'};\n    case 'authStateSignQr': return {name: 'signQR'};\n    case 'authStateAuthCode': return {name: 'authCode', payload: authState.sentCode};\n    case 'authStatePassword': return {name: 'password'};\n    case 'authStateSignUp': return {name: 'signUp', payload: authState.authCode};\n    case 'authStateSignImport': return {name: 'signImport', payload: authState.data};\n  }\n}\n""")
    (root / "src/pages/cards/SignQRCard.tsx").write_text("export default function SignQRCard() { return null; }\n")
    (root / "src/pages/bootstrapIm.ts").write_text("""import rootScope from '@lib/rootScope';\nimport {disposeActiveAuthFlow} from '@/pages/mountAuthFlow';\nexport async function bootstrapIm(): Promise<void> {\n  await rootScope.managers.appStateManager.pushToState('authState', {_: 'authStateSignedIn'});\n  const [{default: appDialogsManager}] = await Promise.all([import('@lib/appDialogsManager')]);\n  appDialogsManager.start();\n  disposeActiveAuthFlow();\n}\n""")
    (root / "src/lib/appImManager.ts").write_text("export class AppImManager {}\n")


def test_passwordless_patcher_is_standalone_and_idempotent(tmp_path: Path):
    root = tmp_path / "tweb"
    make_fixture(root)
    patcher = Path(__file__).parents[1] / "webpush-companion/apply_webk_jerkgram_passwordless_binding_v01.py"

    first = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr + first.stdout

    paths = {
        "auth": root / "src/pages/mountAuthFlow.tsx",
        "qr": root / "src/pages/cards/SignQRCard.tsx",
        "bootstrap": root / "src/pages/bootstrapIm.ts",
        "binding": root / "src/lib/jerkgramCompanionBinding.ts",
        "pure": root / "src/lib/jerkgramPushBinding.ts",
        "shell": root / "src/lib/jerkgramCompanionShell.ts",
    }
    snapshots = {name: path.read_text() for name, path in paths.items()}

    assert "apply_webk_jerkgram_pairing_v01" not in first.stdout
    assert "jerkgram://push/authorize" not in "\n".join(snapshots.values())
    assert "auth.exportLoginToken" not in "\n".join(snapshots.values())
    assert "auth.importLoginToken" not in "\n".join(snapshots.values())
    assert "SESSION_PASSWORD_NEEDED" not in "\n".join(snapshots.values())

    pure = snapshots["pure"]
    assert "normalizeJerkgramPushSubscription" in pure
    assert "buildJerkgramBindingEnvelope" in pure
    assert "encodeJerkgramBinding" in pure
    assert "buildJerkgramBindingUrl" in pure

    binding = snapshots["binding"]
    assert "action !== 'register'" in binding
    assert "action !== 'unregister'" in binding
    assert "pushManager.subscribe" in binding
    assert "applicationServerKey: App.pushServerKey" in binding
    assert "window.location" not in binding
    assert "Notification.requestPermission" not in binding

    second = subprocess.run([sys.executable, str(patcher), str(root)], capture_output=True, text=True)
    assert second.returncode == 0, second.stderr + second.stdout
    for name, path in paths.items():
        assert path.read_text() == snapshots[name], f"{name} changed on second patch"
