#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SETTINGS = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
BLOCKED = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift")
BLOCKED_CONTEXT = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeersContext.swift")
REACTIONS = Path("submodules/TelegramCore/Sources/ApiUtils/ReactionsMessageAttribute.swift")
FOOTER = Path("submodules/TelegramUI/Components/Chat/ChatMessageReactionsFooterContentNode/Sources/ChatMessageReactionsFooterContentNode.swift")
STICKER = Path("submodules/TelegramUI/Components/Chat/ChatMessageStickerItemNode/Sources/ChatMessageStickerItemNode.swift")
INSTANT_VIDEO = Path("submodules/TelegramUI/Components/Chat/ChatMessageInstantVideoItemNode/Sources/ChatMessageInstantVideoItemNode.swift")
ANIMATED_STICKER = Path("submodules/TelegramUI/Components/Chat/ChatMessageAnimatedStickerItemNode/Sources/ChatMessageAnimatedStickerItemNode.swift")
PATCHER = Path("scripts/apply_build132_blocked_reactions_visibility.py")


def fail(message: str) -> None:
    raise SystemExit(f"[Build132 blocked reactions verify] FAIL: {message}")


def read(root: Path, rel: Path) -> str:
    path = root / rel
    if not path.is_file():
        fail(f"missing exact owner: {rel}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_build132_blocked_reactions_visibility.py <materialized-source-root>")

    root = Path(sys.argv[1]).expanduser().resolve()
    settings = read(root, SETTINGS)
    blocked = read(root, BLOCKED)
    blocked_context = read(root, BLOCKED_CONTEXT)
    reactions = read(root, REACTIONS)
    footer = read(root, FOOTER)
    sticker = read(root, STICKER)
    instant_video = read(root, INSTANT_VIDEO)
    animated_sticker = read(root, ANIMATED_STICKER)
    patcher = read(root, PATCHER)

    # User requirement: both visibility features are opt-in.
    for token in (
        'hideBlockedMessages: ghostBaseBool(GhostBaseKey.hideBlockedMessages, defaultValue: false)',
        'static let hideBlockedReactions = "GhostBase.Messages.HideBlockedReactions"',
        'var hideBlockedReactions: Bool',
        'hideBlockedReactions: ghostBaseBool(GhostBaseKey.hideBlockedReactions, defaultValue: false)',
        '"Скрывать реакции заблокированных"',
        'state.hideBlockedReactions',
    ):
        if token not in settings:
            fail(f"OFF-by-default settings contract missing: {token}")

    # Registry is local presentation state only. It is updated on successful
    # block/unblock and also synchronized from contacts.getBlocked results so
    # users blocked before installing this build are covered.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_PEER_REGISTRY",
        "JerkgramBlockedPeerRegistry",
        "setBlocked(peerId:",
        "isBlocked: isBlocked",
    ):
        if token not in blocked:
            fail(f"blocked-peer registry/update missing: {token}")
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_PEER_REGISTRY_SYNC",
        "JerkgramBlockedPeerRegistry.replaceBlockedPeerIds(",
    ):
        if token not in blocked_context:
            fail(f"blocked-peer registry sync missing: {token}")

    # Filtering is a pure view projection. Source ReactionsMessageAttribute
    # stays untouched in Postbox, therefore unblock restores the original data.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_REACTION_FILTER",
        "jerkgramFilteredReactionsForBlockedPeers(",
        "recentPeers.filter",
        "topPeers.filter",
        "MessageReaction(value:",
        "ReactionsMessageAttribute(",
    ):
        if token not in reactions:
            fail(f"reaction projection helper missing: {token}")
    for forbidden in (
        "transaction.updateMessage",
        "withUpdatedBlockedReaction",
        "removeAll(where:",
    ):
        if forbidden in reactions:
            fail(f"reaction source mutation leaked into projection helper: {forbidden}")

    # Every chat rendering path that builds reaction buttons must opt in to the
    # same helper. The helper itself is responsible for group/supergroup-only.
    for text, label in (
        (footer, "footer"),
        (sticker, "sticker"),
        (instant_video, "instant video"),
        (animated_sticker, "animated sticker"),
    ):
        for token in (
            "JERKGRAM_BUILD132_BLOCKED_REACTION_UI_FILTER",
            "jerkgramFilteredReactionsForBlockedPeers(",
            'UserDefaults.standard.bool(forKey: "GhostBase.Messages.HideBlockedReactions")',
        ):
            if token not in text:
                fail(f"{label} reaction filtering missing: {token}")

    for token in (
        "peer is TelegramGroup",
        "case .group = channel.info",
    ):
        if token not in reactions:
            fail(f"group/supergroup-only guard missing: {token}")

    # STEP5 is read-only presentation logic; no destructive message/reaction
    # persistence and no private-chat filtering.
    if "JERKGRAM_BUILD132_BLOCKED_REACTION_PERSIST" in patcher:
        fail("reaction persistence/mutation is forbidden")
    if "rglob(" in patcher or ".glob(" in patcher or "os.walk(" in patcher:
        fail("broad source discovery is forbidden")

    for rel in (SETTINGS, BLOCKED, BLOCKED_CONTEXT, REACTIONS, FOOTER, STICKER, INSTANT_VIDEO, ANIMATED_STICKER):
        if str(rel) not in patcher:
            fail(f"patcher not bound to exact owner: {rel}")

    print("[Build132 blocked reactions verify] PASS: both toggles OFF + synced blocked registry + reversible group-only reaction projection")


if __name__ == "__main__":
    main()
