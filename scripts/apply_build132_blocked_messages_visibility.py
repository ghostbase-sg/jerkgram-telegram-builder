#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent / "apply_build132_blocked_messages_visibility_base.py"

spec = importlib.util.spec_from_file_location("build132_blocked_messages_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"[build132-blocked-messages] cannot load base patcher: {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

base_patch_history = base.patch_history


def matching_swift_brace(text: str, opening: int) -> int:
    depth = 0
    i = opening
    state = "code"
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if char == '"':
                state = "string"
            elif char == "/" and nxt == "/":
                state = "line"
                i += 1
            elif char == "/" and nxt == "*":
                state = "block"
                i += 1
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return i
        elif state == "string":
            if char == "\\":
                i += 1
            elif char == '"':
                state = "code"
        elif state == "line":
            if char == "\n":
                state = "code"
        elif state == "block" and char == "*" and nxt == "/":
            state = "code"
            i += 1
        i += 1
    base.fail("unterminated Swift block while removing Build131 ingress gate")


def patch_settings(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_HIDE_BLOCKED_MESSAGES_SETTING"
    if marker in text:
        return text

    text = base.replace_once(
        text,
        '    static let showEditHistory = "jerkgram.Messages.ShowEditHistory"\n',
        '    static let showEditHistory = "jerkgram.Messages.ShowEditHistory"\n\n'
        '    // MARK: JERKGRAM_BUILD132_HIDE_BLOCKED_MESSAGES_SETTING\n'
        '    static let hideBlockedMessages = "jerkgram.Messages.HideBlockedMessages"\n',
        "settings key",
    )
    text = base.replace_once(
        text,
        "    var showEditHistory: Bool\n",
        "    var showEditHistory: Bool\n    var hideBlockedMessages: Bool\n",
        "settings state property",
    )
    text = base.replace_once(
        text,
        "            showEditHistory: jerkgramScopedBool(accountPeerId: accountPeerId, key: GhostBaseKey.showEditHistory, defaultValue: true),\n",
        "            showEditHistory: jerkgramScopedBool(accountPeerId: accountPeerId, key: GhostBaseKey.showEditHistory, defaultValue: true),\n"
        "            hideBlockedMessages: jerkgramScopedBool(accountPeerId: accountPeerId, key: GhostBaseKey.hideBlockedMessages, defaultValue: true),\n",
        "settings state load",
    )
    text = base.replace_once(
        text,
        "        GhostBaseKey.showEditHistory: .bool(state.showEditHistory),\n",
        "        GhostBaseKey.showEditHistory: .bool(state.showEditHistory),\n"
        "        GhostBaseKey.hideBlockedMessages: .bool(state.hideBlockedMessages),\n",
        "settings state values",
    )
    text = base.replace_once(
        text,
        "            .info(1, strings.savedDataHint),\n",
        '''            .toggle(
                1,
                90,
                GhostBaseKey.hideBlockedMessages,
                "Скрывать сообщения заблокированных",
                state.hideBlockedMessages
            ),
            .info(1, strings.savedDataHint),
''',
        "Messages hide-blocked toggle row",
    )
    text = base.replace_once(
        text,
        '''            case GhostBaseKey.showEditHistory:
                updated.showEditHistory = value
''',
        '''            case GhostBaseKey.showEditHistory:
                updated.showEditHistory = value

            case GhostBaseKey.hideBlockedMessages:
                updated.hideBlockedMessages = value
''',
        "settings toggle handler",
    )
    return text


def patch_attribute(text: str) -> str:
    marker = "// MARK: JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE"
    if marker in text:
        return text

    text = base.replace_once(
        text,
        "    public let deletedAt: Int32\n",
        "    public let deletedAt: Int32\n    // MARK: JERKGRAM_BUILD132_BLOCKED_HIDDEN_ATTRIBUTE\n    public let isBlockedHidden: Bool\n",
        "blocked-hidden property",
    )
    text = base.replace_once(
        text,
        "        deletedAt: Int32,\n        originalEntities: [MessageTextEntity] = [],\n",
        "        deletedAt: Int32,\n        isBlockedHidden: Bool = false,\n        originalEntities: [MessageTextEntity] = [],\n",
        "Build123 blocked-hidden initializer",
    )
    text = base.replace_once(
        text,
        "        self.deletedAt = deletedAt\n    }\n\n    required public init(decoder: PostboxDecoder) {\n",
        "        self.deletedAt = deletedAt\n        self.isBlockedHidden = isBlockedHidden\n    }\n\n    required public init(decoder: PostboxDecoder) {\n",
        "blocked-hidden initializer assignment",
    )
    text = base.replace_once(
        text,
        '        self.deletedAt = decoder.decodeInt32ForKey("dat", orElse: 0)\n',
        '        self.deletedAt = decoder.decodeInt32ForKey("dat", orElse: 0)\n        self.isBlockedHidden = decoder.decodeInt32ForKey("ibh", orElse: 0) != 0\n',
        "blocked-hidden decode",
    )
    text = base.replace_once(
        text,
        '        encoder.encodeInt32(self.deletedAt, forKey: "dat")\n',
        '        encoder.encodeInt32(self.deletedAt, forKey: "dat")\n        encoder.encodeInt32(self.isBlockedHidden ? 1 : 0, forKey: "ibh")\n',
        "blocked-hidden encode",
    )
    text = base.replace_once(
        text,
        "            deletedAt: self.deletedAt,\n            originalEntities: self.originalEntities.isEmpty ? entities : self.originalEntities,\n",
        "            deletedAt: self.deletedAt,\n            isBlockedHidden: self.isBlockedHidden,\n            originalEntities: self.originalEntities.isEmpty ? entities : self.originalEntities,\n",
        "preserve blocked-hidden in edit-history helper",
    )
    text = base.replace_once(
        text,
        "            deletedAt: deletedAt,\n            originalEntities: self.originalEntities,\n",
        "            deletedAt: deletedAt,\n            isBlockedHidden: self.isBlockedHidden,\n            originalEntities: self.originalEntities,\n",
        "preserve blocked-hidden in delete helper",
    )
    text = base.replace_once(
        text,
        '''    public func withUpdatedDeleted(isDeleted: Bool, deletedAt: Int32) -> GhostBaseMessageAttribute {
        return GhostBaseMessageAttribute(
            originalText: self.originalText,
            editHistoryTexts: self.editHistoryTexts,
            editHistoryDates: self.editHistoryDates,
            isDeleted: isDeleted,
            deletedAt: deletedAt,
            isBlockedHidden: self.isBlockedHidden,
            originalEntities: self.originalEntities,
            editHistoryEntities: self.editHistoryEntities,
            editHistorySnapshots: self.editHistorySnapshots
        )
    }
''',
        '''    public func withUpdatedDeleted(isDeleted: Bool, deletedAt: Int32) -> GhostBaseMessageAttribute {
        return GhostBaseMessageAttribute(
            originalText: self.originalText,
            editHistoryTexts: self.editHistoryTexts,
            editHistoryDates: self.editHistoryDates,
            isDeleted: isDeleted,
            deletedAt: deletedAt,
            isBlockedHidden: self.isBlockedHidden,
            originalEntities: self.originalEntities,
            editHistoryEntities: self.editHistoryEntities,
            editHistorySnapshots: self.editHistorySnapshots
        )
    }

    public func withUpdatedBlockedHidden(isBlockedHidden: Bool) -> GhostBaseMessageAttribute {
        return GhostBaseMessageAttribute(
            originalText: self.originalText,
            editHistoryTexts: self.editHistoryTexts,
            editHistoryDates: self.editHistoryDates,
            isDeleted: self.isDeleted,
            deletedAt: self.deletedAt,
            isBlockedHidden: isBlockedHidden,
            originalEntities: self.originalEntities,
            editHistoryEntities: self.editHistoryEntities,
            editHistorySnapshots: self.editHistorySnapshots
        )
    }
''',
        "blocked-hidden updater",
    )
    return text


def patch_state(text: str) -> str:
    old_marker = "// MARK: JERKGRAM_BUILD131_BLOCKED_GROUP_INGRESS_GATE"
    old_helper = "jerkgramBuild131ShouldDropIncomingBlockedGroupMessage"
    new_marker = "// MARK: JERKGRAM_BUILD132_BLOCKED_MESSAGE_INGRESS_ANNOTATION"

    if old_helper in text:
        if text.count(old_helper) < 1:
            base.fail("Build131 ingress helper token unexpectedly missing")
        function_token = "private func jerkgramBuild131ShouldDropIncomingBlockedGroupMessage"
        function_pos = text.find(function_token)
        if function_pos < 0:
            base.fail("Build131 ingress helper declaration missing")
        marker_pos = text.rfind(old_marker, max(0, function_pos - 2000), function_pos)
        start = marker_pos if marker_pos >= 0 else text.rfind("\n", 0, function_pos) + 1
        opening = text.find("{", function_pos)
        if opening < 0:
            base.fail("Build131 ingress helper opening brace missing")
        closing = matching_swift_brace(text, opening)
        end = closing + 1
        while end < len(text) and text[end] in "\r\n":
            end += 1
        text = text[:start] + base.NEW_STATE_HELPER + text[end:]
    elif new_marker not in text:
        base.fail("neither Build131 ingress helper nor Build132 annotation helper found")

    case_token = "case let .AddMessages(messagesValue, location):"
    case_pos = text.find(case_token)
    if case_pos < 0:
        base.fail("AddMessages ingress owner missing")

    old_call = "jerkgramBuild131ShouldDropIncomingBlockedGroupMessage(transaction: transaction, message: message)"
    call_pos = text.find(old_call, case_pos)
    if call_pos >= 0:
        if_token = "if case .UpperHistoryBlock = location {"
        block_start = text.rfind(if_token, case_pos, call_pos)
        if block_start < 0:
            base.fail("Build131 ingress drop owner block missing")
        line_start = text.rfind("\n", 0, block_start) + 1
        opening = text.find("{", block_start)
        closing = matching_swift_brace(text, opening)
        replacement = '''                if case .UpperHistoryBlock = location {
                    messages = messages.map { message in
                        jerkgramBuild132MarkIncomingBlockedGroupMessage(
                            transaction: transaction,
                            message: message
                        )
                    }
                }
'''
        end = closing + 1
        if end < len(text) and text[end] == "\r":
            end += 1
        if end < len(text) and text[end] == "\n":
            end += 1
        text = text[:line_start] + replacement + text[end:]

    tail = text[case_pos:]
    if "jerkgramBuild132MarkIncomingBlockedGroupMessage(" not in tail:
        base.fail("Build132 ingress annotation call missing after cleanup")
    for forbidden in (old_helper, old_marker, "messages.removeAll { message in"):
        if forbidden in text:
            base.fail(f"destructive Build131 ingress token survived: {forbidden}")
    return text


def patch_history(text: str) -> str:
    text = base_patch_history(text)
    old = '"GhostBase.Messages.HideBlockedMessages"'
    new = '"jerkgram.Messages.HideBlockedMessages"'
    if old in text:
        text = text.replace(old, new)
    if new not in text:
        base.fail("current hide-blocked history key missing after patch")
    return text


base.patch_settings = patch_settings
base.patch_attribute = patch_attribute
base.patch_state = patch_state
base.patch_history = patch_history

if __name__ == "__main__":
    base.main()
