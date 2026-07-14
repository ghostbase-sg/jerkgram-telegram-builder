#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / (
    "work/swiftgram-src/submodules/TelegramUI/Sources/"
    "ChatInterfaceStateContextMenus.swift"
)

text = FILE.read_text()

old_marker = (
    "        // MARK: GhostBase v1.0W "
    "forward without author action\n"
)

start = text.find(old_marker)

if start != -1:
    end_anchor = (
        "        if data.messageActions.options.contains("
        ".sendScheduledNow) {"
    )
    end = text.find(end_anchor, start)

    if end == -1:
        raise RuntimeError(
            "[v1.0W forward official] old action end missing"
        )

    text = text[:start] + text[end:]

marker = (
    "        // MARK: GhostBase v1.0W "
    "official forward without author\n"
)

anchor = (
    "        if data.messageActions.options.contains("
    ".sendScheduledNow) {"
)

block = '''        // MARK: GhostBase v1.0W official forward without author
        let ghostBaseForwardWithoutAuthor = (
            UserDefaults.standard.object(
                forKey: "GhostBase.Messages.ForwardWithoutAuthor"
            ) as? Bool
        ) ?? true

        if ghostBaseForwardWithoutAuthor,
           data.messageActions.options.contains(.forward) {
            actions.append(.action(ContextMenuActionItem(
                text: "Переслать без автора",
                icon: { theme in
                    generateTintedImage(
                        image: UIImage(
                            bundleImageName:
                                "Chat/Context Menu/Forward"
                        ),
                        color: theme.actionSheet.primaryTextColor
                    )
                },
                action: { _, f in
                    if let chatController =
                        interfaceInteraction.chatController()
                            as? ChatControllerImpl {
                        let targetMessages =
                            selectAll
                            ? messages
                            : [message]

                        chatController.forwardMessages(
                            messageIds: targetMessages.map { $0.id },
                            options: ChatInterfaceForwardOptionsState(
                                hideNames: true,
                                hideCaptions: false,
                                unhideNamesOnCaptionChange: false
                            ),
                            resetCurrent: true
                        )
                    }

                    f(.dismissWithoutContent)
                }
            )))
        }

'''

if marker not in text:
    if anchor not in text:
        raise RuntimeError(
            "[v1.0W forward official] insertion anchor missing"
        )

    text = text.replace(anchor, block + anchor, 1)

FILE.write_text(text)

print("[v1.0W forward official] applied")
