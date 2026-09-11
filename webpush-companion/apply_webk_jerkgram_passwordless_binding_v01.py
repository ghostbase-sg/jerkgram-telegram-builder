#!/usr/bin/env python3
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
MOUNT_AUTH = ROOT / "src/pages/mountAuthFlow.tsx"
SIGN_QR = ROOT / "src/pages/cards/SignQRCard.tsx"
BOOTSTRAP_IM = ROOT / "src/pages/bootstrapIm.ts"
APP_IM = ROOT / "src/lib/appImManager.ts"
PURE_BINDING = ROOT / "src/lib/jerkgramPushBinding.ts"
BINDING_OWNER = ROOT / "src/lib/jerkgramCompanionBinding.ts"
SHELL = ROOT / "src/lib/jerkgramCompanionShell.ts"
SOURCE_BINDING = Path(__file__).with_name("binding.js")

for path in (MOUNT_AUTH, SIGN_QR, BOOTSTRAP_IM, APP_IM, SOURCE_BINDING):
    if not path.exists():
        raise SystemExit(f"[jerkgram-passwordless-binding] missing {path}")


def patch_auth_routes() -> None:
    text = MOUNT_AUTH.read_text()
    states = (
        "authStateSignIn",
        "authStateSignQr",
        "authStateAuthCode",
        "authStatePassword",
        "authStateSignUp",
        "authStateSignImport",
    )
    for state in states:
        if f"case '{state}':" not in text:
            raise SystemExit(f"[jerkgram-passwordless-binding] auth state missing: {state}")
        pattern = re.compile(
            rf"(case '{re.escape(state)}':\s*)return \{{name: '[^']+'(?:,\s*payload:\s*[^;]+)?\}};"
        )
        text, count = pattern.subn(r"\1return {name: 'signQR'};", text, count=1)
        if count != 1:
            raise SystemExit(f"[jerkgram-passwordless-binding] could not rewrite auth state: {state}")

    if text.count("return {name: 'signQR'};") < len(states):
        raise SystemExit("[jerkgram-passwordless-binding] not all auth states route to passwordless setup")
    MOUNT_AUTH.write_text(text)


def write_binding_owner() -> None:
    BINDING_OWNER.write_text(r'''import App from '@config/app';
import {buildJerkgramBindingUrl} from '@lib/jerkgramPushBinding';

export type JerkgramBindingAction = 'register' | 'unregister';

const INSTALLATION_ID_KEY = 'jerkgram.notifications.installation.v1';
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isJerkgramStandalone(): boolean {
  const navigatorWithStandalone = navigator as Navigator & {standalone?: boolean};
  return window.matchMedia('(display-mode: standalone)').matches || navigatorWithStandalone.standalone === true;
}

function getOrCreateInstallationId(): string {
  const stored = localStorage.getItem(INSTALLATION_ID_KEY);
  if(stored && UUID_RE.test(stored)) return stored;

  const created = crypto.randomUUID();
  localStorage.setItem(INSTALLATION_ID_KEY, created);
  return created;
}

export async function makeJerkgramBindingUrl(action: JerkgramBindingAction): Promise<string | null> {
  if(action !== 'register' && action !== 'unregister') return null;
  if(!isJerkgramStandalone() || !('serviceWorker' in navigator) || !('PushManager' in window)) return null;

  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if(!subscription && action === 'register') {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: App.pushServerKey
    });
  }
  if(!subscription) return null;

  const json = subscription.toJSON();
  if(!json.endpoint || !json.keys?.p256dh || !json.keys?.auth) return null;

  return buildJerkgramBindingUrl(action, getOrCreateInstallationId(), {
    endpoint: json.endpoint,
    keys: {
      p256dh: json.keys.p256dh,
      auth: json.keys.auth
    },
    vapid: true
  });
}
''')


