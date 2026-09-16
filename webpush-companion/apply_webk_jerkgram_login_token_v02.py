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

import AuthCard from '@/pages/AuthCard';
import {CardSpec, useAuthFlow} from '@/pages/authFlow';

if(import.meta.hot) import.meta.hot.accept();

type Spec = Extract<CardSpec, {name: 'signQR'}>;

type PairingState = {
  nonce: string;
  createdAt: number;
};

const JERKGRAM_PAIRING_KEY = 'jerkgram.notifications.pairing.v1';
const INSTALLATION_ID_KEY = 'jerkgram.notifications.installation.v1';
const FETCH_INTERVAL = 2;

function tokenToBase64Url(token: Uint8Array | number[]): string {
  return fixBase64String(bytesToBase64(token), true).replace(/=+$/g, '');
}

function makePairingNonce(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(24));
  return tokenToBase64Url(bytes);
}

function getOrCreateInstallationId(): string {
  const current = localStorage.getItem(INSTALLATION_ID_KEY);
  if(current) return current;

  const created = crypto.randomUUID();
  localStorage.setItem(INSTALLATION_ID_KEY, created);
  return created;
}

function readPairingState(): PairingState | undefined {
  const raw = sessionStorage.getItem(JERKGRAM_PAIRING_KEY);
  if(!raw) return undefined;

  try {
    const parsed = JSON.parse(raw) as PairingState;
    if(!parsed.nonce || typeof parsed.createdAt !== 'number') return undefined;
    return parsed;
  } catch(_) {
    return undefined;
  }
}

function storePairingState(nonce: string): void {
  const value: PairingState = {nonce, createdAt: Date.now()};
  sessionStorage.setItem(JERKGRAM_PAIRING_KEY, JSON.stringify(value));
}

export default function SignQRCard(_props: {spec: Spec}) {
  const {managers, toIm} = useAuthFlow();
  const [busy, setBusy] = createSignal(false);
  const [status, setStatus] = createSignal('Ready to connect');
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

  function reconcileWithJerkgram(userId: string): void {
    const pairing = readPairingState();
    if(!pairing) {
      setStatus('Setup expired. Restart setup in Jerkgram.');
      return;
    }

    const installationId = getOrCreateInstallationId();
    const nonce = pairing.nonce;
    const url = `jerkgram://push/reconcile?v=1&user=${encodeURIComponent(userId)}&installation=${encodeURIComponent(installationId)}&nonce=${encodeURIComponent(nonce)}`;
    sessionStorage.removeItem(JERKGRAM_PAIRING_KEY);
    window.location.assign(url);
  }

  async function handleLoginSuccess(authorization: AuthAuthorization.authAuthorization): Promise<void> {
    await managers.apiManager.setUser(authorization.user);
    reconcileWithJerkgram(String(authorization.user.id));
    stopped = true;
    toIm();
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
            sessionStorage.removeItem(JERKGRAM_PAIRING_KEY);
            return;
          }
        }
        await pause(FETCH_INTERVAL * 1000);
      }
    } finally {
      polling = false;
    }
  }

  async function continueSetup(): Promise<void> {
    if(busy()) return;
    setBusy(true);
    setStatus('Preparing secure connection…');

    try {
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
      setStatus('Confirm this account in Jerkgram, then return here.');
      window.location.assign(url);
    } catch(error) {
      if((error as ApiError).type === 'SESSION_PASSWORD_NEEDED') {
        setStatus('Additional Telegram verification is required. Restart setup in Jerkgram.');
        sessionStorage.removeItem(JERKGRAM_PAIRING_KEY);
      } else {
        setStatus('Could not prepare setup. Try again.');
      }
    } finally {
      setBusy(false);
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

      <p class="secondary" style={{'text-align': 'center', margin: '0 8px 14px'}}>{status()}</p>

      <Button primaryFilled large disabled={busy()} onClick={continueSetup}>
        {busy() ? 'Preparing…' : 'Continue Setup'}
      </Button>

      <button
        type="button"
        onClick={openJerkgram}
        style={{
          display: 'block',
          width: '100%',
          margin: '14px 0 0',
          border: '0',
          background: 'transparent',
          color: 'var(--primary-color)',
          'font-size': '14px',
          cursor: 'pointer'
        }}
      >
        Started setup by mistake? Open Jerkgram
      </button>
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
    print("  replaced:", SIGN_QR)
    print("  flow: export login token -> Jerkgram accept -> Web K success -> reconcile user/install/nonce")


if __name__ == "__main__":
    main()
