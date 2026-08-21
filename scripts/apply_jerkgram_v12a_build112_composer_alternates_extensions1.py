#!/usr/bin/env python3

import os
import re
from pathlib import Path

ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

BUILD = ROOT / "Telegram/BUILD"

OLD_MARKER = "# MARK: Jerkgram v1.2A BUILD112_COMPOSER_ALTERNATES1"
OLD_POST = ROOT / "Telegram/Telegram-iOS/JerkgramIconComposerPostProcessor.sh"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[Build112] " + message)


def main() -> None:
    require(BUILD.is_file(), f"missing {BUILD}")

    build = BUILD.read_text(encoding="utf-8")

    # Build111 is the canonical owner of the native Xcode 26 Composer assets.
    # Build112 must not convert Glass to PNG/.alticon or re-own actool.
    require(
        'primary_app_icon = "Telegram"' in build,
        "Build111 Telegram primary_app_icon missing",
    )

    for name in ("JerkgramGlassReveal", "JerkgramGlassSolid"):
        require(
            f'"{name}"' in build,
            f"Build111 native Composer icon missing: {name}",
        )

    require(
        "Telegram-iOS/JerkgramGlassReveal.alticon" not in build
        and "Telegram-iOS/JerkgramGlassSolid.alticon" not in build,
        "Glass must never use legacy .alticon",
    )

    # Cleanup only the exact obsolete Build112 bridge if this patcher is
    # re-applied to a tree that already contains the previous Build112 attempt.
    old_inline = re.compile(
        r'(?m)^[ \t]*'
        + re.escape(OLD_MARKER)
        + r'[ \t]*\n'
        r'[ \t]*ipa_post_processor[ \t]*=[ \t]*'
        r'":JerkgramIconComposerPostProcessor",[ \t]*\n?'
    )
    build, inline_count = old_inline.subn("", build)

    old_target = re.compile(
        r'\n?'
        + re.escape(OLD_MARKER)
        + r'\n'
        r'sh_binary\(\n'
        r'[ \t]*name = "JerkgramIconComposerPostProcessor",\n'
        r'[ \t]*srcs = \["Telegram-iOS/JerkgramIconComposerPostProcessor\.sh"\],\n'
        r'[ \t]*visibility = \["//visibility:private"\],\n'
        r'\)\n?',
        re.MULTILINE,
    )
    build, target_count = old_target.subn("\n", build)

    require(
        'ipa_post_processor = ":JerkgramIconComposerPostProcessor"' not in build,
        "obsolete Build112 main-app ipa_post_processor survived cleanup",
    )
    require(
        'name = "JerkgramIconComposerPostProcessor"' not in build,
        "obsolete Build112 sh_binary survived cleanup",
    )

    BUILD.write_text(build, encoding="utf-8")

    if OLD_POST.exists():
        payload = OLD_POST.read_text(encoding="utf-8", errors="ignore")
        require(
            "Jerkgram Build112 Icon Composer alternate registration bridge"
            in payload,
            "refusing to delete a non-Build112 postprocessor file",
        )
        OLD_POST.unlink()

    print("[Build112] native Build111 Composer assets preserved")
    print("[Build112] obsolete ipa_post_processor bridge removed")
    print(
        "[Build112] cleanup counts: "
        f"inline={inline_count}, target={target_count}"
    )
    print("[Build112] no Glass PNG/.alticon fallback introduced")


if __name__ == "__main__":
    main()
