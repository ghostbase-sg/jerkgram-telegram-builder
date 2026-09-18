#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
SHELL = ROOT / "src/lib/jerkgramNotificationsShell.ts"


def patch_shell_text(text: str) -> str:
    replacements = {
        "document.addEventListener('visibilitychange', () => {\n    if(document.visibilityState === 'visible') void refresh();\n  });": "document.addEventListener('visibilitychange', (): void => {\n    if(document.visibilityState === 'visible') {\n      void refresh();\n    }\n  });",
    }

    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise RuntimeError(f"[jerkgram-shell-typecheck-v04] expected callback anchor missing: {old}")

    for forbidden in (
        "visibilitychange', () =>",
    ):
        if forbidden in text:
            raise RuntimeError(f"[jerkgram-shell-typecheck-v04] unsafe callback remains: {forbidden}")

    for required in (
        "visibilitychange', (): void => {",
    ):
        if required not in text:
            raise RuntimeError(f"[jerkgram-shell-typecheck-v04] typed callback missing: {required}")

    return text


def patch_tree(root: Path) -> None:
    target = root / "src/lib/jerkgramNotificationsShell.ts"
    if not target.is_file():
        raise RuntimeError(f"[jerkgram-shell-typecheck-v04] missing {target}")
    target.write_text(patch_shell_text(target.read_text(encoding="utf-8")), encoding="utf-8")


def main() -> None:
    patch_tree(ROOT)
    print("[jerkgram-shell-typecheck-v04] OK")
    print("  explicit void callback annotations for TypeScript 7")


if __name__ == "__main__":
    main()
