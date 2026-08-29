#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
STATE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_FORWARD_SETTING_OWNER1"
MENU_MARKER = "// MARK: Jerkgram v1.2M BUILD124_SINGLE_FORWARD_ACCOUNT_SCOPE1"
TARGET_MARKER = "// MARK: Jerkgram v1.2M BUILD124_SINGLE_FORWARD_TARGET_SCOPE1"
BUILD123_MENU_MARKER = "BUILD123_PORTABLE_MENU_RESTRICTIONS1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 single forward] " + message)


OLD_STATE = '''        GhostBaseKey.showEditHistory: .bool(state.showEditHistory),
        ghostBaseSendTextStyleKey: .string(state.sendTextStyle),'''
NEW_STATE = '''        GhostBaseKey.showEditHistory: .bool(state.showEditHistory),
        // MARK: Jerkgram v1.2M BUILD124_FORWARD_SETTING_OWNER1
        GhostBaseKey.forwardWithoutAuthor: .bool(state.forwardWithoutAuthor),
        ghostBaseSendTextStyleKey: .string(state.sendTextStyle),'''

# Build108 canonicalized the legacy GhostBase defaults namespace to jerkgram.*.
# Build123 then replaced the permission gate below this load, but deliberately
# left the load/default itself intact. Match that exact materialized owner.
OLD_MENU = '''        let ghostBaseForwardWithoutAuthor = (
            UserDefaults.standard.object(
                forKey: "jerkgram.Messages.ForwardWithoutAuthor"
            ) as? Bool
        ) ?? true
'''
NEW_MENU = '''        // MARK: Jerkgram v1.2M BUILD124_SINGLE_FORWARD_ACCOUNT_SCOPE1
        // Settings are account-scoped since Build118. Resolve the same value
        // for focused single-message actions, with the canonical jerkgram.*
        // key retained only as migration/default fallback.
        let legacyForwardWithoutAuthorKey = "jerkgram.Messages.ForwardWithoutAuthor"
        let scopedForwardWithoutAuthorKey = "jerkgram.account.\\(context.account.peerId.toInt64()).setting.\\(legacyForwardWithoutAuthorKey)"
        let defaults = UserDefaults.standard
        let ghostBaseForwardWithoutAuthor = (
            defaults.object(forKey: scopedForwardWithoutAuthorKey) as? Bool
        ) ?? (
            defaults.object(forKey: legacyForwardWithoutAuthorKey) as? Bool
        ) ?? true
'''


OLD_TARGET_GATE = '''        if ghostBaseForwardWithoutAuthor,
           messages.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
               && !message.media.contains(where: {
                   $0 is TelegramMediaPaidContent
                   || $0 is TelegramMediaAction
                   || $0 is TelegramMediaExpiredContent
               })
           }) {'''


NEW_TARGET_GATE = '''        // MARK: Jerkgram v1.2M BUILD124_SINGLE_FORWARD_TARGET_SCOPE1
        // Long-pressing one album item must validate that one item. Validating
        // the whole visual message group hid this action when an unrelated
        // neighbour was expired or unsupported.
        let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]
        if ghostBaseForwardWithoutAuthor,
           jerkgramForwardWithoutAuthorTargets.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
               && !message.media.contains(where: {
                   $0 is TelegramMediaPaidContent
                   || $0 is TelegramMediaAction
                   || $0 is TelegramMediaExpiredContent
               })
           }) {'''


def patch_state_text(text: str) -> str:
    if STATE_MARKER in text:
        return text
    require(text.count(OLD_STATE) == 1, f"Build123 settings projection anchor count is {text.count(OLD_STATE)}")
    return text.replace(OLD_STATE, NEW_STATE, 1)


def patch_menu_text(text: str) -> str:
    updated = text
    require(updated.count(BUILD123_MENU_MARKER) == 1 or "data.messageActions.options.contains(.forward) survived portable gate" in updated, "Build123 portable single-message gate missing")
    if MENU_MARKER not in updated:
        require(updated.count(OLD_MENU) == 1, f"canonical Build123 single context setting owner count is {updated.count(OLD_MENU)}")
        updated = updated.replace(OLD_MENU, NEW_MENU, 1)
    if TARGET_MARKER not in updated:
        require(updated.count(OLD_TARGET_GATE) == 1, f"single-forward target gate count is {updated.count(OLD_TARGET_GATE)}")
        updated = updated.replace(OLD_TARGET_GATE, NEW_TARGET_GATE, 1)
    require(BUILD123_MENU_MARKER in updated or "data.messageActions.options.contains(.forward) survived portable gate" in updated, "Build123 portable restrictions were lost")
    return updated


def main() -> None:
    settings = SETTINGS.read_text(encoding="utf-8")
    menu = MENU.read_text(encoding="utf-8")
    # Build123 has no forwardWithoutAuthor state field; this is read from UserDefaults.
    menu = patch_menu_text(menu)
    MENU.write_text(menu, encoding="utf-8")
    print("[Build124 single forward] GREEN")
    print("[Build124 single forward] single long-press validates its actual target and remains independent of Telegram forward permission")


if __name__ == "__main__":
    main()