def write_setup_card() -> None:
    SIGN_QR.write_text(r'''import {createSignal} from 'solid-js';

import Button from '@components/buttonTsx';
import {isJerkgramStandalone, makeJerkgramBindingUrl} from '@lib/jerkgramCompanionBinding';

import AuthCard from '@/pages/AuthCard';

if(import.meta.hot) import.meta.hot.accept();

export default function SignQRCard() {
  const [busy, setBusy] = createSignal(false);
  const [status, setStatus] = createSignal('Jerkgram must already be installed and logged in.');

  async function connectWithJerkgram(): Promise<void> {
    if(busy()) return;
    if(!isJerkgramStandalone()) {
      setStatus('Add Jerkgram Notifications to the Home Screen first. Open it from the Home Screen to connect.');
      return;
    }
    if(!('Notification' in window)) {
      setStatus('Web Push is not available in this browser.');
      return;
    }

    setBusy(true);
    try {
      if(Notification.permission === 'default') {
        await Notification.requestPermission();
      }
      if(Notification.permission !== 'granted') {
        setStatus('Allow notifications in iOS Settings to continue.');
        return;
      }

      const url = await makeJerkgramBindingUrl('register');
      if(!url) {
        setStatus('Could not prepare Web Push on this device. Try again.');
        return;
      }

      setStatus('Approve in Jerkgram…');
      window.location.assign(url);
    } catch(_) {
      setStatus('Could not prepare Web Push on this device. Try again.');
    } finally {
      setBusy(false);
    }
  }

  const standalone = isJerkgramStandalone();
  return (
    <AuthCard inputWrapper={false}>
      <div style={{'text-align': 'center', padding: '12px 8px 20px'}}>
        <h1 style={{margin: '0 0 10px', 'font-size': '28px'}}>Jerkgram Notifications</h1>
        <p class="secondary" style={{margin: 0}}>
          Connect this device to receive Telegram notifications in Jerkgram.
        </p>
      </div>
      <Button
        primaryFilled
        large
        disabled={!standalone || busy()}
        onClick={connectWithJerkgram}
      >
        {busy() ? 'Opening Jerkgram…' : 'Connect with Jerkgram'}
      </Button>
      {!standalone && (
        <p class="secondary" style={{'text-align': 'center', 'font-size': '13px', margin: '12px 8px 0'}}>
          Add Jerkgram Notifications to the Home Screen first. Open it from the Home Screen to connect.
        </p>
      )}
      <p class="secondary" style={{'text-align': 'center', 'font-size': '13px', margin: '12px 8px 0'}}>
        {status()}
      </p>
    </AuthCard>
  );
}
''')


def write_shell() -> None:
    SHELL.write_text(r'''import {isJerkgramStandalone, makeJerkgramBindingUrl} from '@lib/jerkgramCompanionBinding';

let mounted = false;

function make<K extends keyof HTMLElementTagNameMap>(tag: K, text?: string): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  if(text !== undefined) element.textContent = text;
  return element;
}

export default function mountJerkgramCompanionShell(): void {
  if(mounted) return;
  mounted = true;

  const style = make('style');
  style.textContent = `
    #jerkgram-notifications-shell{position:fixed;inset:0;z-index:2147483646;background:#f5f5f7;color:#111;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text",sans-serif;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box}
    #jerkgram-notifications-card{width:min(100%,420px);background:#fff;border-radius:24px;padding:28px;box-sizing:border-box;box-shadow:0 18px 60px rgba(0,0,0,.12)}
    #jerkgram-notifications-card h1{font-size:28px;line-height:1.12;margin:0 0 10px}
    #jerkgram-notifications-card p{font-size:15px;line-height:1.45;margin:0;color:#666}
    #jerkgram-notifications-status{margin-top:16px!important;padding:13px 14px;border-radius:14px;background:#f2f2f7;color:#222!important}
    #jerkgram-notifications-connect,#jerkgram-notifications-disconnect{width:100%;margin-top:18px;border:0;border-radius:14px;padding:14px 16px;font:inherit;font-weight:600}
    #jerkgram-notifications-connect{background:#111;color:#fff}
    #jerkgram-notifications-disconnect{background:#f2f2f7;color:#b42318}
    #jerkgram-notifications-connect:disabled,#jerkgram-notifications-disconnect:disabled{opacity:.45}
  `;

  const shell = make('main');
  shell.id = 'jerkgram-notifications-shell';
  const card = make('section');
  card.id = 'jerkgram-notifications-card';
  const title = make('h1', 'Jerkgram Notifications');
  const intro = make('p', 'Notification companion for Jerkgram. This app can stay closed after setup.');
  const status = make('p', 'Connect Jerkgram to bind this device for Web Push.');
  status.id = 'jerkgram-notifications-status';
  const connect = make('button', 'Connect with Jerkgram');
  connect.id = 'jerkgram-notifications-connect';
  connect.type = 'button';
  const disconnect = make('button', 'Disconnect');
  disconnect.id = 'jerkgram-notifications-disconnect';
  disconnect.type = 'button';

  card.append(title, intro, status, connect, disconnect);
  shell.append(card);
  document.head.append(style);
  document.body.append(shell);

  const setBusy = (busy: boolean) => {
    connect.disabled = busy;
    disconnect.disabled = busy;
  };

  if(!isJerkgramStandalone()) {
    status.textContent = 'Add Jerkgram Notifications to the Home Screen first. Open it from the Home Screen to connect.';
    connect.disabled = true;
    disconnect.disabled = true;
  } else if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
    status.textContent = 'Web Push is not available in this browser.';
    connect.disabled = true;
    disconnect.disabled = true;
  } else if(Notification.permission === 'denied') {
    status.textContent = 'Notifications are blocked. Allow them in iOS Settings to connect.';
  }

  connect.addEventListener('click', async() => {
    setBusy(true);
    try {
      if(Notification.permission === 'default') {
        await Notification.requestPermission();
      }
      if(Notification.permission !== 'granted') {
        status.textContent = 'Allow notifications in iOS Settings to continue.';
        return;
      }
      const url = await makeJerkgramBindingUrl('register');
      if(!url) {
        status.textContent = 'Could not prepare Web Push on this device. Try again.';
        return;
      }
      status.textContent = 'Approve in Jerkgram…';
      window.location.assign(url);
    } catch(_) {
      status.textContent = 'Could not prepare Web Push on this device. Try again.';
    } finally {
      setBusy(false);
    }
  });

  disconnect.addEventListener('click', async() => {
    setBusy(true);
    try {
      const url = await makeJerkgramBindingUrl('unregister');
      if(!url) {
        status.textContent = 'No Web Push subscription was found on this device.';
        return;
      }
      status.textContent = 'Approve disconnect in Jerkgram…';
      window.location.assign(url);
    } catch(_) {
      status.textContent = 'Could not prepare disconnect. Try again.';
    } finally {
      setBusy(false);
    }
  });
}
''')


