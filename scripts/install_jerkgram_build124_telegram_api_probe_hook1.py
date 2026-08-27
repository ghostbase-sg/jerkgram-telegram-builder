#!/usr/bin/env python3

from pathlib import Path
import os


PROBE = Path(os.environ.get("JERKGRAM_PROBE_PATH", str(Path(__file__).resolve().parent / "bazel_build_probe_official.sh"))).resolve()
ANCHOR = '''# Swiftgram config placeholder for BuildConfig\nsg_config = "{}"\nEOF\n'''
APPLY = "apply_jerkgram_build124_telegram_api_credentials1.py"
VERIFY = "verify_jerkgram_build124_telegram_api_credentials1.py"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Jerkgram Telegram API probe hook] " + message)


def patch_probe(text: str) -> str:
    if APPLY in text and VERIFY in text:
        require(text.index(APPLY) < text.index(VERIFY), "credential verifier runs before injection")
        require(text.index(VERIFY) < text.index('"$BAZEL_BIN" build'), "credential verifier runs after Bazel")
        return text

    require(text.count(ANCHOR) == 1, "active configuration creation anchor count")
    block = ANCHOR + '''\n\necho\necho "== Jerkgram private Telegram API credentials =="\npython3 ../../scripts/apply_jerkgram_build124_telegram_api_credentials1.py --variables build-input/configuration-repository/variables.bzl\npython3 ../../scripts/verify_jerkgram_build124_telegram_api_credentials1.py --variables build-input/configuration-repository/variables.bzl\n'''
    text = text.replace(ANCHOR, block, 1)
    require(text.index(APPLY) < text.index(VERIFY), "credential apply/verify order")
    require(text.index(VERIFY) < text.index('"$BAZEL_BIN" build'), "credential verifier runs after Bazel")
    return text


def main() -> None:
    text = PROBE.read_text(encoding="utf-8")
    updated = patch_probe(text)
    PROBE.write_text(updated, encoding="utf-8")
    print("[Jerkgram Telegram API probe hook] GREEN")


if __name__ == "__main__":
    main()
