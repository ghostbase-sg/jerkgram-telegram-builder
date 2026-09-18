#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
SIGN_QR = ROOT / "src/pages/cards/SignQRCard.tsx"


SIGN_QR_SOURCE = r'''import {createSignal, onCleanup, onMount} from 'solid-js';

import Button from '@components/buttonTsx';
import bytesToBase64 from '@helpers/bytes/bytesToBase64';
import fixBase64String from '@helpers/fixBase64String';
import pause from '@helpers/schedulers/pause';
import type {DcId} from '@types';
import {AuthAuthorization, AuthLoginToken} from '@layer';
import App from '@config/app';
import AccountController from '@lib/accounts/accountController';
import {getCurrentAccount} from '@lib/accounts/getCurrentAccount';

import AuthCard from '@/pages/AuthCard';
import {CardSpec, useAuthFlow} from '@/pages/authFlow';

if(import.meta.hot) import.meta.hot.accept();

type Spec = Extract<CardSpec, {name: 'signQR'}>;

type PairingState = {
  nonce: string;
  createdAt: number;
  accountNumber: number;
  telegramUserId?: string;
};

const JERKGRAM_PAIRING_KEY = 'jerkgram.notifications.pairing.v1';
const INSTALLATION_ID_KEY = 'jerkgram.notifications.installation.v1';
const PAIRING_LIFETIME_MS = 120_000;
const FETCH_INTERVAL = 2;

function tokenToBase64Url(token: Uint8Array | number[]): string {
  return fixBase64String(bytesToBase64(token), true).replace(/=+$/g, '');
}

function makePairingNonce(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(24));
  return tokenToBase64Url(bytes);
}

function isJerkgramStandalone(): boolean {
  const nav = navigator as Navigator & {standalone?: boolean};
  return window.matchMedia('(display-mode: standalone)').matches || nav.standalone === true;
}

function getOrCreateInstallationId(): string {
  const current = localStorage.getItem(INSTALLATION_ID_KEY);
  if(current) return current;

  const created = crypto.randomUUID();
  localStorage.setItem(INSTALLATION_ID_KEY, created);
  return created;
}

function readPairingState(): PairingState | undefined {
  const raw = localStorage.getItem(JERKGRAM_PAIRING_KEY);
  if(!raw) return undefined;

  try {
    const parsed = JSON.parse(raw) as PairingState;
    if(!parsed.nonce || typeof parsed.createdAt !== 'number' || !Number.isInteger(parsed.accountNumber) || parsed.accountNumber < 1 || parsed.accountNumber > 4 || (parsed.telegramUserId !== undefined && !/^[1-9][0-9]{0,19}$/.test(parsed.telegramUserId))) {
      localStorage.removeItem(JERKGRAM_PAIRING_KEY);
      return undefined;
    }
    if(Date.now() - parsed.createdAt > PAIRING_LIFETIME_MS) {
      localStorage.removeItem(JERKGRAM_PAIRING_KEY);
      return undefined;
    }
    return parsed;
  } catch(_) {
    localStorage.removeItem(JERKGRAM_PAIRING_KEY);
    return undefined;
  }
}

function storePairingState(nonce: string): void {
  const value: PairingState = {nonce, createdAt: Date.now(), accountNumber: getCurrentAccount()};
  localStorage.setItem(JERKGRAM_PAIRING_KEY, JSON.stringify(value));
}

function storeAcceptedUserId(userId: string): void {
  const pairing = readPairingState();
  if(!pairing || pairing.accountNumber !== getCurrentAccount()) return;
  localStorage.setItem(JERKGRAM_PAIRING_KEY, JSON.stringify({
    ...pairing,
    telegramUserId: userId
  } satisfies PairingState));
}

export default function SignQRCard(_props: {spec: Spec}) {
  const {managers, toIm} = useAuthFlow();
  const [busy, setBusy] = createSignal(false);
  const [status, setStatus] = createSignal('Start setup in Jerkgram first.');
  let stopped = false;
  let polling = false;
  const options: {dcId?: DcId, ignoreErrors: true} = {ignoreErrors: true};

  async function exportOrImportLoginToken(): Promise<AuthLoginToken> {
    const userIds = await AccountController.getUserIds();
    let loginToken = await managers.apiManager.invokeApi('auth.exportLoginToken', {
      api_id: App.id,
      api_hash: App.hash,
      except_ids: userIds.map((userId) => userId.toUserId())
    }, {ignoreErrors: true});

    if(loginToken._ === 'auth.loginTokenMigrateTo') {
      if(!options.dcId) {
        options.dcId = loginToken.dc_id as DcId;
        managers.apiManager.setBaseDcId(loginToken.dc_id);
      }
      loginToken = await managers.apiManager.invokeApi('auth.importLoginToken', {
        token: loginToken.token
      }, options) as AuthLoginToken;
    }

    return loginToken as AuthLoginToken;
  }

  async function handleLoginSuccess(authorization: AuthAuthorization.authAuthorization): Promise<void> {
    await managers.apiManager.setUser(authorization.user);
    storeAcceptedUserId(String(authorization.user.id));
    stopped = true;
    await toIm();
  }

  async function continueSetup(): Promise<void> {
    if(busy()) return;

    if(!isJerkgramStandalone()) {
      setStatus('Add Jerkgram Notifications to the Home Screen first.');
      return;
    }
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
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

      setStatus('Preparing secure connection…');
      const loginToken = await exportOrImportLoginToken();
      if(loginToken._ === 'auth.loginTokenSuccess') {
        await handleLoginSuccess(loginToken.authorization as any as AuthAuthorization.authAuthorization);
        return;
      }
      if(loginToken._ !== 'auth.loginToken') {
        setStatus('Could not prepare setup. Try again.');
        return;
      }

      const nonce = makePairingNonce();
      storePairingState(nonce);
      getOrCreateInstallationId();
      const tokenValue = tokenToBase64Url(loginToken.token);
      const url = `jerkgram://push/authorize?v=1&token=${encodeURIComponent(tokenValue)}&nonce=${encodeURIComponent(nonce)}`;
      setStatus('Jerkgram is opening. Confirm the selected account there, then return here.');
      window.location.assign(url);
    } catch(error) {
      if((error as ApiError).type === 'SESSION_PASSWORD_NEEDED') {
        setStatus('Additional Telegram verification is required. Restart setup in Jerkgram.');
        localStorage.removeItem(JERKGRAM_PAIRING_KEY);
      } else {
        setStatus('Could not prepare setup. Try again.');
      }
    } finally {
      setBusy(false);
    }
  }

  async function pollForAcceptedLogin(): Promise<void> {
    if(polling || stopped || !readPairingState()) return;
    polling = true;
    try {
      while(!stopped && readPairingState()) {
        try {
          const loginToken = await exportOrImportLoginToken();
          if(loginToken._ === 'auth.loginTokenSuccess') {
            await handleLoginSuccess(loginToken.authorization as any as AuthAuthorization.authAuthorization);
            return;
          }
        } catch(error) {
          if((error as ApiError).type === 'SESSION_PASSWORD_NEEDED') {
            setStatus('Additional Telegram verification is required. Restart setup in Jerkgram.');
            localStorage.removeItem(JERKGRAM_PAIRING_KEY);
            return;
          }
        }
        await pause(FETCH_INTERVAL * 1000);
      }
    } finally {
      polling = false;
    }
  }

  function openJerkgram(): void {
    window.location.assign('jerkgram://push');
  }

  const onVisibilityChange = () => {
    if(document.visibilityState === 'visible') {
      void pollForAcceptedLogin();
    }
  };

  onMount(() => {
    document.addEventListener('visibilitychange', onVisibilityChange);
    if(readPairingState()) {
      setStatus('Waiting for confirmation in Jerkgram…');
      void pollForAcceptedLogin();
    } else if(!isJerkgramStandalone()) {
      setStatus('Add Jerkgram Notifications to the Home Screen first.');
    } else if('Notification' in window && Notification.permission === 'denied') {
      setStatus('Allow notifications in iOS Settings to continue.');
    }
  });

  onCleanup(() => {
    stopped = true;
    document.removeEventListener('visibilitychange', onVisibilityChange);
  });

  return (
    <AuthCard inputWrapper={false}>
      <div style={{'text-align': 'center', padding: '10px 8px 20px'}}>
        <h1 style={{margin: '0 0 10px', 'font-size': '28px'}}>Jerkgram Notifications</h1>
        <p class="secondary" style={{margin: 0}}>
          Notifications for Jerkgram without keeping the main app open.
        </p>
      </div>

      <div style={{
        margin: '0 0 14px',
        padding: '14px 16px',
        'border-radius': '14px',
        background: 'var(--surface-color, rgba(120,120,128,.08))',
        'font-size': '14px',
        'line-height': '1.45'
      }}>
        <div><b>1.</b> Open Jerkgram.</div>
        <div><b>2.</b> Go to Settings → Jerkgram → Jerkgram Notifications.</div>
        <div><b>3.</b> Tap Enable Notifications, then return here.</div>
      </div>

      <p class="secondary" style={{'text-align': 'center', margin: '0 8px 14px'}}>{status()}</p>

      <Button primaryFilled large onClick={openJerkgram}>
        Open Jerkgram
      </Button>

      <Button large disabled={busy()} onClick={continueSetup}>
        {busy() ? 'Preparing…' : 'I started it in Jerkgram — Continue'}
      </Button>
    </AuthCard>
  );
}
'''


def patch_sign_qr_text(_text: str) -> str:
    return SIGN_QR_SOURCE


def patch_tree(root: Path) -> None:
    target = root / "src/pages/cards/SignQRCard.tsx"
    if not target.is_file():
        raise RuntimeError(f"[jerkgram-login-token-v02] missing {target}")
    current = target.read_text(encoding="utf-8")
    target.write_text(patch_sign_qr_text(current), encoding="utf-8")


def main() -> None:
    patch_tree(ROOT)
    print("[jerkgram-login-token-v02] OK")
    print("  flow: start in native Jerkgram -> Home Screen + permission -> login token -> native confirm -> explicit finish")
    print("  pairing: origin-local, 120 second TTL, survives standalone process restart")


if __name__ == "__main__":
    main()
