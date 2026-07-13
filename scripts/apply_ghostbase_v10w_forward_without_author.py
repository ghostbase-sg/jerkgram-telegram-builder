#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS = ROOT / (
    "work/swiftgram-src/submodules/SettingsUI/Sources/"
    "GhostBase/GhostBaseSettingsController.swift"
)

CONTEXT = ROOT / (
    "work/swiftgram-src/submodules/TelegramUI/Sources/"
    "ChatInterfaceStateContextMenus.swift"
)

settings = SETTINGS.read_text()
context = CONTEXT.read_text()

def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"[v1.0W forward] missing anchor: {label}")
    return text.replace(old, new, 1)

settings = once(
    settings,
    '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n',
    '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n'
    '    static let forwardWithoutAuthor = '
    '"GhostBase.Messages.ForwardWithoutAuthor"\n',
    "settings key"
)

settings = once(
    settings,
    "    var showEditHistory: Bool\n"
    "    var sendTextStyle: String\n",
    "    var showEditHistory: Bool\n"
    "    var forwardWithoutAuthor: Bool\n"
    "    var sendTextStyle: String\n",
    "state field"
)

settings = once(
    settings,
    "            showEditHistory: ghostBaseBool("
    "GhostBaseKey.showEditHistory, defaultValue: true),\n"
    "            sendTextStyle: ghostBaseString(\n",
    "            showEditHistory: ghostBaseBool("
    "GhostBaseKey.showEditHistory, defaultValue: true),\n"
    "            forwardWithoutAuthor: ghostBaseBool(\n"
    "                GhostBaseKey.forwardWithoutAuthor,\n"
    "                defaultValue: true\n"
    "            ),\n"
    "            sendTextStyle: ghostBaseString(\n",
    "state load"
)

save_anchor = (
    "        UserDefaults.standard.set("
    "self.showEditHistory, forKey: GhostBaseKey.showEditHistory)\n"
)

settings = once(
    settings,
    save_anchor,
    save_anchor
    + "        UserDefaults.standard.set(\n"
    + "            self.forwardWithoutAuthor,\n"
    + "            forKey: GhostBaseKey.forwardWithoutAuthor\n"
    + "        )\n",
    "state save"
)

toggle_anchor = (
    "            case GhostBaseKey.showEditHistory:\n"
    "                updated.showEditHistory = value\n"
)

settings = once(
    settings,
    toggle_anchor,
    toggle_anchor
    + "            case GhostBaseKey.forwardWithoutAuthor:\n"
    + "                updated.forwardWithoutAuthor = value\n",
    "toggle handler"
)

row_anchor = '''            .info(1, "Выключение функций не удаляет уже сохранённые данные."),

            .header(2, "Отправка текста"),
'''

row_new = '''            .info(1, "Выключение функций не удаляет уже сохранённые данные."),

            .header(2, "Пересылка"),
            .toggle(
                2,
                5,
                GhostBaseKey.forwardWithoutAuthor,
                "Показывать «Переслать без автора»",
                state.forwardWithoutAuthor
            ),

            .header(3, "Отправка текста"),
'''

settings = once(
    settings,
    row_anchor,
    row_new,
    "messages toggle row"
)

settings = settings.replace(
    '''            .selector(
                2,
                5,
''',
    '''            .selector(
                3,
                6,
''',
    1
)

settings = settings.replace(
    '''            .stylePreview(
                2,
                6,
''',
    '''            .stylePreview(
                3,
                7,
''',
    1
)

settings = settings.replace(
    '''            .info(
                2,
                "Стиль применяется после нажатия кнопки отправки."
''',
    '''            .info(
                3,
                "Стиль применяется после нажатия кнопки отправки."
''',
    1
)

history_block = '''        if ghostBaseShowEditHistory && !ghostBaseEditHistoryVersions.isEmpty {
            actions.append(.action(ContextMenuActionItem(text: "История", icon: { theme in
                return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Copy"), color: theme.actionSheet.primaryTextColor)
            }, action: { _, f in
                let contents = GhostBaseEditHistoryChatContents(baseMessage: messages[0], versions: ghostBaseEditHistoryVersions)
                let controller = context.sharedContext.makeChatController(context: context, chatLocation: .customChatContents, subject: .customChatContents(contents: contents), botStart: nil, mode: .standard(.previewing), params: nil)
                controller.title = "История"
                controllerInteraction.navigationController()?.pushViewController(controller)
                f(.default)
            })))
        }

'''

forward_block = history_block + '''        // MARK: GhostBase v1.0W forward without author action
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
                            bundleImageName: "Chat/Context Menu/Forward"
                        ),
                        color: theme.actionSheet.primaryTextColor
                    )
                },
                action: { _, f in
                    if let chatController =
                        interfaceInteraction.chatController()
                            as? ChatControllerImpl {
                        chatController.forwardMessages(
                            forceHideNames: true,
                            messages:
                                selectAll || isImage
                                ? messages
                                : [message],
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

context = once(
    context,
    history_block,
    forward_block,
    "context action"
)

SETTINGS.write_text(settings)
CONTEXT.write_text(context)

print("[v1.0W forward] settings toggle applied")
print("[v1.0W forward] native context action applied")
