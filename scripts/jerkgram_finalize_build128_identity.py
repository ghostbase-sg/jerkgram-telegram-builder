#!/usr/bin/env python3

import sys

import jerkgram_finalize_build122_identity as base
import jerkgram_finalize_build126_keychain_package1 as keychain
import jerkgram_finalize_build128_file_picker_package1 as file_picker


base.BUILD = "128"


def main() -> None:
    ipa = keychain.Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    base.main()
    keychain.package_ipa(ipa)
    file_picker.package_file_picker(ipa)
    print("[Build128 identity] GREEN")
    print("[Build128 identity] CFBundleVersion=128; audited main-app-only keychain and FilePicker dylibs are present")


if __name__ == "__main__":
    main()
