#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE_ENV = "GHOSTBASE_SOURCE_ROOT"

# STEP6 diagnostic only. This script never mutates Telegram source.
# Keep the search intentionally bounded to Settings / profile-header UI owners.
CANDIDATE_ROOTS = (
    "submodules/SettingsUI/Sources",
    "submodules/TelegramUI/Components/Settings",
    "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources",
    "submodules/PeerInfoUI/Sources",
)

SCROLL_MARKERS = (
    "contentOffset",
    "visibleContentOffset",
    "contentOffsetChanged",
    "updateScrolling",
    "scrollViewDidScroll",
    "overscroll",
    "isCollapsing",
)

AVATAR_MARKERS = (
    "AvatarNode",
    "avatarNode",
    "avatarView",
    "avatarContainer",
    "avatarImageNode",
    "avatarListNode",
)

SHAPE_MARKERS = (
    "cornerRadius",
    "updateCornerRadius",
    "maskNode",
    "clipsToBounds",
    "masksToBounds",
    "transform",
    "scale",
)

ANIMATION_MARKERS = (
    "animate",
    "transition.update",
    "ContainedViewLayoutTransition",
    "UIViewPropertyAnimator",
    "CADisplayLink",
)

VIDEO_LIFECYCLE_MARKERS = (
    "canAttachVideo",
    "canAttachContent",
    "UniversalVideoNode",
    "videoNode.play()",
    "videoNode.pause()",
)


def source_root() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).resolve()
    value = os.environ.get(SOURCE_ENV)
    if not value:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <telegram-source-root> (or set {SOURCE_ENV})")
    return Path(value).resolve()


def hits(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker in text]


def main() -> int:
    root = source_root()
    if not root.is_dir():
        raise SystemExit(f"source root does not exist: {root}")

    candidates: list[tuple[int, str, list[str], list[str], list[str], list[str], list[str]]] = []
    scanned = 0

    for relative_root in CANDIDATE_ROOTS:
        base = root / relative_root
        if not base.is_dir():
            continue
        for path in base.rglob("*.swift"):
            scanned += 1
            text = path.read_text(encoding="utf-8", errors="ignore")
            scroll = hits(text, SCROLL_MARKERS)
            avatar = hits(text, AVATAR_MARKERS)
            shape = hits(text, SHAPE_MARKERS)
            animation = hits(text, ANIMATION_MARKERS)
            video = hits(text, VIDEO_LIFECYCLE_MARKERS)

            # A stretch/morph owner must at minimum react to scrolling/collapse and own/touch an avatar.
            if not scroll or not avatar:
                continue

            score = len(scroll) * 4 + len(avatar) * 4 + len(shape) * 2 + len(animation) + len(video) * 5
            candidates.append((score, str(path.relative_to(root)), scroll, avatar, shape, animation, video))

    candidates.sort(key=lambda item: (-item[0], item[1]))

    print(f"[build132-settings-avatar-diag] scanned_swift={scanned}")
    if not candidates:
        print("[build132-settings-avatar-diag] no bounded Settings/profile avatar owner found")
        return 2

    for score, path, scroll, avatar, shape, animation, video in candidates[:12]:
        print(f"\nscore={score} path={path}")
        print(f"  scroll={','.join(scroll)}")
        print(f"  avatar={','.join(avatar)}")
        print(f"  shape={','.join(shape) if shape else '-'}")
        print(f"  animation={','.join(animation) if animation else '-'}")
        print(f"  video={','.join(video) if video else '-'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
