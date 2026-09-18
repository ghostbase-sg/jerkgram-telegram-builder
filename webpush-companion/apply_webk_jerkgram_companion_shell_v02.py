#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
MOUNT_AUTH = ROOT / "src/pages/mountAuthFlow.tsx"
BOOTSTRAP_IM = ROOT / "src/pages/bootstrapIm.ts"
SHELL = ROOT / "src/lib/jerkgramNotificationsShell.ts"


AUTH_STATE_FUNCTION = r'''function authStateToCardSpec(_authState: MountAuthFlowState): CardSpec {
  // Jerkgram Notifications never exposes Telegram Web phone/code/password/passkey
  // authentication. Every unauthorised state returns to the single native-driven
  // login-token setup card; Jerkgram is the only place that can approve it.
  return {name: 'signQR'};
}
'''


BOOTSTRAP_SOURCE = r'''import rootScope from '@lib/rootScope';
import mountJerkgramNotificationsShell from '@lib/jerkgramNotificationsShell';

import {disposeActiveAuthFlow} from '@/pages/mountAuthFlow';

let bootstrapped = false;

export async function bootstrapIm(): Promise<void> {
  if(bootstrapped) return;
  bootstrapped = true;

  await rootScope.managers.appStateManager.pushToState('authState', {_: 'authStateSignedIn'});

  // Keep Web K's authenticated runtime alive because UiNotificationsManager owns
  // Telegram Web Push registration/renewal. The actual Telegram Web chat shell is
  // never exposed by the companion.
  const {default: appDialogsManager} = await import('@lib/appDialogsManager');
  appDialogsManager.start();

  const pageChatsEl = document.getElementById('page-chats');
  if(pageChatsEl) pageChatsEl.style.display = 'none';

  disposeActiveAuthFlow();
  document.body.classList.remove('has-auth-pages');
  await mountJerkgramNotificationsShell();
}

export default bootstrapIm;
'''


