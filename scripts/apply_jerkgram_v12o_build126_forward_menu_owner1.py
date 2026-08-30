#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
MARKER = "// MARK: Jerkgram v1.2O BUILD126_FORWARD_MENU_OWNER1"
OLD_MARKER = "// MARK: Jerkgram v1.2N BUILD125_SINGLE_FORWARD_DIRECT_ACTION1"
BROKEN_LEGACY_MARKER = "// MARK: Jerkgram v1.2M BUILD124_SINGLE_FORWARD_TARGET_SCOPE1"
NATIVE_FORWARD = "        if data.messageActions.options.contains(.forward) {"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build126 forward menu] " + message)


def balanced_if_end(text: str, if_start: int) -> int:
    brace_start = text.find("{", if_start)
    require(brace_start >= 0, "Build125 action opening brace missing")
    depth = 0
    for index in range(brace_start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    raise RuntimeError("[Build126 forward menu] Build125 action is unbalanced")


def remove_old_single_forward_action(text: str) -> str:
    marker_start = text.find(OLD_MARKER)
    require(marker_start >= 0, "Build125 single-forward owner missing")
    action_start = text.find("if ghostBaseForwardWithoutAuthor", marker_start)
    require(action_start >= 0, "Build125 single-forward gate missing")
    action_end = balanced_if_end(text, action_start)
    while action_end < len(text) and text[action_end] in " \\t\\r\\n":
        action_end += 1
    return text[:marker_start] + text[action_end:]


def remove_broken_legacy_single_forward_action(text: str) -> str:
    marker_start = text.find(BROKEN_LEGACY_MARKER)
    if marker_start < 0:
        return text
    next_owner = text.find("        if data.messageActions.options.contains(.sendScheduledNow) {", marker_start)
    require(next_owner >= 0, "broken Build124 single-forward action end missing")
    return text[:marker_start] + text[next_owner:]


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    text = remove_broken_legacy_single_forward_action(text)
    text = remove_old_single_forward_action(text)
    native_start = text.find(NATIVE_FORWARD)
    require(native_start >= 0, "native forward owner missing")

    replacement = '''        // MARK: Jerkgram v1.2O BUILD126_FORWARD_MENU_OWNER1
        // The sender below knows how to recreate protected media locally. Its
        // menu entry must therefore be available before Telegram's server
        // `.forward` capability gate hides the native row.
        let jerkgramPortableForwardTargets = selectAll || isImage ? messages : [message]
        let jerkgramNeedsPortableForward = jerkgramPortableForwardTargets.contains { message in
            if message.isCopyProtected() {
                return true
            }
            if let sourcePeer = message.forwardInfo?.author ?? message.effectiveAuthor {
                return sourcePeer.isCopyProtectionEnabled
            }
            return false
        }
        let jerkgramPortableForwardIsSafe = jerkgramPortableForwardTargets.allSatisfy { message in
            message.id.peerId.namespace != Namespaces.Peer.SecretChat
            && !message.media.contains(where: {
                $0 is TelegramMediaPaidContent
                || $0 is TelegramMediaAction
                || $0 is TelegramMediaExpiredContent
            })
        }
        if jerkgramNeedsPortableForward && jerkgramPortableForwardIsSafe {
            actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuForward, icon: { theme in
                return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Forward"), color: theme.actionSheet.primaryTextColor)
            }, action: { _, f in
                interfaceInteraction.forwardMessages(jerkgramPortableForwardTargets)
                f(.dismissWithoutContent)
            })))
        }

        // Rebuild the custom action from its owning single-message scope.
        // This does not depend on the native forward capability and passes the
        // exact pressed message to the existing force-hide sender.
        let jerkgramBuild126ForwardWithoutAuthorTargets = selectAll ? messages : [message]
        if ghostBaseForwardWithoutAuthor,
           jerkgramBuild126ForwardWithoutAuthorTargets.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
               && !message.media.contains(where: {
                   $0 is TelegramMediaPaidContent
                   || $0 is TelegramMediaAction
                   || $0 is TelegramMediaExpiredContent
               })
           }) {
            actions.append(.action(ContextMenuActionItem(text: "Переслать без автора", icon: { theme in
                return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Forward"), color: theme.actionSheet.primaryTextColor)
            }, action: { _, f in
                if let chatController = interfaceInteraction.chatController() as? ChatControllerImpl {
                    chatController.forwardMessages(
                        messageIds: jerkgramBuild126ForwardWithoutAuthorTargets.map { $0.id },
                        options: ChatInterfaceForwardOptionsState(hideNames: true, hideCaptions: false, unhideNamesOnCaptionChange: false),
                        resetCurrent: true
                    )
                }
                f(.dismissWithoutContent)
            })))
        }

'''
    return text[:native_start] + replacement + text[native_start:]


def main() -> None:
    require(TARGET.is_file(), f"missing context-menu owner: {TARGET}")
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build126 forward menu] GREEN")


if __name__ == "__main__":
    main()
