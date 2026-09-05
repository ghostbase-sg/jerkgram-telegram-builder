#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"

# STEP7 diagnostic only: determine whether the installed iOS bundle identifier
# crosses into Telegram/MTProto client initialization. Never mutate source here.
CANDIDATE_ROOTS = (
    "submodules/TelegramCore/Sources",
    "submodules/TelegramUI/Sources",
    "submodules/MtProtoKit/Sources",
    "submodules/AccountContext/Sources",
    "submodules/BuildConfig/Sources",
)

BUNDLE_MARKERS = (
    "Bundle.main.bundleIdentifier",
    "NSBundle mainBundle",
    "BuildConfig.bundleId",
    "[BuildConfig bundleId]",
    ".bundleId",
    "baseAppBundleId",
)

CLIENT_MARKERS = (
    "initConnection",
    "Api.functions.initConnection",
    "apiId",
    "api_id",
    "MtProto",
    "MTProto",
    "NetworkInitialization",
    "NetworkArguments",
    "appVersion",
    "systemVersion",
    "deviceModel",
    "langCode",
)


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def main() -> int:
    root = source_root()
    if not root.is_dir():
        raise SystemExit(f"[build132-client-identity-audit] missing source root: {root}")

    scanned = 0
    bundle_hits: list[tuple[str, list[str]]] = []
    crossing_hits: list[tuple[str, list[str], list[str]]] = []

    for relative_root in CANDIDATE_ROOTS:
        base = root / relative_root
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".swift", ".m", ".mm", ".h", ".hpp", ".cpp"}:
                continue
            if path.stat().st_size > 2_000_000:
                continue
            scanned += 1
            text = path.read_text(encoding="utf-8", errors="ignore")
            bundle = [marker for marker in BUNDLE_MARKERS if marker in text]
            if not bundle:
                continue
            client = [marker for marker in CLIENT_MARKERS if marker in text]
            relative = str(path.relative_to(root))
            bundle_hits.append((relative, bundle))
            if client:
                crossing_hits.append((relative, bundle, client))

    print(f"[build132-client-identity-audit] scanned_source_files={scanned}")
    print(f"[build132-client-identity-audit] bundle_identity_files={len(bundle_hits)}")
    for path, bundle in bundle_hits[:30]:
        print(f"  bundle path={path} markers={','.join(bundle)}")

    if crossing_hits:
        print("[build132-client-identity-audit] REVIEW: bundle identity and client/network markers coexist:")
        for path, bundle, client in crossing_hits:
            print(f"  path={path}")
            print(f"    bundle={','.join(bundle)}")
            print(f"    client={','.join(client)}")
        return 3

    print(
        "[build132-client-identity-audit] PASS: no bounded source file directly combines "
        "installed bundle identity with Telegram/MTProto client initialization markers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