SHELL_SOURCE = r'''import rootScope from '@lib/rootScope';
import {getCurrentAccount} from '@lib/accounts/getCurrentAccount';

let mounted = false;

const JERKGRAM_PAIRING_KEY = 'jerkgram.notifications.pairing.v1';
const INSTALLATION_ID_KEY = 'jerkgram.notifications.installation.v1';
const PAIRING_LIFETIME_MS = 120_000;
const RECONCILE_RETRY_DELAY_MS = 5_000;

type PairingState = {
  nonce: string;
  createdAt: number;
  accountNumber: number;
  reconcileAttemptedAt?: number;
};

function make<K extends keyof HTMLElementTagNameMap>(tag: K, text?: string): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  if(text !== undefined) element.textContent = text;
  return element;
}

function isStandalone(): boolean {
  const nav = navigator as Navigator & {standalone?: boolean};
  return window.matchMedia('(display-mode: standalone)').matches || nav.standalone === true;
}

function userLabel(user: any): string {
  if(user?.username) return '@' + user.username;
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim();
  return name || 'Telegram account';
}

function readPendingPairing(): PairingState | undefined {
  const raw = localStorage.getItem(JERKGRAM_PAIRING_KEY);
  if(!raw) return undefined;
  try {
    const parsed = JSON.parse(raw) as PairingState;
    if(!parsed.nonce || typeof parsed.createdAt !== 'number' || !Number.isInteger(parsed.accountNumber) || parsed.accountNumber < 1 || parsed.accountNumber > 4 || (parsed.reconcileAttemptedAt !== undefined && (typeof parsed.reconcileAttemptedAt !== 'number' || !Number.isFinite(parsed.reconcileAttemptedAt))) || Date.now() - parsed.createdAt > PAIRING_LIFETIME_MS) {
      localStorage.removeItem(JERKGRAM_PAIRING_KEY);
      return undefined;
    }
    return parsed;
  } catch(_) {
    localStorage.removeItem(JERKGRAM_PAIRING_KEY);
    return undefined;
  }
}

function markReconcileAttempt(pairing: PairingState): void {
  localStorage.setItem(JERKGRAM_PAIRING_KEY, JSON.stringify({
    ...pairing,
    reconcileAttemptedAt: Date.now()
  } satisfies PairingState));
}

function armPairingCleanupAfterNativeHandoff(): void {
  let timer = 0;

  const disarm = () => {
    document.removeEventListener('visibilitychange', onVisibilityChange);
    window.removeEventListener('pagehide', onPageHide);
    if(timer) window.clearTimeout(timer);
  };
  const clearPairing = () => {
    localStorage.removeItem(JERKGRAM_PAIRING_KEY);
    disarm();
  };
  const onVisibilityChange = () => {
    if(document.visibilityState === 'hidden') clearPairing();
  };
  const onPageHide = () => clearPairing();

  document.addEventListener('visibilitychange', onVisibilityChange);
  window.addEventListener('pagehide', onPageHide, {once: true});
  timer = window.setTimeout(disarm, RECONCILE_RETRY_DELAY_MS);
}

function recoverPendingReconcile(self: any): boolean {
  const pairing = readPendingPairing();
  const installationId = localStorage.getItem(INSTALLATION_ID_KEY);
  if(!pairing || !installationId || !self?.id) return false;
  if(pairing.accountNumber !== getCurrentAccount()) return false;
  if(pairing.reconcileAttemptedAt && Date.now() - pairing.reconcileAttemptedAt < RECONCILE_RETRY_DELAY_MS) return false;

  const userId = String(self.id);
  const url = `jerkgram://push/reconcile?v=1&user=${encodeURIComponent(userId)}&installation=${encodeURIComponent(installationId)}&nonce=${encodeURIComponent(pairing.nonce)}`;
  markReconcileAttempt(pairing);
  armPairingCleanupAfterNativeHandoff();
  window.location.assign(url);
  return true;
}

async function getSubscriptionState(): Promise<'connected' | 'missing' | 'unavailable'> {
  if(!('serviceWorker' in navigator) || !('PushManager' in window)) return 'unavailable';
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return subscription ? 'connected' : 'missing';
  } catch(_) {
    return 'unavailable';
  }
}

export default async function mountJerkgramNotificationsShell(): Promise<void> {
  if(mounted) return;
  mounted = true;

  const style = make('style');
  style.textContent = `
    :root{color-scheme:light dark}
    #jg-notifications-shell{position:fixed;inset:0;z-index:2147483646;overflow:auto;background:#f1f1f6;color:#000;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}
    #jg-notifications-wrap{width:min(100% - 32px,430px);margin:0 auto;padding:max(36px,env(safe-area-inset-top)) 0 max(32px,env(safe-area-inset-bottom));box-sizing:border-box}
    #jg-notifications-hero{text-align:center;padding:12px 12px 26px}
    #jg-notifications-icon{width:76px;height:76px;margin:0 auto 17px;border-radius:23px;display:grid;place-items:center;background:linear-gradient(145deg,#56aaf3,#2a8be8);box-shadow:0 9px 24px rgba(43,139,232,.22);font-size:34px}
    #jg-notifications-hero h1{font-size:25px;line-height:1.2;letter-spacing:-.35px;margin:0;font-weight:700}
    #jg-notifications-hero p{font-size:14px;line-height:1.4;color:#777;margin:7px 0 0}
    .jg-section-title{font-size:13px;line-height:1.25;color:#6d6d72;text-transform:uppercase;margin:22px 16px 7px}
    .jg-card{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 .5px 0 rgba(0,0,0,.08)}
    .jg-row{min-height:49px;padding:10px 14px;display:flex;align-items:center;gap:12px;box-sizing:border-box;position:relative}
    .jg-row+.jg-row:before{content:"";position:absolute;top:0;left:46px;right:0;height:.5px;background:rgba(60,60,67,.22)}
    .jg-dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto;background:#ff9f0a}
    .jg-dot.ok{background:#34c759}.jg-dot.bad{background:#ff3b30}
    .jg-row-copy{min-width:0;flex:1}.jg-label{font-size:16px;line-height:1.2}.jg-value{font-size:13px;color:#8e8e93;line-height:1.25;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    #jg-state-pill{display:inline-flex;align-items:center;gap:7px;margin-top:13px;padding:7px 11px;border-radius:999px;background:rgba(52,199,89,.12);color:#248a3d;font-size:13px;font-weight:600}
    #jg-state-pill.attention{background:rgba(255,159,10,.14);color:#b36700}
    #jg-manage,#jg-permission{width:100%;border:0;border-radius:12px;padding:13px 15px;font:600 16px/1.2 -apple-system,BlinkMacSystemFont,"SF Pro Text",sans-serif;cursor:pointer;-webkit-tap-highlight-color:transparent}
    #jg-manage{margin-top:22px;background:#3390ec;color:#fff}
    #jg-permission{margin-top:10px;background:#fff;color:#3390ec}
    #jg-footnote{font-size:12px;line-height:1.4;color:#8e8e93;text-align:center;margin:13px 16px 0}
    @media (prefers-color-scheme: dark){#jg-notifications-shell{background:#000;color:#fff}.jg-card,#jg-permission{background:#1c1c1e}.jg-section-title,#jg-notifications-hero p,#jg-footnote{color:#8e8e93}.jg-row+.jg-row:before{background:rgba(84,84,88,.65)}#jg-permission{color:#64b5f6}}
  `;

  const shell = make('main');
  shell.id = 'jg-notifications-shell';
  const wrap = make('div');
  wrap.id = 'jg-notifications-wrap';

  const hero = make('header');
  hero.id = 'jg-notifications-hero';
  const icon = make('div', '🔔');
  icon.id = 'jg-notifications-icon';
  const title = make('h1', 'Jerkgram Notifications');
  const subtitle = make('p', 'Notifications for Jerkgram without keeping the main app open.');
  const statePill = make('div', 'Checking…');
  statePill.id = 'jg-state-pill';
  hero.append(icon, title, subtitle, statePill);

  const accountTitle = make('div', 'Account');
  accountTitle.className = 'jg-section-title';
  const accountCard = make('section');
  accountCard.className = 'jg-card';
  const accountRow = make('div');
  accountRow.className = 'jg-row';
  const accountDot = make('span');
  accountDot.className = 'jg-dot ok';
  const accountCopy = make('div');
  accountCopy.className = 'jg-row-copy';
  const accountLabel = make('div', 'Session');
  accountLabel.className = 'jg-label';
  const accountValue = make('div', 'Loading account…');
  accountValue.className = 'jg-value';
  accountCopy.append(accountLabel, accountValue);
  accountRow.append(accountDot, accountCopy);
  accountCard.append(accountRow);

  const statusTitle = make('div', 'Status');
  statusTitle.className = 'jg-section-title';
  const statusCard = make('section');
  statusCard.className = 'jg-card';

  function statusRow(label: string) {
    const row = make('div'); row.className = 'jg-row';
    const dot = make('span'); dot.className = 'jg-dot';
    const copy = make('div'); copy.className = 'jg-row-copy';
    const labelEl = make('div', label); labelEl.className = 'jg-label';
    const value = make('div', 'Checking…'); value.className = 'jg-value';
    copy.append(labelEl, value); row.append(dot, copy); statusCard.append(row);
    return {dot, value};
  }

  const permissionRow = statusRow('Permission');
  const sessionRow = statusRow('Session');
  const subscriptionRow = statusRow('Push subscription');

  const manage = make('button', 'Manage in Jerkgram');
  manage.id = 'jg-manage'; manage.type = 'button';
  manage.addEventListener('click', () => window.location.assign('jerkgram://push'));

  const permissionButton = make('button', 'Allow Notifications');
  permissionButton.id = 'jg-permission'; permissionButton.type = 'button'; permissionButton.hidden = true;

  const footnote = make('p', 'Connection and account management stay in Jerkgram.');
  footnote.id = 'jg-footnote';

  wrap.append(hero, accountTitle, accountCard, statusTitle, statusCard, manage, permissionButton, footnote);
  shell.append(wrap);
  document.head.append(style);
  document.body.append(shell);

  async function refresh(): Promise<void> {
    let self: any;
    try { self = await rootScope.managers.appUsersManager.getSelf(); } catch(_) {}
    accountValue.textContent = userLabel(self);

    // If iOS killed the standalone process after Telegram accepted the login token
    // but before the deep-link reconcile was delivered, the short-lived local
    // pairing record lets the signed-in companion finish that one pending handoff.
    if(self && recoverPendingReconcile(self)) return;

    const standalone = isStandalone();
    const permission = 'Notification' in window ? Notification.permission : 'denied';
    const subscription = await getSubscriptionState();

    permissionRow.value.textContent = permission === 'granted' ? 'Allowed' : permission === 'default' ? 'Not allowed yet' : 'Blocked in iOS';
    permissionRow.dot.className = 'jg-dot ' + (permission === 'granted' ? 'ok' : permission === 'denied' ? 'bad' : '');

    sessionRow.value.textContent = 'Connected';
    sessionRow.dot.className = 'jg-dot ok';

    subscriptionRow.value.textContent = subscription === 'connected' ? 'Connected' : subscription === 'missing' ? 'Repair required' : 'Unavailable';
    subscriptionRow.dot.className = 'jg-dot ' + (subscription === 'connected' ? 'ok' : subscription === 'unavailable' ? 'bad' : '');

    // Native Jerkgram is the authority for binding ACTIVE after user-id reconcile.
    // The PWA can only prove its own local notification transport readiness.
    const transportReady = standalone && permission === 'granted' && subscription === 'connected';
    statePill.textContent = transportReady ? 'Push ready' : 'Needs attention';
    statePill.className = transportReady ? '' : 'attention';
    statePill.id = 'jg-state-pill';
    permissionButton.hidden = permission !== 'default';
  }

  permissionButton.addEventListener('click', async() => {
    if(!('Notification' in window)) return;
    try { await Notification.requestPermission(); } catch(_) {}
    await refresh();
  });

  document.addEventListener('visibilitychange', () => {
    if(document.visibilityState === 'visible') void refresh();
  });

  await refresh();
  window.setTimeout(() => void refresh(), 800);
  window.setTimeout(() => void refresh(), 2500);
}
'''


