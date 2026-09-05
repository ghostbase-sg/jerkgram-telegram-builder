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
base.patch_history = patch_history

if __name__ == "__main__":
    base.main()
