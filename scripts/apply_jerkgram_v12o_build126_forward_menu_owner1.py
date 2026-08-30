#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
MARKER = "// MARK: Jerkgram v1.2O BUILD126_FORWARD_MENU_OWNER1"
OLD_MARKER = "// MARK: Jerkgram v1.2N BUILD125_SINGLE_FORWARD_DIRECT_ACTION1"
NATIVE_FORWARD = "        if data.messageActions.options.contains(.forward) {"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build126 forward menu] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    old_start = text.find(OLD_MARKER)
    native_start = text.find(NATIVE_FORWARD, old_start)
    require(old_start >= 0, "Build125 single-forward owner missing")
    require(native_start >= 0, "native forward owner missing after Build125 action")

    action_start = text.rfind("        ", 0, old_start)
    require(action_start >= 0, "Build125 action indentation missing")

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
                        forceHideNames: true,
                        messageIds: jerkgramBuild126ForwardWithoutAuthorTargets.map { $0.id },
                        options: ChatInterfaceForwardOptionsState(hideNames: true, hideCaptions: false, unhideNamesOnCaptionChange: false),
                        resetCurrent: true
                    )
                }
                f(.dismissWithoutContent)
            })))
        }

'''
    return text[:action_start] + replacement + text[native_start:]


def main() -> None:
    require(TARGET.is_file(), f"missing context-menu owner: {TARGET}")
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build126 forward menu] GREEN")


if __name__ == "__main__":
    main()
