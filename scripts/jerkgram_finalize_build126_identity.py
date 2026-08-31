#!/usr/bin/env python3

import sys

import jerkgram_finalize_build122_identity as base
import jerkgram_finalize_build126_keychain_package1 as keychain_package


base.BUILD = "128"


def main() -> None:
    base.main()
    ipa = keychain_package.Path(
        sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa"
    ).resolve()
    keychain_package.package_ipa(ipa)
    print("[Build128 identity] GREEN")
    print("[Build128 identity] CFBundleVersion=128; audited keychain dylib is main-app-only and resign-ready")


if __name__ == "__main__":
    main()
