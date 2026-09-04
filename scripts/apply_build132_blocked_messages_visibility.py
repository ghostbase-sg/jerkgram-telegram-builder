#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

SETTINGS = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
ATTRIBUTE = Path("submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift")
BLOCKED = Path("submodules/TelegramCore/Sources/TelegramEngine/Privacy/BlockedPeers.swift")
STATE = Path("submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift")
HISTORY = Path("submodules/TelegramUI/Sources/ChatHistoryEntriesForView.swift")
POSTBOX_HISTORY = Path("submodules/Postbox/Sources/MessageHistoryTable.swift")


def fail(message: str) -> None:
    print(f"[build132-blocked-messages] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(root: Path, rel: Path) -> str:
    path = root / rel
    if not path.is_file():
        fail(f"missing exact owner: {rel}")
    return path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        fail(f"expected one anchor for {label}, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_attribute(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE"
    if marker in text:
        return text

    text = replace_once(
        text,
        "    public let deletedAt: Int32\n",
        "    public let deletedAt: Int32\n    // MARK: JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE\n    public let isBlockedHidden: Bool\n",
        "blocked-hidden property",
    )
    text = replace_once(
        text,
        "    public init(originalText: String?, editHistoryTexts: [String], editHistoryDates: [String], isDeleted: Bool, deletedAt: Int32) {\n",
        "    public init(originalText: String?, editHistoryTexts: [String], editHistoryDates: [String], isDeleted: Bool, deletedAt: Int32, isBlockedHidden: Bool = false) {\n",
        "blocked-hidden initializer",
    )
    text = replace_once(
        text,
        "        self.deletedAt = deletedAt\n    }\n\n    required public init(decoder: PostboxDecoder) {\n",
        "        self.deletedAt = deletedAt\n        self.isBlockedHidden = isBlockedHidden\n    }\n\n    required public init(decoder: PostboxDecoder) {\n",
        "blocked-hidden initializer assignment",
    )
    text = replace_once(
        text,
        "        self.deletedAt = decoder.decodeInt32ForKey(\"dat\", orElse: 0)\n",
        "        self.deletedAt = decoder.decodeInt32ForKey(\"dat\", orElse: 0)\n        self.isBlockedHidden = decoder.decodeInt32ForKey(\"ibh\", orElse: 0) != 0\n",
        "blocked-hidden decode",
    )
    text = replace_once(
        text,
        "        encoder.encodeInt32(self.deletedAt, forKey: \"dat\")\n",
        "        encoder.encodeInt32(self.deletedAt, forKey: \"dat\")\n        encoder.encodeInt32(self.isBlockedHidden ? 1 : 0, forKey: \"ibh\")\n",
        "blocked-hidden encode",
    )

    # Preserve the new bit when the old GhostBase edit/delete helpers rebuild
    # the attribute. Existing call sites remain source-compatible because the
    # new initializer parameter has a default value.
    text = text.replace(
        "            deletedAt: self.deletedAt\n        )",
        "            deletedAt: self.deletedAt,\n            isBlockedHidden: self.isBlockedHidden\n        )",
    )
    text = text.replace(
        "            deletedAt: deletedAt\n        )",
        "            deletedAt: deletedAt,\n            isBlockedHidden: self.isBlockedHidden\n        )",
    )

    anchor = "    public func withUpdatedDeleted(isDeleted: Bool, deletedAt: Int32) -> GhostBaseMessageAttribute {\n"
    start = text.find(anchor)
    if start < 0:
        fail("withUpdatedDeleted helper missing after attribute patch")
    closing = text.find("\n    }\n}", start)
    if closing < 0:
        fail("GhostBaseMessageAttribute closing anchor missing")
    helper = '''\n    public func withUpdatedBlockedHidden(isBlockedHidden: Bool) -> GhostBaseMessageAttribute {\n        return GhostBaseMessageAttribute(\n            originalText: self.originalText,\n            editHistoryTexts: self.editHistoryTexts,\n            editHistoryDates: self.editHistoryDates,\n            isDeleted: self.isDeleted,\n            deletedAt: self.deletedAt,\n            isBlockedHidden: isBlockedHidden\n        )\n    }\n'''
    text = text[: closing + len("\n    }")] + helper + text[closing + len("\n    }") :]
    return text


def patch_settings(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_HIDE_BLOCKED_MESSAGES_SETTING"
    if marker in text:
        return text

    text = replace_once(
        text,
        '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n',
        '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n\n    // MARK: JERKGRAM_BUILD132_HIDE_BLOCKED_MESSAGES_SETTING\n    static let hideBlockedMessages = "GhostBase.Messages.HideBlockedMessages"\n',
        "settings key",
    )
    text = replace_once(
        text,
        "    var showEditHistory: Bool\n",
        "    var showEditHistory: Bool\n    var hideBlockedMessages: Bool\n",
        "settings state property",
    )
    text = replace_once(
        text,
        "            showEditHistory: ghostBaseBool(GhostBaseKey.showEditHistory, defaultValue: true),\n",
        "            showEditHistory: ghostBaseBool(GhostBaseKey.showEditHistory, defaultValue: true),\n            hideBlockedMessages: ghostBaseBool(GhostBaseKey.hideBlockedMessages, defaultValue: true),\n",
        "settings state load",
    )
    text = replace_once(
        text,
        "        UserDefaults.standard.set(self.showEditHistory, forKey: GhostBaseKey.showEditHistory)\n",
        "        UserDefaults.standard.set(self.showEditHistory, forKey: GhostBaseKey.showEditHistory)\n        UserDefaults.standard.set(self.hideBlockedMessages, forKey: GhostBaseKey.hideBlockedMessages)\n",
        "settings state save",
    )

    # Place the independent toggle immediately after Show Edit History. This is
    # bounded to the Messages page entry array, not a redesign of SettingsUI.
    pattern = re.compile(
        r'(\.toggle\(\s*[^\n]*\n(?:.*\n){0,12}?\s*GhostBaseKey\.showEditHistory,.*?\n\s*\),)',
        re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        fail("Messages ShowEditHistory toggle entry anchor missing")
    toggle = '''\n            .toggle(\n                1,\n                90,\n                GhostBaseKey.hideBlockedMessages,\n                "Скрывать сообщения заблокированных",\n                state.hideBlockedMessages\n            ),'''
    text = text[: match.end()] + toggle + text[match.end() :]

    handler_anchor = '''            case GhostBaseKey.showEditHistory:\n                updated.showEditHistory = value\n'''
    handler_new = handler_anchor + '''\n            case GhostBaseKey.hideBlockedMessages:\n                updated.hideBlockedMessages = value\n                UserDefaults.standard.set(value, forKey: GhostBaseKey.hideBlockedMessages)\n'''
    text = replace_once(text, handler_anchor, handler_new, "settings toggle handler")
    return text


def strip_build131(blocked: str, state: str) -> tuple[str, str]:
    # Remove the old helper blocks by their unique markers and exact next
    # declaration anchors. This is intentionally fail-closed.
    b_start = blocked.find("// MARK: JERKGRAM_BUILD131_BLOCKED_GROUP_AUTHOR_PURGE")
    if b_start >= 0:
        b_end = blocked.find("private func _internal_updatePeerIsBlocked", b_start)
        if b_end < 0:
            # Some 12.9.2 layouts place public wrapper first; retain the import
            # section and cut only through the helper's closing brace.
            call = "func jerkgramBuild131IsGroupOrSupergroup"
            helper2 = "private func jerkgramBuild131PurgeBlockedAuthorFromGroupHistories"
            if call not in blocked[b_start:] or helper2 not in blocked[b_start:]:
                fail("Build131 blocked helper block boundary missing")
            # Use the known ordinary block completion anchor as the conservative
            # end-of-helper search boundary.
            b_end = blocked.find("func _internal_updatePeer", b_start)
        if b_end < 0:
            fail("Build131 blocked helper end anchor missing")
        blocked = blocked[:b_start] + blocked[b_end:]

    blocked = blocked.replace(
        '''\n                            if isBlocked {\n                                jerkgramBuild131PurgeBlockedAuthorFromGroupHistories(transaction: transaction, authorId: peerId)\n                            }''',
        "",
    )

    s_start = state.find("// MARK: JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE")
    if s_start >= 0:
        s_end = state.find("func replayFinalState(", s_start)
        if s_end < 0:
            fail("Build131 ingress helper end anchor missing")
        state = state[:s_start] + state[s_end:]

    old_ingress = '''            case let .AddMessages(messagesValue, location):\n                var messages = messagesValue\n\n                // Drop before any thread/unread bookkeeping or Postbox insert.\n                // Therefore blocked authors cannot create a local badge either.\n                if case .UpperHistoryBlock = location {\n                    messages.removeAll { message in\n                        return jerkgramBuild131ShouldDropIncomingBlockedGroupMessage(transaction: transaction, message: message)\n                    }\n                }\n\n                if case .UpperHistoryBlock = location {\n'''
    if old_ingress in state:
        state = state.replace(
            old_ingress,
            '''            case let .AddMessages(messagesValue, location):\n                var messages = messagesValue\n\n                if case .UpperHistoryBlock = location {\n''',
            1,
        )
    return blocked, state


def patch_postbox(text: str) -> str:
    # The final implementation is deliberately anchored to Postbox's existing
    # author index used by removeAllMessagesWithAuthor. We refuse to emulate it
    # with a full-history scan.
    if "removeAllMessagesWithAuthor" not in text:
        fail("Postbox author-index implementation not found in exact MessageHistoryTable owner")
    if "allIndicesWithAuthor" not in text:
        fail("Postbox allIndicesWithAuthor index anchor missing")
    fail("Postbox author-index updater anchor must be finalized before materialized writes")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_build132_blocked_messages_visibility.py <materialized-source-root>")
    root = Path(sys.argv[1]).expanduser().resolve()

    originals = {
        SETTINGS: read(root, SETTINGS),
        ATTRIBUTE: read(root, ATTRIBUTE),
        BLOCKED: read(root, BLOCKED),
        STATE: read(root, STATE),
        HISTORY: read(root, HISTORY),
        POSTBOX_HISTORY: read(root, POSTBOX_HISTORY),
    }

    # Prepare every transform in memory first. Any missing anchor aborts before
    # a single materialized source file is changed.
    settings = patch_settings(originals[SETTINGS])
    attribute = patch_attribute(originals[ATTRIBUTE])
    blocked, state = strip_build131(originals[BLOCKED], originals[STATE])
    _ = settings, attribute, blocked, state, originals[HISTORY]
    patch_postbox(originals[POSTBOX_HISTORY])

    fail("unreachable: STEP4 patcher must not write until Postbox updater is finalized")


if __name__ == "__main__":
    main()
