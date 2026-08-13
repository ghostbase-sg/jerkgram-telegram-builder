#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

AVATAR = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoScreen/Sources/"
      "PeerInfoAvatarTransformContainerNode.swift"
)

errors = []

if not AVATAR.is_file():
    errors.append(
        f"missing {AVATAR}"
    )
else:
    text = AVATAR.read_text(
        encoding="utf-8"
    )

    if (
        "GhostBase v1.1M ANIMCOEXIST1"
        not in text
    ):
        errors.append(
            "animation coexist marker missing"
        )

    if (
        "animatedBackgroundEnabled"
        not in text
        or
        "keepVideoAlive"
        not in text
    ):
        errors.append(
            "GhostBase animation gate missing"
        )

    if (
        "if keepVideoAlive"
        not in text
        or
        "videoNode.play()"
        not in text
    ):
        errors.append(
            "native avatar keep-playing path missing"
        )

    if (
        "else if fraction > 0.0"
        not in text
        or
        "videoNode.pause()"
        not in text
    ):
        errors.append(
            "Official fallback pause behavior lost"
        )

if errors:
    print("[V11M-A2 VERIFY] FAILED")

    for error in errors:
        print(" -", error)

    raise RuntimeError(
        "V11M-A2 verifier failed"
    )

print("[V11M-A2 VERIFY] OK")
print("  native avatar and GhostBase backdrop may play concurrently")
print("  Official transition pause remains when animation is disabled")
