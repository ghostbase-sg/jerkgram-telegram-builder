#!/usr/bin/env python3
"""Non-blocking source audit for the profile secondary video renderer.

This intentionally never fails a build. It reports whether the generated
profile background has the V11Q/V11S ownership contract required before a
future, runtime-changing profile-only optimization is allowed.
"""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
).resolve()

BACKGROUND = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/"
    "PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift"
)


def main() -> None:
    if not BACKGROUND.is_file():
        print("PROFILE_RENDERER_AUDIT: skip (generated background source is absent)")
        return

    source = BACKGROUND.read_text(encoding="utf-8")
    required = (
        "GhostBase v1.1P VIDEO_MIRROR1",
        "registerSecondaryVideoLayer(",
        "secondaryVideoDisposable",
        "desiredVideoIdentity",
        "refreshAnimatedVideoOwner(",
    )
    missing = [token for token in required if token not in source]
    forbidden = (
        "AVPlayer(",
        "AVQueuePlayer(",
        "let videoNode = UniversalVideoNode(",
        "NativeVideoContent(",
    )
    found_forbidden = [token for token in forbidden if token in source]

    if missing or found_forbidden:
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if found_forbidden:
            details.append("forbidden=" + ",".join(found_forbidden))
        print("PROFILE_RENDERER_AUDIT: hold (" + "; ".join(details) + ")")
        return

    print("PROFILE_RENDERER_AUDIT: ready (single decoder + secondary renderer)")


if __name__ == "__main__":
    main()
