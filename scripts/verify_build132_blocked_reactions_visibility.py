#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SETTINGS = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
BLOCKED = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift")
BLOCKED_CONTEXT = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeersContext.swift")
REACTIONS = Path("submodules/TelegramCore/Sources/ApiUtils/ReactionsMessageAttribute.swift")
REACTION_STATE = Path("submodules/TelegramCore/Sources/State/MessageReactions.swift")
FOOTER = Path("submodules/TelegramUI/Components/Chat/ChatMessageReactionsFooterContentNode/Sources/ChatMessageReactionsFooterContentNode.swift")
STICKER = Path("submodules/TelegramUI/Components/Chat/ChatMessageStickerItemNode/Sources/ChatMessageStickerItemNode.swift")
INSTANT_VIDEO = Path("submodules/TelegramUI/Components/Chat/ChatMessageInstantVideoItemNode/Sources/ChatMessageInstantVideoItemNode.swift")
ANIMATED_STICKER = Path("submodules/TelegramUI/Components/Chat/ChatMessageAnimatedStickerItemNode/Sources/ChatMessageAnimatedStickerItemNode.swift")
RICH_DATA = Path("submodules/TelegramUI/Components/Chat/ChatMessageRichDataBubbleContentNode/Sources/ChatMessageRichDataBubbleContentNode.swift")
SCRIPTS = Path(__file__).resolve().parent
PATCHER = SCRIPTS / "apply_build132_blocked_reactions_visibility.py"
LIST_PATCHER = SCRIPTS / "apply_build132_blocked_reaction_list_filter.py"
RICH_PATCHER = SCRIPTS / "apply_build132_blocked_reactions_rich_data.py"


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
    reaction_state = read(root, REACTION_STATE)
    footer = read(root, FOOTER)
    sticker = read(root, STICKER)
    instant_video = read(root, INSTANT_VIDEO)
    animated_sticker = read(root, ANIMATED_STICKER)
    rich_data = read(root, RICH_DATA)
    patcher = read(root, PATCHER)
    list_patcher = read(root, LIST_PATCHER)
    rich_patcher = read(root, RICH_PATCHER)

    # User requirement: both visibility features are opt-in and use the
    # current account-scoped Jerkgram Messages settings owner.
    for token in (
        'static let hideBlockedMessages = "jerkgram.Messages.HideBlockedMessages"',
        'hideBlockedMessages: jerkgramScopedBool(accountPeerId: accountPeerId, key: GhostBaseKey.hideBlockedMessages, defaultValue: false)',
        'static let hideBlockedReactions = "jerkgram.Messages.HideBlockedReactions"',
        'var hideBlockedReactions: Bool',
        'hideBlockedReactions: jerkgramScopedBool(accountPeerId: accountPeerId, key: GhostBaseKey.hideBlockedReactions, defaultValue: false)',
        'GhostBaseKey.hideBlockedReactions: .bool(state.hideBlockedReactions)',
        '"Скрывать реакции заблокированных"',
        'state.hideBlockedReactions',
    ):
        if token not in settings:
            fail(f"OFF-by-default scoped settings contract missing: {token}")
    if 'GhostBase.Messages.HideBlockedReactions' in settings:
        fail("legacy unscoped STEP5 reaction key survived in Settings")

    # Registry is local presentation state only. It is updated on successful
    # block/unblock and synchronized from contacts.getBlocked results so peers
    # blocked before installing this build are covered too.
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

    # Main reaction buttons use a pure view projection. Source reaction
    # attributes stay untouched in Postbox, so unblock restores them naturally.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_REACTION_FILTER",
        "jerkgramFilteredReactionsForBlockedPeers(",
        "reactions.recentPeers.filter",
        "reactions.topPeers.filter",
        "return MessageReaction(",
        "return ReactionsMessageAttribute(",
    ):
        if token not in reactions:
            fail(f"reaction projection helper missing: {token}")

    helper_start = reactions.find("JERKGRAM_BUILD132_BLOCKED_REACTION_FILTER")
    helper_end = reactions.find("public func mergedMessageReactions", helper_start)
    if helper_start < 0 or helper_end <= helper_start:
        fail("reaction projection helper bounds malformed")
    helper_window = reactions[helper_start:helper_end]
    for forbidden in (
        "transaction.updateMessage",
        "withUpdatedBlockedReaction",
        "UserDefaults.standard.set(",
    ):
        if forbidden in helper_window:
            fail(f"reaction source mutation leaked into projection helper: {forbidden}")

    # Every known 12.9.2 chat renderer that directly builds reaction UI opts
    # into the same projection helper. Group/supergroup-only is centralized.
    for text, label in (
        (footer, "footer"),
        (sticker, "sticker"),
        (instant_video, "instant video"),
        (animated_sticker, "animated sticker"),
        (rich_data, "rich data bubble"),
    ):
        for token in (
            "JERKGRAM_BUILD132_BLOCKED_REACTION_UI_FILTER",
            "jerkgramFilteredReactionsForBlockedPeers(",
            'UserDefaults.standard.bool(forKey: "jerkgram.Messages.HideBlockedReactions")',
        ):
            if token not in text:
                fail(f"{label} reaction filtering missing: {token}")

    for token in (
        "peer is TelegramGroup",
        "case .group = channel.info",
    ):
        if token not in reactions:
            fail(f"group/supergroup-only guard missing: {token}")

    # The full reaction peer list has a second projection at its state boundary:
    # initial recentPeers and every paginated API page are filtered, without
    # modifying the message's stored ReactionsMessageAttribute.
    for token in (
        "JERKGRAM_BUILD132_BLOCKED_REACTION_LIST_INITIAL_FILTER",
        "jerkgramFilteredReactionsForBlockedPeers(",
        "JERKGRAM_BUILD132_BLOCKED_REACTION_LIST_PAGE_FILTER",
        "jerkgramBuild132IsGroupOrSupergroup(chatPeer)",
        "JerkgramBlockedPeerRegistry.snapshot()",
        "jerkgramBlockedReactionPeerIds.contains(peer.id)",
        'forKey: "jerkgram.Messages.HideBlockedReactions"',
    ):
        if token not in reaction_state:
            fail(f"reaction-list filtering missing: {token}")

    # STEP5 is presentation-only. Do not add a persistence layer for filtered
    # reactions or private-chat special cases.
    for source, label in (
        (patcher, "main patcher"),
        (list_patcher, "list patcher"),
        (rich_patcher, "rich-data patcher"),
    ):
        if "JERKGRAM_BUILD132_BLOCKED_REACTION_PERSIST" in source:
            fail(f"reaction persistence/mutation forbidden in {label}")
        if "rglob(" in source or ".glob(" in source or "os.walk(" in source:
            fail(f"broad source discovery forbidden in {label}")
        if 'GhostBase.Messages.HideBlockedReactions' in source:
            fail(f"legacy reaction settings namespace survived in {label}")

    for rel in (SETTINGS, BLOCKED, BLOCKED_CONTEXT, REACTIONS, FOOTER, STICKER, INSTANT_VIDEO, ANIMATED_STICKER):
        if str(rel) not in patcher:
            fail(f"main patcher not bound to exact owner: {rel}")
    if str(REACTION_STATE) not in list_patcher:
        fail(f"list patcher not bound to exact owner: {REACTION_STATE}")
    if str(RICH_DATA) not in rich_patcher:
        fail(f"rich-data patcher not bound to exact owner: {RICH_DATA}")

    print("[Build132 blocked reactions verify] PASS: both toggles OFF + scoped Messages owner + synced registry + reversible group-only reaction buttons/list projection")


if __name__ == "__main__":
    main()