def write_bootstrap() -> None:
    BOOTSTRAP_IM.write_text(r'''import rootScope from '@lib/rootScope';
import mountJerkgramCompanionShell from '@lib/jerkgramCompanionShell';

import {disposeActiveAuthFlow} from '@/pages/mountAuthFlow';

let bootstrapped = false;

export async function bootstrapIm(): Promise<void> {
  if(bootstrapped) return;
  bootstrapped = true;

  await rootScope.managers.appStateManager.pushToState('authState', {_: 'authStateSignedIn'});
  mountJerkgramCompanionShell();
  disposeActiveAuthFlow();
  document.body.classList.remove('has-auth-pages');
}

export default bootstrapIm;
''')


def remove_stale_app_im_overlay() -> None:
    text = APP_IM.read_text()
    text = text.replace("import mountJerkgramCompanionShell from '@lib/jerkgramCompanionShell';\n", "")
    text = text.replace("\n    mountJerkgramCompanionShell();\n", "\n")
    APP_IM.write_text(text)


patch_auth_routes()
shutil.copyfile(SOURCE_BINDING, PURE_BINDING)
write_binding_owner()
write_setup_card()
write_shell()
write_bootstrap()
remove_stale_app_im_overlay()

combined = "\n".join(
    path.read_text()
    for path in (MOUNT_AUTH, SIGN_QR, BOOTSTRAP_IM, BINDING_OWNER, PURE_BINDING, SHELL)
)
for forbidden in (
    "auth.exportLoginToken",
    "auth.importLoginToken",
    "auth.loginTokenSuccess",
    "SESSION_PASSWORD_NEEDED",
    "jerkgram://push/authorize",
    "apiManagerProxy.pushSingleManager.registerDevice",
    "apiManagerProxy.pushSingleManager.unregisterDevice",
    "apiManager.logOut",
    "appDialogsManager",
):
    if forbidden in combined:
        raise SystemExit(f"[jerkgram-passwordless-binding] forbidden legacy dependency remains: {forbidden}")

for required in (
    "navigator.serviceWorker.ready",
    "pushManager.getSubscription()",
    "pushManager.subscribe",
    "App.pushServerKey",
    "crypto.randomUUID()",
    "Notification.requestPermission()",
    "jerkgram://push/register",
    "jerkgram://push/unregister",
    "Connect with Jerkgram",
    "Disconnect",
):
    if required not in combined:
        raise SystemExit(f"[jerkgram-passwordless-binding] missing invariant: {required}")

print("[jerkgram-passwordless-binding] OK")
print("  patched:", MOUNT_AUTH)
print("  replaced:", SIGN_QR)
print("  replaced:", BOOTSTRAP_IM)
print("  created:", PURE_BINDING)
print("  created:", BINDING_OWNER)
print("  created:", SHELL)
