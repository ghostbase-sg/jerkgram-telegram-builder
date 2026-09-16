#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
BOOTSTRAP_IM = ROOT / "src/pages/bootstrapIm.ts"


BOOTSTRAP_SOURCE = r'''import rootScope from '@lib/rootScope';
import uiNotificationsManager from '@lib/uiNotificationsManager';
import mountJerkgramNotificationsShell from '@lib/jerkgramNotificationsShell';

import {disposeActiveAuthFlow} from '@/pages/mountAuthFlow';

let bootstrapped = false;

export async function bootstrapIm(): Promise<void> {
  if(bootstrapped) return;
  bootstrapped = true;

  await rootScope.managers.appStateManager.pushToState('authState', {_: 'authStateSignedIn'});

  // Start only Web K's notification/update runtime. Do not boot appDialogsManager,
  // chat lists, calls, media controllers or the rest of Telegram Web's visible UI.
  uiNotificationsManager.constructAndStartAll();

  const pageChatsEl = document.getElementById('page-chats');
  if(pageChatsEl) pageChatsEl.style.display = 'none';

  disposeActiveAuthFlow();
  document.body.classList.remove('has-auth-pages');
  await mountJerkgramNotificationsShell();
}

export default bootstrapIm;
'''


def patch_bootstrap_text(_text: str) -> str:
    return BOOTSTRAP_SOURCE


def patch_tree(root: Path) -> None:
    target = root / "src/pages/bootstrapIm.ts"
    if not target.is_file():
        raise RuntimeError(f"[jerkgram-notification-runtime-v03] missing {target}")
    target.write_text(patch_bootstrap_text(target.read_text(encoding="utf-8")), encoding="utf-8")


def main() -> None:
    patch_tree(ROOT)
    print("[jerkgram-notification-runtime-v03] OK")
    print("  runtime: uiNotificationsManager only; Telegram chat shell remains dormant")


if __name__ == "__main__":
    main()