def patch_mount_auth_text(text: str) -> str:
    marker = "function authStateToCardSpec("
    start = text.find(marker)
    if start < 0:
        raise RuntimeError("[jerkgram-companion-shell-v02] authStateToCardSpec missing")
    end_marker = "\nif(import.meta.hot)"
    end = text.find(end_marker, start)
    if end < 0:
        end = len(text)
    return text[:start] + AUTH_STATE_FUNCTION + text[end:]


def patch_bootstrap_text(_text: str) -> str:
    return BOOTSTRAP_SOURCE


def patch_tree(root: Path) -> None:
    mount = root / "src/pages/mountAuthFlow.tsx"
    bootstrap = root / "src/pages/bootstrapIm.ts"
    shell = root / "src/lib/jerkgramNotificationsShell.ts"
    if not mount.is_file() or not bootstrap.is_file():
        raise RuntimeError("[jerkgram-companion-shell-v02] pinned Web K files missing")

    mount.write_text(patch_mount_auth_text(mount.read_text(encoding="utf-8")), encoding="utf-8")
    bootstrap.write_text(patch_bootstrap_text(bootstrap.read_text(encoding="utf-8")), encoding="utf-8")
    shell.parent.mkdir(parents=True, exist_ok=True)
    shell.write_text(SHELL_SOURCE + "\n", encoding="utf-8")


def main() -> None:
    patch_tree(ROOT)
    print("[jerkgram-companion-shell-v02] OK")
    print("  auth: all unauthorised states -> Jerkgram login-token setup")
    print("  signed in: Telegram runtime retained for push, Telegram chat UI hidden")
    print("  shell: account + permission + session + subscription + pending reconcile recovery")


if __name__ == "__main__":
    main()
